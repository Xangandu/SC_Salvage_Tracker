-- =====================================================
-- SALES
-- =====================================================

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    location TEXT NOT NULL,
    sale_date TEXT NOT NULL,

    total_amount REAL NOT NULL DEFAULT 0,

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT,
    created_by INTEGER,
    updated_by INTEGER,

    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_sales_date
ON sales(sale_date);

-- =====================================================
-- SALE_ITEMS
-- =====================================================

CREATE TABLE IF NOT EXISTS sale_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    sale_id INTEGER NOT NULL,
    storage_item_id INTEGER NOT NULL,

    quantity REAL NOT NULL,
    unit_price REAL NOT NULL,
    total_price REAL NOT NULL,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),

    FOREIGN KEY (sale_id)
        REFERENCES sales(id),

    FOREIGN KEY (storage_item_id)
        REFERENCES storage_items(id)
);

CREATE INDEX IF NOT EXISTS idx_sale_items_sale_id
ON sale_items(sale_id);

CREATE INDEX IF NOT EXISTS idx_sale_items_storage_item_id
ON sale_items(storage_item_id);
