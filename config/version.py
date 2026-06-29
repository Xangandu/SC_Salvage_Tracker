"""
Zentrale Versionsinformation — einzige Quelle für Programm und Splash.

Alle UI-Anzeigen (Splash, Navigation, Changelog) nutzen die format_*-Helfer
aus diesem Modul, damit Version, Build und Codename immer synchron sind.

Beta 0.16.0: Standorte & Materialfluss (Lager, Schiff, Kontext-Dashboard) — siehe Changelogs/PATCHNOTES.txt.
Beta 0.15.2: Vollständige UI-Internationalisierung (EN/DE) — siehe Changelogs/PATCHNOTES.txt.
Beta 0.15.0: Produkt-Editionen (SOLO / CREW / ORGA) — siehe config/editions.py
und Changelogs/EDITIONS.txt.

Build-Edition in .exe: config/build_edition.txt (PyInstaller, siehe installer/).
"""

from config.paths import app_root, is_frozen

APP_PRODUCT_NAME = "SC Salvage Tracker"

_VALID_BUILD_EDITIONS = frozenset({"solo", "crew", "orga"})


def _read_build_edition() -> str:
    """Dev: build_edition.txt / SST_EDITION. Frozen: Marker aus dem Installer-Build."""
    import os

    env = (os.environ.get("SST_EDITION") or "").strip().lower()
    if env in _VALID_BUILD_EDITIONS:
        return env

    marker = app_root() / "config" / "build_edition.txt"
    try:
        edition = marker.read_text(encoding="utf-8-sig").strip().lower()
    except OSError:
        edition = ""
    if edition in _VALID_BUILD_EDITIONS:
        return edition

    if is_frozen():
        return "solo"
    return "solo"


# Build-Edition: solo | crew | orga
APP_EDITION = _read_build_edition()

EDITION_TITLES = {
    "solo": "SOLO Version",
    "crew": "CREW Version",
    "orga": "ORGA Version",
}

APP_VERSION = "0.16.0 Beta"
APP_BUILD = "2026.11"
APP_CODENAME = "LOCATION FLOW"

DEVELOPER_NAME = "Christian"
DEVELOPER_ALIAS = "Xan-Gan-Du"

# Abwärtskompatibel — Standard-Build = SOLO
APP_NAME = f"{APP_PRODUCT_NAME} - {EDITION_TITLES[APP_EDITION]}"


def format_version_subtitle(separator: str = " | ") -> str:
    """Einzeiler: Patchnotes-Dialog, Statuszeilen."""
    return (
        f"{APP_VERSION}{separator}Build {APP_BUILD}"
        f"{separator}{APP_CODENAME}"
    )


def format_version_splash() -> str:
    """Splash-Screen unten links (zweizeilig)."""
    return (
        f"VERSION {APP_VERSION.upper()}\n"
        f"Build {APP_BUILD} · {APP_CODENAME}"
    )


def format_version_nav_html(edition_label: str | None = None) -> str:
    """Navigationsleiste unten (Rich-Text mit Changelog-Link)."""
    if edition_label is None:
        edition_label = EDITION_TITLES.get(APP_EDITION, "SOLO Version")
    display_name = f"{APP_PRODUCT_NAME} - {edition_label}"
    return (
        f"{display_name}<br>"
        f"{APP_VERSION}<br>"
        f"Build {APP_BUILD}<br>"
        f"<span style='color:#708696;'>{APP_CODENAME}</span><br><br>"
        f"Erstellt von<br>"
        f"<span style='color:#D9F4FF;'>{DEVELOPER_NAME}</span><br>"
        f"<span style='color:#C9A227;'>{DEVELOPER_ALIAS}</span><br><br>"
        f"<a href='changelog'>Patchnotes & Roadmap</a>"
    )
