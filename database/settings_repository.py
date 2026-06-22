"""Persistenz für App- und Benutzer-Designeinstellungen."""

from config.debug import debug_log

DEFAULT_APP_SETTINGS = {
    "theme": "star_citizen",
    "language": "de",
    "font_size": "normal",
    "accent_color": "",
    "transparency": "100",
    "animations": "full",
    "dashboard_layout": "classic",
    "dashboard_font_scale": "200",
    "dashboard_title_font_scale": "",
    "dashboard_button_font_scale": "",
}

DEFAULT_USER_SETTINGS = {
    "theme": None,
    "language": None,
    "font_size": None,
    "accent_color": None,
    "transparency": None,
    "animations": None,
    "dashboard_layout": None,
    "dashboard_font_scale": None,
    "dashboard_title_font_scale": None,
    "dashboard_button_font_scale": None,
}


class SettingsRepository:

    def __init__(self, database):
        self.db = database
        self.cursor = database.cursor
        self.connection = database.connection
        self.migrate_settings_schema()

    def migrate_settings_schema(self):
        columns = {
            row[1]
            for row in self.cursor.execute(
                "PRAGMA table_info(user_settings)"
            )
        }
        if "dashboard_font_scale" not in columns:
            self.cursor.execute(
                """
                ALTER TABLE user_settings
                ADD COLUMN dashboard_font_scale INTEGER
                """
            )
            self.connection.commit()

        columns = {
            row[1]
            for row in self.cursor.execute(
                "PRAGMA table_info(user_settings)"
            )
        }
        if "dashboard_title_font_scale" not in columns:
            self.cursor.execute(
                """
                ALTER TABLE user_settings
                ADD COLUMN dashboard_title_font_scale INTEGER
                """
            )
            self.connection.commit()

        columns = {
            row[1]
            for row in self.cursor.execute(
                "PRAGMA table_info(user_settings)"
            )
        }
        if "dashboard_button_font_scale" not in columns:
            self.cursor.execute(
                """
                ALTER TABLE user_settings
                ADD COLUMN dashboard_button_font_scale INTEGER
                """
            )
            self.connection.commit()

        if self.get_app_setting("dashboard_font_scale") is None:
            self.set_app_setting(
                "dashboard_font_scale",
                DEFAULT_APP_SETTINGS["dashboard_font_scale"],
            )

    def get_app_setting(self, key, default=None):
        self.cursor.execute(
            """
            SELECT setting_value
            FROM app_settings
            WHERE setting_key = ?
            """,
            (key,),
        )
        row = self.cursor.fetchone()
        if row is None:
            return default
        return row[0]

    def set_app_setting(self, key, value):
        self.cursor.execute(
            """
            INSERT INTO app_settings (setting_key, setting_value)
            VALUES (?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value = excluded.setting_value
            """,
            (key, value),
        )
        self.connection.commit()

    def get_app_settings(self):
        settings = dict(DEFAULT_APP_SETTINGS)
        self.cursor.execute(
            "SELECT setting_key, setting_value FROM app_settings"
        )
        for key, value in self.cursor.fetchall():
            settings[key] = value
        return settings

    def save_app_settings(self, settings):
        for key, value in settings.items():
            if value is None:
                continue
            self.set_app_setting(key, str(value))

    def _resolve_dashboard_scale(self, user, app, specific_key):
        raw = user.get(specific_key)
        if raw is None or raw == "":
            raw = app.get(specific_key)
        if raw is None or raw == "":
            widget_raw = user.get("dashboard_font_scale")
            if widget_raw is None or widget_raw == "":
                widget_raw = app.get(
                    "dashboard_font_scale",
                    DEFAULT_APP_SETTINGS["dashboard_font_scale"],
                )
            return int(widget_raw)
        return int(raw)

    def get_user_settings(self, user_id):
        self.cursor.execute(
            """
            SELECT
                theme,
                language,
                font_size,
                accent_color,
                transparency,
                animations,
                dashboard_layout,
                dashboard_font_scale,
                dashboard_title_font_scale,
                dashboard_button_font_scale
            FROM user_settings
            WHERE user_id = ?
            """,
            (user_id,),
        )
        row = self.cursor.fetchone()
        if not row:
            return dict(DEFAULT_USER_SETTINGS)

        keys = (
            "theme",
            "language",
            "font_size",
            "accent_color",
            "transparency",
            "animations",
            "dashboard_layout",
            "dashboard_font_scale",
            "dashboard_title_font_scale",
            "dashboard_button_font_scale",
        )
        return dict(zip(keys, row))

    def save_user_settings(self, user_id, settings):
        existing = self.get_user_settings(user_id)
        merged = {**existing, **settings}

        self.cursor.execute(
            """
            INSERT INTO user_settings (
                user_id,
                theme,
                language,
                font_size,
                accent_color,
                transparency,
                animations,
                dashboard_layout,
                dashboard_font_scale,
                dashboard_title_font_scale,
                dashboard_button_font_scale,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
            ON CONFLICT(user_id) DO UPDATE SET
                theme = excluded.theme,
                language = excluded.language,
                font_size = excluded.font_size,
                accent_color = excluded.accent_color,
                transparency = excluded.transparency,
                animations = excluded.animations,
                dashboard_layout = excluded.dashboard_layout,
                dashboard_font_scale = excluded.dashboard_font_scale,
                dashboard_title_font_scale = excluded.dashboard_title_font_scale,
                dashboard_button_font_scale = excluded.dashboard_button_font_scale,
                updated_at = datetime('now', 'localtime')
            """,
            (
                user_id,
                merged.get("theme"),
                merged.get("language"),
                merged.get("font_size"),
                merged.get("accent_color"),
                merged.get("transparency"),
                merged.get("animations"),
                merged.get("dashboard_layout"),
                merged.get("dashboard_font_scale"),
                merged.get("dashboard_title_font_scale"),
                merged.get("dashboard_button_font_scale"),
            ),
        )
        self.connection.commit()
        debug_log(
            "Benutzer-Einstellungen gespeichert:",
            user_id,
        )

    def resolve_effective_settings(self, user_id=None):
        """Benutzer-Einstellungen mit App-Defaults zusammenführen."""
        app = self.get_app_settings()
        user = (
            self.get_user_settings(user_id)
            if user_id
            else dict(DEFAULT_USER_SETTINGS)
        )

        def pick(key, cast=str):
            value = user.get(key)
            if value is not None and value != "":
                return cast(value) if cast else value
            return cast(app.get(key, DEFAULT_APP_SETTINGS[key]))

        transparency_raw = user.get("transparency")
        if transparency_raw is None or transparency_raw == "":
            transparency_raw = app.get(
                "transparency",
                DEFAULT_APP_SETTINGS["transparency"],
            )

        dashboard_font_raw = user.get("dashboard_font_scale")
        if dashboard_font_raw is None or dashboard_font_raw == "":
            dashboard_font_raw = app.get(
                "dashboard_font_scale",
                DEFAULT_APP_SETTINGS["dashboard_font_scale"],
            )

        accent = user.get("accent_color")
        if not accent:
            accent = app.get(
                "accent_color",
                DEFAULT_APP_SETTINGS["accent_color"],
            )

        return {
            "theme": pick("theme"),
            "language": pick("language"),
            "font_size": pick("font_size"),
            "accent_color": accent or "",
            "transparency": int(transparency_raw),
            "animations": pick("animations"),
            "dashboard_layout": pick("dashboard_layout"),
            "dashboard_font_scale": int(dashboard_font_raw),
            "dashboard_title_font_scale": self._resolve_dashboard_scale(
                user,
                app,
                "dashboard_title_font_scale",
            ),
            "dashboard_button_font_scale": self._resolve_dashboard_scale(
                user,
                app,
                "dashboard_button_font_scale",
            ),
        }
