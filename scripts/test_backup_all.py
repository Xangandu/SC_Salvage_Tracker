"""Alle Backup-/Migrations-Tests der Version 0.13.0 nacheinander."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = [
    "test_backup_migration.py",
    "test_backup_phase2.py",
    "test_backup_phase3.py",
    "test_backup_phase4.py",
    "test_backup_phase5.py",
    "integration_test_flow.py",
]


def main():
    failed = []

    for name in SCRIPTS:
        path = ROOT / "scripts" / name
        print("=" * 60)
        print(f"RUN {name}")
        print("=" * 60)
        result = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(ROOT),
        )

        if result.returncode != 0:
            failed.append(name)

    print("=" * 60)

    if failed:
        print("FEHLGESCHLAGEN:", ", ".join(failed))
        return 1

    print("ALLE TESTS OK (0.13.0 Database Guard)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
