"""Interaktive Vorschau des Setup-Assistenten (ohne echte Installation)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from installer.wizard_app import run_wizard


def main(argv: list[str] | None = None) -> int:
    return run_wizard(demo_mode=True, argv=argv)


if __name__ == "__main__":
    raise SystemExit(main())
