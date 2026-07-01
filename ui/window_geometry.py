"""Fensterposition und -größe zwischen Sitzungen speichern."""

from __future__ import annotations

import json

from PySide6.QtCore import QPoint, QRect, QSize
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication

_SETTING_KEY = "window_geometry"
_DASHBOARD_GEOMETRY_KEY = "dashboard_window_geometry"
_DASHBOARD_OPEN_KEY = "dashboard_window_open"
_LAST_NAV_PAGE_PREFIX = "last_nav_page_"

MAIN_WINDOW_MIN_SIZE = QSize(640, 480)
DASHBOARD_WINDOW_MIN_SIZE = QSize(960, 640)


def _load_geometry_from_db(db, setting_key: str) -> dict | None:
    raw = db.settings.get_app_setting(setting_key, "")
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


def _load_geometry(db) -> dict | None:
    return _load_geometry_from_db(db, _SETTING_KEY)


def _effective_minimum_size(window) -> QSize:
    min_size = window.minimumSize()
    hint = window.minimumSizeHint()
    return QSize(
        max(min_size.width(), hint.width()),
        max(min_size.height(), hint.height()),
    )


def _default_window_size(screen, *, ratio: float = 0.85) -> tuple[int, int]:
    if screen is None:
        return 1280, 720

    available = screen.availableGeometry()
    width = max(
        MAIN_WINDOW_MIN_SIZE.width(),
        min(int(available.width() * ratio), available.width()),
    )
    height = max(
        MAIN_WINDOW_MIN_SIZE.height(),
        min(int(available.height() * ratio), available.height()),
    )
    return width, height


def _save_geometry_to_db(window, db, setting_key: str) -> None:
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
        setting_key,
        json.dumps(payload),
    )


def _clamp_to_screen(
    rect: QRect,
    screen,
    *,
    window=None,
    min_size: QSize | None = None,
) -> QRect:
    if screen is None:
        return rect

    available = screen.availableGeometry()
    if min_size is None and window is not None:
        min_size = _effective_minimum_size(window)
    if min_size is None:
        min_size = MAIN_WINDOW_MIN_SIZE

    width = min(rect.width(), available.width())
    height = min(rect.height(), available.height())
    width = max(width, min(min_size.width(), available.width()))
    height = max(height, min(min_size.height(), available.height()))

    left = max(
        available.left(),
        min(rect.left(), available.right() - width + 1),
    )
    top = max(
        available.top(),
        min(rect.top(), available.bottom() - height + 1),
    )
    return QRect(left, top, width, height)


def fit_window_to_screen(window) -> None:
    """Fenster an den verfügbaren Bildschirmbereich anpassen (nach Restore/Layout)."""
    if hasattr(window, "mobiglas_is_maximized") and window.mobiglas_is_maximized():
        screen = window.screen() or QApplication.primaryScreen()
        if screen is not None:
            window.setGeometry(screen.availableGeometry())
        return

    screen = window.screen() or QApplication.primaryScreen()
    if screen is None:
        return

    rect = _clamp_to_screen(
        window.geometry(),
        screen,
        window=window,
    )
    window.setGeometry(rect)


def _restore_window_geometry(
    window,
    db,
    setting_key: str,
    *,
    default_width: int | None = None,
    default_height: int | None = None,
    min_size: QSize | None = None,
) -> None:
    screen = window.screen() or QApplication.primaryScreen()
    if default_width is None or default_height is None:
        auto_w, auto_h = _default_window_size(screen)
        default_width = default_width or auto_w
        default_height = default_height or auto_h

    data = _load_geometry_from_db(db, setting_key)
    if not data:
        _center_on_primary(
            window,
            default_width,
            default_height,
            min_size=min_size,
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
            min_size=min_size,
        )
        return

    screen = _resolve_screen(
        str(data.get("screen_name") or ""),
        rect.center(),
    )
    rect = _clamp_to_screen(
        rect,
        screen,
        window=window,
        min_size=min_size,
    )
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


def _center_on_primary(
    window,
    width: int,
    height: int,
    *,
    min_size: QSize | None = None,
):
    screen = QApplication.primaryScreen()
    if screen is None:
        window.resize(width, height)
        return

    available = screen.availableGeometry()
    rect = _clamp_to_screen(
        QRect(0, 0, width, height),
        screen,
        window=window,
        min_size=min_size,
    )
    left = available.left() + (available.width() - rect.width()) // 2
    top = available.top() + (available.height() - rect.height()) // 2
    window.setGeometry(left, top, rect.width(), rect.height())


def restore_window_geometry(
    window,
    db,
    *,
    default_width: int | None = None,
    default_height: int | None = None,
) -> None:
    _restore_window_geometry(
        window,
        db,
        _SETTING_KEY,
        default_width=default_width,
        default_height=default_height,
        min_size=MAIN_WINDOW_MIN_SIZE,
    )
    if _load_geometry_from_db(db, _SETTING_KEY):
        fit_window_to_screen(window)


def save_window_geometry(window, db) -> None:
    _save_geometry_to_db(window, db, _SETTING_KEY)


def restore_dashboard_window_geometry(
    window,
    db,
    *,
    default_width: int | None = None,
    default_height: int | None = None,
) -> None:
    _restore_window_geometry(
        window,
        db,
        _DASHBOARD_GEOMETRY_KEY,
        default_width=default_width,
        default_height=default_height,
        min_size=DASHBOARD_WINDOW_MIN_SIZE,
    )
    if _load_geometry_from_db(db, _DASHBOARD_GEOMETRY_KEY):
        fit_window_to_screen(window)


def save_dashboard_window_geometry(window, db) -> None:
    _save_geometry_to_db(window, db, _DASHBOARD_GEOMETRY_KEY)


def dashboard_open_on_startup(db) -> bool:
    return (
        db.settings.get_app_setting(_DASHBOARD_OPEN_KEY, "0")
        == "1"
    )


def set_dashboard_open_on_startup(db, open_state: bool) -> None:
    db.settings.set_app_setting(
        _DASHBOARD_OPEN_KEY,
        "1" if open_state else "0",
    )


def _last_nav_page_key(user_id: int | str) -> str:
    return f"{_LAST_NAV_PAGE_PREFIX}{user_id}"


def save_last_nav_page(db, user_id: int | str, page_key: str) -> None:
    if not page_key:
        return
    db.settings.set_app_setting(
        _last_nav_page_key(user_id),
        page_key,
    )


def load_last_nav_page(db, user_id: int | str) -> str | None:
    raw = db.settings.get_app_setting(
        _last_nav_page_key(user_id),
        "",
    )
    return raw.strip() or None
