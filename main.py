import sys

import PySide6.QtSvg  # SVG-Plugin für Icon-Dateien
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox
from PySide6.QtGui import QFontDatabase

from ui.splash_screen import run_startup_splash
from ui.main_window import MainWindow
from ui.login_dialog import LoginDialog
from ui.connection_assistant_dialog import ConnectionAssistantDialog
from ui.change_password_dialog import (
    ChangePasswordDialog
)
from ui.initial_setup_wizard import InitialSetupWizard
from ui.super_admin_recovery_dialog import (
    SuperAdminRecoveryDialog,
)
from config.permissions import is_super_administrator
from config.editions import requires_forced_password_change_on_login
from config.font_families import existing_font_paths
from database.database import Database
from database.access import (
    get_database,
    get_client_connection,
    get_host_server,
    set_client_connection,
    set_database,
    set_host_server,
)
from network.host_relay import start_host_relay_if_enabled, stop_host_relay
from ui.theme_manager import ThemeManager
from ui.wheel_guard import install_wheel_guard
from ui.mobiglas_message_box import install_mobiglas_message_boxes
import auth.session as user_session
from auth.remember_me import (
    load_remember_data,
    clear_remember_data,
)
from auth.app_restart import consume_language_restart_pending
from network.constants import (
    NETWORK_MODE_CLIENT,
    NETWORK_MODE_HOST,
    NETWORK_MODE_STANDALONE,
)
from network.host_server import HostServer
from network.network_state import get_network_state
from network.client_connect import restore_saved_client_connection
from config.editions import (
    enforce_standalone_network,
    has_feature,
)
from config.i18n import (
    DEFAULT_LANGUAGE,
    init_language_from_db,
    is_language_confirmed,
    normalize_language,
    save_language_choice,
    set_language,
    tr,
)
from ui.language_dialog import LanguageDialog


