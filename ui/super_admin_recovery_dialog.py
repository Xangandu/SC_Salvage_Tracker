"""Notfall-Wartung für den Super-Administrator nach der Erstinstallation."""



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

from config.i18n import tr

from database.access import get_database

from ui.mobiglas_window_frame import (

    MobiglasFramelessMixin,

    apply_mobiglas_window_frame,

)

from ui.page_layout import (

    add_form_field,

    hud_divider,

    page_title,

    primary_button,

    subsection_title,

)





class SuperAdminRecoveryDialog(MobiglasFramelessMixin, QDialog):



    def __init__(self, parent=None):

        super().__init__(parent)



        self.db = get_database()



        self.setObjectName("mobiglasDialog")

        self.setWindowTitle(tr("recovery.window_title"))

        self.setModal(True)

        self.resize(580, 560)



        layout = QVBoxLayout()

        layout.setSpacing(12)

        layout.setContentsMargins(24, 24, 24, 24)



        subtitle = QLabel(tr("recovery.subtitle"))

        subtitle.setWordWrap(True)

        subtitle.setObjectName("mutedLabel")



        self.stack = QStackedWidget()

        self.stack.addWidget(self._build_menu_page())

        self.stack.addWidget(self._build_create_admin_page())

        self.stack.addWidget(self._build_reset_password_page())



        self.back_button = QPushButton(tr("common.back"))

        self.back_button.setObjectName("secondaryAction")

        self.back_button.clicked.connect(self._go_back)



        self.action_button = primary_button(tr("common.continue"))

        self.action_button.clicked.connect(self._on_action)



        self.logout_button = QPushButton(tr("common.logout"))

        self.logout_button.setObjectName("secondaryAction")

        self.logout_button.clicked.connect(self.accept)



        button_row = QHBoxLayout()

        button_row.addWidget(self.logout_button)

        button_row.addStretch()

        button_row.addWidget(self.back_button)

        button_row.addWidget(self.action_button)



        layout.addWidget(page_title(tr("recovery.title")))

        layout.addWidget(subtitle)

        layout.addLayout(hud_divider())

        layout.addWidget(self.stack)

        layout.addLayout(button_row)

        self.setLayout(layout)



        self._show_menu()



        apply_mobiglas_window_frame(

            self,

            title=tr("recovery.window_title"),

            dialog=True,

        )



    def _build_menu_page(self):

        page = QWidget()

        page_layout = QVBoxLayout()

        page_layout.setSpacing(10)



        panel = QFrame()

        panel.setObjectName("pagePanel")

        panel_layout = QVBoxLayout()

        panel_layout.setSpacing(10)



        panel_layout.addWidget(

            subsection_title(tr("recovery.section.options"))

        )



        admin_count = self.db.count_org_administrators()

        status = QLabel(

            tr("recovery.status.admins", count=admin_count)

        )

        status.setWordWrap(True)

        panel_layout.addWidget(status)



        create_button = primary_button(

            tr("recovery.button.create_admin")

        )

        create_button.clicked.connect(self._open_create_admin)

        panel_layout.addWidget(create_button)



        reset_button = QPushButton(

            tr("recovery.button.reset_password")

        )

        reset_button.setObjectName("secondaryAction")

        reset_button.clicked.connect(self._open_reset_password)

        panel_layout.addWidget(reset_button)



        panel.setLayout(panel_layout)

        page_layout.addWidget(panel)

        page_layout.addStretch()

        page.setLayout(page_layout)

        return page



    def _build_create_admin_page(self):

        page = QWidget()

        page_layout = QVBoxLayout()

        page_layout.setSpacing(10)



        panel = QFrame()

        panel.setObjectName("pagePanel")

        panel_layout = QVBoxLayout()

        panel_layout.setSpacing(10)



        panel_layout.addWidget(

            subsection_title(tr("recovery.section.create_admin"))

        )



        hint = QLabel(

            tr("recovery.create.hint", role=ROLE_ADMIN)

        )

        hint.setWordWrap(True)

        hint.setObjectName("formLabel")

        panel_layout.addWidget(hint)



        self.create_username_input = QLineEdit()

        add_form_field(

            panel_layout,

            tr("login.username"),

            self.create_username_input,

        )



        self.create_display_name_input = QLineEdit()

        add_form_field(

            panel_layout,

            tr("admin.users.label.display_name"),

            self.create_display_name_input,

        )



        self.create_password_input = QLineEdit()

        self.create_password_input.setEchoMode(QLineEdit.Password)

        add_form_field(

            panel_layout,

            tr("admin.users.label.password"),

            self.create_password_input,

        )



        self.create_confirm_input = QLineEdit()

        self.create_confirm_input.setEchoMode(QLineEdit.Password)

        add_form_field(

            panel_layout,

            tr("password.label.confirm"),

            self.create_confirm_input,

        )



        panel.setLayout(panel_layout)

        page_layout.addWidget(panel)

        page_layout.addStretch()

        page.setLayout(page_layout)

        return page



    def _build_reset_password_page(self):

        page = QWidget()

        page_layout = QVBoxLayout()

        page_layout.setSpacing(10)



        panel = QFrame()

        panel.setObjectName("pagePanel")

        panel_layout = QVBoxLayout()

        panel_layout.setSpacing(10)



        panel_layout.addWidget(

            subsection_title(tr("recovery.section.reset_password"))

        )



        hint = QLabel(tr("recovery.reset.hint"))

        hint.setWordWrap(True)

        hint.setObjectName("formLabel")

        panel_layout.addWidget(hint)



        self.reset_username_input = QLineEdit()

        add_form_field(

            panel_layout,

            tr("login.username"),

            self.reset_username_input,

        )



        self.reset_password_input = QLineEdit()

        self.reset_password_input.setEchoMode(QLineEdit.Password)

        add_form_field(

            panel_layout,

            tr("password.label.new"),

            self.reset_password_input,

        )



        self.reset_confirm_input = QLineEdit()

        self.reset_confirm_input.setEchoMode(QLineEdit.Password)

        add_form_field(

            panel_layout,

            tr("password.label.confirm"),

            self.reset_confirm_input,

        )



        panel.setLayout(panel_layout)

        page_layout.addWidget(panel)

        page_layout.addStretch()

        page.setLayout(page_layout)

        return page



    def _admin_role_id(self):

        return self.db._get_role_id_by_name(ROLE_ADMIN)



    def _show_menu(self):

        self.stack.setCurrentIndex(0)

        self.back_button.setVisible(False)

        self.action_button.setVisible(False)



    def _open_create_admin(self):

        self.stack.setCurrentIndex(1)

        self.back_button.setVisible(True)

        self.action_button.setVisible(True)

        self.action_button.setText(tr("recovery.button.create"))

        self.create_username_input.setFocus()



    def _open_reset_password(self):

        self.stack.setCurrentIndex(2)

        self.back_button.setVisible(True)

        self.action_button.setVisible(True)

        self.action_button.setText(tr("recovery.button.reset"))

        self.reset_username_input.setFocus()



    def _go_back(self):

        self._show_menu()



    def _on_action(self):

        index = self.stack.currentIndex()



        if index == 1:

            self._create_administrator()

        elif index == 2:

            self._reset_password()



    def _create_administrator(self):

        username = self.create_username_input.text().strip()

        display_name = (

            self.create_display_name_input.text().strip()

            or username

        )

        password = self.create_password_input.text()

        confirm = self.create_confirm_input.text()



        if not username:

            QMessageBox.warning(

                self,

                tr("recovery.msg.title"),

                tr("setup.error.username"),

            )

            return



        if username.lower() == SUPERADMIN_USERNAME.lower():

            QMessageBox.warning(

                self,

                tr("recovery.msg.title"),

                tr("setup.error.reserved_username"),

            )

            return



        if len(password) < 6:

            QMessageBox.warning(

                self,

                tr("recovery.msg.title"),

                tr("setup.error.password_length"),

            )

            return



        if password != confirm:

            QMessageBox.warning(

                self,

                tr("recovery.msg.title"),

                tr("setup.error.password_mismatch"),

            )

            return



        role_id = self._admin_role_id()

        if role_id is None:

            QMessageBox.critical(

                self,

                tr("recovery.msg.title"),

                tr("setup.error.role_missing", role=ROLE_ADMIN),

            )

            return



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

                tr("recovery.msg.title"),

                str(error),

            )

            return

        except Exception:

            QMessageBox.warning(

                self,

                tr("recovery.msg.title"),

                tr("recovery.msg.user_create_failed"),

            )

            return



        self.create_username_input.clear()

        self.create_display_name_input.clear()

        self.create_password_input.clear()

        self.create_confirm_input.clear()



        QMessageBox.information(

            self,

            tr("recovery.msg.title"),

            tr(

                "recovery.msg.admin_created_detail",

                username=username,

            ),

        )

        self._show_menu()



    def _reset_password(self):

        username = self.reset_username_input.text().strip()

        password = self.reset_password_input.text()

        confirm = self.reset_confirm_input.text()



        if not username:

            QMessageBox.warning(

                self,

                tr("recovery.msg.title"),

                tr("setup.error.username"),

            )

            return



        if username.lower() == SUPERADMIN_USERNAME.lower():

            QMessageBox.warning(

                self,

                tr("recovery.msg.title"),

                tr("recovery.msg.superadmin_password_locked"),

            )

            return



        if len(password) < 6:

            QMessageBox.warning(

                self,

                tr("recovery.msg.title"),

                tr("setup.error.password_length"),

            )

            return



        if password != confirm:

            QMessageBox.warning(

                self,

                tr("recovery.msg.title"),

                tr("setup.error.password_mismatch"),

            )

            return



        self.db.cursor.execute("""

        SELECT users.id

        FROM users

        INNER JOIN roles

            ON roles.id = users.role_id

        WHERE users.username = ?

        AND users.is_deleted = 0

        AND COALESCE(users.is_system, 0) = 0

        """, (username,))



        row = self.db.cursor.fetchone()

        if not row:

            QMessageBox.warning(

                self,

                tr("recovery.msg.title"),

                tr("recovery.msg.user_not_found", username=username),

            )

            return



        try:

            self.db.reset_user_password(row[0], password)

        except ValueError as error:

            QMessageBox.warning(

                self,

                tr("recovery.msg.title"),

                str(error),

            )

            return



        self.reset_username_input.clear()

        self.reset_password_input.clear()

        self.reset_confirm_input.clear()



        QMessageBox.information(

            self,

            tr("recovery.msg.title"),

            tr(

                "recovery.msg.password_reset_detail",

                username=username,

            ),

        )

        self._show_menu()

