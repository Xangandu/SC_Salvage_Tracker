"""Leistungstest: Dashboard-Skalierung (Live-Vorschau vs. Voll-Apply)."""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.context_dashboard.components import TimelineRow
from ui.theme_manager import ThemeManager


def _build_heavy_dashboard(page: QWidget) -> None:
    layout = QVBoxLayout(page)
    for index in range(40):
        layout.addWidget(
            TimelineRow(
                "12.03. 18:45",
                f"Material {index}",
                f"Detailzeile {index} · 120 SCU",
            )
        )
    for index in range(60):
        label = QLabel(f"KPI {index}")
        label.setObjectName("cardValue")
        layout.addWidget(label)


def _time_call(label: str, fn, *, iterations: int) -> float:
    samples: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        QApplication.processEvents()
        samples.append(time.perf_counter() - start)

    avg_ms = statistics.mean(samples) * 1000
    p95_ms = sorted(samples)[max(0, int(len(samples) * 0.95) - 1)] * 1000
    fps = 1000 / avg_ms if avg_ms > 0 else 0
    print(f"{label:28}  avg {avg_ms:6.2f} ms   p95 {p95_ms:6.2f} ms   ~{fps:5.0f} Hz")
    return avg_ms


def main() -> int:
    app = QApplication(sys.argv)
    ThemeManager.apply_settings({"theme": "dark", "font_family": "segoe_ui"})

    page = QWidget()
    page.setObjectName("dashboardPage")
    ThemeManager.register_dashboard_page(page)
    _build_heavy_dashboard(page)
    page.resize(960, 720)
    page.show()
    QApplication.processEvents()

    scales = {
        "dashboard_font_scale": 100,
        "dashboard_title_font_scale": 100,
        "dashboard_button_font_scale": 100,
    }

    print(
        "Dashboard-Skalierung — Widgets:",
        len(page.findChildren(QLabel)),
        "Labels",
    )
    print("-" * 72)

    ThemeManager.refresh_dashboard_font_scale(scales, live_preview=False)

    def legacy_scan_full():
        for widget in app.allWidgets():
            if widget.objectName() == "dashboardPage":
                ThemeManager.apply_dashboard_fonts(widget, scales)

    def registered_full():
        ThemeManager.refresh_dashboard_font_scale(
            scales,
            live_preview=False,
        )

    def registered_live():
        ThemeManager.refresh_dashboard_font_scale(
            scales,
            live_preview=True,
        )

    def bump_scale():
        scales["dashboard_font_scale"] = (
            scales["dashboard_font_scale"] + 5
        )
        if scales["dashboard_font_scale"] > 150:
            scales["dashboard_font_scale"] = 80

    legacy_ms = _time_call(
        "Legacy (allWidgets + full)",
        legacy_scan_full,
        iterations=8,
    )
    full_ms = _time_call(
        "Registry + full apply",
        registered_full,
        iterations=8,
    )
    live_ms = _time_call(
        "Registry + live preview",
        lambda: (bump_scale(), registered_live()),
        iterations=120,
    )

    print("-" * 72)
    if live_ms > 0:
        print(f"Live vs. Legacy: {legacy_ms / live_ms:.1f}x schneller")
    print(f"Full apply (Loslassen):     {full_ms:.2f} ms")
    target_hz = 120
    target_ms = 1000 / target_hz
    ok = live_ms <= target_ms
    print(
        f"Ziel {target_hz} Hz ({target_ms:.1f} ms/Tick): "
        + ("OK" if ok else f"noch {live_ms - target_ms:.1f} ms zu langsam")
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
