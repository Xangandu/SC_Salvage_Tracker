"""Beispieldaten für die Kontext-Dashboard-Demo (keine DB)."""

GLOBAL_ALERT = {
    "severity": "warning",
    "message": "Auszahlung offen — RMC · Session „Stanton III Run“",
    "action_label": "Zu Auszahlung wechseln",
    "target_context": "payout",
}

CONTEXT_META= {
    "overview": ("ÜBERSICHT", "Alle Bereiche · Nächste Aktionen"),
    "session": ("SESSION", "Aktive Sitzung · Drake Vulture"),
    "refinery": ("RAFFINERIE", "Offene Jobs · Abholung & Effizienz"),
    "storage": ("LAGER", "Bestand · Standorte · Inaktiv-Warnungen"),
    "sales": ("VERKAUF", "Verkaufsbereit · Offene Verkäufe"),
    "payout": ("AUSZAHLUNG", "Offene Payouts · Session-Zuordnung"),
    "history": ("HISTORIE", "Verlauf · Statistik · Trends"),
}

OVERVIEW = {
    "actions": [
        ("Auszahlung offen", "RMC", "12.4 SCU", "Session Stanton III Run"),
        ("Abholbereit", "Raffinerie", "18.0 SCU Input", "CRU-L1"),
        ("Verkaufsbereit", "CM", "6.2 SCU", "Schiff · Vulture"),
        ("Inaktiv-Warnung", "RMC", "9.0 SCU", "Orison Lager · 14 Tage"),
    ],
    "kpis": {
        "revenue": 284_500,
        "profit": 192_300,
        "open_jobs": 2,
        "sellable_scu": 27.6,
    },
}

SESSION = {
    "ship": "Drake Vulture",
    "status": "ACTIVE",
    "status_label": "AKTIV",
    "crew": 1,
    "sessions_flown": 14,
    "session_scu_total": 42.8,
    "materials": {
        "RMC": 8.4,
        "CM": 3.2,
        "CM_RUBBLE": 12.0,
        "CM_SCRAPS": 6.5,
        "CM_SALVAGE": 4.1,
    },
    "locations": [
        ("Am Schiff (Vulture)", "RMC 4.0 · CM 2.1 SCU", 42),
        ("Session-Batches", "Rubble 12.0 · Scraps 6.5 SCU", 68),
        ("Raffinerie CRU-L1", "Job #17 · 18.0 SCU Input", 55),
        ("Lager Orison", "RMC 4.4 SCU (Reserve)", 28),
    ],
    "processes": [
        ("Raffinerie läuft", "CM_RUBBLE → CM · CRU-L1 · ~22 min"),
        ("Verkauf vorbereitet", "CM 2.1 SCU am Schiff"),
    ],
}

REFINERY = {
    "open_jobs": 2,
    "ready_jobs": 1,
    "avg_efficiency": 94.2,
    "total_input": 38.0,
    "total_output": 35.8,
    "jobs": [
        {
            "id": 17,
            "station": "CRU-L1",
            "status": "RUNNING",
            "status_label": "Läuft",
            "input_scu": 18.0,
            "eta_minutes": 22,
            "material": "CM_RUBBLE",
        },
        {
            "id": 16,
            "station": "HUR-L2",
            "status": "READY",
            "status_label": "Abholbereit",
            "input_scu": 20.0,
            "output_scu": 18.8,
            "material": "CM_SCRAPS",
        },
    ],
    "by_material": [
        ("CM_RUBBLE", 93.1, 8),
        ("CM_SCRAPS", 95.4, 6),
        ("CM_SALVAGE", 91.8, 3),
    ],
}

STORAGE = {
    "total_scu": 31.4,
    "locations": [
        ("Orison · Hangar 4", "RMC 9.0 · CM 2.4 SCU", True),
        ("Schiff · Vulture", "RMC 4.0 · CM 2.1 SCU", False),
        ("Grim HEX · Container", "CM 6.2 SCU", False),
        ("Reserve · Guild", "RMC 4.4 SCU", False),
    ],
    "idle_warnings": 1,
    "recent_events": [
        ("Heute 14:32", "Transfer", "RMC 4.4 SCU → Orison"),
        ("Gestern 21:10", "Reserve gesetzt", "Orison · Guild-Tag"),
        ("Mo 18:45", "Eingelagert", "CM 6.2 SCU · Grim HEX"),
    ],
}

SALES = {
    "ready_total_scu": 14.7,
    "ready_value_estimate": 48_200,
    "items": [
        ("RMC", "Orison Lager", 9.0, 31_500),
        ("CM", "Schiff · Vulture", 2.1, 8_400),
        ("CM", "Grim HEX", 6.2, 18_600),
    ],
    "pending_sales": 1,
    "pending_amount": 12_800,
}

PAYOUT = {
    "open_count": 2,
    "open_total": 44_300,
    "items": [
        ("Session Stanton III Run", "RMC", 12.4, 43_400, "Grim HEX"),
        ("Session Pyro Sweep", "CM", 0.8, 900, "Orison"),
    ],
}

HISTORY = {
    "sold_sessions": 11,
    "total_sessions": 14,
    "total_revenue": 284_500,
    "recent": [
        ("28.06.", "Verkauf abgeschlossen", "Session „Pyro Sweep“ · 18.400 aUEC"),
        ("27.06.", "Auszahlung", "RMC · Session „Stanton Belt“"),
        ("26.06.", "Raffinerie abgeschlossen", "Job #15 · 94.8 % Effizienz"),
        ("25.06.", "Session beendet", "Drake Vulture · 38.2 SCU"),
    ],
    "monthly_revenue": [
        ("Mär", 62_000),
        ("Apr", 78_400),
        ("Mai", 91_200),
        ("Jun", 52_900),
    ],
}
