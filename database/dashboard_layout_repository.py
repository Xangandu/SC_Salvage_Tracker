"""Speichern und Laden modularer Dashboard-Layouts."""

import json

from config.debug import debug_log
from ui.dashboard_grid_utils import (
    migrate_layout,
    layout_needs_migration,
)

MAX_CUSTOM_PRESETS = 10


class DashboardLayoutRepository:

    def __init__(self, database):
        self.db = database
        self.cursor = database.cursor
        self.connection = database.connection

    def get_active_layout(self, user_id):
        self.cursor.execute(
            """
            SELECT layout_json
            FROM user_dashboard_layout
            WHERE user_id = ?
            """,
            (user_id,),
        )
        row = self.cursor.fetchone()
        if not row or not row[0]:
            return None
        raw = json.loads(row[0])
        migrated = migrate_layout(raw)
        if layout_needs_migration(raw):
            self.save_active_layout(user_id, migrated)
        return migrated

    def save_active_layout(self, user_id, layout):
        payload = json.dumps(
            migrate_layout(layout),
            ensure_ascii=False,
        )
        self.cursor.execute(
            """
            INSERT INTO user_dashboard_layout (
                user_id,
                layout_json,
                updated_at
            )
            VALUES (?, ?, datetime('now', 'localtime'))
            ON CONFLICT(user_id) DO UPDATE SET
                layout_json = excluded.layout_json,
                updated_at = datetime('now', 'localtime')
            """,
            (user_id, payload),
        )
        self.connection.commit()
        debug_log("Dashboard-Layout gespeichert:", user_id)

    def list_custom_presets(self, user_id):
        self.cursor.execute(
            """
            SELECT id, preset_name, updated_at
            FROM user_dashboard_presets
            WHERE user_id = ?
            ORDER BY preset_name COLLATE NOCASE
            """,
            (user_id,),
        )
        return self.cursor.fetchall()

    def get_custom_preset(self, user_id, preset_name):
        self.cursor.execute(
            """
            SELECT layout_json
            FROM user_dashboard_presets
            WHERE user_id = ? AND preset_name = ?
            """,
            (user_id, preset_name),
        )
        row = self.cursor.fetchone()
        if not row:
            return None
        raw = json.loads(row[0])
        migrated = migrate_layout(raw)
        if layout_needs_migration(raw):
            self.save_custom_preset(user_id, preset_name, migrated)
        return migrated

    def save_custom_preset(self, user_id, preset_name, layout):
        count = self.count_custom_presets(user_id)
        self.cursor.execute(
            """
            SELECT id FROM user_dashboard_presets
            WHERE user_id = ? AND preset_name = ?
            """,
            (user_id, preset_name),
        )
        exists = self.cursor.fetchone()

        if not exists and count >= MAX_CUSTOM_PRESETS:
            raise ValueError(
                f"Maximal {MAX_CUSTOM_PRESETS} eigene Presets erlaubt."
            )

        payload = json.dumps(
            migrate_layout(layout),
            ensure_ascii=False,
        )
        self.cursor.execute(
            """
            INSERT INTO user_dashboard_presets (
                user_id,
                preset_name,
                layout_json,
                updated_at
            )
            VALUES (?, ?, ?, datetime('now', 'localtime'))
            ON CONFLICT(user_id, preset_name) DO UPDATE SET
                layout_json = excluded.layout_json,
                updated_at = datetime('now', 'localtime')
            """,
            (user_id, preset_name, payload),
        )
        self.connection.commit()

    def delete_custom_preset(self, user_id, preset_name):
        self.cursor.execute(
            """
            DELETE FROM user_dashboard_presets
            WHERE user_id = ? AND preset_name = ?
            """,
            (user_id, preset_name),
        )
        self.connection.commit()

    def count_custom_presets(self, user_id):
        self.cursor.execute(
            """
            SELECT COUNT(*) FROM user_dashboard_presets
            WHERE user_id = ?
            """,
            (user_id,),
        )
        return self.cursor.fetchone()[0]
