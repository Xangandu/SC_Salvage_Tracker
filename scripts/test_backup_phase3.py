"""Phase 3: verify_database, rerun_migrations, reinitialize_database."""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config.paths as paths

_test_data = Path(tempfile.mkdtemp(prefix="sst_backup_p3_"))
paths.data_dir = lambda: _test_data

from database.database import Database
from database.access import reconnect_database


def main():
    db = Database()
    verify = db.verify_database()
    assert "schema_version" in verify
    assert "target_schema_version" in verify
    assert "ok" in verify
    print("verify_database:", verify)

    migrated = db.rerun_migrations()
    assert migrated["schema_version"] == migrated["target_schema_version"]
    print("rerun_migrations:", migrated["schema_version"])

    db.create_session(
        None,
        "TestShip",
        "2026-06-22 12:00:00",
        created_by=1,
    )

    result = db.reinitialize_database(clear_remember_me=False)
    assert result.get("schema_status")
    assert result["schema_status"]["schema_version"] == result[
        "schema_status"
    ]["target_schema_version"]

    fresh_db = reconnect_database()
    assert fresh_db.get_total_session_count() == 0, (
        "reinitialize should clear sessions"
    )

    print("reinitialize_database:", result["schema_status"]["schema_version"])
    print("Phase 3 tests OK")


if __name__ == "__main__":
    main()
