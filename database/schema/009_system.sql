-- =====================================================
-- SETTINGS
-- =====================================================

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    setting_key TEXT NOT NULL UNIQUE,
    setting_value TEXT,

    description TEXT,

    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_settings_key
ON settings(setting_key);

-- =====================================================
-- VERSION_INFO
-- =====================================================

CREATE TABLE IF NOT EXISTS version_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    version TEXT NOT NULL,
    build TEXT NOT NULL,
    release_date TEXT NOT NULL,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_version_info_version
ON version_info(version);

-- =====================================================
-- DATABASE_VERSION (Schema-Migrationen)
-- =====================================================

CREATE TABLE IF NOT EXISTS database_version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    version TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_database_version_version
ON database_version(version);

-- Abwaertskompatibilitaet: system_settings -> settings
CREATE TABLE IF NOT EXISTS system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT NOT NULL UNIQUE,
    setting_value TEXT,
    description TEXT,
    updated_at TEXT NOT NULL
);
