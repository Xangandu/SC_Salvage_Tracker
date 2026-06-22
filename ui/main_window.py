from ui.session_page import SessionPage
from ui.salvage_page import SalvagePage
from ui.statistics_page import StatisticsPage
from ui.history_page import HistoryPage
from PySide6.QtCore import Qt
from ui.refinery_page import RefineryPage
from ui.sales_page import SalesPage
from ui.admin_page import AdminPage
from ui.changelog_dialog import (
    ChangelogDialog
)

from config.version import (
    APP_NAME,
    format_version_nav_html,
)
from config.permissions import can_access

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget,
    QFrame,
)

from ui.dashboard_page import DashboardPage

from ui.dashboard_window import (
    DashboardWindow
)
from ui.mobiglas_window_frame import (
    MobiglasFramelessMixin,
    apply_mobiglas_window_frame,
)
from ui.page_layout import hud_divider


class MainWindow(MobiglasFramelessMixin, QMainWindow):

    def __init__(
        self,
        user,
        on_logout=None,
        is_network_client=False,
    ):
        super().__init__()

        from database.access import get_database

        db = get_database()
        if hasattr(db, "permissions"):
            user = db.permissions.ensure_user_permissions(user)

        self.current_user = user
        self.current_role = user["role_name"]
        self.on_logout = on_logout
        self.logged_out = False
        self.is_network_client = is_network_client
        self._wired_host_server = None
        self._wired_client_connection = None

        self.setObjectName("mainWindow")
        self.setWindowTitle(APP_NAME)
        self.resize(1600, 900)

        central_widget = QWidget()
        central_widget.setObjectName("mainCentral")
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        nav_widget = QWidget()
        nav_widget.setObjectName("navPanel")
        nav_widget.setMinimumWidth(248)
        nav_widget.setMaximumWidth(268)

        nav_layout = QVBoxLayout()
        nav_widget.setLayout(nav_layout)
        nav_layout.setSpacing(4)
        nav_layout.setContentsMargins(
            0,
            20,
            0,
            20
        )

        brand_block = QWidget()
        brand_block.setObjectName("navBrandBlock")
        brand_outer = QVBoxLayout(brand_block)
        brand_outer.setContentsMargins(12, 0, 12, 4)
        brand_outer.setSpacing(0)

        brand_card = QFrame()
        brand_card.setObjectName("navBrandCard")
        brand_layout = QVBoxLayout(brand_card)
        brand_layout.setContentsMargins(14, 14, 14, 12)
        brand_layout.setSpacing(0)

        title_primary = QLabel("SALVAGE")
        title_primary.setObjectName("navTitlePrimary")
        title_primary.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        title_secondary = QLabel("TRACKER")
        title_secondary.setObjectName("navTitleSecondary")
        title_secondary.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        user_panel = QFrame()
        user_panel.setObjectName("navUserPanel")
        user_panel_layout = QVBoxLayout(user_panel)
        user_panel_layout.setContentsMargins(10, 10, 10, 10)
        user_panel_layout.setSpacing(4)

        user_heading = QLabel("◆  BENUTZER")
        user_heading.setObjectName("navUserHeading")
        user_heading.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        display_name = (
            user.get("display_name")
            or user["username"]
        )
        self.user_label = QLabel(display_name)
        self.user_label.setObjectName("navUserName")
        self.user_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.role_label = QLabel(self.current_role.upper())
        self.role_label.setObjectName("navRoleBadge")
        self.role_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.network_label = QLabel("")
        self.network_label.setObjectName("navNetworkBadge")
        self.network_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )
        self.network_label.setWordWrap(True)
        self._update_network_label()

        brand_layout.addWidget(title_primary)
        brand_layout.addWidget(title_secondary)
        brand_layout.addSpacing(10)
        brand_layout.addLayout(hud_divider())
        brand_layout.addSpacing(10)

        user_panel_layout.addWidget(user_heading)
        user_panel_layout.addWidget(self.user_label)
        user_panel_layout.addWidget(self.role_label)
        user_panel_layout.addWidget(self.network_label)

        brand_layout.addWidget(user_panel)
        brand_outer.addWidget(brand_card)

        self.btn_dashboard = QPushButton("Übersicht")
        self.btn_dashboard.setObjectName(
            "navButton"
        )

        self.btn_session = QPushButton("Sitzung")
        self.btn_session.setObjectName("navButton")

        self.btn_refinery = QPushButton("Raffinerie")
        self.btn_refinery.setObjectName("navButton")

        self.btn_sales = QPushButton("Verkäufe")
        self.btn_sales.setObjectName("navButton")

        self.btn_stats = QPushButton("Auszahlung")
        self.btn_stats.setObjectName("navButton")

        self.btn_history = QPushButton("Historie")
        self.btn_history.setObjectName("navButton")

        self.btn_admin = QPushButton("Einstellungen")
        self.btn_admin.setObjectName("navButton")

        self.pages = QStackedWidget()
        self.pages.setObjectName("contentStack")

        self.dashboard_page = DashboardPage()

        self.dashboard_page.set_parent_window(
            self
        )

        self.dashboard_window = (
            DashboardWindow(
                self.dashboard_page
            )
        )

        self.dashboard_page.set_detached_window(
            self.dashboard_window
        )

        self.session_page = SessionPage(
            is_network_client=self.is_network_client,
        )
        self.refinery_page = RefineryPage()
        self.sales_page = SalesPage()
        self.salvage_page = SalvagePage()
        self.statistics_page = StatisticsPage()
        self.history_page = HistoryPage()
        self.admin_page = AdminPage()

        self.pages.addWidget(
            QWidget()
        )

        self.pages.addWidget(
            self.session_page
        )

        self.pages.addWidget(self.refinery_page)
        self.pages.addWidget(self.sales_page)
        self.pages.addWidget(self.salvage_page)
        self.pages.addWidget(self.statistics_page)
        self.pages.addWidget(self.history_page)
        self.pages.addWidget(self.admin_page)

        self.btn_dashboard.clicked.connect(
            self.toggle_dashboard_window
        )

        self.btn_session.clicked.connect(
            lambda: self.switch_page(
                self.session_page,
                self.btn_session
            )
        )

        self.btn_refinery.clicked.connect(
            lambda: self.switch_page(
                self.refinery_page,
                self.btn_refinery
            )
        )

        self.btn_sales.clicked.connect(
            lambda: self.switch_page(
                self.sales_page,
                self.btn_sales
            )
        )

        self.btn_stats.clicked.connect(
            lambda: self.switch_page(
                self.statistics_page,
                self.btn_stats
            )
        )

        self.btn_history.clicked.connect(
            lambda: self.switch_page(
                self.history_page,
                self.btn_history
            )
        )

        self.btn_admin.clicked.connect(
            lambda: self.switch_page(
                self.admin_page,
                self.btn_admin
            )
        )

        nav_layout.addWidget(brand_block)

        nav_divider = QFrame()
        nav_divider.setObjectName("navDivider")
        nav_divider.setFixedHeight(1)
        nav_layout.addSpacing(8)
        nav_layout.addWidget(nav_divider)
        nav_layout.addSpacing(8)

        self.nav_buttons = {
            "dashboard": self.btn_dashboard,
            "session": self.btn_session,
            "refinery": self.btn_refinery,
            "sales": self.btn_sales,
            "statistics": self.btn_stats,
            "history": self.btn_history,
            "settings": self.btn_admin,
        }

        for page_name, button in self.nav_buttons.items():
            nav_layout.addWidget(button)

        self._refresh_nav_visibility()

        version_label = QLabel(format_version_nav_html())
        version_label.setObjectName("versionLabel")

        version_label.setAlignment(
            Qt.AlignCenter
        )

        version_label.setTextFormat(
            Qt.RichText
        )

        version_label.setOpenExternalLinks(
            False
        )

        version_label.linkActivated.connect(
            self.show_changelog
        )

        nav_layout.addWidget(
            version_label
        )

        nav_layout.addStretch()

        main_layout.addWidget(nav_widget, 1)
        main_layout.addWidget(self.pages, 5)

        self.apply_permissions()

        start_page = self._default_page()
        start_button = self._button_for_page(
            start_page
        )

        self.set_active_button(start_button)
        self.pages.setCurrentWidget(start_page)

        title_bar = apply_mobiglas_window_frame(
            self,
            title=APP_NAME,
        )
        title_bar.add_action_button(
            "Abmelden",
            self.logout,
        )

        self._wire_network_events()

    def refresh_network_display(self):
        """Navigations-Anzeige und Client-/Host-UI aktualisieren."""
        self.apply_network_mode()

    def apply_network_mode(self):
        """Client-Modus und Seiten an aktuellen Verbindungszustand anpassen."""
        from database.access import get_client_connection

        connection = get_client_connection()
        is_client = (
            connection is not None
            and connection.is_connected
        )
        mode_changed = is_client != self.is_network_client

        if mode_changed:
            self.is_network_client = is_client
            self.session_page.set_network_client_mode(is_client)

        self._refresh_page_databases()
        self._wire_network_events()
        self._update_network_label()

        if mode_changed and is_client:
            self._on_network_data_changed()

    def _refresh_page_databases(self):
        from database.access import get_database

        db = get_database()
        for page in (
            self.session_page,
            self.salvage_page,
            self.refinery_page,
            self.sales_page,
            self.statistics_page,
            self.history_page,
            self.dashboard_page,
            self.admin_page,
        ):
            if hasattr(page, "db"):
                page.db = db

    def _wire_network_events(self):
        from database.access import get_client_connection, get_host_server

        connection = get_client_connection()
        if connection is not self._wired_client_connection:
            if self._wired_client_connection is not None:
                for signal, slot in (
                    (
                        self._wired_client_connection.disconnected,
                        self._on_client_disconnected,
                    ),
                    (
                        self._wired_client_connection.data_changed,
                        self._on_network_data_changed,
                    ),
                ):
                    try:
                        signal.disconnect(slot)
                    except (RuntimeError, TypeError):
                        pass

            self._wired_client_connection = connection
            if connection:
                connection.disconnected.connect(
                    self._on_client_disconnected
                )
                connection.data_changed.connect(
                    self._on_network_data_changed
                )

        server = get_host_server()
        if server is self._wired_host_server:
            return

        if self._wired_host_server is not None:
            old = self._wired_host_server
            for signal, slot in (
                (old.started, self._on_host_network_event),
                (old.stopped, self._on_host_network_event),
                (old.client_connected, self._on_host_network_event),
                (old.client_disconnected, self._on_host_network_event),
                (old.data_changed, self._on_network_data_changed),
            ):
                try:
                    signal.disconnect(slot)
                except (RuntimeError, TypeError):
                    pass

        self._wired_host_server = server
        if not server:
            return

        server.started.connect(self._on_host_network_event)
        server.stopped.connect(self._on_host_network_event)
        server.client_connected.connect(
            self._on_host_network_event
        )
        server.client_disconnected.connect(
            self._on_host_network_event
        )
        server.data_changed.connect(
            self._on_network_data_changed
        )

    def _on_host_network_event(self, *_args):
        self._update_network_label()
        if hasattr(self, "admin_page"):
            self.admin_page._refresh_network_tab()

    def _on_client_disconnected(self):
        self.apply_network_mode()

    def _update_network_label(self):
        from database.access import get_host_server
        from network.network_state import get_network_state

        state = get_network_state()
        if state.is_client():
            host = state.host_address or "Host"
            self.network_label.setText(
                f"◆ CLIENT · {host}:{state.host_port}"
            )
            self.network_label.setVisible(True)
            return

        server = get_host_server()
        if server and server.is_running():
            clients = len(state.connected_clients)
            addrs = ", ".join(server.addresses[:2])
            self.network_label.setText(
                f"◆ HOST · {addrs}:{server.port}\n"
                f"Code: {server.join_code} · "
                f"{clients} Client(s)"
            )
            self.network_label.setVisible(True)
            return

        if state.mode == "host" or state.host_running:
            self.network_label.setText(
                "◆ HOST · nicht aktiv"
            )
            self.network_label.setVisible(True)
            return

        self.network_label.setText("")

        self.network_label.setVisible(False)

    def _on_network_data_changed(self):
        self.session_page.refresh_session()
        self.salvage_page.load_session()
        self.refinery_page.load_data()
        self.sales_page.load_data()
        self.statistics_page.refresh_data()
        self.history_page.refresh_history()
        if self.dashboard_page.isVisible() or (
            self.dashboard_window.isVisible()
        ):
            self.dashboard_page.refresh_dashboard()

        self._update_network_label()

    def _default_page(self):
        if can_access(
            self.current_user,
            "session",
        ):
            return self.session_page

        if can_access(
            self.current_user,
            "statistics",
        ):
            return self.statistics_page

        return self.history_page

    def _button_for_page(self, page):
        mapping = {
            self.session_page: self.btn_session,
            self.refinery_page: self.btn_refinery,
            self.sales_page: self.btn_sales,
            self.statistics_page: self.btn_stats,
            self.history_page: self.btn_history,
            self.admin_page: self.btn_admin,
        }

        return mapping.get(
            page,
            self.btn_history,
        )

    def apply_permissions(self):
        pages = [
            (self.session_page, "session"),
            (self.salvage_page, "salvage"),
            (self.refinery_page, "refinery"),
            (self.sales_page, "sales"),
            (self.statistics_page, "statistics"),
            (self.history_page, "history"),
            (self.admin_page, "settings"),
            (self.dashboard_page, "dashboard"),
        ]

        for page, page_name in pages:
            if hasattr(page, "apply_permissions"):
                page.apply_permissions(
                    self.current_user,
                    page_name,
                )

        self._refresh_nav_visibility()

    def refresh_current_user_from_db(self):
        from database.access import get_database
        import auth.session as user_session

        if not self.current_user:
            return False

        db = get_database()
        refreshed = db.permissions.refresh_session_user(
            self.current_user["id"]
        )

        if not refreshed:
            return False

        self.current_user = refreshed
        self.current_role = refreshed["role_name"]
        self.user_label.setText(refreshed["username"])
        self.role_label.setText(refreshed["role_name"])
        self.apply_permissions()
        return True

    def _refresh_nav_visibility(self):
        for page_name, button in self.nav_buttons.items():
            button.setVisible(
                can_access(
                    self.current_user,
                    page_name,
                )
            )

    def _close_detached_dashboard(self):
        if not self.dashboard_window.isVisible():
            return

        if self.dashboard_page.is_ready_for_attach():
            self.dashboard_page.mark_as_embedded()

        self.dashboard_window.hide()

    def closeEvent(self, event):
        self._close_detached_dashboard()
        super().closeEvent(event)

    def logout(self):
        self.logged_out = True

        self._close_detached_dashboard()

        self.close()

        if self.on_logout:
            self.on_logout()

    def switch_page(
        self,
        page,
        button
    ):

        if page == self.dashboard_page:
            self.dashboard_page.apply_dashboard_layout()
            self.dashboard_page.refresh_dashboard()

        if page == self.salvage_page:
            self.salvage_page.load_session()

        if page == self.sales_page:
            self.sales_page.load_data()

        if page == self.session_page:
            self.session_page.refresh_session()

        if page == self.refinery_page:
            self.refinery_page.load_data()

        if page == self.statistics_page:
            self.statistics_page.refresh_data()

        if page == self.history_page:
            self.history_page.refresh_history()

        if page == self.admin_page:
            self.admin_page.refresh_data()

        self.pages.setCurrentWidget(page)

        self.set_active_button(button)

    def set_active_button(
        self,
        active_button
    ):
        buttons = list(self.nav_buttons.values())

        for button in buttons:

            button.setProperty(
                "active",
                False
            )

            button.style().unpolish(button)
            button.style().polish(button)

            button.update()

        active_button.setProperty(
            "active",
            True
        )

        active_button.style().unpolish(
            active_button
        )

        active_button.style().polish(
            active_button
        )
        active_button.update()

    def get_dashboard_page(self):

        return self.dashboard_page

    def is_dashboard_detached(self):

        return (
            self.dashboard_page
            .is_dashboard_detached()
        )

    def get_dashboard_mode(self):

        return (
            self.dashboard_page
            .get_dashboard_mode()
        )

    def has_detached_dashboard(self):

        return (
            self.dashboard_page
            .get_detached_window()
            is not None
        )

    def show_dashboard_window(self):

        self.dashboard_page.apply_permissions(
            self.current_user,
            "dashboard",
        )

        if (
            self.dashboard_page
            .is_ready_for_detach()
        ):

            self.dashboard_page.mark_as_detached()

        self.dashboard_window.show_dashboard()

        self.btn_dashboard.setText(
            "Übersicht ●"
        )

    def hide_dashboard_window(self):

        if (
            self.dashboard_page
            .is_ready_for_attach()
        ):

            self.dashboard_page.mark_as_embedded()

        self.dashboard_window.hide_dashboard()

        self.btn_dashboard.setText(
            "Übersicht ⧉"
        )

    def toggle_dashboard_window(self):

        if (
            self.dashboard_page
            .is_detached()
        ):

            self.hide_dashboard_window()

        else:

            self.show_dashboard_window()

    def get_detached_dashboard(self):

        return (
            self.dashboard_page
            .get_detached_window()
        )

    def set_detached_dashboard(
        self,
        window
    ):

        self.dashboard_page.set_detached_window(
            window
        )

    def clear_detached_dashboard(self):

        self.dashboard_page.clear_detached_window()

    def show_changelog(self):

        dialog = ChangelogDialog()

        dialog.exec()
