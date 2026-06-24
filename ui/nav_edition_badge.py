"""Edition-Badge in der Navigations-Leiste (zentriert in der Glowbox)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QSizePolicy

_BADGE_PAD_H = 16
_BADGE_PAD_V = 10


def build_nav_edition_badge(
    text: str,
    edition_key: str,
) -> tuple[QFrame, QLabel]:
    host = QFrame()
    host.setObjectName("navEditionBadgeHost")
    host.setProperty("edition", edition_key)

    label = QLabel(text.upper())
    label.setObjectName("navEditionBadge")
    label.setProperty("edition", edition_key)
    label.setAlignment(
        Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
    )
    label.setIndent(0)
    label.setContentsMargins(0, 0, 0, 0)
    label.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Expanding,
    )

    layout = QVBoxLayout(host)
    layout.setContentsMargins(
        _BADGE_PAD_H,
        _BADGE_PAD_V,
        _BADGE_PAD_H,
        _BADGE_PAD_V,
    )
    layout.setSpacing(0)
    layout.addWidget(label)

    sync_nav_edition_badge_size(host, label)
    return host, label


def _measure_badge_text(label: QLabel) -> tuple[int, int]:
    metrics = QFontMetrics(label.font())
    text = label.text()
    bounds = metrics.tightBoundingRect(text)
    font = label.font()

    extra_spacing = 0.0
    if font.letterSpacingType() != QFont.SpacingType.PercentageSpacing:
        extra_spacing = max(0, len(text) - 1) * font.letterSpacing()

    hint = label.sizeHint()
    text_w = max(int(bounds.width() + extra_spacing), hint.width())
    text_h = max(bounds.height(), hint.height(), metrics.height())
    return text_w, text_h


def sync_nav_edition_badge_size(host: QFrame, label: QLabel) -> None:
    """Größe nach Theme/Font neu berechnen (Letter-Spacing, Orbitron, …)."""
    label.ensurePolished()
    host.ensurePolished()

    text_w, text_h = _measure_badge_text(label)
    margins = host.layout().contentsMargins()
    host.setFixedSize(
        text_w + margins.left() + margins.right(),
        text_h + margins.top() + margins.bottom(),
    )

