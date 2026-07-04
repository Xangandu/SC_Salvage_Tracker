"""Datenmodelle für UEX-API-Antworten."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class UexTerminalRef:
    id_terminal: int
    code: str
    name: str


@dataclass(frozen=True)
class UexCommodityPrice:
    commodity_code: str
    commodity_name: str
    price_sell: float
    id_terminal: int


@dataclass
class UexFetchResult:
    terminal: UexTerminalRef
    prices_by_tracker_code: dict[str, float] = field(default_factory=dict)


class UexApiError(Exception):
    """Fehler beim Abruf oder bei der Auswertung der UEX-API."""
