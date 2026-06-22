-- =====================================================
-- COST_TYPES
-- =====================================================

CREATE TABLE IF NOT EXISTS cost_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    cost_code TEXT NOT NULL UNIQUE,
    cost_name TEXT NOT NULL,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_cost_types_code
ON cost_types(cost_code);

-- =====================================================
-- COSTS
-- =====================================================

CREATE TABLE IF NOT EXISTS costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER,

    cost_type_id INTEGER NOT NULL,

    amount REAL NOT NULL,

    paid_by TEXT,

    description TEXT,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT,
    created_by INTEGER,
    updated_by INTEGER,

    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT,

    FOREIGN KEY (session_id)
        REFERENCES sessions(id),

    FOREIGN KEY (cost_type_id)
        REFERENCES cost_types(id)
);

CREATE INDEX IF NOT EXISTS idx_costs_session_id
ON costs(session_id);

CREATE INDEX IF NOT EXISTS idx_costs_cost_type_id
ON costs(cost_type_id);
