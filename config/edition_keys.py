"""Supporter-Keys für Edition-Freischaltung (CREW / ORGA)."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets

from config.editions import EDITION_CREW, EDITION_ORGA

# Pepper für HMAC — Keys nur mit scripts/generate_supporter_keys.py erzeugen.
_KEY_PEPPER = b"SST-0.15.0-Edition-Foundation-Support-Keys-v1"


def _checksum(edition: str, payload: str) -> str:
    message = f"{edition.lower()}:{payload.upper()}".encode()
    digest = hmac.new(
        _KEY_PEPPER,
        message,
        hashlib.sha256,
    ).hexdigest()
    return digest[:8].upper()


def _parse_key_parts(raw_key: str) -> tuple[str, str, str] | None:
    cleaned = re.sub(r"[^A-Za-z0-9]", "", raw_key).upper()
    for edition in (EDITION_CREW, EDITION_ORGA):
        prefix = edition.upper()
        if not cleaned.startswith(prefix):
            continue
        body = cleaned[len(prefix) :]
        if len(body) != 16:
            return None
        return edition, body[:8], body[8:]
    return None


def edition_for_supporter_key(raw_key: str) -> str | None:
    """Gültige Edition (crew/orga) oder None."""
    if not raw_key or not raw_key.strip():
        return None
    parsed = _parse_key_parts(raw_key)
    if parsed is None:
        return None
    edition, payload, check = parsed
    expected = _checksum(edition, payload)
    if not hmac.compare_digest(expected, check):
        return None
    return edition


def format_supporter_key(edition: str, payload: str) -> str:
    payload = payload.upper()
    check = _checksum(edition, payload)
    return f"{edition.upper()}-{payload[:4]}-{payload[4:]}-{check}"


def generate_supporter_key(edition: str) -> str:
    if edition not in (EDITION_CREW, EDITION_ORGA):
        raise ValueError(f"Unbekannte Edition: {edition}")
    payload = secrets.token_hex(4).upper()
    return format_supporter_key(edition, payload)
