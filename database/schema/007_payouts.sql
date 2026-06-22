-- =====================================================
-- PAYOUTS
-- =====================================================

CREATE TABLE IF NOT EXISTS payouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    sale_id INTEGER NOT NULL,

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT,
    created_by INTEGER,
    approved_by INTEGER,
    updated_by INTEGER,

    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT,

    FOREIGN KEY (sale_id)
        REFERENCES sales(id)
);

CREATE INDEX IF NOT EXISTS idx_payouts_sale_id
ON payouts(sale_id);

-- =====================================================
-- PAYOUT_ITEMS
-- =====================================================

CREATE TABLE IF NOT EXISTS payout_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    payout_id INTEGER NOT NULL,

    crew_member TEXT NOT NULL,
    amount REAL NOT NULL,

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),

    FOREIGN KEY (payout_id)
        REFERENCES payouts(id)
);

CREATE INDEX IF NOT EXISTS idx_payout_items_payout_id
ON payout_items(payout_id);
