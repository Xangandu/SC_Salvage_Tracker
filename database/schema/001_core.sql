PRAGMA foreign_keys = ON;

-- =====================================================
-- MISSIONS (Missionstypen / Vorlagen)
-- =====================================================

CREATE TABLE IF NOT EXISTS missions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    mission_name TEXT NOT NULL UNIQUE,
    mission_type TEXT,
    description TEXT,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT,

    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_missions_name
ON missions(mission_name);

-- =====================================================
-- SHIPS
-- =====================================================

CREATE TABLE IF NOT EXISTS ships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    ship_name TEXT NOT NULL UNIQUE,
    ship_type TEXT NOT NULL,
    description TEXT,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT,

    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_ships_name
ON ships(ship_name);

CREATE INDEX IF NOT EXISTS idx_ships_type
ON ships(ship_type);

-- =====================================================
-- MATERIAL_TYPES
-- =====================================================

CREATE TABLE IF NOT EXISTS material_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    material_code TEXT NOT NULL UNIQUE,
    material_name TEXT NOT NULL,
    description TEXT,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_material_types_code
ON material_types(material_code);

CREATE INDEX IF NOT EXISTS idx_material_types_name
ON material_types(material_name);

-- =====================================================
-- CREW_MEMBERS (Referenz)
-- =====================================================

CREATE TABLE IF NOT EXISTS crew_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    player_name TEXT NOT NULL UNIQUE,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT,

    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_crew_members_player_name
ON crew_members(player_name);
