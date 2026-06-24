"""Automatische Dashboard-Widget-Größe anhand Textüberlauf."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QLabel, QWidget

from ui.dashboard_fit_label import DashboardFitLabel

SIZE_ESCALATION_ORDER = ("1x1", "2x1", "2x2")


def next_larger_size(current: str, allowed_sizes) -> str | None:
    allowed = [
        size
        for size in SIZE_ESCALATION_ORDER
        if size in allowed_sizes
    ]
    try:
        index = allowed.index(current)
    except ValueError:
        return None
    if index + 1 < len(allowed):
        return allowed[index + 1]
    return None


def _label_text_fits(
    label: QLabel,
    width: int,
    *,
    max_lines: int = 3,
) -> bool:
    text = label.text()
    if width <= 0 or not text:
        return True

    metrics = QFontMetrics(label.font())
    rect = metrics.boundingRect(
        0,
        0,
        width,
        10000,
        int(Qt.TextFlag.TextWordWrap),
        text,
    )
    line_h = metrics.height()
    line_count = max(1, (rect.height() + line_h - 1) // line_h)
    if line_count > max_lines:
        return False
    return rect.width() <= width + 1


def widget_needs_wider_size(
    inner: QWidget,
    content_width: int,
) -> bool:
    """True, wenn Inhalt bei Dashboard-Basisschrift nicht in die Breite passt."""
    if content_width <= 0:
        return False

    for label in inner.findChildren(DashboardFitLabel):
        if not label.text_fits_at_width(content_width):
            return True

    for label in inner.findChildren(QLabel):
        name = label.objectName()
        if name != "dashboardKpiTitle":
            continue
        if isinstance(label, DashboardFitLabel):
            continue
        if not _label_text_fits(label, content_width, max_lines=2):
            return True

    return False
