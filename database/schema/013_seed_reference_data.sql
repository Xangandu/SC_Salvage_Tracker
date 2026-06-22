-- =====================================================
-- REFERENZDATEN (Missionen, Schiffe, Materialien, Kosten)
-- =====================================================

-- Missionstypen
INSERT OR IGNORE INTO missions (mission_name, mission_type, created_at) VALUES
    ('Panels', 'Salvage', datetime('now', 'localtime')),
    ('Hammerhead', 'Salvage', datetime('now', 'localtime')),
    ('Constellation', 'Salvage', datetime('now', 'localtime')),
    ('890 Jump', 'Salvage', datetime('now', 'localtime'));

-- Schiffe
INSERT OR IGNORE INTO ships (ship_name, ship_type, created_at) VALUES
    ('Vulture', 'Salvage', datetime('now', 'localtime')),
    ('Reclaimer', 'Salvage', datetime('now', 'localtime')),
    ('Prospector', 'Mining', datetime('now', 'localtime')),
    ('Mole', 'Mining', datetime('now', 'localtime')),
    ('RSI Salvation', 'Salvage', datetime('now', 'localtime')),
    ('MISC Fortune', 'Salvage', datetime('now', 'localtime')),
    ('Drake Vulture', 'Salvage', datetime('now', 'localtime')),
    ('ARGO MOTH', 'Salvage', datetime('now', 'localtime')),
    ('Aegis Reclaimer', 'Salvage', datetime('now', 'localtime'));

-- Materialtypen
-- RMC / CM = verkaufbar (CM nur nach Raffinerie)
-- CM_RUBBLE / CM_SCRAPS / CM_SALVAGE = Rohmaterial (nur Raffinerie-Input)
INSERT OR IGNORE INTO material_types (material_code, material_name, created_at) VALUES
    ('RMC', 'Recyclable Material Composite', datetime('now', 'localtime')),
    ('CM', 'Construction Material', datetime('now', 'localtime')),
    ('CM_RUBBLE', 'CM Rubble', datetime('now', 'localtime')),
    ('CM_SCRAPS', 'CM Scraps', datetime('now', 'localtime')),
    ('CM_SALVAGE', 'CM Salvage', datetime('now', 'localtime')),
    ('SALVAGE', 'Salvage', datetime('now', 'localtime')),
    ('Quantanium', 'Quantanium', datetime('now', 'localtime')),
    ('Gold', 'Gold', datetime('now', 'localtime')),
    ('Bexalite', 'Bexalite', datetime('now', 'localtime'));

-- Kostenarten
INSERT OR IGNORE INTO cost_types (cost_code, cost_name, created_at) VALUES
    ('Mission', 'Mission', datetime('now', 'localtime')),
    ('Fuel', 'Treibstoff', datetime('now', 'localtime')),
    ('Repair', 'Reparatur', datetime('now', 'localtime')),
    ('Refinery', 'Raffinerie', datetime('now', 'localtime')),
    ('Transport', 'Transport', datetime('now', 'localtime'));

-- Version
INSERT OR IGNORE INTO version_info (version, build, release_date, created_at)
SELECT '0.8.4 Alpha', '2026.06', date('now', 'localtime'), datetime('now', 'localtime')
WHERE NOT EXISTS (
    SELECT 1 FROM version_info WHERE version = '0.8.4 Alpha'
);

INSERT OR IGNORE INTO version_info (version, build, release_date, created_at)
SELECT '0.8.3 Alpha', '2026.06', date('now', 'localtime'), datetime('now', 'localtime')
WHERE NOT EXISTS (
    SELECT 1 FROM version_info WHERE version = '0.8.3 Alpha'
);
