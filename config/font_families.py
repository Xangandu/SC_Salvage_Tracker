"""Futuristische Schriftarten — Registry und Lade-Hilfen."""

from __future__ import annotations

from config.paths import asset_path

# Basis-Schriftarten im Star-Citizen-QSS (werden ersetzt).
BASE_HEADING_FONT = "Orbitron"
BASE_BODY_FONT = "Rajdhani"
DEFAULT_FONT_FAMILY = "oxanium"

FONT_FAMILIES: dict[str, dict] = {
    "launcher": {
        "label": "Launcher (Orbitron / Rajdhani)",
        "heading": "Orbitron",
        "body": "Rajdhani",
        "files": (
            "assets/fonts/Orbitron-Bold.ttf",
            "assets/fonts/Rajdhani-Regular.ttf",
            "assets/fonts/Rajdhani-Bold.ttf",
        ),
    },
    "system": {
        "label": "System (Segoe UI)",
        "heading": "Segoe UI",
        "body": "Segoe UI",
        "files": (),
    },
    "exo2": {
        "label": "Exo 2",
        "heading": "Exo 2",
        "body": "Exo 2",
        "files": (
            "assets/fonts/scifi/Exo2-Variable.ttf",
        ),
    },
    "audiowide": {
        "label": "Audiowide",
        "heading": "Audiowide",
        "body": "Audiowide",
        "files": (
            "assets/fonts/scifi/Audiowide-Regular.ttf",
        ),
    },
    "michroma_exo2": {
        "label": "Michroma / Exo 2",
        "heading": "Michroma",
        "body": "Exo 2",
        "files": (
            "assets/fonts/scifi/Michroma-Regular.ttf",
            "assets/fonts/scifi/Exo2-Variable.ttf",
        ),
    },
    "oxanium": {
        "label": "Oxanium",
        "heading": "Oxanium",
        "body": "Oxanium",
        "files": (
            "assets/fonts/scifi/Oxanium-Variable.ttf",
        ),
    },
    "teko": {
        "label": "Teko",
        "heading": "Teko",
        "body": "Teko",
        "files": (
            "assets/fonts/scifi/Teko-Variable.ttf",
        ),
    },
    "jura": {
        "label": "Jura",
        "heading": "Jura",
        "body": "Jura",
        "files": (
            "assets/fonts/scifi/Jura-Variable.ttf",
        ),
    },
    "electrolize": {
        "label": "Electrolize",
        "heading": "Electrolize",
        "body": "Electrolize",
        "files": (
            "assets/fonts/scifi/Electrolize-Regular.ttf",
        ),
    },
    "share_tech_mono": {
        "label": "Share Tech Mono",
        "heading": "Share Tech Mono",
        "body": "Share Tech Mono",
        "files": (
            "assets/fonts/scifi/ShareTechMono-Regular.ttf",
        ),
    },
}

FONT_FAMILY_LABELS = {
    key: profile["label"]
    for key, profile in FONT_FAMILIES.items()
}


def font_family_ids() -> tuple[str, ...]:
    return tuple(FONT_FAMILIES.keys())


def get_font_profile(family_id: str) -> dict:
    return FONT_FAMILIES.get(
        family_id,
        FONT_FAMILIES[DEFAULT_FONT_FAMILY],
    )


def resolve_body_font(
    family_id: str,
    *,
    theme_id: str = "star_citizen",
    palette: dict | None = None,
) -> str:
    profile = get_font_profile(family_id)
    if family_id == "system":
        if theme_id != "star_citizen" and palette:
            return palette.get("font_ui", "Segoe UI")
        return "Segoe UI"
    return profile["body"]


def resolve_heading_font(family_id: str) -> str:
    return get_font_profile(family_id)["heading"]


def iter_font_files():
    seen: set[str] = set()
    for profile in FONT_FAMILIES.values():
        for rel_path in profile["files"]:
            if rel_path in seen:
                continue
            seen.add(rel_path)
            yield rel_path


def existing_font_paths():
    for rel_path in iter_font_files():
        path = asset_path(rel_path)
        if path.exists():
            yield path


# Dashboard-Labels: (heading|body, base_px)
_DASHBOARD_LABEL_ROLES: dict[str, tuple[str, int]] = {
    "dashboardKpiTitle": ("heading", 10),
    "dashboardKpiValue": ("body", 16),
    "dashboardKpiValueAccent": ("body", 16),
    "dashboardKpiStatusValue": ("body", 13),
    "dashboardSessionHeading": ("heading", 10),
    "dashboardStatLabel": ("body", 11),
    "dashboardStatValue": ("body", 12),
    "dashboardCatalogTitle": ("heading", 12),
    "dashboardCatalogHint": ("body", 11),
    "dashboardCatalogDropLabel": ("body", 10),
    "dashboardCatalogLabel": ("body", 12),
}


def dashboard_label_fonts(family_id: str) -> dict[str, tuple[str, int]]:
    heading = resolve_heading_font(family_id)
    body = resolve_body_font(family_id)
    return {
        name: (heading if role == "heading" else body, px)
        for name, (role, px) in _DASHBOARD_LABEL_ROLES.items()
    }


def apply_font_family_to_qss(qss: str, family_id: str) -> str:
    profile = get_font_profile(family_id)
    heading = profile["heading"]
    body = profile["body"]

    if family_id == "system":
        heading = body = "Segoe UI"

    replacements = (
        (f'"{BASE_HEADING_FONT}"', f'"{heading}"'),
        (f'"{BASE_BODY_FONT}"', f'"{body}"'),
        (f"font-family: {BASE_HEADING_FONT};", f"font-family: {heading};"),
        (f"font-family: {BASE_BODY_FONT};", f"font-family: {body};"),
        (f"font-family: Orbitron;", f"font-family: {heading};"),
        (f"font-family: Rajdhani;", f"font-family: {body};"),
    )
    for old, new in replacements:
        qss = qss.replace(old, new)
    return qss
