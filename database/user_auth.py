from datetime import datetime

from auth.password import hash_password, verify_password
from config.dates import now_db_timestamp
from config.debug import debug_log
from config.i18n import tr
from config.permissions import PERM_USERS_MANAGE, has_permission
from config.setup import (
    DEFAULT_SUPERADMIN_PASSWORD,
    ROLE_SUPER_ADMIN,
    SUPERADMIN_USERNAME,
)
import auth.session as user_session


class UserAuthMixin:

    def _table_columns(self, table_name):
        self.cursor.execute(
            f"PRAGMA table_info({table_name})"
        )
        return {
            row[1]
            for row in self.cursor.fetchall()
        }

    def _add_column_if_missing(
        self,
        table_name,
        column_name,
        column_definition,
    ):
        columns = self._table_columns(table_name)

        if column_name in columns:
            return

        self.cursor.execute(
            f"ALTER TABLE {table_name} "
            f"ADD COLUMN {column_name} {column_definition}"
        )

    def migrate_auth_schema(self):
        user_columns = {
            "password_hash": "TEXT",
            "role_id": "INTEGER",
            "active": "INTEGER NOT NULL DEFAULT 1",
            "must_change_password": (
                "INTEGER NOT NULL DEFAULT 0"
            ),
            "is_system": "INTEGER NOT NULL DEFAULT 0",
        }

        for column, definition in user_columns.items():
            self._add_column_if_missing(
                "users",
                column,
                definition,
            )

        self._add_column_if_missing(
            "roles",
            "is_system",
            "INTEGER NOT NULL DEFAULT 0",
        )

        audit_tables = [
            "sessions",
            "material_batches",
            "refinery_jobs",
            "sales",
            "payouts",
            "costs",
        ]

        for table in audit_tables:
            columns = self._table_columns(table)

            if not columns:
                continue

            self._add_column_if_missing(
                table,
                "created_by",
                "INTEGER",
            )
            self._add_column_if_missing(
                table,
                "updated_by",
                "INTEGER",
            )

        if self._table_exists("payouts"):
            self._add_column_if_missing(
                "payouts",
                "approved_by",
                "INTEGER",
            )

        self.connection.commit()

    def create_remember_token(self, user_id):
        from auth.remember_me import (
            generate_token,
            get_expiry_time,
            _hash_token,
        )

        token = generate_token()
        token_hash = _hash_token(token)
        expires_at = get_expiry_time()

        self.revoke_remember_tokens(user_id)

        self.cursor.execute("""
        INSERT INTO remember_tokens (
            user_id,
            token_hash,
            expires_at,
            created_at
        )
        VALUES (?, ?, ?, datetime('now', 'localtime'))
        """, (
            user_id,
            token_hash,
            expires_at,
        ))

        self.connection.commit()

        return token

    def authenticate_remember_token(
        self,
        username,
        token,
    ):
        from auth.remember_me import _hash_token

        token_hash = _hash_token(token)

        user_columns = self._table_columns("users")
        system_select = (
            "users.is_system,"
            if "is_system" in user_columns
            else "0 AS is_system,"
        )

        self.cursor.execute(f"""
        SELECT
            users.id,
            users.username,
            users.display_name,
            users.role_id,
            users.active,
            users.must_change_password,
            roles.role_name,
            {system_select}
            remember_tokens.expires_at
        FROM remember_tokens
        INNER JOIN users
            ON users.id = remember_tokens.user_id
        INNER JOIN roles
            ON roles.id = users.role_id
        WHERE users.username = ?
        AND remember_tokens.token_hash = ?
        AND users.is_deleted = 0
        AND users.active = 1
        """, (
            username.strip(),
            token_hash,
        ))

        row = self.cursor.fetchone()

        if not row:
            return None

        expires_at = datetime.strptime(
            row[8],
            "%Y-%m-%d %H:%M:%S",
        )

        if datetime.now() > expires_at:
            self.revoke_remember_token(token_hash)
            return None

        user = {
            "id": row[0],
            "username": row[1],
            "display_name": row[2],
            "role_id": row[3],
            "active": row[4],
            "must_change_password": row[5],
            "role_name": row[6],
            "is_system": bool(row[7]),
        }

        if not self.can_login_user(user):
            return None

        return user

    def revoke_remember_token(self, token_hash):
        self.cursor.execute("""
        DELETE FROM remember_tokens
        WHERE token_hash = ?
        """, (token_hash,))

        self.connection.commit()

    def revoke_remember_tokens(self, user_id):
        self.cursor.execute("""
        DELETE FROM remember_tokens
        WHERE user_id = ?
        """, (user_id,))

        self.connection.commit()

    def _user_is_system(self, user_id):
        columns = self._table_columns("users")

        if "is_system" not in columns:
            return False

        self.cursor.execute("""
        SELECT is_system
        FROM users
        WHERE id = ?
        """, (user_id,))

        row = self.cursor.fetchone()
        return bool(row and row[0])

    def _get_role_id_by_name(self, role_name):
        self.cursor.execute("""
        SELECT id
        FROM roles
        WHERE role_name = ?
        LIMIT 1
        """, (role_name,))

        row = self.cursor.fetchone()
        return row[0] if row else None

    def _ensure_super_admin_role(self):
        role_id = self._get_role_id_by_name(ROLE_SUPER_ADMIN)

        if role_id is None:
            self.cursor.execute("""
            INSERT INTO roles (
                role_name,
                description,
                is_system,
                created_at
            )
            VALUES (?, ?, 1, datetime('now', 'localtime'))
            """, (
                ROLE_SUPER_ADMIN,
                "System — Erstinstallation und Notfall",
            ))
            role_id = self.cursor.lastrowid
        else:
            self.cursor.execute("""
            UPDATE roles
            SET is_system = 1
            WHERE id = ?
            """, (role_id,))

        return role_id

    def seed_system_accounts(self):
        self.cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE password_hash IS NOT NULL
        AND password_hash != ''
        AND is_deleted = 0
        """)

        has_any_user = self.cursor.fetchone()[0] > 0

        super_role_id = self._ensure_super_admin_role()
        password_hash = hash_password(
            DEFAULT_SUPERADMIN_PASSWORD
        )

        self.cursor.execute("""
        SELECT id
        FROM users
        WHERE username = ?
        LIMIT 1
        """, (SUPERADMIN_USERNAME,))

        existing_super = self.cursor.fetchone()

        if existing_super:
            self.cursor.execute("""
            UPDATE users
            SET
                role_id = ?,
                is_system = 1,
                active = 1,
                is_deleted = 0
            WHERE id = ?
            """, (super_role_id, existing_super[0]))
        else:
            self.cursor.execute("""
            INSERT INTO users (
                username,
                display_name,
                password_hash,
                role_id,
                active,
                must_change_password,
                is_system,
                created_at
            )
            VALUES (?, ?, ?, ?, 1, 1, 1, datetime('now', 'localtime'))
            """, (
                SUPERADMIN_USERNAME,
                "Super-Administrator",
                password_hash,
                super_role_id,
            ))

        if not has_any_user:
            debug_log(
                "Super-Administrator erstellt "
                f"({SUPERADMIN_USERNAME} / "
                f"{DEFAULT_SUPERADMIN_PASSWORD})"
            )
            self.connection.commit()
            return

        self.cursor.execute("""
        UPDATE users
        SET is_system = 0
        WHERE username != ?
        """, (SUPERADMIN_USERNAME,))

        self.connection.commit()

        debug_log(
            "Super-Administrator bereitgestellt "
            f"({SUPERADMIN_USERNAME})"
        )

    def seed_default_admin(self):
        """Abwärtskompatibilität — delegiert an seed_system_accounts."""
        self.seed_system_accounts()

    def authenticate_user(
        self,
        username,
        password,
    ):
        user_columns = self._table_columns("users")
        system_select = (
            "users.is_system"
            if "is_system" in user_columns
            else "0 AS is_system"
        )

        self.cursor.execute(f"""
        SELECT
            users.id,
            users.username,
            users.display_name,
            users.password_hash,
            users.role_id,
            users.active,
            users.must_change_password,
            roles.role_name,
            {system_select}
        FROM users
        INNER JOIN roles
            ON roles.id = users.role_id
        WHERE users.username = ?
        AND users.is_deleted = 0
        """, (username.strip(),))

        row = self.cursor.fetchone()

        if not row:
            return None

        if not row[5]:
            return None

        if not verify_password(
            password,
            row[3],
        ):
            return None

        return {
            "id": row[0],
            "username": row[1],
            "display_name": row[2],
            "role_id": row[4],
            "active": row[5],
            "must_change_password": row[6],
            "role_name": row[7],
            "is_system": bool(row[8]),
        }

    def record_login(self, user_id):
        login_time = now_db_timestamp()

        self.cursor.execute("""
        INSERT INTO login_history (
            user_id,
            login_time
        )
        VALUES (?, ?)
        """, (user_id, login_time))

        self.connection.commit()

        return self.cursor.lastrowid

    def record_logout(self, login_id):
        if not login_id:
            return

        logout_time = now_db_timestamp()

        self.cursor.execute("""
        UPDATE login_history
        SET logout_time = ?
        WHERE id = ?
        """, (logout_time, login_id))

        self.connection.commit()

    def change_password(
        self,
        user_id,
        new_password,
        must_change_password=0,
    ):
        acting_user = user_session.get_user()

        if acting_user and acting_user.get("id") != user_id:
            if not has_permission(
                PERM_USERS_MANAGE,
                acting_user,
            ):
                raise ValueError(
                    tr("error.password.no_permission_other_user")
                )
            self.permissions.assert_can_manage_user(user_id)

        password_hash = hash_password(new_password)

        self.cursor.execute("""
        UPDATE users
        SET
            password_hash = ?,
            must_change_password = ?,
            updated_at = datetime('now', 'localtime')
        WHERE id = ?
        """, (
            password_hash,
            must_change_password,
            user_id,
        ))

        self.connection.commit()

        self.revoke_remember_tokens(user_id)

    def get_all_users(self):
        user_columns = self._table_columns("users")
        system_filter = ""

        if "is_system" in user_columns:
            system_filter = "AND users.is_system = 0"

        self.cursor.execute(f"""
        SELECT
            users.id,
            users.username,
            users.display_name,
            roles.role_name,
            users.active,
            users.created_at
        FROM users
        INNER JOIN roles
            ON roles.id = users.role_id
        WHERE users.is_deleted = 0
        {system_filter}
        ORDER BY users.username
        """)

        return self.cursor.fetchall()

    def get_roles(self):
        role_columns = self._table_columns("roles")
        system_filter = ""

        if "is_system" in role_columns:
            system_filter = "WHERE is_system = 0"

        self.cursor.execute(f"""
        SELECT id, role_name
        FROM roles
        {system_filter}
        ORDER BY id
        """)

        return self.cursor.fetchall()

    def create_user(
        self,
        username,
        password,
        role_id,
        display_name=None,
        *,
        must_change_password=None,
    ):
        self.permissions.assert_can_assign_role(role_id)

        if must_change_password is None:
            from config.editions import (
                requires_forced_password_change_on_login,
            )

            must_change_password = (
                requires_forced_password_change_on_login(self)
            )

        password_hash = hash_password(password)

        self.cursor.execute("""
        INSERT INTO users (
            username,
            display_name,
            password_hash,
            role_id,
            active,
            must_change_password,
            created_at
        )
        VALUES (?, ?, ?, ?, 1, ?, datetime('now', 'localtime'))
        """, (
            username.strip(),
            display_name or username.strip(),
            password_hash,
            role_id,
            int(bool(must_change_password)),
        ))

        self.connection.commit()

        return self.cursor.lastrowid

    def update_user_role(
        self,
        user_id,
        role_id,
    ):
        if self._user_is_system(user_id):
            raise ValueError(tr("error.user.system_immutable"))

        self.permissions.assert_can_manage_user(user_id)
        self.permissions.assert_can_assign_role(
            role_id,
            user_id=user_id,
        )

        self.cursor.execute("""
        UPDATE users
        SET
            role_id = ?,
            updated_at = datetime('now', 'localtime')
        WHERE id = ?
        """, (role_id, user_id))

        self.connection.commit()

    def update_user_display_name(
        self,
        user_id,
        display_name,
    ):
        self.permissions.assert_can_manage_user(user_id)

        self.cursor.execute("""
        UPDATE users
        SET
            display_name = ?,
            updated_at = datetime('now', 'localtime')
        WHERE id = ?
        """, (display_name.strip(), user_id))

        self.connection.commit()

    def set_user_active(
        self,
        user_id,
        active,
    ):
        self.permissions.assert_can_manage_user(user_id)

        self.cursor.execute("""
        UPDATE users
        SET
            active = ?,
            updated_at = datetime('now', 'localtime')
        WHERE id = ?
        """, (active, user_id))

        self.connection.commit()

        if not active:
            self.revoke_remember_tokens(user_id)

    def delete_user(self, user_id):
        self.permissions.assert_can_manage_user(user_id)
        self.revoke_remember_tokens(user_id)

        self.cursor.execute("""
        UPDATE users
        SET
            is_deleted = 1,
            active = 0,
            deleted_at = datetime('now', 'localtime'),
            updated_at = datetime('now', 'localtime')
        WHERE id = ?
        """, (user_id,))

        self.connection.commit()

    def reset_user_password(
        self,
        user_id,
        new_password,
    ):
        self.permissions.assert_can_manage_user(user_id)
        self.change_password(
            user_id,
            new_password,
            must_change_password=1,
        )

    def get_login_history(self, limit=100):
        self.cursor.execute("""
        SELECT
            login_history.id,
            users.username,
            login_history.login_time,
            login_history.logout_time
        FROM login_history
        LEFT JOIN users
            ON users.id = login_history.user_id
        ORDER BY login_history.id DESC
        LIMIT ?
        """, (limit,))

        return self.cursor.fetchall()

    def get_current_user_record(self, user_id):
        user_columns = self._table_columns("users")
        system_select = (
            "users.is_system"
            if "is_system" in user_columns
            else "0 AS is_system"
        )

        self.cursor.execute(f"""
        SELECT
            users.id,
            users.username,
            users.display_name,
            users.role_id,
            users.active,
            users.must_change_password,
            roles.role_name,
            {system_select}
        FROM users
        INNER JOIN roles
            ON roles.id = users.role_id
        WHERE users.id = ?
        """, (user_id,))

        row = self.cursor.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "username": row[1],
            "display_name": row[2],
            "role_id": row[3],
            "active": row[4],
            "must_change_password": row[5],
            "role_name": row[6],
            "is_system": bool(row[7]),
        }
