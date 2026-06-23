"""Fensterposition und -größe zwischen Sitzungen speichern."""

from __future__ import annotations

import json

from PySide6.QtCore import QPoint, QRect
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication

_SETTING_KEY = "window_geometry"


def _load_geometry(db) -> dict | None:
    raw = db.settings.get_app_setting(_SETTING_KEY, "")
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    required = ("x", "y", "w", "h")
    if not all(key in data for key in required):
        return None
    return data


def _resolve_screen(screen_name: str, center: QPoint):
    app = QGuiApplication.instance()
    if app is None:
        return None

    if screen_name:
        for screen in app.screens():
            if screen.name() == screen_name:
                return screen

    screen = app.screenAt(center)
    if screen is not None:
        return screen

    return app.primaryScreen()


def _clamp_to_screen(rect: QRect, screen) -> QRect:
    if screen is None:
        return rect

    available = screen.availableGeometry()
    width = min(rect.width(), available.width())
    height = min(rect.height(), available.height())
    width = max(width, 640)
    height = max(height, 480)

    left = max(
        available.left(),
        min(rect.left(), available.right() - width + 1),
    )
    top = max(
        available.top(),
        min(rect.top(), available.bottom() - height + 1),
    )
    return QRect(left, top, width, height)


def _center_on_primary(window, width: int, height: int):
    screen = QApplication.primaryScreen()
    if screen is None:
        window.resize(width, height)
        return

    available = screen.availableGeometry()
    width = min(width, available.width())
    height = min(height, available.height())
    left = available.left() + (available.width() - width) // 2
    top = available.top() + (available.height() - height) // 2
    window.setGeometry(left, top, width, height)


def restore_window_geometry(
    window,
    db,
    *,
    default_width: int = 1600,
    default_height: int = 900,
) -> None:
    data = _load_geometry(db)
    if not data:
        _center_on_primary(
            window,
            default_width,
            default_height,
        )
        return

    try:
        rect = QRect(
            int(data["x"]),
            int(data["y"]),
            int(data["w"]),
            int(data["h"]),
        )
    except (TypeError, ValueError):
        _center_on_primary(
            window,
            default_width,
            default_height,
        )
        return

    screen = _resolve_screen(
        str(data.get("screen_name") or ""),
        rect.center(),
    )
    rect = _clamp_to_screen(rect, screen)
    maximized = bool(data.get("maximized"))

    title_bar = getattr(window, "_mobiglas_title_bar", None)
    if maximized and title_bar is not None:
        title_bar._normal_geometry = rect
        if screen is not None:
            window.setGeometry(screen.availableGeometry())
        else:
            window.setGeometry(rect)
        title_bar._custom_maximized = True
        title_bar._sync_maximize_button()
        return

    window.setGeometry(rect)


def save_window_geometry(window, db) -> None:
    title_bar = getattr(window, "_mobiglas_title_bar", None)
    maximized = (
        window.mobiglas_is_maximized()
        if hasattr(window, "mobiglas_is_maximized")
        else window.isMaximized()
    )

    if (
        maximized
        and title_bar is not None
        and title_bar._normal_geometry is not None
    ):
        geom = title_bar._normal_geometry
    else:
        geom = window.geometry()

    screen = window.screen()
    payload = {
        "x": geom.x(),
        "y": geom.y(),
        "w": geom.width(),
        "h": geom.height(),
        "maximized": maximized,
        "screen_name": screen.name() if screen is not None else "",
    }
    db.settings.set_app_setting(
        _SETTING_KEY,
        json.dumps(payload),
    )
