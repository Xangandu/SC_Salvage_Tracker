from PySide6.QtWidgets import (

    QDialog,

    QVBoxLayout,

    QLabel,

    QLineEdit,

    QPushButton,

    QMessageBox,

    QFrame,

    QCheckBox,

    QHBoxLayout,

)

from PySide6.QtCore import Qt



from config.setup import SUPERADMIN_USERNAME

from config.i18n import tr

from database.access import get_database

import auth.session as user_session

from auth.remember_me import (

    load_remember_data,

    save_remember_data,

    clear_remember_data,

)

from ui.page_layout import (

    primary_button,

    add_form_field,

    hud_divider,

)

from ui.mobiglas_window_frame import (

    MobiglasFramelessMixin,

    apply_mobiglas_window_frame,

)





class LoginDialog(MobiglasFramelessMixin, QDialog):



    def __init__(self):

        super().__init__()



        self.user = None

        self.db = get_database()



        self.setObjectName("mobiglasDialog")

        self.setWindowTitle(tr("login.title"))

        self.setModal(True)

        self.resize(480, 520)



        layout = QVBoxLayout()

        layout.setSpacing(12)

        layout.setContentsMargins(24, 24, 24, 24)



        recovery_hint = QLabel(

            tr(

                "login.recovery.hint",

                username=SUPERADMIN_USERNAME,

            )

        )

        recovery_hint.setWordWrap(True)

        recovery_hint.setObjectName("mutedLabel")

        recovery_hint.setAlignment(Qt.AlignCenter)

        layout.addWidget(recovery_hint)



        card = QFrame()

        card.setObjectName("loginCard")
        card.setFixedWidth(420)

        card_layout = QVBoxLayout(card)

        card_layout.setContentsMargins(32, 28, 32, 24)

        card_layout.setSpacing(12)



        logo = QLabel("MOBIGLAS")

        logo.setObjectName("loginLogo")

        logo.setAlignment(Qt.AlignCenter)



        tagline = QLabel(tr("login.tagline"))

        tagline.setObjectName("loginTagline")

        tagline.setAlignment(Qt.AlignCenter)



        card_layout.addWidget(logo)

        card_layout.addWidget(tagline)

        card_layout.addSpacing(4)

        card_layout.addLayout(hud_divider())



        self.username_input = QLineEdit()

        self.username_input.setPlaceholderText(tr("login.username"))



        self.password_input = QLineEdit()

        self.password_input.setEchoMode(QLineEdit.Password)

        self.password_input.setPlaceholderText(tr("login.password"))



        add_form_field(

            card_layout,

            tr("login.username"),

            self.username_input,

        )

        add_form_field(

            card_layout,

            tr("login.password"),

            self.password_input,

        )



        self.remember_checkbox = QCheckBox(

            tr("login.remember")

        )

        card_layout.addWidget(

            self.remember_checkbox

        )



        self.login_button = primary_button(tr("login.button"))

        self.login_button.clicked.connect(

            self.try_login

        )

        card_layout.addWidget(self.login_button)



        card_row = QHBoxLayout()

        card_row.addStretch()

        card_row.addWidget(card)

        card_row.addStretch()

        layout.addStretch(1)

        layout.addLayout(card_row)

        layout.addStretch(1)



        self.setLayout(layout)



        self.password_input.returnPressed.connect(

            self.try_login

        )



        self._load_remember_preferences()



        apply_mobiglas_window_frame(

            self,

            title=tr("login.title"),

            dialog=True,

        )



    def _is_initial_setup_pending(self):

        return not self.db.is_initial_setup_complete()



    def _load_remember_preferences(self):

        if self._is_initial_setup_pending():

            return



        remember_data = load_remember_data()



        if not remember_data:

            return



        self.username_input.setText(

            remember_data["username"]

        )

        self.remember_checkbox.setChecked(True)



    def _apply_remember_me(self, user):

        if self.remember_checkbox.isChecked():

            token = self.db.create_remember_token(

                user["id"]

            )

            save_remember_data(

                user["username"],

                token,

            )

            return



        clear_remember_data()

        self.db.revoke_remember_tokens(user["id"])



    def try_login(self):

        username = self.username_input.text().strip()

        password = self.password_input.text()



        if not username or not password:

            QMessageBox.warning(

                self,

                tr("login.error.blocked_title"),

                tr("login.error.empty"),

            )

            return



        user = self.db.authenticate_user(

            username,

            password,

        )



        if not user:

            QMessageBox.warning(

                self,

                tr("login.error.failed_title"),

                tr("login.error.invalid_credentials"),

            )

            return



        user = self.db.permissions.attach_permissions_to_user(

            user

        )



        if not self.db.can_login_user(user):

            if self._is_initial_setup_pending():

                detail = tr("login.error.blocked_setup")

            else:

                detail = tr("login.error.blocked")



            QMessageBox.warning(

                self,

                tr("login.error.blocked_title"),

                detail,

            )

            return



        if self._is_initial_setup_pending():

            self.remember_checkbox.setChecked(False)

        else:

            self._apply_remember_me(user)



        login_id = self.db.record_login(user["id"])

        user_session.set_session(user, login_id)



        self.user = user

        self.accept()


