"""Dashboard-Layout-Konfigurationen (Struktur; Labels über i18n)."""

DASHBOARD_LAYOUTS = {
    "blank": {
        "order": (),
        "stretch": {},
        "cards": None,
    },
    "classic": {
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


def dashboard_preset_label(preset_id: str) -> str:
    from config.i18n import tr

    return tr(f"dashboard.preset.{preset_id}.label", default=preset_id)


def dashboard_preset_description(preset_id: str) -> str:
    from config.i18n import tr

    return tr(f"dashboard.preset.{preset_id}.description", default="")
