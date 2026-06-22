-- =====================================================
-- USERS & ROLES (Authentifizierung)
-- =====================================================

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,

    password_hash TEXT,
    role_id INTEGER,
    active INTEGER NOT NULL DEFAULT 1,
    must_change_password INTEGER NOT NULL DEFAULT 0,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT,

    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_users_username
ON users(username);

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    role_name TEXT NOT NULL UNIQUE,
    description TEXT,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_roles_name
ON roles(role_name);

-- =====================================================
-- LOGIN HISTORY
-- =====================================================

CREATE TABLE IF NOT EXISTS login_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    login_time TEXT,
    logout_time TEXT,

    FOREIGN KEY(user_id)
        REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_login_history_user_id
ON login_history(user_id);

-- =====================================================
-- STANDARDROLLEN
-- =====================================================

INSERT OR IGNORE INTO roles (
    id,
    role_name,
    description,
    created_at
) VALUES (
    1,
    'Administrator',
    'Vollzugriff auf das gesamte System',
    datetime('now', 'localtime')
);

