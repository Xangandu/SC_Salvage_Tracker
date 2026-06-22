"""Phase 4: list, delete, restore via instance API."""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config.paths as paths

_test_data = Path(tempfile.mkdtemp(prefix="sst_backup_p4_"))
paths.data_dir = lambda: _test_data

from database.database import Database
from database.access import reconnect_database


def main():
    db = Database()
    session_id = db.create_session(
        None,
        "TestShip",
        "2026-06-22 12:00:00",
        created_by=1,
    )
    db.add_crew_member(session_id, "Pilot-A")

    snapshot = db.create_database_backup(reason="snapshot")
    filename = snapshot["filename"]

    backups = db.list_database_backups()
    assert any(item["filename"] == filename for item in backups)

    db.add_crew_member(session_id, "Pilot-B")
    assert len(db.get_crew_members(session_id)) == 2

    restore_result = db.restore_from_backup(filename)
    assert restore_result["restored_from"] == filename

    db = reconnect_database()
    assert len(db.get_crew_members(session_id)) == 1

    extra = db.create_database_backup(reason="extra")
    backups = db.list_database_backups()
    assert len(backups) >= 2

    db.delete_database_backup(extra["filename"])
    backups_after = db.list_database_backups()
    assert not any(
        item["filename"] == extra["filename"]
        for item in backups_after
    )

    status = db.get_database_backup_status()
    assert status["backup_count"] == len(backups_after)
    assert Path(status["backup_directory"]).exists()

    print("Phase 4 tests OK")
    print(f"  Backups: {status['backup_count']}")
    print(f"  Ordner:  {status['backup_directory']}")


if __name__ == "__main__":
    main()
