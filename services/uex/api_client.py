"""HTTP-Client für die UEX Corp API 2.0 (öffentlicher Lesezugriff)."""

from __future__ import annotations

import time
from typing import Any

from services.uex.commodities import (
    tracker_materials_for_uex,
    uex_commodity_code,
)
from services.uex.http import (
    DEFAULT_TIMEOUT_SEC,
    uex_get,
    uex_rows,
)
from services.uex.mapping import UexTerminalResolver
from services.uex.models import (
    UexApiError,
    UexFetchResult,
    UexTerminalRef,
)

_PRICE_CACHE: dict[int, tuple[float, dict[str, float]]] = {}
_PRICE_CACHE_TTL_SEC = 15 * 60


class UexApiClient:
    """Kommunikation mit der UEX Corp API — ohne UI-Abhängigkeiten."""

    def __init__(
        self,
        *,
        timeout_sec: float = DEFAULT_TIMEOUT_SEC,
        resolver: UexTerminalResolver | None = None,
    ):
        self._timeout_sec = timeout_sec
        self._resolver = resolver or UexTerminalResolver()

    def fetch_sale_prices(
        self,
        *,
        system: str,
        location_kind: str,
        location_key: str,
        location_label: str,
    ) -> UexFetchResult:
        terminal = self._resolver.resolve(
            system=system,
            location_kind=location_kind,
            location_key=location_key,
            location_label=location_label,
        )
        if terminal is None:
            raise UexApiError("terminal_not_found")

        prices = self._fetch_prices_for_terminal(terminal)
        return UexFetchResult(
            terminal=terminal,
            prices_by_tracker_code=prices,
        )

    def _fetch_prices_for_terminal(
        self,
        terminal: UexTerminalRef,
    ) -> dict[str, float]:
        cached = _PRICE_CACHE.get(terminal.id_terminal)
        if cached is not None:
            cached_at, prices = cached
            if time.monotonic() - cached_at < _PRICE_CACHE_TTL_SEC:
                return dict(prices)

        payload = uex_get(
            "commodities_prices",
            {"id_terminal": terminal.id_terminal},
            timeout_sec=self._timeout_sec,
        )
        rows = uex_rows(payload)
        uex_codes = {
            uex_commodity_code(code)
            for code in tracker_materials_for_uex()
        }
        uex_codes.discard(None)

        by_uex: dict[str, float] = {}
        for row in rows:
            code = (row.get("commodity_code") or "").strip()
            if code not in uex_codes:
                continue
            price = self._positive_price(row.get("price_sell"))
            if price is not None:
                by_uex[code] = price

        result: dict[str, float] = {}
        for tracker_code in tracker_materials_for_uex():
            uex_code = uex_commodity_code(tracker_code)
            if uex_code and uex_code in by_uex:
                result[tracker_code] = by_uex[uex_code]

        _PRICE_CACHE[terminal.id_terminal] = (
            time.monotonic(),
            dict(result),
        )
        return result

    def search_terminals(self, name: str) -> list[UexTerminalRef]:
        payload = uex_get(
            "terminals",
            {"name": name},
            timeout_sec=self._timeout_sec,
        )
        rows = uex_rows(payload)
        result: list[UexTerminalRef] = []
        for row in rows:
            if (row.get("type") or "").casefold() != "commodity":
                continue
            terminal_id = row.get("id")
            if terminal_id is None:
                continue
            result.append(
                UexTerminalRef(
                    id_terminal=int(terminal_id),
                    code=str(row.get("code") or ""),
                    name=str(row.get("name") or row.get("displayname") or ""),
                )
            )
        return result

    @staticmethod
    def _positive_price(value: Any) -> float | None:
        try:
            price = float(value)
        except (TypeError, ValueError):
            return None
        if price <= 0:
            return None
        return price
