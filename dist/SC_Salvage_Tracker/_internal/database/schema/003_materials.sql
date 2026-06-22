-- =====================================================
-- MATERIAL_BATCHES
-- Jede Materialerfassung erzeugt einen nachverfolgbaren Batch
-- =====================================================

CREATE TABLE IF NOT EXISTS material_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER NOT NULL,
    material_type_id INTEGER NOT NULL,

    quantity REAL NOT NULL,

    remaining_quantity REAL,

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT,
    created_by INTEGER,
    updated_by INTEGER,

    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT,

    FOREIGN KEY (session_id)
        REFERENCES sessions(id),

    FOREIGN KEY (material_type_id)
        REFERENCES material_types(id)
);

CREATE INDEX IF NOT EXISTS idx_material_batches_session_id
ON material_batches(session_id);

CREATE INDEX IF NOT EXISTS idx_material_batches_material_type_id
ON material_batches(material_type_id);

CREATE INDEX IF NOT EXISTS idx_material_batches_created_at
ON material_batches(created_at);
