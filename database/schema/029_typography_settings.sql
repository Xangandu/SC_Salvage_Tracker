-- Schrift-Einstellungen (JSON) — App-Default; Spalte user_settings.typography_json
-- wird in settings_repository.migrate_settings_schema() angelegt (idempotent).

INSERT OR IGNORE INTO app_settings (setting_key, setting_value)
VALUES ('typography_json', '');
