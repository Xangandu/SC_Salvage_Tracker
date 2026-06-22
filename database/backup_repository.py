"""
Datenbank-Backups: .db-Kopien unter data/backups/

Backups enthalten die SQLite-Datei; beim Wiederherstellen (Phase 2+)
übernimmt das Programm-Schema via Migration.
"""

from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from config.paths import backups_dir
from database.migration_manager import (
    BACKUP_AUTO_BEFORE_RESET_KEY,
    BACKUP_AUTO_BEFORE_RESTORE_KEY,
    BACKUP_MAX_COUNT_KEY,
    DEFAULT_BACKUP_MAX_COUNT,
)


class BackupRepository:
    BACKUP_PREFIX = "backup_"
    BACKUP_SUFFIX = ".db"

    def __init__(self, db):
        self.db = db

    @classmethod
    def backup_directory(cls) -> Path:
        return backups_dir()

    @classmethod
    def _is_backup_file(cls, path: Path) -> bool:
        return (
            path.is_file()
            and path.suffix.lower() == cls.BACKUP_SUFFIX
            and path.name.startswith(cls.BACKUP_PREFIX)
        )

    def max_backup_count(self) -> int:
        if not hasattr(self.db, "settings"):
            return DEFAULT_BACKUP_MAX_COUNT

        raw = self.db.settings.get_app_setting(
            BACKUP_MAX_COUNT_KEY,
            str(DEFAULT_BACKUP_MAX_COUNT),
        )

        try:
            value = int(raw or DEFAULT_BACKUP_MAX_COUNT)
        except (TypeError, ValueError):
            value = DEFAULT_BACKUP_MAX_COUNT

        return max(1, value)

    def _timestamp_label(self, when: datetime | None = None) -> str:
        moment = when or datetime.now()
        return moment.strftime("%Y-%m-%d_%H-%M-%S")

    def _backup_path_for(self, when: datetime | None = None) -> Path:
        label = self._timestamp_label(when)
        return (
            self.backup_directory()
            / f"{self.BACKUP_PREFIX}{label}{self.BACKUP_SUFFIX}"
        )

    def list_backups(self) -> list[dict]:
        directory = self.backup_directory()

        if not directory.exists():
            return []

        backups = []

        for path in directory.glob(
            f"{self.BACKUP_PREFIX}*{self.BACKUP_SUFFIX}"
        ):
            if not self._is_backup_file(path):
                continue

            stat = path.stat()
            backups.append({
                "path": str(path),
                "filename": path.name,
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(
                    stat.st_mtime
                ).strftime("%Y-%m-%d %H:%M:%S"),
            })

        backups.sort(
            key=lambda item: item["filename"],
            reverse=True,
        )
        return backups

    def create_backup(
        self,
        *,
        reason: str = "manual",
    ) -> dict:
        source_path = self.db.database_path()

        if not source_path.exists():
            raise FileNotFoundError(
                "Datenbankdatei nicht gefunden."
            )

        directory = self.backup_directory()
        directory.mkdir(parents=True, exist_ok=True)

        created_at = datetime.now()
        label = self._timestamp_label(created_at)
        destination = (
            directory
            / f"{self.BACKUP_PREFIX}{label}{self.BACKUP_SUFFIX}"
        )
        suffix = 0

        while destination.exists():
            suffix += 1
            destination = (
                directory
                / f"{self.BACKUP_PREFIX}{label}_{suffix}"
                f"{self.BACKUP_SUFFIX}"
            )

        self.db.connection.commit()
        dest_conn = sqlite3.connect(destination)
        try:
            self.db.connection.backup(dest_conn)
        finally:
            dest_conn.close()

        removed = self.enforce_retention()

        stat = destination.stat()
        return {
            "path": str(destination),
            "filename": destination.name,
            "size_bytes": stat.st_size,
            "created_at": created_at.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "reason": reason,
            "removed_count": removed,
        }

    def enforce_retention(self) -> int:
        backups = self.list_backups()
        limit = self.max_backup_count()
        removed = 0

        for entry in backups[limit:]:
            path = Path(entry["path"])

            if path.exists():
                path.unlink()
                removed += 1

        return removed

    def delete_backup(self, filename: str) -> None:
        path = self.backup_directory() / filename

        if not self._is_backup_file(path):
            raise ValueError(
                "Ungültige Backup-Datei."
            )

        if not path.exists():
            raise FileNotFoundError(
                "Backup nicht gefunden."
            )

        path.unlink()

    def resolve_backup_path(self, filename: str) -> Path:
        path = self.backup_directory() / filename

        if not self._is_backup_file(path):
            raise ValueError(
                "Ungültige Backup-Datei."
            )

        if not path.exists():
            raise FileNotFoundError(
                "Backup nicht gefunden."
            )

        return path

    @classmethod
    def auto_backup_enabled(
        cls,
        db,
        setting_key: str,
        *,
        default: bool = True,
    ) -> bool:
        if not hasattr(db, "settings"):
            return default

        raw = db.settings.get_app_setting(
            setting_key,
            "1" if default else "0",
        )
        return str(raw).strip().lower() not in (
            "0",
            "false",
            "no",
            "off",
        )

    def create_backup_if_enabled(
        self,
        reason: str,
        setting_key: str,
        *,
        default: bool = True,
    ) -> dict | None:
        if not self.auto_backup_enabled(
            self.db,
            setting_key,
            default=default,
        ):
            return None

        return self.create_backup(reason=reason)

    @classmethod
    def copy_backup_to_database(
        cls,
        backup_path: Path,
        target_path: Path,
    ) -> None:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_path, target_path)

        for suffix in ("-wal", "-shm"):
            sidecar = target_path.with_name(
                target_path.name + suffix
            )
            if sidecar.exists():
                sidecar.unlink()

    def get_status(self) -> dict:
        backups = self.list_backups()
        total_size = sum(
            item["size_bytes"] for item in backups
        )

        return {
            "backup_directory": str(self.backup_directory()),
            "backup_count": len(backups),
            "total_size_bytes": total_size,
            "max_backup_count": self.max_backup_count(),
            "auto_before_reset": self.auto_backup_enabled(
                self.db,
                BACKUP_AUTO_BEFORE_RESET_KEY,
            ),
            "auto_before_restore": self.auto_backup_enabled(
                self.db,
                BACKUP_AUTO_BEFORE_RESTORE_KEY,
            ),
            "latest_backup": backups[0] if backups else None,
        }
