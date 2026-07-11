"""Mock-Daten für die Verkaufs-Layout-Demo (keine DB)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InventoryRow:
    material: str
    quantity: int


@dataclass(frozen=True)
class HistoryRow:
    number: int
    date: str
    location: str
    materials: str
    revenue: float
    seller: str


REVENUE_TOTAL = 245_500
COSTS_TOTAL = 38_200
PROFIT_TOTAL = REVENUE_TOTAL - COSTS_TOTAL

INVENTORY: tuple[InventoryRow, ...] = (
    InventoryRow("Recycled Material Composite", 42),
    InventoryRow("Construction Material", 18),
)

HISTORY: tuple[HistoryRow, ...] = (
    HistoryRow(
        12,
        "11.07.2026",
        "Area18",
        "24 SCU RMC, 6 SCU CM",
        88_000,
        "Xangandu",
    ),
    HistoryRow(
        11,
        "04.07.2026",
        "Orison",
        "12 SCU RMC",
        31_500,
        "Xangandu",
    ),
    HistoryRow(
        10,
        "28.06.2026",
        "Grim HEX",
        "8 SCU CM",
        18_200,
        "Crew-Mitglied",
    ),
)
