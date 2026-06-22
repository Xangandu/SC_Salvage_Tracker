"""Smoke test: Migration-Metadaten und DB-Backup (Phase 1)."""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config.paths as paths

_test_data = Path(tempfile.mkdtemp(prefix="sst_backup_test_"))
paths.data_dir = lambda: _test_data

from database.database import Database


def main():
    db = Database()

    status = db.get_schema_status()
    assert status["target_schema_version"] >= 24
    assert status["schema_version"] == status["target_schema_version"]
    assert status["migration_needed"] is False
    assert status["app_version"]

    backup = db.create_database_backup(reason="test")
    assert Path(backup["path"]).exists()

    backups = db.list_database_backups()
    assert len(backups) == 1

    info = db.get_database_backup_status()
    assert info["backup_count"] == 1
    assert info["max_backup_count"] == 20

    print("=" * 60)
    print("BACKUP / MIGRATION TEST OK")
    print(f"  Schema: {status['schema_version']}")
    print(f"  Backup: {backup['filename']}")
    print(f"  Ordner: {info['backup_directory']}")
    print("=" * 60)
    print(f"Test data: {_test_data}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
