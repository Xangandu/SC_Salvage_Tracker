"""Dashboard-Layout-Konfigurationen."""

DASHBOARD_LAYOUTS = {
    "blank": {
        "label": "Leer",
        "description": "Keine Widgets — leeres Dashboard",
        "order": (),
        "stretch": {},
        "cards": None,
    },
    "classic": {
        "label": "Classic",
        "description": "Alle Bereiche gleich gewichtet",
        "order": (
            "operation",
            "materials",
            "overview",
            "finance",
            "session",
            "refinery_stats",
        ),
        "stretch": {
            "operation": 1,
            "materials": 1,
            "overview": 1,
            "finance": 1,
            "session": 0,
            "refinery_stats": 0,
        },
        "cards": None,
    },
    "operations": {
        "label": "Operations",
        "description": "Fokus: aktive Session, Crew, Material",
        "order": (
            "operation",
            "session",
            "materials",
            "overview",
        ),
        "stretch": {
            "operation": 2,
            "session": 3,
            "materials": 1,
            "overview": 1,
        },
        "cards": {
            "operation": (
                "status",
                "crew",
                "rmc",
                "cm",
            ),
            "materials": (
                "rubble",
                "scraps",
                "salvage",
            ),
            "overview": (
                "active_sessions",
                "ready_sessions",
            ),
            "finance": (),
        },
    },
    "refinery": {
        "label": "Refinery",
        "description": "Fokus: Raffinerie-Jobs und Rohmaterial",
        "order": (
            "materials",
            "operation",
            "refinery_stats",
            "session",
        ),
        "stretch": {
            "materials": 2,
            "operation": 1,
            "refinery_stats": 2,
            "session": 2,
        },
        "cards": {
            "materials": (
                "rubble",
                "scraps",
                "salvage",
                "refinery_jobs",
            ),
            "operation": (
                "rmc",
                "cm",
                "status",
            ),
            "overview": (),
            "finance": (),
        },
    },
    "storage": {
        "label": "Storage",
        "description": "Fokus: Lager, Verkäufe, Gewinn",
        "order": (
            "overview",
            "finance",
            "materials",
        ),
        "stretch": {
            "overview": 2,
            "finance": 2,
            "materials": 1,
        },
        "cards": {
            "overview": (
                "ready_sessions",
                "sold_sessions",
                "active_sessions",
            ),
            "finance": (
                "total_sales",
                "total_profit",
            ),
            "materials": (
                "rubble",
                "scraps",
                "salvage",
            ),
            "operation": (),
        },
    },
}

SECTION_CARD_KEYS = {
    "operation": (
        "status",
        "crew",
        "rmc",
        "cm",
    ),
    "materials": (
        "rubble",
        "scraps",
        "salvage",
        "refinery_jobs",
    ),
    "overview": (
        "active_sessions",
        "total_sessions",
        "sold_sessions",
        "ready_sessions",
    ),
    "finance": (
        "total_sales",
        "total_profit",
    ),
}
