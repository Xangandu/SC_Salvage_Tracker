"""Operations Base Alpha — interaktive Vorschau (0.15 Konzept)."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ui.operations_base_preview import run_operations_base_preview


def main():
    parser = argparse.ArgumentParser(
        description=(
            "SC Salvage Tracker — Operations Base Alpha Vorschau"
        ),
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Echte Tracker-Daten aus der DB laden (falls vorhanden)",
    )
    args = parser.parse_args()
    raise SystemExit(
        run_operations_base_preview(live=args.live)
    )


if __name__ == "__main__":
    main()
