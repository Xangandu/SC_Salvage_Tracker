"""Tracker-Standorte → UEX-Handels-Terminals."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from config.paths import asset_path
from services.uex.http import uex_get, uex_rows
from services.uex.models import UexTerminalRef

_OVERRIDE_PATH = Path(__file__).resolve().parents[2] / "config" / "uex_terminal_map.json"

# Manuelle Aliase für schwierige Ortsnamen (UEX-Suche)
_SEARCH_ALIASES: dict[str, tuple[str, ...]] = {
    "AREA18": ("Area 18", "Area18"),
    "NEW-BABBAGE": ("New Babbage",),
    "CHECKMATE-CZ": ("Checkmate",),
    "L19": ("L19", "Lorville"),
    "ORISON": ("Orison",),
    "LORVILLE": ("Lorville",),
    "LEVSKI": ("Levski",),
}


@lru_cache(maxsize=1)
def _load_overrides() -> dict[str, dict[str, Any]]:
    path = asset_path("config", "uex_terminal_map.json")
    if not path.is_file():
        path = _OVERRIDE_PATH
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data.get("locations", {})


def _override_key(
    system: str,
    location_kind: str,
    location_key: str,
) -> str:
    return f"{system}|{location_kind}|{location_key}"


class UexTerminalResolver:
    """Löst Tracker-Standorte in UEX-Terminal-IDs auf (mit Cache)."""

    def __init__(self):
        self._cache: dict[str, UexTerminalRef | None] = {}

    def resolve(
        self,
        *,
        system: str,
        location_kind: str,
        location_key: str,
        location_label: str,
    ) -> UexTerminalRef | None:
        cache_key = _override_key(system, location_kind, location_key)
        if cache_key in self._cache:
            return self._cache[cache_key]

        terminal = self._resolve_uncached(
            system=system,
            location_kind=location_kind,
            location_key=location_key,
            location_label=location_label,
        )
        self._cache[cache_key] = terminal
        return terminal

    def _resolve_uncached(
        self,
        *,
        system: str,
        location_kind: str,
        location_key: str,
        location_label: str,
    ) -> UexTerminalRef | None:
        overrides = _load_overrides()
        override = overrides.get(_override_key(
            system,
            location_kind,
            location_key,
        ))
        if override:
            terminal_id = override.get("id_terminal")
            if terminal_id is not None:
                return UexTerminalRef(
                    id_terminal=int(terminal_id),
                    code=str(override.get("code") or ""),
                    name=str(override.get("name") or location_label),
                )

        for query in self._search_queries(location_key, location_label):
            terminals = self._search_terminals(query)
            picked = self._pick_terminal(terminals)
            if picked is not None:
                return picked

        return None

    def _search_terminals(self, name: str) -> list[UexTerminalRef]:
        payload = uex_get("terminals", {"name": name})
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
                    name=str(
                        row.get("name")
                        or row.get("displayname")
                        or ""
                    ),
                )
            )
        return result

    def _search_queries(
        self,
        location_key: str,
        location_label: str,
    ) -> tuple[str, ...]:
        queries: list[str] = []
        seen: set[str] = set()

        def add(value: str) -> None:
            value = (value or "").strip()
            if not value:
                return
            key = value.casefold()
            if key in seen:
                return
            seen.add(key)
            queries.append(value)

        for alias in _SEARCH_ALIASES.get(location_key.upper(), ()):
            add(alias)

        add(location_key.replace("-", " "))
        add(location_key)

        label = (location_label or "").strip()
        add(label)
        if "(" in label:
            add(label.split("(")[0].strip())

        short = re.split(r"\s[-—]\s", label)[0].strip()
        add(short)

        return tuple(queries)

    @staticmethod
    def _pick_terminal(
        terminals: list[UexTerminalRef],
    ) -> UexTerminalRef | None:
        if not terminals:
            return None

        def score(terminal: UexTerminalRef) -> tuple[int, int]:
            name = terminal.name.casefold()
            if "trade and development" in name or name.startswith("tdd"):
                return (0, terminal.id_terminal)
            if "admin" in name:
                return (1, terminal.id_terminal)
            if "municipal" in name:
                return (2, terminal.id_terminal)
            return (3, terminal.id_terminal)

        return min(terminals, key=score)
