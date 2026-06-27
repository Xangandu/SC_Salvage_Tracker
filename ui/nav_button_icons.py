"""Icons für die linke Hauptnavigation."""

from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton

from config.paths import asset_path

NAV_BUTTON_ICON_SIZE = QSize(100, 100)

_NAV_ICON_FILES = {
    "dashboard": "overviewlink-Photoroom.png",
    "session": "sessionlink-Photoroom.png",
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


def apply_nav_button_icon(button: QPushButton, key: str) -> bool:
    icon = nav_button_icon(key)
    if icon is None:
        return False

    button.setIcon(icon)
    button.setIconSize(NAV_BUTTON_ICON_SIZE)
    return True


def configure_nav_button(button: QPushButton, key: str) -> None:
    button.setObjectName("navButton")
    apply_nav_button_icon(button, key)
