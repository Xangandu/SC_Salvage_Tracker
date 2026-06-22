"""Phase-2-Test: Auto-Backup vor Reset/Restore und Migration nach Restore."""

import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config.paths as paths

_test_data = Path(tempfile.mkdtemp(prefix="sst_backup_p2_"))
paths.data_dir = lambda: _test_data

from database.database import Database
from database.access import reconnect_database


def assert_eq(label, got, expected):
    if got != expected:
        raise AssertionError(
            f"{label}: expected {expected!r}, got {got!r}"
        )


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
    assert Path(snapshot["path"]).exists()

    db.add_crew_member(session_id, "Pilot-B")
    crew_after_change = len(db.get_crew_members(session_id))
    assert_eq("crew after change", crew_after_change, 2)

    restore_result = Database._do_restore_from_backup(
        snapshot["filename"]
    )
    assert restore_result["schema_status"]["migration_needed"] is False
    assert_eq(
        "schema after restore",
        restore_result["schema_status"]["schema_version"],
        restore_result["schema_status"]["target_schema_version"],
    )

    db = reconnect_database()
    crew_restored = len(db.get_crew_members(session_id))
    assert_eq("crew after restore", crew_restored, 1)

    pre_restore = restore_result.get("pre_restore_backup")
    assert pre_restore is not None

    db.add_crew_member(session_id, "Temp")
    reset_result = Database.reset_database_with_backup()
    pre_reset = reset_result.get("pre_reset_backup")
    assert pre_reset is not None
    assert Path(pre_reset["path"]).exists()
    assert not db.database_path().exists()

    db = Database()
    sessions = db.get_total_session_count()
    assert_eq("sessions after reset", sessions, 0)

    old_backup = snapshot["path"]
    conn = sqlite3.connect(old_backup)
    try:
        conn.execute(
            "DELETE FROM app_settings WHERE setting_key = 'schema_version'"
        )
        conn.commit()
    finally:
        conn.close()

    Database._do_restore_from_backup(snapshot["filename"])
    db = reconnect_database()
    status = db.get_schema_status()
    assert status["schema_version"] == status["target_schema_version"]

    backups = db.list_database_backups()
    assert len(backups) >= 2

    print("=" * 60)
    print("PHASE 2 BACKUP / RESTORE / RESET TEST OK")
    print(f"  Backups: {len(backups)}")
    print(f"  Schema:  {status['schema_version']}")
    print("=" * 60)
    print(f"Test data: {_test_data}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
