"""Rechte-Eskalation und Benutzer-/Rollenschutz."""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config.paths as paths

_test_data = Path(tempfile.mkdtemp(prefix="sst_escalation_test_"))
paths.data_dir = lambda: _test_data

import auth.session as user_session
from config.permissions import (
    PERM_DATABASE_RESET,
    PERM_ROLES_MANAGE,
    PERM_USERS_MANAGE,
)
from database.database import Database


def _captain_user(role_id, user_id=2):
    return {
        "id": user_id,
        "username": "captain_user",
        "role_id": role_id,
        "role_name": "Captain",
        "permissions": {
            PERM_USERS_MANAGE,
            PERM_ROLES_MANAGE,
        },
    }


def main():
    db = Database()

    captain_role_id = db.permissions.create_role(
        "Captain",
        "Test captain",
    )
    db.permissions.set_role_permissions(
        captain_role_id,
        [PERM_USERS_MANAGE, PERM_ROLES_MANAGE],
    )

    actor = _captain_user(captain_role_id)
    user_session.set_session(actor, 0)

    try:
        db.permissions.set_role_permissions(
            captain_role_id,
            [
                PERM_USERS_MANAGE,
                PERM_ROLES_MANAGE,
                PERM_DATABASE_RESET,
            ],
        )
        raise AssertionError(
            "Escalation should raise ValueError"
        )
    except ValueError as error:
        if "database.reset" in str(error) or "Datenbank" in str(
            error
        ):
            pass
        else:
            raise

    saved = db.permissions.get_role_permissions(
        captain_role_id
    )
    assert PERM_DATABASE_RESET not in saved, saved

    admin_role = next(
        role["id"]
        for role in db.permissions.get_roles_with_permission_counts()
        if role["role_name"] == "Administrator"
    )

    try:
        db.update_user_role(actor["id"], admin_role)
        raise AssertionError(
            "Captain should not assign Administrator role"
        )
    except ValueError:
        pass

    admin_user = db.get_current_user_record(1)
    assert admin_user is not None

    try:
        db.reset_user_password(admin_user["id"], "hacked123")
        raise AssertionError(
            "Captain should not reset admin password"
        )
    except ValueError:
        pass

    try:
        db.permissions.create_role("Administrator", "fake")
        raise AssertionError(
            "Reserved role name should be blocked"
        )
    except ValueError:
        pass

    db.permissions.set_role_permissions(
        captain_role_id,
        [PERM_USERS_MANAGE],
    )
    actor["permissions"] = {PERM_USERS_MANAGE, PERM_ROLES_MANAGE}
    user_session.set_session(actor, 0)

    try:
        db.permissions.set_role_permissions(
            captain_role_id,
            [PERM_USERS_MANAGE, PERM_ROLES_MANAGE],
        )
        raise AssertionError(
            "Stale session must not allow granting removed rights"
        )
    except ValueError:
        pass

    fresh = db.permissions.get_actor_permissions(actor)
    assert PERM_ROLES_MANAGE not in fresh, fresh

    user_session.clear_session()
    print("test_permission_escalation: OK")


if __name__ == "__main__":
    main()
