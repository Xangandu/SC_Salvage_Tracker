"""Vereinfachte Vernetzung — Host teilt Code, Client gibt Code ein."""

from __future__ import annotations

import re
import secrets
import string

from network.client_connect import connect_to_host_client
from network.connection_guide import (
    SCENARIO_RELAY,
    default_relay_host,
    default_relay_port,
)
from network.constants import DEFAULT_PORT

_JOIN_CODE = re.compile(r"\b([A-Z0-9]{6})\b")
_ADDRESS = re.compile(
    r"(?:Adresse|Relay|Host)\s*:\s*([^\s:\n]+)(?::(\d+))?",
    re.IGNORECASE,
)
_HOST_PORT_CODE = re.compile(
    r"^([^\s:]+):(\d+)\s+([A-Z0-9]{6})\s*$",
    re.IGNORECASE,
)


def generate_join_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(6))


def parse_join_input(text: str) -> dict:
    """Code (und optional Adresse) aus Freitext oder Einladung extrahieren."""
    raw = (text or "").strip()
    upper = raw.upper()
    codes = _JOIN_CODE.findall(upper)
    join_code = ""
    if len(raw) == 6 and raw.isalnum():
        join_code = upper
    elif codes:
        join_code = codes[0]

    host = ""
    port = DEFAULT_PORT
    compact = _HOST_PORT_CODE.match(raw)
    if compact:
        host = compact.group(1).strip()
        port = int(compact.group(2))
        join_code = compact.group(3).upper()
    else:
        match = _ADDRESS.search(raw)
        if match:
            host = match.group(1).strip()
            if match.group(2):
                port = int(match.group(2))

    return {
        "join_code": join_code,
        "host": host,
        "port": port,
    }


def format_simple_invite(join_code: str) -> str:
    """Nur der Code — zum Einfügen in „Crew beitreten“."""
    return (join_code or "").strip().upper()


def apply_host_simple_defaults(db, join_code: str) -> None:
    """Sinnvolle Standardwerte — Relay, Port, TLS intern."""
    code = (join_code or generate_join_code()).strip().upper()
    db.settings.set_app_setting("network_mode", "host")
    db.settings.set_app_setting("network_connection_scenario", SCENARIO_RELAY)
    db.settings.set_app_setting("network_use_relay", "1")
    db.settings.set_app_setting("network_use_tls", "0")
    db.settings.set_app_setting("network_host_port", str(DEFAULT_PORT))
    db.settings.set_app_setting(
        "network_relay_host",
        default_relay_host(),
    )
    db.settings.set_app_setting(
        "network_relay_port",
        str(default_relay_port()),
    )
    db.settings.set_app_setting("network_join_code", code)


def connect_client_simple(
    db,
    parent,
    invite_text: str,
    *,
    client_name: str = "",
    username: str = "",
    password: str = "",
):
    """Client verbinden: zuerst Relay (nur Code), sonst direkte Adresse."""
    parsed = parse_join_input(invite_text)
    join_code = parsed["join_code"]
    if not join_code:
        return None

    relay_host = default_relay_host()
    relay_port = default_relay_port()

    if parsed["host"]:
        return connect_to_host_client(
            db,
            parent,
            host=parsed["host"],
            port=parsed["port"],
            join_code=join_code,
            username=username,
            password=password,
            client_name=client_name,
            use_tls=True,
            scenario=SCENARIO_RELAY,
            save_settings=True,
            show_errors=True,
        )

    return connect_to_host_client(
        db,
        parent,
        host="",
        port=relay_port,
        join_code=join_code,
        username=username,
        password=password,
        client_name=client_name,
        use_tls=False,
        scenario=SCENARIO_RELAY,
        relay_host=relay_host,
        relay_port=relay_port,
        via_relay=True,
        save_settings=True,
        show_errors=True,
    )