class SalvageTrackerApp:

    def __init__(self):
        self.app = QApplication(sys.argv)
        install_wheel_guard(self.app)
        self.db = None
        self.main_window = None
        self._network_mode = NETWORK_MODE_STANDALONE
        self._skip_client_restore = False
        self._initial_setup_created_username = None

    def _initialize_backend(self, splash):
        def schema_progress(current, total, name):
            splash.set_status(
                tr(
                    "splash.db_step",
                    name=name,
                    current=current,
                    total=total,
                )
            )

        splash.set_status(tr("splash.db_preparing"))
        self.db = Database(
            schema_progress=schema_progress,
        )
        set_database(self.db)
        init_language_from_db(self.db)

        splash.set_status(tr("splash.fonts_loading"))
        self._load_fonts()

        splash.set_status(tr("splash.ui_preparing"))
        ThemeManager.ensure_derived_themes()
        self._load_default_theme()
        install_mobiglas_message_boxes()

    def _load_fonts(self):
        for font_path in existing_font_paths():
            QFontDatabase.addApplicationFont(str(font_path))

    def _load_default_theme(self):
        settings = self.db.settings.get_app_settings()
        ThemeManager.apply_settings(settings)

    def _apply_user_theme(self, user):
        ThemeManager.apply_for_user(self.db, user["id"])

    def _load_saved_network_mode(self):
        enforce_standalone_network(self.db)
        settings = self.db.settings.get_app_settings()
        saved_mode = settings.get(
            "network_mode",
            NETWORK_MODE_STANDALONE,
        )
        if not has_feature("network.crew_edition", self.db):
            saved_mode = NETWORK_MODE_STANDALONE
        get_network_state().mode = saved_mode
        self._network_mode = saved_mode

    def _offer_connection_assistant(self):
        """Optional nach der Anmeldung — Standard: überspringen (Solo-Spiel)."""
        enforce_standalone_network(self.db)
        if not has_feature("network.crew_edition", self.db):
            self._network_mode = NETWORK_MODE_STANDALONE
            get_network_state().mode = NETWORK_MODE_STANDALONE
            return True

        settings = self.db.settings.get_app_settings()
        if settings.get("network_show_assistant", "0") == "0":
            self._load_saved_network_mode()
            return True

        dialog = ConnectionAssistantDialog(self.db)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return False

        self._network_mode = dialog.selected_mode
        get_network_state().mode = self._network_mode

        if self._network_mode == NETWORK_MODE_HOST and not has_feature(
            "network.host",
            self.db,
        ):
            self._network_mode = NETWORK_MODE_STANDALONE
            get_network_state().mode = NETWORK_MODE_STANDALONE
            return True

        if self._network_mode == NETWORK_MODE_CLIENT and not has_feature(
            "network.client",
            self.db,
        ):
            self._network_mode = NETWORK_MODE_STANDALONE
            get_network_state().mode = NETWORK_MODE_STANDALONE
            return True

        if self._network_mode == NETWORK_MODE_CLIENT:
            set_client_connection(dialog.client_connection)
            set_database(get_database())
            host_user = dialog.client_user
            if host_user:
                user_session.set_session(host_user, 0)
            return True

        self.db = get_database()
        return True

    def _try_restore_client_connection(self):
        """Gespeicherte Gast-Verbindung still wiederherstellen (ohne Assistent)."""
        if not has_feature("network.client", self.db):
            return

        if self._skip_client_restore:
            self._skip_client_restore = False
            return

        if self._network_mode != NETWORK_MODE_CLIENT:
            return

        if get_client_connection() is not None:
            return

        result = restore_saved_client_connection(self.db)
        if not result:
            return

        _connection, host_user = result
        if host_user:
            user_session.set_session(host_user, 0)
        self.db = get_database()

    def _start_host_server(self):
        if not has_feature("network.host", self.db):
            return
        if self._network_mode != NETWORK_MODE_HOST:
            return

        state = get_network_state()
        port = int(
            self.db.settings.get_app_setting(
                "network_host_port",
                str(state.host_port),
            )
        )
        join_code = self.db.settings.get_app_setting(
            "network_join_code",
            state.join_code,
        )
        use_tls = self.db.settings.get_app_setting(
            "network_use_tls",
            "1",
        ) == "1"

        server = HostServer(self.db)
        set_host_server(server)

        if not server.start(
            port=port,
            join_code=join_code or None,
            use_tls=use_tls,
        ):
            QMessageBox.warning(
                None,
                tr("main.host.title"),
                tr("main.host.start_failed"),
            )
            return

        start_host_relay_if_enabled(self.db, server)

    def _ensure_language_selected(self):
        init_language_from_db(self.db)

        if not is_language_confirmed(self.db):
            set_language(DEFAULT_LANGUAGE)
            dialog = LanguageDialog()
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return False
            save_language_choice(self.db, dialog.selected_language)
        else:
            init_language_from_db(self.db)

        return True

    def _run_initial_setup_if_needed(self):
        if self.db.is_initial_setup_complete():
            return True

        if not self._run_initial_setup_wizard():
            return False

        clear_remember_data()
        created_user = (
            self._initial_setup_created_username
            or "Administrator"
        )
        QMessageBox.information(
            None,
            tr("setup.complete.title"),
            tr("setup.complete.message", username=created_user),
        )
        return True

    def run(self):
        run_startup_splash(self._initialize_backend)

        if not self._ensure_language_selected():
            return 0

        if not self._run_initial_setup_if_needed():
            return 0

        language_restart = consume_language_restart_pending()

        while True:
            user = None

            if language_restart:
                language_restart = False
                self._load_saved_network_mode()
                if self._network_mode == NETWORK_MODE_CLIENT:
                    user = self._try_restore_client_session_after_restart()
                if not user:
                    user = self._try_remembered_login()

            if not user:
                user = self._try_remembered_login()

            if not user:
                user = self._login()

            if not user:
                break

            user = self.db.permissions.ensure_user_permissions(
                user
            )

            if not self.db.can_login_user(user):
                QMessageBox.warning(
                    None,
                    tr("main.login.blocked.title"),
                    tr("main.login.blocked.message"),
                )
                user_session.clear_session()
                continue

            if (
                user["must_change_password"]
                and requires_forced_password_change_on_login(
                    self.db
                )
            ):
                if not self._force_password_change(user):
                    user_session.clear_session()
                    continue
                user = user_session.get_user()
                if user:
                    user = (
                        self.db.permissions.ensure_user_permissions(
                            user
                        )
                    )
                    user_session.set_session(
                        user,
                        user_session.get_login_id(),
                    )

            if not self.db.can_use_main_application(user):
                if (
                    is_super_administrator(user)
                    and self.db.is_initial_setup_complete()
                ):
                    self._run_super_admin_recovery()
                    user_session.clear_session()
                    continue

                QMessageBox.information(
                    None,
                    tr("main.superadmin.title"),
                    tr("main.superadmin.message"),
                )
                user_session.clear_session()
                continue

            self._apply_user_theme(user)
            effective = self.db.settings.resolve_effective_settings(
                user["id"]
            )
            set_language(
                normalize_language(effective.get("language"))
            )
            self._load_saved_network_mode()

            if not self._offer_connection_assistant():
                user_session.clear_session()
                break

            self._try_restore_client_connection()

            connection = get_client_connection()
            is_client = (
                connection is not None
                and connection.is_connected
            )

            if is_client:
                user = user_session.get_user() or user

            self._start_host_server()
            user = self.db.permissions.ensure_user_permissions(
                user
            )
            self._show_main_window(user, is_client=is_client)

            exit_code = self.app.exec()

            if not self.main_window or (
                not self.main_window.logged_out
            ):
                host = get_host_server()
                if host and host.is_running():
                    host.stop()
                stop_host_relay()
                return exit_code

            self._network_mode = NETWORK_MODE_STANDALONE
            self.db = Database()
            set_database(self.db)
            set_client_connection(None)
            set_host_server(None)
            self.main_window = None

            state = get_network_state()
            state.connected = False
            state.host_running = False

    def _try_restore_client_session_after_restart(self):
        """Nach Sprach-Neustart: gespeicherte Crew-Verbindung still wiederherstellen."""
        if not has_feature("network.client", self.db):
            return None

        if self._network_mode != NETWORK_MODE_CLIENT:
            return None

        result = restore_saved_client_connection(self.db)
        if not result:
            return None

        _connection, host_user = result
        if not host_user:
            return None

        user_session.set_session(host_user, 0)
        self.db = get_database()
        return self.db.permissions.ensure_user_permissions(host_user)

    def _try_remembered_login(self):
        remember_data = load_remember_data()

        if not remember_data:
            return None

        user = self.db.authenticate_remember_token(
            remember_data["username"],
            remember_data["token"],
        )

        if not user:
            clear_remember_data()
            return None

        if not self.db.can_login_user(user):
            clear_remember_data()
            return None

        login_id = self.db.record_login(user["id"])
        user = self.db.permissions.attach_permissions_to_user(
            user
        )
        user_session.set_session(user, login_id)

        return user

    def _login(self):
        dialog = LoginDialog()

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None

        return dialog.user

    def _force_password_change(self, user):
        dialog = ChangePasswordDialog(
            user,
            required=True,
        )

        return (
            dialog.exec()
            == QDialog.DialogCode.Accepted
        )

    def _run_initial_setup_wizard(self):
        wizard = InitialSetupWizard()
        accepted = (
            wizard.exec()
            == QDialog.DialogCode.Accepted
        )
        self._initial_setup_created_username = (
            wizard.created_username
        )
        return accepted

    def _run_super_admin_recovery(self):
        dialog = SuperAdminRecoveryDialog()
        dialog.exec()

    def _show_main_window(self, user, *, is_client=False):
        try:
            self.main_window = MainWindow(
                user,
                on_logout=self._handle_logout,
                is_network_client=is_client,
            )
            self.main_window.show()
        except Exception as error:
            QMessageBox.critical(
                None,
                tr("main.start.error.title"),
                tr("main.start.error.message", error=error),
            )
            raise

    def _handle_logout(self):
        self._skip_client_restore = True

        connection = get_client_connection()
        if connection:
            connection.disconnect_from_host()
        set_client_connection(None)

        host = get_host_server()
        if host and host.is_running():
            host.stop()
        stop_host_relay()
        set_host_server(None)

        state = get_network_state()
        state.connected = False
        state.host_running = False

        local_db = Database()
        set_database(local_db)

        login_id = user_session.get_login_id()
        if login_id:
            local_db.record_logout(login_id)

        user = user_session.get_user()
        if user and not user.get("is_network_guest"):
            local_db.revoke_remember_tokens(user["id"])

        clear_remember_data()
        user_session.clear_session()
        self.db = local_db


def main():
    app = SalvageTrackerApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
