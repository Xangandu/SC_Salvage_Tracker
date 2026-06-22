"""Erstinstallation — Organisations-Administrator anlegen."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config.permissions import ROLE_ADMIN
from config.setup import SUPERADMIN_USERNAME
from config.version import format_version_subtitle
from database.access import get_database
from ui.mobiglas_window_frame import (
    MobiglasFramelessMixin,
    apply_mobiglas_window_frame,
)
from ui.page_layout import (
    add_form_field,
    hud_divider,
    primary_button,
    subsection_title,
)

_SETUP_STEPS = (
    "WILLKOMMEN",
    "ADMINISTRATOR",
    "ABSCHLUSS",
)


class InitialSetupWizard(MobiglasFramelessMixin, QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.db = get_database()
        self.created_username = None

        self.setObjectName("mobiglasDialog")
        self.setWindowTitle("Erstinstallation")
        self.setModal(True)
        self.resize(520, 680)

        outer = QVBoxLayout()
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(0)

        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(460)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 24)
        card_layout.setSpacing(12)

        logo = QLabel("MOBIGLAS")
        logo.setObjectName("loginLogo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        tagline = QLabel("ERSTINSTALLATION")
        tagline.setObjectName("loginTagline")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(logo)
        card_layout.addWidget(tagline)
        card_layout.addSpacing(4)
        card_layout.addLayout(hud_divider())

        self.step_indicator = QLabel()
        self.step_indicator.setObjectName("setupStepIndicator")
        self.step_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.step_indicator)

        self.stack = QStackedWidget()
        self.stack.setObjectName("setupWizardStack")
        self.stack.addWidget(self._build_welcome_page())
        self.stack.addWidget(self._build_admin_page())
        self.stack.addWidget(self._build_finish_page())
        card_layout.addWidget(self.stack, 1)

        card_layout.addLayout(hud_divider())

        self.back_button = QPushButton("ZURÜCK")
        self.back_button.setObjectName("secondaryAction")
        self.back_button.clicked.connect(self._go_back)

        self.next_button = primary_button("WEITER")
        self.next_button.clicked.connect(self._go_next)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        button_row.addWidget(self.back_button)
        button_row.addWidget(self.next_button, 1)
        card_layout.addLayout(button_row)

        card_row = QHBoxLayout()
        card_row.addStretch()
        card_row.addWidget(card)
        card_row.addStretch()

        version_footer = QLabel(format_version_subtitle(" · "))
        version_footer.setObjectName("setupVersionFooter")
        version_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        outer.addStretch(1)
        outer.addLayout(card_row)
        outer.addSpacing(12)
        outer.addWidget(version_footer)
        outer.addStretch(1)
        self.setLayout(outer)

        self._update_navigation()

        apply_mobiglas_window_frame(
            self,
            title="Erstinstallation",
            dialog=True,
            show_close=False,
        )

    def _build_welcome_page(self):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 4, 0, 0)
        page_layout.setSpacing(12)

        banner = QLabel(
            "ERSTINSTALLATION\n\n"
            f"Der Super-Administrator ({SUPERADMIN_USERNAME}) "
            "ist nur für diesen Setup-Lauf und Notfälle "
            "vorgesehen."
        )
        banner.setWordWrap(True)
        banner.setObjectName("warningBanner")
        banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_layout.addWidget(banner)

        info = QLabel(
            "Im nächsten Schritt legst du einen "
            "Organisations-Administrator an. Dieser Benutzer "
            "verwaltet danach Benutzer, Rollen und den "
            "normalen Betrieb.\n\n"
            "Nach Abschluss meldest du dich mit dem neuen "
            "Administrator an — nicht mehr mit dem "
            "Super-Administrator."
        )
        info.setWordWrap(True)
        info.setObjectName("mutedLabel")
        page_layout.addWidget(info)
        page_layout.addStretch()
        return page

    def _build_admin_page(self):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 4, 0, 0)
        page_layout.setSpacing(10)

        page_layout.addWidget(
            subsection_title("Organisations-Administrator")
        )

        hint = QLabel(
            f"Rolle: {ROLE_ADMIN} (fest)\n"
            "Der neue Benutzer setzt beim ersten Login "
            "ein eigenes Passwort."
        )
        hint.setWordWrap(True)
        hint.setObjectName("formLabel")
        page_layout.addWidget(hint)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Benutzername")
        add_form_field(
            page_layout,
            "Benutzername",
            self.username_input,
        )

        self.display_name_input = QLineEdit()
        self.display_name_input.setPlaceholderText(
            "Anzeigename (optional)"
        )
        add_form_field(
            page_layout,
            "Anzeigename",
            self.display_name_input,
        )

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText(
            "Passwort (mindestens 6 Zeichen)"
        )
        add_form_field(
            page_layout,
            "Passwort",
            self.password_input,
        )

        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setPlaceholderText(
            "Passwort wiederholen"
        )
        add_form_field(
            page_layout,
            "Passwort bestätigen",
            self.confirm_input,
        )

        page_layout.addStretch()
        return page

    def _build_finish_page(self):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 4, 0, 0)
        page_layout.setSpacing(12)

        page_layout.addWidget(subsection_title("Bereit"))

        self.finish_label = QLabel("")
        self.finish_label.setWordWrap(True)
        self.finish_label.setObjectName("mutedLabel")
        page_layout.addWidget(self.finish_label)

        success = QLabel("Erstinstallation abgeschlossen")
        success.setObjectName("setupSuccessLabel")
        success.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_layout.addWidget(success)

        page_layout.addStretch()
        return page

    def _admin_role_id(self):
        return self.db._get_role_id_by_name(ROLE_ADMIN)

    def _go_back(self):
        index = self.stack.currentIndex()

        if index <= 0:
            return

        self.stack.setCurrentIndex(index - 1)
        self._update_navigation()

    def _go_next(self):
        index = self.stack.currentIndex()

        if index == 0:
            self.stack.setCurrentIndex(1)
            self._update_navigation()
            self.username_input.setFocus()
            return

        if index == 1:
            if not self._create_org_administrator():
                return

            self.stack.setCurrentIndex(2)
            self._update_navigation()
            return

        if index == 2:
            self.accept()

    def _create_org_administrator(self):
        username = self.username_input.text().strip()
        display_name = (
            self.display_name_input.text().strip()
            or username
        )
        password = self.password_input.text()
        confirm = self.confirm_input.text()

        if not username:
            QMessageBox.warning(
                self,
                "Erstinstallation",
                "Bitte einen Benutzernamen eingeben.",
            )
            return False

        if username.lower() == SUPERADMIN_USERNAME.lower():
            QMessageBox.warning(
                self,
                "Erstinstallation",
                f"Der Benutzername „{SUPERADMIN_USERNAME}“ "
                "ist für den Super-Administrator reserviert.",
            )
            return False

        if len(password) < 6:
            QMessageBox.warning(
                self,
                "Erstinstallation",
                "Das Passwort muss mindestens "
                "6 Zeichen lang sein.",
            )
            return False

        if password != confirm:
            QMessageBox.warning(
                self,
                "Erstinstallation",
                "Die Passwörter stimmen nicht überein.",
            )
            return False

        role_id = self._admin_role_id()

        if role_id is None:
            QMessageBox.critical(
                self,
                "Erstinstallation",
                f"Die Rolle „{ROLE_ADMIN}“ wurde nicht "
                "gefunden. Bitte starte die Anwendung neu.",
            )
            return False

        try:
            self.db.create_user(
                username,
                password,
                role_id,
                display_name=display_name,
            )
        except ValueError as error:
            QMessageBox.warning(
                self,
                "Erstinstallation",
                str(error),
            )
            return False
        except Exception:
            QMessageBox.warning(
                self,
                "Erstinstallation",
                "Der Administrator konnte nicht angelegt "
                "werden. Der Benutzername existiert "
                "möglicherweise bereits.",
            )
            return False

        self.db.mark_initial_setup_complete()
        self.created_username = username

        self.finish_label.setText(
            f"Der Organisations-Administrator "
            f"„{username}“ wurde angelegt.\n\n"
            "Klicke auf „Fertig“ und melde dich danach "
            "mit dem neuen Administrator an."
        )
        return True

    def _update_navigation(self):
        index = self.stack.currentIndex()
        step_total = len(_SETUP_STEPS)
        step_name = _SETUP_STEPS[index]

        self.step_indicator.setText(
            f"SCHRITT {index + 1} · {step_total}  —  {step_name}"
        )

        self.back_button.setEnabled(index > 0)

        if index == 0:
            self.next_button.setText("WEITER")
        elif index == 1:
            self.next_button.setText("ADMINISTRATOR ANLEGEN")
        else:
            self.next_button.setText("FERTIG")

    def closeEvent(self, event):
        QMessageBox.warning(
            self,
            "Erstinstallation",
            "Die Erstinstallation muss abgeschlossen werden, "
            "bevor der Salvage Tracker genutzt werden kann.",
        )
        event.ignore()
