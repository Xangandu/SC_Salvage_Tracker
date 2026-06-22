import os
import sys
from pathlib import Path


def is_frozen():
    return getattr(sys, "frozen", False)


def app_root():
    """Read-only bundle root (PyInstaller) or project root (dev)."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS"))

    return Path(__file__).resolve().parent.parent


def install_root():
    """Directory of the running executable or project root in dev."""
    if is_frozen():
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent.parent


def data_dir():
    """Writable data directory (DB, remember-me, user files)."""
    if is_frozen():
        base = os.environ.get(
            "LOCALAPPDATA",
            str(Path.home() / "AppData" / "Local"),
        )
        path = Path(base) / "SC Salvage Tracker" / "data"
    else:
        path = install_root() / "data"

    path.mkdir(parents=True, exist_ok=True)
    return path


def backups_dir():
    """Writable directory for SQLite database backups."""
    path = data_dir() / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def asset_path(*parts):
    return app_root().joinpath(*parts)


def changelogs_dir():
    return app_root() / "Changelogs"
