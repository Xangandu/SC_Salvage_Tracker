"""

Rechte-Verwaltung: permissions, role_permissions, Rollen-CRUD.

"""



import auth.session as user_session

from config.permissions import (

    ALL_PERMISSION_NAMES,

    LEGACY_ROLE_PERMISSIONS,

    PERMISSION_LABELS,

    ROLE_ADMIN,

    filter_role_permissions_for_actor,

    forbidden_role_permission_changes,

    is_administrator,

    is_super_administrator,

    role_permissions_exceed_actor,

)

from config.i18n import tr, permission_label
from config.setup import ROLE_SUPER_ADMIN





class PermissionRepository:

    def __init__(self, db):

        self.db = db

        self.cursor = db.cursor

        self.connection = db.connection



    def migrate_permissions(self):

        if not self.db._table_exists("permissions"):

            return



        self._ensure_permission_catalog()

        self._grant_administrator_all_permissions()

        self._grant_storage_to_operational_roles()

        self._backfill_legacy_role_permissions()



        self.connection.commit()



    def _ensure_permission_catalog(self):

        for permission_name in ALL_PERMISSION_NAMES:

            self.cursor.execute("""

            INSERT OR IGNORE INTO permissions (

                permission_name,

                description

            )

            VALUES (?, ?)

            """, (

                permission_name,

                PERMISSION_LABELS.get(

                    permission_name,

                    permission_name,

                ),

            ))



    def _grant_administrator_all_permissions(self):

        for role_name in (ROLE_ADMIN, ROLE_SUPER_ADMIN):

            self.cursor.execute("""

            SELECT id

            FROM roles

            WHERE role_name = ?

            LIMIT 1

            """, (role_name,))



            row = self.cursor.fetchone()



            if not row:

                continue



            role_id = row[0]



            for permission_name in ALL_PERMISSION_NAMES:

                self._grant_permission_to_role(

                    role_id,

                    permission_name,

                )



    def _grant_storage_to_operational_roles(self):

        source_permissions = (
            "sessions.manage",
            "sessions.manage_own",
            "sales.manage",
            "refinery.manage",
        )

        for permission_name in source_permissions:

            self.cursor.execute("""

            SELECT DISTINCT role_permissions.role_id

            FROM role_permissions

            INNER JOIN permissions

                ON permissions.id =
                    role_permissions.permission_id

            WHERE permissions.permission_name = ?

            """, (permission_name,))

            for (role_id,) in self.cursor.fetchall():

                self._grant_permission_to_role(

                    role_id,

                    "storage.manage",

                )



    def _backfill_legacy_role_permissions(self):

        for role_name, permission_names in (

            LEGACY_ROLE_PERMISSIONS.items()

        ):

            self.cursor.execute("""

            SELECT id

            FROM roles

            WHERE role_name = ?

            LIMIT 1

            """, (role_name,))



            row = self.cursor.fetchone()



            if not row:

                continue



            role_id = row[0]



            self.cursor.execute("""

            SELECT COUNT(*)

            FROM role_permissions

            WHERE role_id = ?

            """, (role_id,))



            if self.cursor.fetchone()[0] > 0:

                continue



            for permission_name in permission_names:

                self._grant_permission_to_role(

                    role_id,

                    permission_name,

                )



    def _grant_permission_to_role(

        self,

        role_id,

        permission_name,

    ):

        self.cursor.execute("""

        SELECT id

        FROM permissions

        WHERE permission_name = ?

        LIMIT 1

        """, (permission_name,))



        row = self.cursor.fetchone()



        if not row:

            return



        self.cursor.execute("""

        INSERT OR IGNORE INTO role_permissions (

            role_id,

            permission_id,

            created_at

        )

        VALUES (?, ?, datetime('now', 'localtime'))

        """, (role_id, row[0]))



    def get_permissions_for_role(self, role_id):

        if not self.db._table_exists("role_permissions"):

            return set()



        self.cursor.execute("""

        SELECT permissions.permission_name

        FROM role_permissions

        INNER JOIN permissions

            ON permissions.id =

                role_permissions.permission_id

        WHERE role_permissions.role_id = ?

        ORDER BY permissions.permission_name

        """, (role_id,))



        return {

            row[0]

            for row in self.cursor.fetchall()

        }



    def get_role_name(self, role_id):

        self.cursor.execute("""

        SELECT role_name

        FROM roles

        WHERE id = ?

        """, (role_id,))



        row = self.cursor.fetchone()

        return row[0] if row else None



    def get_actor_permissions(self, acting_user):

        """Aktuelle Rechte des Handelnden — immer aus der DB."""

        if not acting_user:

            return set()



        role_id = acting_user.get("role_id")

        if role_id is None:

            return set()



        role_name = self.get_role_name(role_id)

        if role_name == ROLE_ADMIN:

            return set(ALL_PERMISSION_NAMES)



        if role_name == ROLE_SUPER_ADMIN:

            return set(ALL_PERMISSION_NAMES)



        return self.get_permissions_for_role(role_id)



    def attach_permissions_to_user(self, user):

        if not user:

            return user



        user = dict(user)

        user["permissions"] = self.get_actor_permissions(user)

        return user



    def ensure_user_permissions(self, user):

        if not user:

            return user



        return self.attach_permissions_to_user(user)



    def refresh_session_user(self, user_id=None):

        acting_user = user_session.get_user()

        target_id = user_id or (

            acting_user.get("id") if acting_user else None

        )



        if not target_id:

            return None



        record = self.db.get_current_user_record(target_id)

        if not record:

            return None



        refreshed = self.attach_permissions_to_user(record)



        if acting_user and acting_user.get("id") == target_id:

            user_session.set_session(

                refreshed,

                user_session.get_login_id(),

            )



        return refreshed



    def _validate_role_name(self, name, role_id=None):

        cleaned = (name or "").strip()



        if not cleaned:

            raise ValueError(tr("error.role.name_required"))



        if cleaned == ROLE_ADMIN:

            raise ValueError(tr("error.role.name_admin_reserved"))



        if cleaned == ROLE_SUPER_ADMIN:

            raise ValueError(tr("error.role.name_super_admin_reserved"))



        if role_id is not None:

            current_name = self.get_role_name(role_id)

            if current_name == ROLE_ADMIN:

                raise ValueError(tr("error.role.admin_cannot_rename"))



            if current_name == ROLE_SUPER_ADMIN:

                raise ValueError(tr("error.role.super_admin_cannot_rename"))



        return cleaned



    def get_all_permissions(self):

        if not self.db._table_exists("permissions"):

            return []



        self.cursor.execute("""

        SELECT

            id,

            permission_name,

            description

        FROM permissions

        ORDER BY permission_name

        """)



        return [

            {

                "id": row[0],

                "permission_name": row[1],

                "description": row[2],

            }

            for row in self.cursor.fetchall()

        ]



    def get_roles_with_permission_counts(self):

        role_columns = self.db._table_columns("roles")

        system_filter = ""

        if "is_system" in role_columns:

            system_filter = "WHERE roles.is_system = 0"



        self.cursor.execute(f"""

        SELECT

            roles.id,

            roles.role_name,

            roles.description,

            COUNT(DISTINCT role_permissions.permission_id),

            COUNT(DISTINCT users.id)

        FROM roles

        LEFT JOIN role_permissions

            ON role_permissions.role_id = roles.id

        LEFT JOIN users

            ON users.role_id = roles.id

            AND users.is_deleted = 0

        {system_filter}

        GROUP BY roles.id, roles.role_name, roles.description

        ORDER BY roles.id

        """)



        return [

            {

                "id": row[0],

                "role_name": row[1],

                "description": row[2] or "",

                "permission_count": row[3],

                "user_count": row[4],

            }

            for row in self.cursor.fetchall()

        ]



    def get_role_permissions(self, role_id):

        return sorted(

            self.get_permissions_for_role(role_id)

        )



    def create_role(self, role_name, description=None):

        name = self._validate_role_name(role_name)



        self.cursor.execute("""

        INSERT INTO roles (

            role_name,

            description,

            created_at

        )

        VALUES (?, ?, datetime('now', 'localtime'))

        """, (name, description))



        self.connection.commit()



        return self.cursor.lastrowid



    def update_role(

        self,

        role_id,

        role_name=None,

        description=None,

    ):

        if role_name is not None:

            name = self._validate_role_name(

                role_name,

                role_id=role_id,

            )

            self.cursor.execute("""

            UPDATE roles

            SET role_name = ?

            WHERE id = ?

            """, (name, role_id))



        if description is not None:

            self.cursor.execute("""

            UPDATE roles

            SET description = ?

            WHERE id = ?

            """, (description, role_id))



        self.connection.commit()



    def _resolve_role_permissions_for_actor(

        self,

        acting_user,

        existing,

        requested,

    ):

        if not acting_user or is_administrator(acting_user):

            return sorted(set(requested or ()))



        if is_super_administrator(acting_user):

            return sorted(set(requested or ()))



        grantable = self.get_actor_permissions(acting_user)

        forbidden = forbidden_role_permission_changes(

            acting_user,

            existing,

            requested,

            actor_grantable=grantable,

        )



        if forbidden:

            labels = [

                permission_label(name)

                for name in sorted(forbidden)

            ]

            raise ValueError(

                tr("error.role.forbidden_permissions")

                + "\n• "

                + "\n• ".join(labels)

            )



        resolved = filter_role_permissions_for_actor(

            acting_user,

            existing,

            requested,

            actor_grantable=grantable,

        )

        return sorted(resolved)



    def set_role_permissions(

        self,

        role_id,

        permission_names,

    ):

        role_name = self.get_role_name(role_id)



        if not role_name:

            raise ValueError(tr("error.role.not_found"))



        if role_name == ROLE_ADMIN:

            raise ValueError(tr("error.role.admin_perms_immutable"))



        if role_name == ROLE_SUPER_ADMIN:

            raise ValueError(tr("error.role.super_admin_perms_immutable"))



        existing = self.get_permissions_for_role(role_id)

        acting_user = user_session.get_user()

        permission_names = self._resolve_role_permissions_for_actor(

            acting_user,

            existing,

            permission_names,

        )



        self.cursor.execute("""

        DELETE FROM role_permissions

        WHERE role_id = ?

        """, (role_id,))



        for permission_name in permission_names:

            self._grant_permission_to_role(

                role_id,

                permission_name,

            )



        self.connection.commit()



    def assert_can_assign_role(self, role_id, user_id=None):

        acting_user = user_session.get_user()



        if not acting_user or is_administrator(acting_user):

            return



        if is_super_administrator(acting_user):

            return



        role_name = self.get_role_name(role_id)



        if not role_name:

            raise ValueError(tr("error.role.not_found"))



        if role_name == ROLE_ADMIN:

            raise ValueError(tr("error.role.only_admin_can_assign_admin"))



        role_perms = self.get_permissions_for_role(role_id)

        actor_grantable = self.get_actor_permissions(acting_user)



        if role_permissions_exceed_actor(

            acting_user,

            role_perms,

            actor_grantable=actor_grantable,

        ):

            raise ValueError(tr("error.role.exceeds_actor_permissions"))



    def assert_can_manage_user(self, target_user_id):

        acting_user = user_session.get_user()



        if not acting_user or not target_user_id:

            return



        if acting_user.get("id") == target_user_id:

            return



        target = self.db.get_current_user_record(

            target_user_id

        )



        if not target:

            raise ValueError(tr("error.user.not_found"))



        if target.get("is_system"):

            raise ValueError(tr("error.user.system_cannot_manage"))



        if target.get("role_name") == ROLE_SUPER_ADMIN:

            raise ValueError(tr("error.user.super_admin_cannot_manage"))



        if is_administrator(acting_user):

            return



        if is_super_administrator(acting_user):

            return



        if target.get("role_name") == ROLE_ADMIN:

            raise ValueError(tr("error.user.admin_only_manages_admin"))



    def delete_role(self, role_id):

        role_name = self.get_role_name(role_id)



        if not role_name:

            raise ValueError(tr("error.role.not_found"))



        if role_name == ROLE_ADMIN:

            raise ValueError(tr("error.role.admin_cannot_delete"))



        if role_name == ROLE_SUPER_ADMIN:

            raise ValueError(tr("error.role.super_admin_cannot_delete"))



        self.cursor.execute("""

        SELECT COUNT(*)

        FROM users

        WHERE role_id = ?

        AND is_deleted = 0

        """, (role_id,))



        if self.cursor.fetchone()[0] > 0:

            raise ValueError(tr("error.role.still_assigned"))



        self.cursor.execute("""

        DELETE FROM role_permissions

        WHERE role_id = ?

        """, (role_id,))



        self.cursor.execute("""

        DELETE FROM roles

        WHERE id = ?

        """, (role_id,))



        self.connection.commit()


