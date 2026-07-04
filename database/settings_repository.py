"""Persistenz für App- und Benutzer-Designeinstellungen."""

from config.debug import debug_log
from config.font_families import DEFAULT_FONT_FAMILY
from config.typography import (
    TYPOGRAPHY_SETTINGS_KEY,
    TYPOGRAPHY_BASELINE_KEY,
    normalize_typography_settings,
    serialize_typography_settings,
)

DEFAULT_APP_SETTINGS = {
    "theme": "star_citizen",
    "language": "en",
    "font_size": "normal",
    "font_family": DEFAULT_FONT_FAMILY,
    "accent_color": "",
    "label_color": "",
    "primary_button_color": "",
    "secondary_button_color": "",
    "nav_width": "normal",
    "transparency": "100",
    "panel_transparency": "100",
    "table_density": "normal",
    "animations": "full",
    "dashboard_layout": "classic",
    "dashboard_font_scale": "100",
    "dashboard_title_font_scale": "",
    "dashboard_button_font_scale": "",
    TYPOGRAPHY_SETTINGS_KEY: "",
    TYPOGRAPHY_BASELINE_KEY: "",
    "update_auto_check": "1",
    "update_skipped_version": "",
    "update_last_check": "",
    "language_confirmed": "0",
}

DEFAULT_USER_SETTINGS = {
    "theme": None,
    "language": None,
    "font_size": None,
    "font_family": None,
    "accent_color": None,
    "label_color": None,
    "primary_button_color": None,
    "secondary_button_color": None,
    "nav_width": None,
    "transparency": None,
    "panel_transparency": None,
    "table_density": None,
    "animations": None,
    "dashboard_layout": None,
    "dashboard_font_scale": None,
    "dashboard_title_font_scale": None,
    "dashboard_button_font_scale": None,
    TYPOGRAPHY_SETTINGS_KEY: None,
    TYPOGRAPHY_BASELINE_KEY: None,
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

        columns = {
            row[1]
            for row in self.cursor.execute(
                "PRAGMA table_info(user_settings)"
            )
        }
        if "font_family" not in columns:
            self.cursor.execute(
                """
                ALTER TABLE user_settings
                ADD COLUMN font_family TEXT
                """
            )
            self.connection.commit()

        for column in (
            "label_color",
            "primary_button_color",
            "secondary_button_color",
            "nav_width",
            "panel_transparency",
            "table_density",
        ):
            columns = {
                row[1]
                for row in self.cursor.execute(
                    "PRAGMA table_info(user_settings)"
                )
            }
            if column not in columns:
                self.cursor.execute(
                    f"""
                    ALTER TABLE user_settings
                    ADD COLUMN {column} TEXT
                    """
                )
                self.connection.commit()

        columns = {
            row[1]
            for row in self.cursor.execute(
                "PRAGMA table_info(user_settings)"
            )
        }
        if TYPOGRAPHY_SETTINGS_KEY not in columns:
            self.cursor.execute(
                f"""
                ALTER TABLE user_settings
                ADD COLUMN {TYPOGRAPHY_SETTINGS_KEY} TEXT
                """
            )
            self.connection.commit()

        if TYPOGRAPHY_BASELINE_KEY not in columns:
            self.cursor.execute(
                f"""
                ALTER TABLE user_settings
                ADD COLUMN {TYPOGRAPHY_BASELINE_KEY} TEXT
                """
            )
            self.connection.commit()

        if self.get_app_setting("dashboard_font_scale") is None:
            self.set_app_setting(
                "dashboard_font_scale",
                DEFAULT_APP_SETTINGS["dashboard_font_scale"],
            )

        if self.get_app_setting("font_family") is None:
            self.set_app_setting(
                "font_family",
                DEFAULT_APP_SETTINGS["font_family"],
            )

        if self.get_app_setting("panel_transparency") is None:
            legacy = self.get_app_setting("transparency")
            if legacy is not None and legacy != "" and int(legacy) < 100:
                self.set_app_setting(
                    "panel_transparency",
                    legacy,
                )
            else:
                self.set_app_setting(
                    "panel_transparency",
                    DEFAULT_APP_SETTINGS["panel_transparency"],
                )

        if self.get_app_setting("table_density") is None:
            self.set_app_setting(
                "table_density",
                DEFAULT_APP_SETTINGS["table_density"],
            )

        if self.get_app_setting(TYPOGRAPHY_SETTINGS_KEY) is None:
            self.set_app_setting(
                TYPOGRAPHY_SETTINGS_KEY,
                DEFAULT_APP_SETTINGS[TYPOGRAPHY_SETTINGS_KEY],
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
                font_family,
                accent_color,
                label_color,
                primary_button_color,
                secondary_button_color,
                nav_width,
                transparency,
                panel_transparency,
                table_density,
                animations,
                dashboard_layout,
                dashboard_font_scale,
                dashboard_title_font_scale,
                dashboard_button_font_scale,
                typography_json,
                typography_baseline_json
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
            "font_family",
            "accent_color",
            "label_color",
            "primary_button_color",
            "secondary_button_color",
            "nav_width",
            "transparency",
            "panel_transparency",
            "table_density",
            "animations",
            "dashboard_layout",
            "dashboard_font_scale",
            "dashboard_title_font_scale",
            "dashboard_button_font_scale",
            TYPOGRAPHY_SETTINGS_KEY,
            TYPOGRAPHY_BASELINE_KEY,
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
                font_family,
                accent_color,
                label_color,
                primary_button_color,
                secondary_button_color,
                nav_width,
                transparency,
                panel_transparency,
                table_density,
                animations,
                dashboard_layout,
                dashboard_font_scale,
                dashboard_title_font_scale,
                dashboard_button_font_scale,
                typography_json,
                typography_baseline_json,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
            ON CONFLICT(user_id) DO UPDATE SET
                theme = excluded.theme,
                language = excluded.language,
                font_size = excluded.font_size,
                font_family = excluded.font_family,
                accent_color = excluded.accent_color,
                label_color = excluded.label_color,
                primary_button_color = excluded.primary_button_color,
                secondary_button_color = excluded.secondary_button_color,
                nav_width = excluded.nav_width,
                transparency = excluded.transparency,
                panel_transparency = excluded.panel_transparency,
                table_density = excluded.table_density,
                animations = excluded.animations,
                dashboard_layout = excluded.dashboard_layout,
                dashboard_font_scale = excluded.dashboard_font_scale,
                dashboard_title_font_scale = excluded.dashboard_title_font_scale,
                dashboard_button_font_scale = excluded.dashboard_button_font_scale,
                typography_json = excluded.typography_json,
                typography_baseline_json = excluded.typography_baseline_json,
                updated_at = datetime('now', 'localtime')
            """,
            (
                user_id,
                merged.get("theme"),
                merged.get("language"),
                merged.get("font_size"),
                merged.get("font_family"),
                merged.get("accent_color"),
                merged.get("label_color"),
                merged.get("primary_button_color"),
                merged.get("secondary_button_color"),
                merged.get("nav_width"),
                merged.get("transparency"),
                merged.get("panel_transparency"),
                merged.get("table_density"),
                merged.get("animations"),
                merged.get("dashboard_layout"),
                merged.get("dashboard_font_scale"),
                merged.get("dashboard_title_font_scale"),
                merged.get("dashboard_button_font_scale"),
                merged.get(TYPOGRAPHY_SETTINGS_KEY),
                merged.get(TYPOGRAPHY_BASELINE_KEY),
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

        panel_transparency_raw = user.get("panel_transparency")
        if panel_transparency_raw is None or panel_transparency_raw == "":
            panel_transparency_raw = app.get(
                "panel_transparency",
                DEFAULT_APP_SETTINGS["panel_transparency"],
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

        def pick_color(key):
            value = user.get(key)
            if value:
                return value
            return app.get(
                key,
                DEFAULT_APP_SETTINGS[key],
            ) or ""

        def pick_typography_json():
            value = user.get(TYPOGRAPHY_SETTINGS_KEY)
            if value is not None and str(value).strip():
                return serialize_typography_settings(
                    normalize_typography_settings(value)
                )
            app_value = app.get(
                TYPOGRAPHY_SETTINGS_KEY,
                DEFAULT_APP_SETTINGS[TYPOGRAPHY_SETTINGS_KEY],
            )
            return serialize_typography_settings(
                normalize_typography_settings(app_value)
            )

        def pick_typography_baseline_json():
            value = user.get(TYPOGRAPHY_BASELINE_KEY)
            if value is not None and str(value).strip():
                return serialize_typography_settings(
                    normalize_typography_settings(value)
                )
            app_value = app.get(
                TYPOGRAPHY_BASELINE_KEY,
                DEFAULT_APP_SETTINGS[TYPOGRAPHY_BASELINE_KEY],
            )
            return serialize_typography_settings(
                normalize_typography_settings(app_value)
            )

        return {
            "theme": pick("theme"),
            "language": pick("language"),
            "font_size": pick("font_size"),
            "font_family": pick("font_family"),
            "accent_color": accent or "",
            "label_color": pick_color("label_color"),
            "primary_button_color": pick_color(
                "primary_button_color"
            ),
            "secondary_button_color": pick_color(
                "secondary_button_color"
            ),
            "nav_width": pick("nav_width"),
            "transparency": int(transparency_raw),
            "panel_transparency": int(panel_transparency_raw),
            "table_density": pick("table_density"),
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
            TYPOGRAPHY_SETTINGS_KEY: pick_typography_json(),
            TYPOGRAPHY_BASELINE_KEY: pick_typography_baseline_json(),
        }
