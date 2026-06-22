-- Theme- und Design-Einstellungen (0.8.9)

CREATE TABLE IF NOT EXISTS app_settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT
);

CREATE TABLE IF NOT EXISTS user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    theme TEXT,
    language TEXT,
    font_size TEXT,
    accent_color TEXT,
    transparency INTEGER,
    animations TEXT,
    dashboard_layout TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_user_settings_user
ON user_settings(user_id);

INSERT OR IGNORE INTO app_settings (setting_key, setting_value) VALUES
    ('theme', 'star_citizen'),
    ('language', 'de'),
    ('font_size', 'normal'),
    ('accent_color', ''),
    ('transparency', '100'),
    ('animations', 'full'),
    ('dashboard_layout', 'classic');
