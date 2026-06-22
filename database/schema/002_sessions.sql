-- =====================================================
-- SESSIONS (Salvage-Runs)
-- =====================================================

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    mission_id INTEGER,

    session_name TEXT NOT NULL,

    start_time TEXT NOT NULL,
    end_time TEXT,

    status TEXT NOT NULL DEFAULT 'ACTIVE',

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT,
    created_by INTEGER,
    updated_by INTEGER,

    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT,

    FOREIGN KEY (mission_id)
        REFERENCES missions(id)
);

CREATE INDEX IF NOT EXISTS idx_sessions_status
ON sessions(status);

CREATE INDEX IF NOT EXISTS idx_sessions_mission_id
ON sessions(mission_id);

CREATE INDEX IF NOT EXISTS idx_sessions_start_time
ON sessions(start_time);

-- =====================================================
-- SESSION_SHIPS (Mehrere Schiffe pro Session)
-- =====================================================

CREATE TABLE IF NOT EXISTS session_ships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER NOT NULL,
    ship_id INTEGER NOT NULL,

    purpose TEXT,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),

    FOREIGN KEY (session_id)
        REFERENCES sessions(id),

    FOREIGN KEY (ship_id)
        REFERENCES ships(id)
);

CREATE INDEX IF NOT EXISTS idx_session_ships_session_id
ON session_ships(session_id);

CREATE INDEX IF NOT EXISTS idx_session_ships_ship_id
ON session_ships(ship_id);

-- =====================================================
-- SESSION_CREW (Mehrere Crewmitglieder pro Session)
-- =====================================================

CREATE TABLE IF NOT EXISTS session_crew (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER NOT NULL,
    crew_member_id INTEGER NOT NULL,

    role_name TEXT NOT NULL DEFAULT 'Operator',

    joined_at TEXT,
    left_at TEXT,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),

    FOREIGN KEY (session_id)
        REFERENCES sessions(id),

    FOREIGN KEY (crew_member_id)
        REFERENCES crew_members(id)
);

CREATE INDEX IF NOT EXISTS idx_session_crew_session_id
ON session_crew(session_id);

CREATE INDEX IF NOT EXISTS idx_session_crew_member_id
ON session_crew(crew_member_id);
