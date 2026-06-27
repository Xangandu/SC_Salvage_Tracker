"""Splash-Screen Demo — zeigt den neuen Tracker-Ladebalken."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from PySide6.QtCore import QTimer, QEventLoop
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

from config.font_families import existing_font_paths
from config.i18n import tr
from ui.splash_screen import SplashScreen, SPLASH_DURATION_MS


_DEMO_STEPS = (
    "splash.initializing",
    "splash.db_preparing",
    "splash.fonts_loading",
    "splash.ui_preparing",
    "splash.complete",
)


def main() -> int:
    app = QApplication(sys.argv)

    for font_path in existing_font_paths():
        QFontDatabase.addApplicationFont(str(font_path))

    splash = SplashScreen(duration_ms=max(SPLASH_DURATION_MS, 10000))
    splash.show_splash()

    step_index = {"value": 0}

    def advance_status() -> None:
        idx = step_index["value"]
        if idx < len(_DEMO_STEPS):
            splash.set_status(tr(_DEMO_STEPS[idx]))
            step_index["value"] += 1
            QTimer.singleShot(1400, advance_status)
        else:
            splash.notify_init_complete()

    QTimer.singleShot(900, advance_status)

    loop = QEventLoop()
    splash.finished.connect(loop.quit)
    loop.exec()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
