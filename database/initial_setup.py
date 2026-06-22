"""Erstinstallation: Status und Organisations-Administratoren."""

from config.permissions import ROLE_ADMIN
from config.setup import INITIAL_SETUP_COMPLETE_KEY


class InitialSetupMixin:
    def is_initial_setup_complete(self):
        if not hasattr(self, "settings"):
            return False

        return (
            self.settings.get_app_setting(
                INITIAL_SETUP_COMPLETE_KEY,
                "0",
            )
            == "1"
        )

    def mark_initial_setup_complete(self):
        self.settings.set_app_setting(
            INITIAL_SETUP_COMPLETE_KEY,
            "1",
        )

    def count_non_system_users(self):
        if not self._table_exists("users"):
            return 0

        columns = self._table_columns("users")
        system_filter = ""

        if "is_system" in columns:
            system_filter = "AND users.is_system = 0"

        self.cursor.execute(f"""
        SELECT COUNT(*)
        FROM users
        WHERE users.is_deleted = 0
        AND users.password_hash IS NOT NULL
        AND users.password_hash != ''
        {system_filter}
        """)

        return self.cursor.fetchone()[0]

    def count_org_administrators(self):
        if not self._table_exists("users"):
            return 0

        columns = self._table_columns("users")
        system_filter = ""

        if "is_system" in columns:
            system_filter = "AND users.is_system = 0"

        self.cursor.execute(f"""
        SELECT COUNT(*)
        FROM users
        INNER JOIN roles
            ON roles.id = users.role_id
        WHERE users.is_deleted = 0
        AND users.active = 1
        AND roles.role_name = ?
        {system_filter}
        """, (ROLE_ADMIN,))

        return self.cursor.fetchone()[0]

    def finalize_initial_setup_state(self):
        """Bestehende Installationen nach Upgrade automatisch abschließen."""
        if not hasattr(self, "settings"):
            return

        if self.is_initial_setup_complete():
            return

        if self.count_org_administrators() > 0:
            self.mark_initial_setup_complete()

    def can_use_main_application(self, user):
        from config.permissions import is_super_administrator

        if not user:
            return False

        if is_super_administrator(user):
            return False

        if not self.is_initial_setup_complete():
            return False

        return True

    def can_login_user(self, user):
        from config.permissions import is_super_administrator

        if not user:
            return False

        if not self.is_initial_setup_complete():
            return is_super_administrator(user)

        return True
