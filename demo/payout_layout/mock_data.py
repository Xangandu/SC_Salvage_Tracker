"""Mock-Daten für die Auszahlungs-Layout-Demo (keine DB)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UnpaidSale:
    number: int
    date: str
    location: str
    revenue: str
    seller: str


@dataclass(frozen=True)
class CrewPayoutRow:
    date: str
    location: str
    amount: float
    crew_members: tuple[str, ...]


PENDING_COUNT = 0
PAID_TOTAL = 101_001

UNPAID_SALES: tuple[UnpaidSale, ...] = ()

CREW_PAYOUTS: tuple[CrewPayoutRow, ...] = (
    CrewPayoutRow(
        date="11.07.2024 12:04:16",
        location="Area18",
        amount=13_001,
        crew_members=("Pilot A", "Gunner B"),
    ),
    CrewPayoutRow(
        date="11.07.2026 12:04:09",
        location="Area18",
        amount=88_000,
        crew_members=("Xangandu", "Crew-Mitglied 2", "Crew-Mitglied 3"),
    ),
)

CREW_MEMBERS = ("Xangandu", "Crew-Mitglied 2")
