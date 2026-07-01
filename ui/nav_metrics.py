"""Navigationsleiste — Breite, Icon-Größen und Abstände."""

from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

NAV_WIDTH_KEYS = frozenset({"narrow", "normal", "wide"})

NAV_MIDDLE_KEYS = (
    "session",
    "refinery",
    "storage",
    "sales",
    "statistics",
    "history",
)

NAV_DIVIDER_PADDING = 6
NAV_SETTINGS_DIVIDER_AFTER = 10

NAV_WIDTH_PX = {
    "narrow": (188, 208),
    "normal": (248, 268),
    "wide": (288, 308),
}

# Icon-Größe, Button-Abstand, Außenabstände der Leiste
NAV_LAYOUT = {
    "narrow": {
        "icon_px": 76,
        "button_spacing": 8,
        "panel_margin_v": 10,
        "panel_margin_h": 0,
        "brand_h_margin": 8,
    },
    "normal": {
        "icon_px": 100,
        "button_spacing": 10,
        "panel_margin_v": 12,
        "panel_margin_h": 0,
        "brand_h_margin": 12,
    },
    "wide": {
        "icon_px": 112,
        "button_spacing": 12,
        "panel_margin_v": 14,
        "panel_margin_h": 0,
        "brand_h_margin": 12,
    },
}


def normalize_nav_width(nav_width: str) -> str:
    if nav_width in NAV_WIDTH_KEYS:
        return nav_width
    return "normal"


def nav_icon_size(nav_width: str) -> QSize:
    key = normalize_nav_width(nav_width)
    px = NAV_LAYOUT[key]["icon_px"]
    return QSize(px, px)


def _repolish_nav_panel(nav_panel: QWidget) -> None:
    style = nav_panel.style()
    if style is None:
        return
    style.unpolish(nav_panel)
    style.polish(nav_panel)
    nav_panel.update()


def apply_nav_panel_metrics(
    nav_panel: QWidget,
    nav_outer_layout: QVBoxLayout,
    nav_scroll_layout: QVBoxLayout,
    buttons: dict[str, QPushButton],
    *,
    badge_buttons: list[QPushButton] | None = None,
    brand_block: QWidget | None = None,
    nav_middle_layout: QVBoxLayout | None = None,
    nav_width: str = "normal",
) -> None:
    """Breite, Icon-Größen und Abstände der Navigationsleiste setzen."""
    key = normalize_nav_width(nav_width)
    metrics = NAV_LAYOUT[key]
    min_w, max_w = NAV_WIDTH_PX[key]
    icon = nav_icon_size(key)

    nav_panel.setProperty("navWidth", key)
    nav_panel.setMinimumWidth(min_w)
    nav_panel.setMaximumWidth(max_w)

    nav_outer_layout.setContentsMargins(
        metrics["panel_margin_h"],
        metrics["panel_margin_v"],
        metrics["panel_margin_h"],
        metrics["panel_margin_v"],
    )
    nav_scroll_layout.setSpacing(metrics["button_spacing"])

    if nav_middle_layout is not None:
        nav_middle_layout.setSpacing(metrics["button_spacing"])

    if brand_block is not None:
        brand_layout = brand_block.layout()
        if brand_layout is not None:
            h = metrics["brand_h_margin"]
            brand_layout.setContentsMargins(h, 0, h, 4)

    for button in buttons.values():
        button.setIconSize(icon)

    for button in badge_buttons or []:
        button.setIconSize(icon)

    _repolish_nav_panel(nav_panel)
