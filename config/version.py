"""
Zentrale Versionsinformation — einzige Quelle für Programm und Splash.

Alle UI-Anzeigen (Splash, Navigation, Changelog) nutzen die format_*-Helfer
aus diesem Modul, damit Version, Build und Codename immer synchron sind.
"""

APP_NAME = "SC Salvage Tracker"

APP_VERSION = "0.14.1 Alpha"
APP_BUILD = "2026.06"
APP_CODENAME = "Launcher Polish"

DEVELOPER_NAME = "Christian"
DEVELOPER_ALIAS = "Xan-Gan-Du"


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


def format_version_nav_html() -> str:
    """Navigationsleiste unten (Rich-Text mit Changelog-Link)."""
    return (
        f"{APP_NAME}<br>"
        f"{APP_VERSION}<br>"
        f"Build {APP_BUILD}<br>"
        f"<span style='color:#708696;'>{APP_CODENAME}</span><br><br>"
        f"Erstellt von<br>"
        f"<span style='color:#D9F4FF;'>{DEVELOPER_NAME}</span><br>"
        f"<span style='color:#C9A227;'>{DEVELOPER_ALIAS}</span><br><br>"
        f"<a href='changelog'>Patchnotes & Roadmap</a>"
    )
