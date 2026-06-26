from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFrame,
)
from PySide6.QtCore import Qt

from database.access import get_database
from config.i18n import tr
import auth.session as user_session
from ui.page_layout import (
    primary_button,
    add_form_field,
    hud_divider,
    page_title,
)
from ui.mobiglas_window_frame import (
    MobiglasFramelessMixin,
    apply_mobiglas_window_frame,
)


class ChangePasswordDialog(MobiglasFramelessMixin, QDialog):

    def __init__(
        self,
        user,
        required=False,
    ):
        super().__init__()

        self.user = user
        self.required = required
        self.db = get_database()

        self.setObjectName("mobiglasDialog")

        if required:
            self.setWindowTitle(
                tr("password.required.window_title")
            )
        else:
            self.setWindowTitle(tr("password.change.title"))

        self.setModal(True)
        self.resize(520, 480 if required else 380)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        if required:
            title = QLabel(tr("password.required.banner_title"))
            title.setObjectName("warningBannerTitle")
            layout.addWidget(title)

            banner = QLabel(
                tr(
                    "password.required.banner",
                    username=user.get("username", "admin"),
                )
            )
            banner.setWordWrap(True)
            banner.setObjectName("warningBanner")
            layout.addWidget(banner)
        else:
            layout.addWidget(
                page_title(tr("password.change.title").upper())
            )

        layout.addLayout(hud_divider())

        panel = QFrame()
        panel.setObjectName("pagePanel")
        panel_layout = QVBoxLayout()
        panel_layout.setSpacing(10)

        if required:
            step_hint = QLabel(tr("password.required.step"))
            step_hint.setObjectName("formLabel")
            panel_layout.addWidget(step_hint)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(
            QLineEdit.Password
        )
        self.password_input.setPlaceholderText(
            tr("password.placeholder.new")
        )
        add_form_field(
            panel_layout,
            tr("password.label.new"),
            self.password_input,
        )

        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(
            QLineEdit.Password
        )
        self.confirm_input.setPlaceholderText(
            tr("password.placeholder.confirm")
        )
        add_form_field(
            panel_layout,
            tr("password.label.confirm"),
            self.confirm_input,
        )

        button_label = (
            tr("password.button.set_and_continue")
            if required
            else tr("common.save")
        )
        self.save_button = primary_button(button_label)
        self.save_button.clicked.connect(
            self.save_password
        )
        panel_layout.addWidget(self.save_button)

        if not required:
            cancel_button = QPushButton(tr("common.cancel"))
            cancel_button.setObjectName("secondaryAction")
            cancel_button.clicked.connect(
                self.reject
            )
            panel_layout.addWidget(cancel_button)

        panel.setLayout(panel_layout)
        layout.addWidget(panel)

        self.setLayout(layout)

        self.password_input.setFocus()

        if required:
            self.confirm_input.returnPressed.connect(
                self.save_password
            )
            self.password_input.returnPressed.connect(
                self.confirm_input.setFocus
            )

        frame_title = (
            tr("password.required.frame_title")
            if required
            else tr("password.change.title")
        )
        apply_mobiglas_window_frame(
            self,
            title=frame_title,
            dialog=True,
            show_close=not required,
        )

    def closeEvent(self, event):
        if self.required:
            QMessageBox.warning(
                self,
                tr("password.msg.blocked.title"),
                tr("password.msg.blocked"),
            )
            event.ignore()
            return

        super().closeEvent(event)

    def reject(self):
        if self.required:
            QMessageBox.warning(
                self,
                tr("password.msg.blocked.title"),
                tr("password.msg.blocked"),
            )
            return

        super().reject()

    def save_password(self):
        password = self.password_input.text()
        confirm = self.confirm_input.text()

        if len(password) < 6:
            QMessageBox.warning(
                self,
                tr("password.msg.title"),
                tr("password.msg.length"),
            )
            return

        if password != confirm:
            QMessageBox.warning(
                self,
                tr("password.msg.title"),
                tr("password.msg.mismatch"),
            )
            return

        self.db.change_password(
            self.user["id"],
            password,
            must_change_password=0,
        )

        updated_user = (
            self.db.get_current_user_record(
                self.user["id"]
            )
        )

        if updated_user:
            updated_user = (
                self.db.permissions.ensure_user_permissions(
                    updated_user
                )
            )
            login_id = user_session.get_login_id()
            user_session.set_session(
                updated_user,
                login_id,
            )
            self.user = updated_user

        success_title = (
            tr("password.msg.required_success.title")
            if self.required
            else tr("password.msg.title")
        )
        success_text = (
            tr("password.msg.required_success")
            if self.required
            else tr("password.msg.changed")
        )

        QMessageBox.information(
            self,
            success_title,
            success_text,
        )

        self.accept()
