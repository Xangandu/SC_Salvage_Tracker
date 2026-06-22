"""Rechte bleiben nach Passwortwechsel (Erstanmeldung) erhalten."""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config.paths as paths

_test_data = Path(tempfile.mkdtemp(prefix="sst_perm_test_"))
paths.data_dir = lambda: _test_data

from config.permissions import (
    PERM_DASHBOARD_VIEW,
    PERM_DATABASE_RESET,
    PERM_SESSIONS_MANAGE,
    can_access,
)
from database.database import Database


def main():
    db = Database()

    role_id = db.permissions.create_role(
        "Officer",
        "Testrolle",
    )
    db.permissions.set_role_permissions(
        role_id,
        [
            PERM_SESSIONS_MANAGE,
            PERM_DASHBOARD_VIEW,
        ],
    )

    user_id = db.create_user(
        "Xangandu",
        "111111",
        role_id,
        display_name="Xangandu",
    )

    user = db.authenticate_user("Xangandu", "111111")
    assert user is not None
    user = db.permissions.attach_permissions_to_user(user)
    assert PERM_SESSIONS_MANAGE in user["permissions"]
    assert can_access(user, "session")

    db.change_password(user_id, "222222", must_change_password=0)
    refreshed = db.get_current_user_record(user_id)
    assert "permissions" not in refreshed

    fixed = db.permissions.ensure_user_permissions(refreshed)
    assert PERM_SESSIONS_MANAGE in fixed["permissions"]
    assert PERM_DATABASE_RESET not in fixed["permissions"]
    assert can_access(fixed, "session")
    assert can_access(fixed, "dashboard")

    print("Permission session test OK")


if __name__ == "__main__":
    main()
