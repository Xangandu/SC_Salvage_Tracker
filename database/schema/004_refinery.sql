-- =====================================================
-- REFINERY_JOBS
-- =====================================================

CREATE TABLE IF NOT EXISTS refinery_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    station TEXT NOT NULL,

    start_time TEXT NOT NULL,
    end_time TEXT,

    status TEXT NOT NULL DEFAULT 'RUNNING',

    cost REAL NOT NULL DEFAULT 0,

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT,
    created_by INTEGER,
    updated_by INTEGER,

    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_refinery_jobs_status
ON refinery_jobs(status);

-- =====================================================
-- REFINERY_JOB_ITEMS
-- Verbindet Material-Batches mit Raffineriejobs
-- =====================================================

CREATE TABLE IF NOT EXISTS refinery_job_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    job_id INTEGER NOT NULL,
    batch_id INTEGER NOT NULL,

    input_material TEXT,
    input_quantity REAL NOT NULL,

    output_material TEXT,
    output_quantity REAL NOT NULL DEFAULT 0,

    yield_percent REAL NOT NULL DEFAULT 0,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT,

    FOREIGN KEY (job_id)
        REFERENCES refinery_jobs(id),

    FOREIGN KEY (batch_id)
        REFERENCES material_batches(id)
);

CREATE INDEX IF NOT EXISTS idx_refinery_job_items_job_id
ON refinery_job_items(job_id);

CREATE INDEX IF NOT EXISTS idx_refinery_job_items_batch_id
ON refinery_job_items(batch_id);
