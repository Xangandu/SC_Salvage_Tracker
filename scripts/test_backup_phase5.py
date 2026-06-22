"""Phase 5: backup settings persistence and retention."""

import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config.paths as paths

_test_data = Path(tempfile.mkdtemp(prefix="sst_backup_p5_"))
paths.data_dir = lambda: _test_data

from database.database import Database
from database.access import reconnect_database


def main():
    db = Database()

    status = db.get_database_backup_status()
    assert status["auto_before_reset"] is True
    assert status["auto_before_restore"] is True
    assert status["max_backup_count"] == 20

    db.save_database_backup_settings(
        max_count=2,
        auto_before_reset=False,
        auto_before_restore=False,
    )

    status = db.get_database_backup_status()
    assert status["max_backup_count"] == 2
    assert status["auto_before_reset"] is False
    assert status["auto_before_restore"] is False

    names = []
    for index in range(3):
        result = db.create_database_backup(reason=f"n{index}")
        names.append(result["filename"])
        time.sleep(1.1)

    backups = db.list_database_backups()
    assert len(backups) == 2
    remaining = {item["filename"] for item in backups}
    assert names[0] not in remaining
    assert names[2] in remaining

    db = reconnect_database()
    db.save_database_backup_settings(
        max_count=20,
        auto_before_reset=True,
        auto_before_restore=False,
    )

    session_id = db.create_session(
        None,
        "TestShip",
        "2026-06-22 12:00:00",
        created_by=1,
    )
    db.add_crew_member(session_id, "Pilot-A")
    snapshot = db.create_database_backup(reason="snapshot")
    db.add_crew_member(session_id, "Pilot-B")

    restore_result = db.restore_from_backup(snapshot["filename"])
    assert restore_result.get("pre_restore_backup") is None

    db = reconnect_database()
    assert len(db.get_crew_members(session_id)) == 1

    print("Phase 5 tests OK")
    print(f"  Limit:   {db.get_database_backup_status()['max_backup_count']}")
    print(f"  Backups: {len(db.list_database_backups())}")


if __name__ == "__main__":
    main()
