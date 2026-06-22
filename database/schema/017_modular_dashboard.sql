-- Modulares Dashboard (0.9.0)

CREATE TABLE IF NOT EXISTS user_dashboard_layout (
    user_id INTEGER PRIMARY KEY,
    layout_json TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS user_dashboard_presets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    preset_name TEXT NOT NULL,
    layout_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, preset_name)
);

CREATE INDEX IF NOT EXISTS idx_dashboard_presets_user
ON user_dashboard_presets(user_id);
