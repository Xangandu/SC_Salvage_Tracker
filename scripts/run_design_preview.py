"""Design-Vorschau starten (Star-Citizen-Launcher-Stil)."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ui.design_preview_window import run_design_preview


def main():
    parser = argparse.ArgumentParser(
        description="SC Salvage Tracker — Design-Vorschau",
    )
    parser.add_argument(
        "--scifi",
        action="store_true",
        help="Alternative mit Audiowide / Michroma / Exo 2 / Share Tech Mono",
    )
    args = parser.parse_args()
    variant = "scifi" if args.scifi else "classic"
    raise SystemExit(run_design_preview(variant=variant))


if __name__ == "__main__":
    main()
