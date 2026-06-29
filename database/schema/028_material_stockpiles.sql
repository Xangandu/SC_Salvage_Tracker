-- =====================================================
-- MATERIAL_STOCKPILES — ortsbezogener Bestand
-- =====================================================

CREATE TABLE IF NOT EXISTS material_stockpiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    material_type_id INTEGER NOT NULL,

    quantity_scu REAL NOT NULL CHECK (quantity_scu >= 0),

    location_kind TEXT NOT NULL DEFAULT 'STATION',
    location_key TEXT,
    location_label TEXT NOT NULL,

    status TEXT NOT NULL DEFAULT 'STORED',

    ship_id INTEGER,
    session_id INTEGER,
    refinery_job_id INTEGER,
    storage_item_id INTEGER,

    reserve_tag TEXT,
    notes TEXT,

    last_activity_at TEXT NOT NULL,
    idle_reminded_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT,
    created_by INTEGER,
    updated_by INTEGER,

    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT,

    FOREIGN KEY (material_type_id)
        REFERENCES material_types(id),
    FOREIGN KEY (ship_id)
        REFERENCES ships(id),
    FOREIGN KEY (session_id)
        REFERENCES sessions(id),
    FOREIGN KEY (refinery_job_id)
        REFERENCES refinery_jobs(id),
    FOREIGN KEY (storage_item_id)
        REFERENCES storage_items(id)
);

CREATE INDEX IF NOT EXISTS idx_material_stockpiles_location
ON material_stockpiles(location_key, material_type_id);

CREATE INDEX IF NOT EXISTS idx_material_stockpiles_status
ON material_stockpiles(status);

CREATE INDEX IF NOT EXISTS idx_material_stockpiles_activity
ON material_stockpiles(last_activity_at);

CREATE INDEX IF NOT EXISTS idx_material_stockpiles_ship
ON material_stockpiles(ship_id);

-- =====================================================
-- MATERIAL_STOCKPILE_EVENTS — Historie
-- =====================================================

CREATE TABLE IF NOT EXISTS material_stockpile_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    stockpile_id INTEGER,

    event_type TEXT NOT NULL,
    quantity_delta REAL,
    from_label TEXT,
    to_label TEXT,
    payload_json TEXT,
    notes TEXT,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    created_by INTEGER,

    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT,

    FOREIGN KEY (stockpile_id)
        REFERENCES material_stockpiles(id)
);

CREATE INDEX IF NOT EXISTS idx_stockpile_events_stockpile
ON material_stockpile_events(stockpile_id);

CREATE INDEX IF NOT EXISTS idx_stockpile_events_created
ON material_stockpile_events(created_at);

INSERT OR IGNORE INTO permissions (permission_name, description) VALUES
    ('storage.manage', 'Lager und Standorte verwalten');
