"""Erstinstallation und Super-Administrator."""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config.paths as paths

_test_data = Path(tempfile.mkdtemp(prefix="sst_setup_test_"))
paths.data_dir = lambda: _test_data

import auth.session as user_session
from config.permissions import ROLE_ADMIN, is_super_administrator
from config.setup import (
    DEFAULT_SUPERADMIN_PASSWORD,
    ROLE_SUPER_ADMIN,
    SUPERADMIN_USERNAME,
)
from database.database import Database


def main():
    db = Database()

    assert not db.is_initial_setup_complete(), (
        "Fresh DB should need setup"
    )

    super_user = db.authenticate_user(
        SUPERADMIN_USERNAME,
        DEFAULT_SUPERADMIN_PASSWORD,
    )
    assert super_user, "Super admin login failed"
    assert super_user.get("is_system"), super_user
    assert super_user.get("must_change_password"), super_user

    super_user = db.permissions.attach_permissions_to_user(
        super_user
    )
    assert is_super_administrator(super_user)
    assert db.can_login_user(super_user)
    assert not db.can_use_main_application(super_user)

    admin_role_id = db._get_role_id_by_name(ROLE_ADMIN)
    assert admin_role_id is not None

    user_session.set_session(super_user, 0)
    org_admin_id = db.create_user(
        "orgadmin",
        "secret123",
        admin_role_id,
        display_name="Org Admin",
    )
    assert org_admin_id > 0

    db.mark_initial_setup_complete()

    assert db.is_initial_setup_complete()
    assert db.count_org_administrators() == 1
    assert db.can_login_user(super_user)
    users = db.get_all_users()
    usernames = [row[1] for row in users]
    assert SUPERADMIN_USERNAME not in usernames, usernames
    assert "orgadmin" in usernames, usernames

    super_role_id = db._get_role_id_by_name(ROLE_SUPER_ADMIN)
    db.cursor.execute(
        "SELECT id FROM users WHERE username = ?",
        (SUPERADMIN_USERNAME,),
    )
    super_user_id = db.cursor.fetchone()[0]

    org_user = db.authenticate_user("orgadmin", "secret123")
    assert org_user
    org_user = db.permissions.attach_permissions_to_user(org_user)
    assert db.can_login_user(org_user)
    assert db.can_use_main_application(org_user)

    user_session.set_session(org_user, 0)

    try:
        db.permissions.assert_can_manage_user(super_user_id)
        raise AssertionError(
            "Org admin must not manage super admin"
        )
    except ValueError as error:
        assert "System" in str(error) or "Super" in str(error)

    roles = db.permissions.get_roles_with_permission_counts()
    role_names = [role["role_name"] for role in roles]
    assert ROLE_SUPER_ADMIN not in role_names
    assert ROLE_ADMIN in role_names

    try:
        db.permissions.set_role_permissions(
            super_role_id,
            [],
        )
        raise AssertionError(
            "Super admin role permissions should be locked"
        )
    except ValueError as error:
        assert "Super-Administrator" in str(error)

    print("OK: initial setup and super admin tests passed")


if __name__ == "__main__":
    main()
