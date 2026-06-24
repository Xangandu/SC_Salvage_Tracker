#!/usr/bin/env python3
"""Supporter-Keys für CREW/ORGA erzeugen (offline, nicht ins Repo committen)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.edition_keys import generate_supporter_key  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Supporter-Keys für SC Salvage Tracker erzeugen.",
    )
    parser.add_argument(
        "edition",
        choices=("crew", "orga"),
        help="Ziel-Edition",
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=1,
        help="Anzahl Keys (Standard: 1)",
    )
    args = parser.parse_args()
    count = max(1, args.count)

    print(f"Edition: {args.edition.upper()}  |  Anzahl: {count}\n")
    for index in range(count):
        key = generate_supporter_key(args.edition)
        print(f"{index + 1:3d}.  {key}")
    print(
        "\nKeys sicher aufbewahren — nicht in Git committen.\n"
        "Einlösung: Einstellungen → Unterstützen → Supporter-Key"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
