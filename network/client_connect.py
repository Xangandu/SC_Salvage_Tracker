"""Gemeinsame Client-Verbindungslogik (Assistent, Einstellungen, Auto-Reconnect)."""

from __future__ import annotations

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QMessageBox, QWidget

from config.i18n import tr
from database.access import set_client_connection, set_database
from network.client_connection import ClientConnection
from network.constants import DEFAULT_PORT
from network.connection_guide import (
    default_relay_host,
    default_relay_port,
    is_relay_scenario,
    normalize_scenario,
    SCENARIO_RELAY,
)
from network.network_state import get_network_state
from network.remote_database import RemoteDatabase


def read_client_settings(db) -> dict:
    settings = db.settings.get_app_settings()
    auth_mode = settings.get("network_client_auth", "guest")
    join_code = settings.get(
        "network_client_join_code",
        settings.get("network_join_code", ""),
    )
    return {
        "host": settings.get("network_last_host", "").strip(),
        "port": int(settings.get("network_host_port", str(DEFAULT_PORT))),
        "join_code": join_code.strip().upper(),
        "auth_mode": auth_mode if auth_mode in ("guest", "user") else "guest",
        "client_name": settings.get("network_client_name", "").strip(),
        "username": settings.get("network_client_username", "").strip(),
        "use_tls": settings.get("network_use_tls", "1") == "1",
        "scenario": normalize_scenario(
            settings.get("network_connection_scenario", "lan")
        ),
        "relay_host": settings.get(
            "network_relay_host",
            default_relay_host(),
        ).strip(),
        "relay_port": int(
            settings.get(
                "network_relay_port",
                str(default_relay_port()),
            )
        ),
    }


def save_client_settings(
    db,
    *,
    host: str,
    port: int,
    join_code: str = "",
    auth_mode: str = "guest",
    client_name: str = "",
    username: str = "",
    use_tls: bool = True,
    scenario: str = "lan",
    relay_host: str = "",
    relay_port: int | None = None,
) -> None:
    db.settings.set_app_setting("network_mode", "client")
    db.settings.set_app_setting("network_last_host", host.strip())
    db.settings.set_app_setting("network_host_port", str(port))
    db.settings.set_app_setting(
        "network_use_tls",
        "1" if use_tls else "0",
    )
    db.settings.set_app_setting(
        "network_client_join_code",
        (join_code or "").strip().upper(),
    )
    db.settings.set_app_setting(
        "network_client_auth",
        auth_mode if auth_mode in ("guest", "user") else "guest",
    )
    db.settings.set_app_setting(
        "network_client_name",
        (client_name or "").strip(),
    )
    db.settings.set_app_setting(
        "network_client_username",
        (username or "").strip(),
    )
    db.settings.set_app_setting(
        "network_connection_scenario",
        normalize_scenario(scenario),
    )
    if relay_host:
        db.settings.set_app_setting(
            "network_relay_host",
            relay_host.strip(),
        )
    if relay_port is not None:
        db.settings.set_app_setting(
            "network_relay_port",
            str(relay_port),
        )


def can_auto_reconnect(db) -> bool:
    settings = read_client_settings(db)
    if settings["auth_mode"] != "guest":
        return False
    if is_relay_scenario(settings["scenario"]):
        return bool(settings["join_code"] and settings["relay_host"])
    return bool(settings["host"] and settings["join_code"])


