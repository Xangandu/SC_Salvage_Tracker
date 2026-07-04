"""Manueller Test: UEX-Verkaufspreise für Tracker-Standorte."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.locations.catalog import (
    SYSTEM_ORDER,
    cities_for_system,
    stations_for_system,
)
from services.uex.api_client import UexApiClient
from services.uex.models import UexApiError


def _sample_locations(limit: int = 12):
    count = 0
    for system in SYSTEM_ORDER:
        for location_id, name in stations_for_system(system):
            yield system, "STATION", location_id, name
            count += 1
            if count >= limit:
                return
        for location_id, name in cities_for_system(system):
            yield system, "CITY", location_id, name
            count += 1
            if count >= limit:
                return


def main() -> int:
    client = UexApiClient()
    ok = 0
    failed = 0

    for system, kind, key, label in _sample_locations():
        try:
            result = client.fetch_sale_prices(
                system=system,
                location_kind=kind,
                location_key=key,
                location_label=label,
            )
        except UexApiError as error:
            print(f"FAIL {label:40} {error}")
            failed += 1
            continue

        prices = result.prices_by_tracker_code
        if not prices:
            print(f"EMPTY {label:40} terminal={result.terminal.code}")
            failed += 1
            continue

        print(
            f"OK   {label:40} terminal={result.terminal.code} prices={prices}"
        )
        ok += 1

    print("-" * 72)
    print(f"OK: {ok}  Failed/empty: {failed}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
