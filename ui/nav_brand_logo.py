"""Navigations-Logo (editionsspezifische PNG-Dateien)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from config.editions import effective_edition
from config.paths import asset_path
from ui.nav_edition_badge import (
    build_nav_edition_badge,
    sync_nav_edition_badge_size,
)
from ui.nav_metrics import normalize_nav_width
from ui.page_layout import nav_edition_divider

_NAV_BRAND_LOGO_WIDTH = {
    "narrow": 156,
    "normal": 196,
    "wide": 236,
}


def nav_brand_logo_path(edition_key: str) -> Path | None:
    path = asset_path("assets", "images", f"scst_{edition_key}_logo.png")
    return path if path.is_file() else None


def refresh_nav_brand_logo(
    label: QLabel,
    edition_key: str,
    nav_width: str = "normal",
) -> bool:
    path = nav_brand_logo_path(edition_key)
    if path is None:
        return False

    pixmap = QPixmap(str(path))
    if pixmap.isNull():
        return False

    max_width = _NAV_BRAND_LOGO_WIDTH.get(
        normalize_nav_width(nav_width),
        _NAV_BRAND_LOGO_WIDTH["normal"],
    )
    scaled = pixmap.scaledToWidth(
        max_width,
        Qt.TransformationMode.SmoothTransformation,
    )
    label.setPixmap(scaled)
    label.setFixedSize(scaled.size())
    return True


def _clear_layout(layout: QVBoxLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
        sub_layout = item.layout()
        if sub_layout is not None:
            while sub_layout.count():
                sub_item = sub_layout.takeAt(0)
                sub_widget = sub_item.widget()
                if sub_widget is not None:
                    sub_widget.deleteLater()


def rebuild_nav_brand_header(
    host: QWidget,
    layout: QVBoxLayout,
    db,
    *,
    edition_short_label_fn,
    nav_width: str = "normal",
) -> dict[str, QWidget | None]:
    """Logo oder Text+Badge neu aufbauen. Gibt Widget-Referenzen zurück."""
    _clear_layout(layout)

    edition_key = effective_edition(db)
    refs: dict[str, QWidget | None] = {
        "logo_label": None,
        "badge_host": None,
        "badge": None,
        "title_primary": None,
        "title_secondary": None,
    }

    if nav_brand_logo_path(edition_key) is not None:
        logo_label = QLabel(host)
        logo_label.setObjectName("navBrandLogo")
        logo_label.setAlignment(
            Qt.AlignmentFlag.AlignHCenter
            | Qt.AlignmentFlag.AlignVCenter
        )
        refresh_nav_brand_logo(logo_label, edition_key, nav_width)
        layout.addWidget(
            logo_label,
            0,
            Qt.AlignmentFlag.AlignHCenter,
        )
        refs["logo_label"] = logo_label
        return refs

    title_primary = QLabel("SALVAGE", host)
    title_primary.setObjectName("navTitlePrimary")
    title_primary.setAlignment(
        Qt.AlignmentFlag.AlignLeft
        | Qt.AlignmentFlag.AlignVCenter
    )

    title_secondary = QLabel("TRACKER", host)
    title_secondary.setObjectName("navTitleSecondary")
    title_secondary.setAlignment(
        Qt.AlignmentFlag.AlignLeft
        | Qt.AlignmentFlag.AlignVCenter
    )

    badge_host, badge = build_nav_edition_badge(
        edition_short_label_fn(db),
        edition_key,
    )

    title_stack = QVBoxLayout()
    title_stack.setContentsMargins(0, 0, 0, 0)
    title_stack.setSpacing(0)
    title_stack.addWidget(title_primary)
    title_stack.addWidget(title_secondary)

    layout.addLayout(title_stack)
    layout.addSpacing(6)
    layout.addLayout(nav_edition_divider(badge_host))
    layout.addSpacing(8)

    refs["title_primary"] = title_primary
    refs["title_secondary"] = title_secondary
    refs["badge_host"] = badge_host
    refs["badge"] = badge
    return refs


def sync_nav_brand_badge_after_theme(
    badge_host: QWidget | None,
    badge: QLabel | None,
) -> None:
    if badge_host is None or badge is None:
        return
    sync_nav_edition_badge_size(badge_host, badge)
