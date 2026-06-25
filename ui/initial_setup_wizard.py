"""Erstinstallation — Notfall-Zugang und Organisations-Administrator."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
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

from config.i18n import tr
from config.permissions import ROLE_ADMIN
from config.setup import DEFAULT_SUPERADMIN_PASSWORD, SUPERADMIN_USERNAME
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


class InitialSetupWizard(MobiglasFramelessMixin, QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.db = get_database()
        self.created_username = None

        self.setObjectName("mobiglasDialog")
        self.setWindowTitle(tr("setup.wizard.title"))
        self.setModal(True)
        self.resize(520, 720)

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

        tagline = QLabel(tr("setup.wizard.tagline"))
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
        self.stack.addWidget(self._build_emergency_page())
        self.stack.addWidget(self._build_admin_page())
        self.stack.addWidget(self._build_finish_page())
        card_layout.addWidget(self.stack, 1)

        card_layout.addLayout(hud_divider())

        self.back_button = QPushButton(tr("setup.button.back"))
        self.back_button.setObjectName("secondaryAction")
        self.back_button.clicked.connect(self._go_back)

        self.next_button = primary_button(tr("setup.button.next"))
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
            title=tr("setup.wizard.title"),
            dialog=True,
            show_close=False,
        )

    def _step_names(self):
        return (
            tr("setup.step.welcome"),
            tr("setup.step.emergency"),
            tr("setup.step.admin"),
            tr("setup.step.finish"),
        )

    def _build_welcome_page(self):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 4, 0, 0)
        page_layout.setSpacing(12)

        info = QLabel(tr("setup.welcome.info"))
        info.setWordWrap(True)
        info.setObjectName("mutedLabel")
        page_layout.addWidget(info)
        page_layout.addStretch()
        return page

    def _build_emergency_page(self):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 4, 0, 0)
        page_layout.setSpacing(10)

        page_layout.addWidget(
            subsection_title(tr("setup.emergency.title"))
        )

        banner = QLabel(
            tr(
                "setup.emergency.banner",
                username=SUPERADMIN_USERNAME,
            )
        )
        banner.setWordWrap(True)
        banner.setObjectName("warningBanner")
        banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_layout.addWidget(banner)

        info = QLabel(tr("setup.emergency.info"))
        info.setWordWrap(True)
        info.setObjectName("mutedLabel")
        page_layout.addWidget(info)

        self.superadmin_password_input = QLineEdit()
        self.superadmin_password_input.setEchoMode(QLineEdit.Password)
        add_form_field(
            page_layout,
            tr("setup.emergency.password"),
            self.superadmin_password_input,
        )

        self.superadmin_confirm_input = QLineEdit()
        self.superadmin_confirm_input.setEchoMode(QLineEdit.Password)
        add_form_field(
            page_layout,
            tr("setup.emergency.confirm"),
            self.superadmin_confirm_input,
        )

        self.superadmin_note_checkbox = QCheckBox(
            tr("setup.emergency.note_checkbox")
        )
        self.superadmin_note_checkbox.setObjectName("formLabel")
        page_layout.addWidget(self.superadmin_note_checkbox)

        page_layout.addStretch()
        return page

    def _build_admin_page(self):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 4, 0, 0)
        page_layout.setSpacing(10)

        page_layout.addWidget(
            subsection_title(tr("setup.admin.title"))
        )

        hint = QLabel(
            tr("setup.admin.hint", role=ROLE_ADMIN)
        )
        hint.setWordWrap(True)
        hint.setObjectName("formLabel")
        page_layout.addWidget(hint)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(
            tr("setup.admin.username")
        )
        add_form_field(
            page_layout,
            tr("setup.admin.username"),
            self.username_input,
        )

        self.display_name_input = QLineEdit()
        self.display_name_input.setPlaceholderText(
            tr("setup.admin.display_name_optional")
        )
        add_form_field(
            page_layout,
            tr("setup.admin.display_name"),
            self.display_name_input,
        )

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText(
            tr("setup.admin.password_placeholder")
        )
        add_form_field(
            page_layout,
            tr("setup.admin.password"),
            self.password_input,
        )

        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setPlaceholderText(
            tr("setup.admin.confirm_placeholder")
        )
        add_form_field(
            page_layout,
            tr("setup.admin.confirm"),
            self.confirm_input,
        )

        page_layout.addStretch()
        return page

    def _build_finish_page(self):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 4, 0, 0)
        page_layout.setSpacing(12)

        page_layout.addWidget(subsection_title(tr("setup.finish.title")))

        self.finish_label = QLabel("")
        self.finish_label.setWordWrap(True)
        self.finish_label.setObjectName("mutedLabel")
        page_layout.addWidget(self.finish_label)

        success = QLabel(tr("setup.finish.success"))
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
            self.superadmin_password_input.setFocus()
            return

        if index == 1:
            if not self._secure_superadmin_password():
                return

            self.stack.setCurrentIndex(2)
            self._update_navigation()
            self.username_input.setFocus()
            return

        if index == 2:
            if not self._create_org_administrator():
                return

            self.stack.setCurrentIndex(3)
            self._update_navigation()
            return

        if index == 3:
            self.accept()

    def _secure_superadmin_password(self):
        password = self.superadmin_password_input.text()
        confirm = self.superadmin_confirm_input.text()

        if len(password) < 6:
            QMessageBox.warning(
                self,
                tr("setup.error.title"),
                tr("setup.error.password_length"),
            )
            return False

        if password == DEFAULT_SUPERADMIN_PASSWORD:
            QMessageBox.warning(
                self,
                tr("setup.error.title"),
                tr("setup.emergency.error.default_password"),
            )
            return False

        if password != confirm:
            QMessageBox.warning(
                self,
                tr("setup.error.title"),
                tr("setup.error.password_mismatch"),
            )
            return False

        if not self.superadmin_note_checkbox.isChecked():
            QMessageBox.warning(
                self,
                tr("setup.error.title"),
                tr("setup.emergency.error.note"),
            )
            return False

        try:
            self.db.set_superadmin_password_for_setup(password)
        except ValueError as error:
            QMessageBox.warning(
                self,
                tr("setup.error.title"),
                str(error),
            )
            return False

        return True

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
                tr("setup.error.title"),
                tr("setup.error.username"),
            )
            return False

        if username.lower() == SUPERADMIN_USERNAME.lower():
            QMessageBox.warning(
                self,
                tr("setup.error.title"),
                tr(
                    "setup.error.reserved_username",
                    username=SUPERADMIN_USERNAME,
                ),
            )
            return False

        if len(password) < 6:
            QMessageBox.warning(
                self,
                tr("setup.error.title"),
                tr("setup.error.password_length"),
            )
            return False

        if password != confirm:
            QMessageBox.warning(
                self,
                tr("setup.error.title"),
                tr("setup.error.password_mismatch"),
            )
            return False

        role_id = self._admin_role_id()

        if role_id is None:
            QMessageBox.critical(
                self,
                tr("setup.error.title"),
                tr("setup.error.role_missing", role=ROLE_ADMIN),
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
                tr("setup.error.title"),
                str(error),
            )
            return False
        except Exception:
            QMessageBox.warning(
                self,
                tr("setup.error.title"),
                tr("setup.error.create_failed"),
            )
            return False

        self.db.mark_initial_setup_complete()
        self.created_username = username

        self.finish_label.setText(
            tr("setup.finish.message", username=username)
        )
        return True

    def _update_navigation(self):
        index = self.stack.currentIndex()
        step_names = self._step_names()
        step_total = len(step_names)
        step_name = step_names[index]

        self.step_indicator.setText(
            tr(
                "setup.step.indicator",
                current=index + 1,
                total=step_total,
                name=step_name,
            )
        )

        self.back_button.setEnabled(index > 0)

        if index == 0:
            self.next_button.setText(tr("setup.button.next"))
        elif index == 1:
            self.next_button.setText(tr("setup.emergency.button"))
        elif index == 2:
            self.next_button.setText(tr("setup.admin.button"))
        else:
            self.next_button.setText(tr("setup.button.finish"))

    def closeEvent(self, event):
        QMessageBox.warning(
            self,
            tr("setup.error.title"),
            tr("setup.close_blocked"),
        )
        event.ignore()
