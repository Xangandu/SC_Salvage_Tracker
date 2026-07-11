"""Kanonical App-Icon — einzige Quelle für EXE, Setup und Fenster."""

from __future__ import annotations

import sys
from pathlib import Path

from config.paths import app_root, asset_path

SOLO_APP_ICON_NAME = "scst_solo_logo.ico"
SOLO_APP_ICON_PNG = "scst_solo_logo.png"


def solo_app_icon_path() -> Path:
    """Projekt-Icon unter assets/images/."""
    return asset_path("assets", "images", SOLO_APP_ICON_NAME)


def installer_app_icon_path(installer_dir: Path | None = None) -> Path:
    """Kopie für Setup-Build unter installer/assets/."""
    if installer_dir is None:
        installer_dir = app_root() / "installer"
    return installer_dir / "assets" / SOLO_APP_ICON_NAME


def resolve_app_icon_path() -> Path | None:
    """Icon für Laufzeit (Dev, frozen App, Setup-Assistent)."""
    project = solo_app_icon_path()
    if project.is_file():
        return project

    installer = installer_app_icon_path()
    if installer.is_file():
        return installer

    if getattr(sys, "frozen", False):
        bundled = (
            Path(getattr(sys, "_MEIPASS", ""))
            / "installer"
            / "assets"
            / SOLO_APP_ICON_NAME
        )
        if bundled.is_file():
            return bundled

    return None
