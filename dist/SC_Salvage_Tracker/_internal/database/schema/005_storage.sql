-- =====================================================
-- STORAGE_ITEMS
-- Zentraler Materialbestand – alle Materialien landen hier
-- =====================================================

CREATE TABLE IF NOT EXISTS storage_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    material_type_id INTEGER NOT NULL,

    quantity REAL NOT NULL,

    source_type TEXT NOT NULL,
    source_id INTEGER,

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT,
    created_by INTEGER,
    updated_by INTEGER,

    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT,

    FOREIGN KEY (material_type_id)
        REFERENCES material_types(id)
);

CREATE INDEX IF NOT EXISTS idx_storage_items_material_type_id
ON storage_items(material_type_id);

CREATE INDEX IF NOT EXISTS idx_storage_items_source
ON storage_items(source_type, source_id);
