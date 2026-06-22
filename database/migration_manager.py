"""
Schema-Versionierung und Migrations-Metadaten.

Schritt 1 (graduell): Bestehende Upgrades bleiben in Database.__init__.
Dieses Modul verwaltet schema_version / app_version / build_version in
app_settings und bereitet spätere Migrationsschritte vor.
"""

from __future__ import annotations

import re
from pathlib import Path

from config.debug import debug_log
from config.version import APP_BUILD, APP_VERSION


SCHEMA_VERSION_KEY = "schema_version"
APP_VERSION_KEY = "app_version"
BUILD_VERSION_KEY = "build_version"

BACKUP_MAX_COUNT_KEY = "backup_max_count"
BACKUP_AUTO_ON_START_KEY = "backup_auto_on_start"
BACKUP_AUTO_BEFORE_RESET_KEY = "backup_auto_before_reset"
BACKUP_AUTO_BEFORE_RESTORE_KEY = "backup_auto_before_restore"

DEFAULT_BACKUP_MAX_COUNT = 20


class MigrationManager:
    def __init__(self, db):
        self.db = db
        self.cursor = db.cursor
        self.connection = db.connection

    def schema_directory(self) -> Path:
        return self.db.get_schema_directory()

    def target_schema_version(self) -> int:
        versions = []

        for schema_file in self.schema_directory().glob("*.sql"):
            match = re.match(r"^(\d+)", schema_file.name)

            if match:
                versions.append(int(match.group(1)))

        return max(versions) if versions else 0

    def current_schema_version(self) -> int:
        if not hasattr(self.db, "settings"):
            return 0

        raw = self.db.settings.get_app_setting(
            SCHEMA_VERSION_KEY,
            "0",
        )

        try:
            return int(raw or 0)
        except (TypeError, ValueError):
            return 0

    def ensure_backup_defaults(self) -> None:
        if not hasattr(self.db, "settings"):
            return

        defaults = {
            BACKUP_MAX_COUNT_KEY: str(DEFAULT_BACKUP_MAX_COUNT),
            BACKUP_AUTO_ON_START_KEY: "0",
            BACKUP_AUTO_BEFORE_RESET_KEY: "1",
            BACKUP_AUTO_BEFORE_RESTORE_KEY: "1",
        }

        for key, value in defaults.items():
            if self.db.settings.get_app_setting(key) is None:
                self.db.settings.set_app_setting(key, value)

    def finalize_version_metadata(self) -> dict:
        if not hasattr(self.db, "settings"):
            return {}

        target = self.target_schema_version()
        previous = self.current_schema_version()

        self.db.settings.set_app_setting(
            SCHEMA_VERSION_KEY,
            str(target),
        )
        self.db.settings.set_app_setting(
            APP_VERSION_KEY,
            APP_VERSION,
        )
        self.db.settings.set_app_setting(
            BUILD_VERSION_KEY,
            APP_BUILD,
        )

        if target > previous and self.db._table_exists(
            "database_version"
        ):
            self.cursor.execute("""
            INSERT INTO database_version (version)
            VALUES (?)
            """, (str(target),))
            self.connection.commit()

        if target > previous:
            debug_log(
                "SCHEMA-MIGRATION:",
                f"{previous} -> {target}",
            )

        return self.get_status()

    def get_status(self) -> dict:
        target = self.target_schema_version()
        current = self.current_schema_version()

        app_version = APP_VERSION
        build_version = APP_BUILD

        if hasattr(self.db, "settings"):
            app_version = (
                self.db.settings.get_app_setting(
                    APP_VERSION_KEY,
                    APP_VERSION,
                )
                or APP_VERSION
            )
            build_version = (
                self.db.settings.get_app_setting(
                    BUILD_VERSION_KEY,
                    APP_BUILD,
                )
                or APP_BUILD
            )
            current = self.current_schema_version()

        return {
            "target_schema_version": target,
            "schema_version": current,
            "app_version": app_version,
            "build_version": build_version,
            "database_path": str(self.db.database_path()),
            "migration_needed": current < target,
        }

    def verify_database(self) -> dict:
        status = self.get_status()
        status["ok"] = not status["migration_needed"]
        return status
