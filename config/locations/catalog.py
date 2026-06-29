"""Standort-Katalog (Stationen, Landeplätze) für Dropdowns — nur Daten, keine DB."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parent

_SYSTEM_ORDER = ("Stanton", "Pyro", "Nyx")
SYSTEM_ORDER = _SYSTEM_ORDER

# Comm Arrays sind fuer Salvage-Lager/Verkauf selten relevant.
_HIDDEN_CATEGORIES = frozenset({"comm_array"})


def _visible_station(entry: dict[str, Any]) -> bool:
    return entry.get("category") not in _HIDDEN_CATEGORIES


def _filter_stations(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [entry for entry in entries if _visible_station(entry)]


def _load_json(name: str) -> dict[str, Any]:
    path = _DATA_DIR / name
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def stations_catalog() -> dict[str, Any]:
    return _load_json("stations.json")


@lru_cache(maxsize=1)
def landing_zones_catalog() -> dict[str, Any]:
    return _load_json("landing_zones.json")


def _station_entries(
    system: str,
    *,
    include_hidden: bool = False,
) -> tuple[list[dict], list[dict]]:
    block = stations_catalog()["systems"].get(system, {})
    with_ref = list(block.get("with_refinery", []))
    without = list(block.get("without_refinery", []))
    if include_hidden:
        return with_ref, without
    return _filter_stations(with_ref), _filter_stations(without)


def _groups_from_stations(
    with_ref: list[dict],
    without: list[dict],
    *,
    system: str,
) -> list[tuple[str, list[tuple[str, str]]]]:
    groups: list[tuple[str, list[tuple[str, str]]]] = []
    if with_ref:
        groups.append((
            f"{system} — Raffinerie",
            [(e["id"], e["name"]) for e in with_ref],
        ))
    if without:
        groups.append((
            f"{system} — ohne Raffinerie",
            [(e["id"], e["name"]) for e in without],
        ))
    return groups


def cities_for_system(system: str) -> list[tuple[str, str]]:
    """Landeplätze / Städte eines Systems: [(id, name), …]."""
    entries = landing_zones_catalog().get("systems", {}).get(system, [])
    return [(e["id"], e["name"]) for e in entries]


def stations_for_system(
    system: str,
    *,
    refinery_only: bool = False,
) -> list[tuple[str, str]]:
    """Weltraum-Stationen eines Systems: [(id, name), …]."""
    with_ref, without = _station_entries(system)
    if refinery_only:
        entries = with_ref
    else:
        entries = with_ref + without
    return [(e["id"], e["name"]) for e in entries]


def station_dropdown_groups() -> list[tuple[str, list[tuple[str, str]]]]:
    """
    Gruppen für QComboBox: (Gruppenlabel, [(id, Anzeigename), …]).
    Pro System: zuerst mit Raffinerie, dann ohne.
    """
    groups: list[tuple[str, list[tuple[str, str]]]] = []
    for system in _SYSTEM_ORDER:
        with_ref, without = _station_entries(system)
        groups.extend(
            _groups_from_stations(with_ref, without, system=system)
        )
    return groups


def refinery_station_dropdown_groups() -> list[tuple[str, list[tuple[str, str]]]]:
    """Weltraum-Stationen mit Raffinerie + Landeplaetze (Orison, Area18, …)."""
    groups: list[tuple[str, list[tuple[str, str]]]] = []
    landing = landing_zones_catalog().get("systems", {})
    for system in _SYSTEM_ORDER:
        with_ref, _ = _station_entries(system)
        entries = [(e["id"], e["name"]) for e in with_ref]
        zone_entries = landing.get(system, [])
        if zone_entries:
            entries.extend(
                (e["id"], e["name"]) for e in zone_entries
            )
        if entries:
            groups.append((f"{system} — Raffinerie", entries))
    return groups


def station_by_id(station_id: str) -> dict[str, Any] | None:
    for system in _SYSTEM_ORDER:
        with_ref, without = _station_entries(system)
        for entry in with_ref + without:
            if entry["id"] == station_id:
                return {**entry, "system": system}
    return None


def landing_zone_dropdown_groups() -> list[tuple[str, list[tuple[str, str]]]]:
    """Landeplätze / Städte für Verkauf (RMC/CM-Ankauf)."""
    catalog = landing_zones_catalog()
    groups: list[tuple[str, list[tuple[str, str]]]] = []
    for system in _SYSTEM_ORDER:
        entries = catalog.get("systems", {}).get(system, [])
        if entries:
            groups.append((
                system,
                [(e["id"], e["name"]) for e in entries],
            ))
    return groups


def sale_location_dropdown_groups() -> list[tuple[str, list[tuple[str, str]]]]:
    """Stationen + Landeplätze für Verkaufsort."""
    groups = list(station_dropdown_groups())
    for label, items in landing_zone_dropdown_groups():
        groups.append((f"{label} — Landeplatz", items))
    return groups


def all_station_ids() -> set[str]:
    ids: set[str] = set()
    for system in _SYSTEM_ORDER:
        with_ref, without = _station_entries(system)
        for entry in with_ref + without:
            ids.add(entry["id"])
    return ids
