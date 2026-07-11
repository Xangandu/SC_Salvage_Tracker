#!/usr/bin/env python3
"""
Auszahlungs-Layout DEMO für SC Salvage Tracker.

Start (aus dem Projektroot):
    python demo/payout_layout_demo.py

Zeigt drei Varianten der Auszahlungsseite mit denselben Mock-Daten:
  A — Aktuell (vertikal, wie Screenshot)
  B — Zweispaltig (KPI oben, links Workflow, rechts Historie)
  C — Workflow (Master-Detail)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import PySide6.QtSvg  # noqa: F401 — SVG-Plugin
from PySide6.QtWidgets import QApplication

from config.i18n import init_language_from_db, set_language
from demo.payout_layout.window import PayoutLayoutDemoWindow
from ui.theme_manager import ThemeManager
from ui.wheel_guard import install_wheel_guard


def main() -> int:
    app = QApplication(sys.argv)
    install_wheel_guard(app)

    try:
        init_language_from_db()
    except Exception:
        set_language("de")

    ThemeManager.apply_settings({
        "theme": "star_citizen",
        "font_size": "normal",
        "animations": "full",
    })

    window = PayoutLayoutDemoWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
