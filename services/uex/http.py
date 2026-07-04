"""Gemeinsame HTTP-Hilfen für die UEX Corp API."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from services.uex.models import UexApiError

UEX_API_BASE = "https://api.uexcorp.uk/2.0"
UEX_USER_AGENT = "SC-Salvage-Tracker/1.0"
DEFAULT_TIMEOUT_SEC = 20


def uex_get(
    resource: str,
    params: dict[str, Any] | None = None,
    *,
    timeout_sec: float = DEFAULT_TIMEOUT_SEC,
) -> dict[str, Any]:
    query = urlencode(params or {}, doseq=True)
    url = f"{UEX_API_BASE}/{resource.strip('/')}/"
    if query:
        url = f"{url}?{query}"

    request = Request(
        url,
        headers={
            "User-Agent": UEX_USER_AGENT,
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=timeout_sec) as response:
            raw = response.read()
    except HTTPError as error:
        raise UexApiError(f"http_{error.code}") from error
    except URLError as error:
        reason = getattr(error, "reason", error)
        if "timed out" in str(reason).casefold():
            raise UexApiError("timeout") from error
        raise UexApiError("network") from error
    except TimeoutError as error:
        raise UexApiError("timeout") from error

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise UexApiError("invalid_response") from error

    if not isinstance(payload, dict):
        raise UexApiError("invalid_response")

    status = (payload.get("status") or "").casefold()
    if status and status not in ("ok", "success"):
        raise UexApiError(status or "api_error")

    return payload


def uex_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data")
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        for key in ("commodities_prices", "terminals", "commodities"):
            nested = data.get(key)
            if isinstance(nested, list):
                return [row for row in nested if isinstance(row, dict)]
    return []
