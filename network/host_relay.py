"""Salvage-Relay — Host-Bridge starten/stoppen."""

from __future__ import annotations

from database.access import (
    get_host_relay_bridge,
    set_host_relay_bridge,
)
from network.connection_guide import (
    default_relay_host,
    default_relay_port,
    is_relay_scenario,
    normalize_scenario,
)
from network.relay_bridge import HostRelayBridge


def should_register_at_relay(db) -> bool:
    settings = db.settings.get_app_settings()
    if settings.get("network_use_relay", "0") == "1":
        return True
    scenario = normalize_scenario(
        settings.get("network_connection_scenario", "lan")
    )
    return is_relay_scenario(scenario)


def start_host_relay_if_enabled(db, server) -> HostRelayBridge | None:
    if not should_register_at_relay(db):
        return None

    if not server or not server.is_running():
        return None

    relay_host = db.settings.get_app_setting(
        "network_relay_host",
        default_relay_host(),
    ).strip()
    relay_port = int(
        db.settings.get_app_setting(
            "network_relay_port",
            str(default_relay_port()),
        )
    )
    join_code = (server.join_code or "").strip().upper()
    if not relay_host or not join_code:
        return None

    existing = get_host_relay_bridge()
    if existing and existing.is_active:
        return existing

    bridge = HostRelayBridge(server)
    if bridge.start(
        relay_host=relay_host,
        relay_port=relay_port,
        join_code=join_code,
        local_port=server.port,
    ):
        set_host_relay_bridge(bridge)
        return bridge

    return None


def stop_host_relay() -> None:
    bridge = get_host_relay_bridge()
    if bridge:
        bridge.stop()
    set_host_relay_bridge(None)
