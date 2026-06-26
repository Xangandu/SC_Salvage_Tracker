"""Verbindungsszenarien — Texte und Hilfsfunktionen."""

from __future__ import annotations

import socket
import urllib.error
import urllib.request

from network.constants import DEFAULT_PORT
from network.relay_constants import DEFAULT_RELAY_HOST, DEFAULT_RELAY_PORT

SCENARIO_LAN = "lan"
SCENARIO_INTERNET = "internet"
SCENARIO_RELAY = "relay"
SCENARIO_ROUTER = "router"

SCENARIO_TAILSCALE = "tailscale"

SCENARIO_LABELS = {
    SCENARIO_LAN: "Gleiches WLAN / LAN",
    SCENARIO_RELAY: "Internet — Salvage-Relay (nur Code)",
    SCENARIO_INTERNET: "Internet — Crew-Einladung (Adresse + Code)",
    SCENARIO_ROUTER: "Internet — Router manuell (Fallback)",
}

CLIENT_HINTS = {
    SCENARIO_LAN: (
        "Ihr seid im gleichen Netzwerk. Trage die LAN-IP des Host-Rechners ein "
        "(z. B. 192.168.x.x — steht auf dem Host unter Einstellungen → Vernetzung)."
    ),
    SCENARIO_RELAY: (
        "Nur Salvage Tracker nötig — keine extra Software, keine IP vom Host. "
        "Trage die Relay-Adresse (vom Host mitgeteilt) und den Beitrittscode ein. "
        "Der Host muss am Relay registriert sein (Einstellungen → Vernetzung)."
    ),
    SCENARIO_INTERNET: (
        "Der Host sendet dir eine Einladung (Adresse + Beitrittscode). "
        "Trage beides ein — kein Zusatzprogramm nötig."
    ),
    SCENARIO_ROUTER: (
        "Fallback: Host hat Port 47890 am Router weitergeleitet. "
        "Externe Internet-Adresse eintragen (nicht 192.168.x.x)."
    ),
}

HOST_HINTS = {
    SCENARIO_LAN: (
        "Clients im gleichen WLAN verbinden sich mit einer LAN-Adresse dieses "
        "Rechners und dem Beitrittscode. Test auf demselben PC: 127.0.0.1."
    ),
    SCENARIO_RELAY: (
        "Host-Server starten und „Am Salvage-Relay registrieren“ aktivieren. "
        "Teile der Crew nur Relay-Adresse und Beitrittscode — keine IP nötig. "
        "Für Tests: Relay lokal starten (scripts/start_relay_server.py)."
    ),
    SCENARIO_INTERNET: (
        "Kopiere die Einladung an deine Crew. Optional: „Internet freigeben (UPnP)“ "
        "für automatische Portweiterleitung am Router."
    ),
    SCENARIO_ROUTER: (
        "Am Router TCP-Port 47890 auf diesen PC weiterleiten. "
        "Externe IP abrufen und mit Code teilen."
    ),
}

CLIENT_PLACEHOLDERS = {
    SCENARIO_LAN: "LAN-IP des Hosts, z. B. 192.168.1.10",
    SCENARIO_RELAY: "Relay-Adresse, z. B. relay.example.com",
    SCENARIO_INTERNET: "Adresse aus der Host-Einladung",
    SCENARIO_ROUTER: "Externe IP des Hosts, z. B. 85.123.45.67",
}

HOST_PLACEHOLDERS = {
    SCENARIO_LAN: "LAN-IP für die Crew",
    SCENARIO_RELAY: "Salvage-Relay, z. B. relay.example.com",
    SCENARIO_INTERNET: (
        "Erreichbare Adresse für die Einladung "
        "(externe IP oder LAN-IP)"
    ),
    SCENARIO_ROUTER: (
        "Externe IP — „Externe IP abrufen“ oder vom Provider"
    ),
}


def scenario_label(scenario: str) -> str:
    from config.i18n import tr

    key = normalize_scenario(scenario)
    return tr(
        f"network.scenario.{key}.label",
        default=SCENARIO_LABELS.get(key, key),
    )


def scenario_hint(scenario: str, *, role: str) -> str:
    from config.i18n import tr

    key = normalize_scenario(scenario)
    prefix = "client" if role == "client" else "host"
    fallback_source = CLIENT_HINTS if role == "client" else HOST_HINTS
    return tr(
        f"network.scenario.{prefix}_hint.{key}",
        default=fallback_source.get(key, ""),
    )


def scenario_client_placeholder(scenario: str) -> str:
    from config.i18n import tr

    key = normalize_scenario(scenario)
    return tr(
        f"network.scenario.placeholder.{key}",
        default=CLIENT_PLACEHOLDERS.get(key, ""),
    )


def scenario_host_placeholder(scenario: str) -> str:
    from config.i18n import tr

    key = normalize_scenario(scenario)
    return tr(
        f"network.scenario.host_placeholder.{key}",
        default=HOST_PLACEHOLDERS.get(key, ""),
    )


def default_relay_host() -> str:
    return DEFAULT_RELAY_HOST


def default_relay_port() -> int:
    return DEFAULT_RELAY_PORT


def local_lan_addresses() -> list[str]:
    from network.host_server import _local_addresses

    return [
        address
        for address in _local_addresses()
        if address != "127.0.0.1"
    ]


def fetch_public_ip(timeout: float = 4.0) -> str | None:
    try:
        with urllib.request.urlopen(
            "https://api.ipify.org",
            timeout=timeout,
        ) as response:
            text = response.read().decode("utf-8", errors="ignore").strip()
            return text or None
    except (urllib.error.URLError, OSError, socket.timeout, ValueError):
        return None


def format_invite_text(
    *,
    host: str,
    port: int = DEFAULT_PORT,
    join_code: str,
    use_tls: bool = True,
    scenario: str = SCENARIO_LAN,
    relay_host: str = "",
    relay_port: int = DEFAULT_RELAY_PORT,
) -> str:
    scenario_key = normalize_scenario(scenario)

    if scenario_key == SCENARIO_RELAY:
        return (join_code or "").strip().upper()

    return f"{host}:{port} {(join_code or '').strip().upper()}".strip()


def normalize_scenario(value: str | None) -> str:
    if value == SCENARIO_TAILSCALE:
        return SCENARIO_INTERNET
    if value in SCENARIO_LABELS:
        return value
    return SCENARIO_LAN


def is_relay_scenario(value: str | None) -> bool:
    return normalize_scenario(value) == SCENARIO_RELAY
