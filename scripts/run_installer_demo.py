"""Setup-Assistent als interaktive Demo starten."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from installer.installer_demo import main

if __name__ == "__main__":
    raise SystemExit(main())
