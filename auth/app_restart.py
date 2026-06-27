"""Anwendungs-Neustart (z. B. nach Sprachwechsel) mit automatischer Anmeldung."""

from __future__ import annotations

import subprocess
import sys

from auth.remember_me import save_remember_data
from config.paths import install_root, is_frozen
from database.access import (
    get_client_connection,
    get_host_server,
    set_client_connection,
    set_host_server,
)
from network.host_relay import stop_host_relay

SETTING_LANGUAGE_RESTART_PENDING = "language_restart_pending"
SETTING_LANGUAGE_RESTART_USERNAME = "language_restart_username"


def prepare_language_restart_login(
    db,
    user: dict,
    *,
    is_network_client: bool = False,
) -> None:
    """Merkt Anmeldung für den Neustart (Remember-Token und/oder Client-Reconnect)."""
    from database.access import get_local_database

    local_db = get_local_database()
    username = (user.get("username") or "").strip()
    local_db.settings.set_app_setting(
        SETTING_LANGUAGE_RESTART_PENDING,
        "1",
    )
    local_db.settings.set_app_setting(
        SETTING_LANGUAGE_RESTART_USERNAME,
        username,
    )

    if user.get("is_network_guest") or is_network_client:
        return

    if not hasattr(db, "create_remember_token"):
        return

    token = db.create_remember_token(user["id"])
    save_remember_data(username, token)


def consume_language_restart_pending() -> bool:
    from database.access import get_local_database

    local_db = get_local_database()
    pending = (
        local_db.settings.get_app_setting(
            SETTING_LANGUAGE_RESTART_PENDING,
            "0",
        )
        == "1"
    )
    if not pending:
        return False

    local_db.settings.set_app_setting(
        SETTING_LANGUAGE_RESTART_PENDING,
        "0",
    )
    local_db.settings.set_app_setting(
        SETTING_LANGUAGE_RESTART_USERNAME,
        "",
    )
    return True


def shutdown_before_restart() -> None:
    connection = get_client_connection()
    if connection:
        connection.disconnect_from_host()
    set_client_connection(None)

    host = get_host_server()
    if host and host.is_running():
        host.stop()
    stop_host_relay()
    set_host_server(None)


def restart_application() -> None:
    if is_frozen():
        command = [sys.executable]
        workdir = str(install_root())
    else:
        command = [sys.executable, str(install_root() / "main.py")]
        workdir = str(install_root())

    creationflags = 0
    if sys.platform == "win32":
        creationflags = getattr(subprocess, "DETACHED_PROCESS", 0)

    subprocess.Popen(
        command,
        cwd=workdir,
        close_fds=True,
        creationflags=creationflags,
    )
