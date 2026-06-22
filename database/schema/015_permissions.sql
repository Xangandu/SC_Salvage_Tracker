-- =====================================================
-- PERMISSIONS (feingranulare Rechte)
-- =====================================================

CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    permission_name TEXT NOT NULL UNIQUE,
    description TEXT,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_permissions_name
ON permissions(permission_name);

-- =====================================================
-- ROLE_PERMISSIONS (Rollen ↔ Rechte)
-- =====================================================

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,

    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),

    PRIMARY KEY (role_id, permission_id),

    FOREIGN KEY (role_id)
        REFERENCES roles(id),

    FOREIGN KEY (permission_id)
        REFERENCES permissions(id)
);

CREATE INDEX IF NOT EXISTS idx_role_permissions_role
ON role_permissions(role_id);

-- =====================================================
-- RECHTE-KATALOG (nur Definitionen, keine Rollenzuweisung)
-- =====================================================

INSERT OR IGNORE INTO permissions (permission_name, description) VALUES
    ('users.manage', 'Benutzer verwalten'),
    ('roles.manage', 'Rollen und Rechte verwalten'),
    ('settings.manage', 'Systemeinstellungen ändern'),
    ('database.reset', 'Datenbank zurücksetzen'),
    ('sessions.manage', 'Alle Sitzungen verwalten'),
    ('sessions.manage_own', 'Eigene Sitzungen verwalten'),
    ('crew.manage', 'Crew verwalten'),
    ('refinery.manage', 'Raffinerie verwalten'),
    ('sales.manage', 'Verkäufe durchführen'),
    ('payouts.manage', 'Auszahlungen erstellen'),
    ('payouts.approve', 'Auszahlungen freigeben'),
    ('payouts.view_own', 'Eigene Auszahlungen ansehen'),
    ('history.view', 'Historie ansehen'),
    ('statistics.view', 'Statistiken und Auszahlung ansehen'),
    ('dashboard.view', 'Dashboard nutzen');
