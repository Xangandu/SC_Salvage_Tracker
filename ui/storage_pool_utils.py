"""Hilfsfunktionen: Lager-Zeilen zu Material-Pools zusammenfassen."""

from __future__ import annotations


def pool_key_for_row(entry: dict) -> tuple:
    material_code = entry.get("material_code")
    if entry.get("location_kind") == "SHIP" or entry.get("status") == "IN_SHIP":
        return ("SHIP", entry.get("ship_id"), material_code)
    return (
        "STORED",
        entry.get("location_kind"),
        entry.get("location_key"),
        material_code,
    )


def build_pools_from_rows(rows: list[dict]) -> list[dict]:
    merged: dict[tuple, dict] = {}

    for entry in rows:
        qty = float(entry.get("quantity_scu") or 0)
        if qty <= 0:
            continue
        if entry.get("status") not in {"STORED", "IN_SHIP"}:
            continue

        key = pool_key_for_row(entry)
        if key not in merged:
            if key[0] == "SHIP":
                merged[key] = {
                    "pool_kind": "SHIP",
                    "material_code": entry.get("material_code"),
                    "quantity_scu": 0.0,
                    "ship_id": entry.get("ship_id"),
                    "ship_name": entry.get("ship_name"),
                    "location_kind": "SHIP",
                    "location_key": str(entry.get("ship_id") or ""),
                    "location_label": entry.get("ship_name") or entry.get(
                        "location_label"
                    ),
                }
            else:
                merged[key] = {
                    "pool_kind": "STORED",
                    "material_code": entry.get("material_code"),
                    "quantity_scu": 0.0,
                    "ship_id": None,
                    "ship_name": None,
                    "location_kind": entry.get("location_kind"),
                    "location_key": entry.get("location_key"),
                    "location_label": entry.get("location_label"),
                }
        merged[key]["quantity_scu"] += qty

    return sorted(
        merged.values(),
        key=lambda pool: (
            pool.get("location_label") or "",
            pool.get("material_code") or "",
        ),
    )


def entry_pool(entry: dict) -> dict:
    """Einzelne Zeile → zugehöriger Pool (Summe nur dieser Zeile wenn allein)."""
    if entry.get("location_kind") == "SHIP" or entry.get("status") == "IN_SHIP":
        return {
            "pool_kind": "SHIP",
            "material_code": entry.get("material_code"),
            "quantity_scu": float(entry.get("quantity_scu") or 0),
            "ship_id": entry.get("ship_id"),
            "ship_name": entry.get("ship_name"),
            "location_kind": "SHIP",
            "location_key": str(entry.get("ship_id") or ""),
            "location_label": entry.get("ship_name") or entry.get("location_label"),
        }
    return {
        "pool_kind": "STORED",
        "material_code": entry.get("material_code"),
        "quantity_scu": float(entry.get("quantity_scu") or 0),
        "ship_id": None,
        "ship_name": None,
        "location_kind": entry.get("location_kind"),
        "location_key": entry.get("location_key"),
        "location_label": entry.get("location_label"),
    }
