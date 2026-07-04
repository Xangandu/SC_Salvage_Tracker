"""Tracker-Materialcodes ↔ UEX-Rohstoffcodes."""

from __future__ import annotations

from config.materials import REFINED_SELLABLE_CODES

# Tracker-Code -> UEX commodity_code (Verkauf an Terminal: price_sell)
TRACKER_TO_UEX_COMMODITY: dict[str, str] = {
    "RMC": "RMC",
    "CM": "CMAT",
}


def tracker_materials_for_uex() -> tuple[str, ...]:
    return REFINED_SELLABLE_CODES


def uex_commodity_code(material_code: str) -> str | None:
    return TRACKER_TO_UEX_COMMODITY.get(material_code)


def register_uex_commodity(material_code: str, uex_code: str) -> None:
    """Erweiterung für künftige Materialien."""
    TRACKER_TO_UEX_COMMODITY[material_code] = uex_code
