"""Icons für die linke Hauptnavigation."""

from __future__ import annotations

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton

from config.paths import asset_path
from ui.nav_metrics import nav_icon_size, normalize_nav_width

_NAV_ICON_FILES = {
    "dashboard": "overviewlink-Photoroom.png",
    "session": "sessionlink-Photoroom.png",
    "storage": "warehouselink.png",
    "refinery": "refinerylink-Photoroom.png",
    "sales": "salelink-Photoroom.png",
    "payout": "payoutlink-Photoroom.png",
    "history": "historylink.png",
    "settings": "settingslink-Photoroom.png",
}


def nav_button_icon(key: str) -> QIcon | None:
    filename = _NAV_ICON_FILES.get(key)
    if not filename:
        return None

    path = asset_path("assets", "images", filename)
    if not path.exists():
        return None

    return QIcon(str(path))


def apply_nav_button_icon(
    button: QPushButton,
    key: str,
    *,
    nav_width: str = "normal",
) -> bool:
    icon = nav_button_icon(key)
    if icon is None:
        return False

    button.setIcon(icon)
    button.setIconSize(nav_icon_size(normalize_nav_width(nav_width)))
    return True


def configure_nav_button(
    button: QPushButton,
    key: str,
    *,
    nav_width: str = "normal",
) -> None:
    button.setObjectName("navButton")
    apply_nav_button_icon(button, key, nav_width=nav_width)