def connect_to_host_client(
    db,
    parent: QWidget | None = None,
    *,
    host: str,
    port: int,
    join_code: str = "",
    username: str = "",
    password: str = "",
    client_name: str = "",
    use_tls: bool = True,
    timeout_ms: int = 15_000,
    save_settings: bool = True,
    show_errors: bool = True,
    scenario: str | None = None,
    relay_host: str = "",
    relay_port: int | None = None,
    via_relay: bool = False,
) -> tuple[ClientConnection, dict] | None:
    scenario = normalize_scenario(scenario or "lan")
    via_relay = via_relay or is_relay_scenario(scenario)

    if via_relay:
        relay_host = (relay_host or default_relay_host()).strip()
        relay_port = relay_port if relay_port is not None else default_relay_port()
        if not relay_host:
            if show_errors and parent:
                QMessageBox.warning(
                    parent,
                    tr("network.error.connect_title"),
                    tr("network.error.relay_address_required"),
                )
            return None
    else:
        host = host.strip()
        if not host:
            if show_errors and parent:
                QMessageBox.warning(
                    parent,
                    tr("network.error.connect_title"),
                    tr("network.error.host_address_required"),
                )
            return None

    auth_mode = "user" if username else "guest"
    join_code = (join_code or "").strip().upper()

    if auth_mode == "guest" and not join_code:
        if show_errors and parent:
            QMessageBox.warning(
                parent,
                tr("network.error.connect_title"),
                tr("network.error.guest_code_required"),
            )
        return None

    if auth_mode == "user" and (not username or not password):
        if show_errors and parent:
            QMessageBox.warning(
                parent,
                tr("network.error.connect_title"),
                tr("network.error.credentials_required"),
            )
        return None

    connection = ClientConnection(parent)
    loop = _ConnectWaitLoop(parent)

    user_holder: dict = {}

    def on_auth_ok(user):
        user_holder["user"] = user
        set_client_connection(connection)
        set_database(RemoteDatabase(connection))
        if save_settings:
            save_client_settings(
                db,
                host=relay_host if via_relay else host,
                port=relay_port if via_relay else port,
                join_code=join_code,
                auth_mode=auth_mode,
                client_name=client_name,
                username=username,
                use_tls=False if via_relay else use_tls,
                scenario=scenario,
                relay_host=relay_host if via_relay else "",
                relay_port=relay_port if via_relay else None,
            )
        get_network_state().mode = "client"
        loop.quit_success()

    def on_auth_fail(error):
        if show_errors and parent:
            QMessageBox.critical(
                parent,
                tr("network.error.connection_failed"),
                error,
            )
        loop.quit_fail()

    def on_error(error):
        message = error
        if show_errors and "refused" in error.lower():
            message = (
                f"{error}\n\n"
                + tr("network.error.host_refused_hint")
            )
        if show_errors and parent:
            QMessageBox.critical(
                parent,
                tr("network.error.connect_error"),
                message,
            )
        loop.quit_fail()

    connection.authenticated.connect(on_auth_ok)
    connection.auth_failed.connect(on_auth_fail)
    connection.error.connect(on_error)

    if via_relay:
        connection.connect_via_relay(
            relay_host,
            relay_port,
            join_code=join_code,
            username=username if auth_mode == "user" else "",
            password=password if auth_mode == "user" else "",
            client_name=client_name,
        )
    else:
        connection.connect_to_host(
            host,
            port,
            join_code=join_code,
            username=username if auth_mode == "user" else "",
            password=password if auth_mode == "user" else "",
            client_name=client_name,
            use_tls=use_tls,
        )

    if not loop.wait(timeout_ms):
        if show_errors and parent:
            QMessageBox.critical(
                parent,
                "Timeout",
                "Keine Antwort vom Host.",
            )
        connection.disconnect_from_host()
        return None

    if "user" not in user_holder:
        connection.disconnect_from_host()
        return None

    return connection, user_holder["user"]


def restore_saved_client_connection(
    db,
    parent: QWidget | None = None,
) -> tuple[ClientConnection, dict] | None:
    if not can_auto_reconnect(db):
        return None

    settings = read_client_settings(db)
    if is_relay_scenario(settings["scenario"]):
        return connect_to_host_client(
            db,
            parent,
            host="",
            port=settings["relay_port"],
            join_code=settings["join_code"],
            client_name=settings["client_name"],
            use_tls=False,
            save_settings=False,
            show_errors=False,
            scenario=SCENARIO_RELAY,
            relay_host=settings["relay_host"],
            relay_port=settings["relay_port"],
            via_relay=True,
        )
    return connect_to_host_client(
        db,
        parent,
        host=settings["host"],
        port=settings["port"],
        join_code=settings["join_code"],
        client_name=settings["client_name"],
        use_tls=settings["use_tls"],
        save_settings=False,
        show_errors=False,
    )


class _ConnectWaitLoop:

    def __init__(self, parent: QWidget | None):
        self._success = False
        self._timer = QTimer(parent)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)
        self._loop: QEventLoop | None = None

    def wait(self, timeout_ms: int) -> bool:
        self._loop = QEventLoop()
        self._timer.start(timeout_ms)
        self._loop.exec()
        return self._success

    def quit_success(self):
        self._success = True
        self._timer.stop()
        if self._loop:
            self._loop.quit()

    def quit_fail(self):
        self._success = False
        self._timer.stop()
        if self._loop:
            self._loop.quit()

    def _on_timeout(self):
        if self._loop:
            self._loop.quit()
