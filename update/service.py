"""Update-Logik: Einstellungen, Download, Prüfsumme, Installer-Start."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Callable
from urllib.error import URLError
from urllib.request import urlopen

from config.paths import is_frozen, updates_cache_dir
from config.update import (
    UpdateManifest,
    fetch_update_manifest,
    is_update_available,
    local_release_version,
)
from config.version import APP_BUILD
from database.access import get_client_connection, get_host_server
from network.constants import NETWORK_MODE_CLIENT, NETWORK_MODE_HOST
from network.network_state import get_network_state

SETTING_AUTO_CHECK = "update_auto_check"
SETTING_SKIPPED_VERSION = "update_skipped_version"
SETTING_LAST_CHECK = "update_last_check"

DOWNLOAD_CHUNK_BYTES = 256 * 1024
INSTALLER_SILENT_ARGS = (
    "/VERYSILENT",
    "/SUPPRESSMSGBOXES",
    "/NORESTART",
)


def is_auto_check_enabled(db) -> bool:
    return db.settings.get_app_setting(SETTING_AUTO_CHECK, "1") == "1"


def set_auto_check_enabled(db, enabled: bool) -> None:
    db.settings.set_app_setting(
        SETTING_AUTO_CHECK,
        "1" if enabled else "0",
    )


def get_skipped_version(db) -> str:
    return db.settings.get_app_setting(SETTING_SKIPPED_VERSION, "") or ""


def set_skipped_version(db, version: str) -> None:
    db.settings.set_app_setting(SETTING_SKIPPED_VERSION, version)


def get_last_check(db) -> str:
    return db.settings.get_app_setting(SETTING_LAST_CHECK, "") or ""


def record_last_check(db) -> None:
    from config.dates import now_db_timestamp

    db.settings.set_app_setting(SETTING_LAST_CHECK, now_db_timestamp())


def should_offer_update(db, manifest: UpdateManifest) -> bool:
    if not is_update_available(
        manifest,
        local_release_version(),
        APP_BUILD,
    ):
        return False
    return manifest.version != get_skipped_version(db)


def fetch_update_manifest_online() -> tuple[UpdateManifest | None, str | None]:
    """Nur Netzwerk — ohne SQLite (für Hintergrund-Thread)."""
    try:
        return fetch_update_manifest(), None
    except RuntimeError as error:
        return None, str(error)


def check_for_update(db) -> tuple[UpdateManifest | None, str | None]:
    """Lädt Manifest und wertet auf dem UI-Thread aus (mit DB)."""
    manifest, error = fetch_update_manifest_online()
    if error:
        return None, error

    record_last_check(db)

    if should_offer_update(db, manifest):
        return manifest, None
    return None, None


def get_network_update_warning() -> str | None:
    state = get_network_state()
    host = get_host_server()
    if state.host_running or (
        state.mode == NETWORK_MODE_HOST
        and host
        and host.is_running()
    ):
        return (
            "Der Host-Modus ist aktiv. Clients sollten die Verbindung "
            "trennen, bevor ein Update installiert wird."
        )

    connection = get_client_connection()
    if state.mode == NETWORK_MODE_CLIENT and connection:
        if connection.is_connected:
            return (
                "Sie sind als Client mit einem Host verbunden. "
                "Trennen Sie die Verbindung vor dem Update."
            )
    return None


def verify_file_sha256(path: Path, expected: str) -> bool:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(DOWNLOAD_CHUNK_BYTES)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest().lower() == expected.lower()


def download_update_file(
    manifest: UpdateManifest,
    progress_callback: Callable[[int, int], None] | None = None,
) -> Path:
    download = manifest.download
    cache_dir = updates_cache_dir()
    destination = cache_dir / download.filename

    if destination.exists() and verify_file_sha256(
        destination,
        download.sha256,
    ):
        if progress_callback and download.size_bytes:
            progress_callback(download.size_bytes, download.size_bytes)
        return destination

    total_bytes = max(download.size_bytes, 0)
    received = 0

    try:
        with urlopen(download.url, timeout=60) as response:
            with destination.open("wb") as handle:
                while True:
                    chunk = response.read(DOWNLOAD_CHUNK_BYTES)
                    if not chunk:
                        break
                    handle.write(chunk)
                    received += len(chunk)
                    if progress_callback:
                        if total_bytes > 0:
                            progress_callback(received, total_bytes)
                        else:
                            progress_callback(received, received)
    except URLError as error:
        if destination.exists():
            destination.unlink(missing_ok=True)
        raise RuntimeError(
            f"Download fehlgeschlagen: {error}"
        ) from error

    if not verify_file_sha256(destination, download.sha256):
        destination.unlink(missing_ok=True)
        raise RuntimeError(
            "Die heruntergeladene Datei ist beschädigt "
            "(SHA256-Prüfsumme stimmt nicht)."
        )

    return destination


def can_launch_installer() -> bool:
    return is_frozen() and sys.platform == "win32"


def launch_installer(setup_path: Path) -> None:
    if not can_launch_installer():
        raise RuntimeError(
            "Updates können nur in der installierten Windows-App "
            "automatisch installiert werden."
        )

    subprocess.Popen(
        [str(setup_path), *INSTALLER_SILENT_ARGS],
        close_fds=True,
        creationflags=getattr(subprocess, "DETACHED_PROCESS", 0),
    )
