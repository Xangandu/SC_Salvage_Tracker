"""MobiGlas-Fensterrahmen mit eigener Titelleiste."""

from __future__ import annotations

import sys

from config.i18n import tr
from PySide6.QtCore import Qt, QPoint, QSize, QEvent, QRect, QObject
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QBoxLayout,
    QMainWindow,
    QDialog,
    QSizePolicy,
    QFrame,
    QStyle,
    QStyleOptionButton,
    QStylePainter,
)

from config.paths import asset_path

_ICON_SIZE = QSize(14, 14)
_TITLE_BAR_HEIGHT = 40
_BEVEL_TOP_HEIGHT = 2
_ROW_HEIGHT = _TITLE_BAR_HEIGHT - _BEVEL_TOP_HEIGHT
_CONTROL_SIZE = QSize(40, 32)
_CONTROLS_H_MARGIN = 0
_CONTROLS_V_MARGIN = 0
_CONTROLS_BUTTON_SPACING = 0
_CONTROLS_FRAME_BORDER = 0


def _win32_minimize(window) -> bool:
    try:
        import ctypes

        hwnd = int(window.winId())
        if hwnd:
            return bool(ctypes.windll.user32.ShowWindow(hwnd, _SW_MINIMIZE))
    except (AttributeError, OSError, ValueError):
        pass
    return False


def _win32_force_rect(window, rect: QRect) -> bool:
    """Fenstergröße setzen — auch nach nativem Aero-Snap-Maximize."""
    try:
        import ctypes

        hwnd = int(window.winId())
        if not hwnd:
            return False
        user32 = ctypes.windll.user32
        if window.isMaximized():
            user32.ShowWindow(hwnd, _SW_RESTORE)
        user32.SetWindowPos(
            hwnd,
            0,
            int(rect.left()),
            int(rect.top()),
            int(rect.width()),
            int(rect.height()),
            _SWP_NOZORDER,
        )
        return window.geometry() == rect
    except (AttributeError, OSError, ValueError):
        return False


def _clear_native_window_maximize(window) -> None:
    """Native Windows-Maximize ohne showNormal() lösen (vermeidet setGeometry-Konflikte)."""
    if not window.isMaximized():
        return
    if sys.platform == "win32":
        try:
            import ctypes

            hwnd = int(window.winId())
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, _SW_RESTORE)
                return
        except (AttributeError, OSError, ValueError):
            pass
    state = window.windowState()
    if state & Qt.WindowState.WindowMaximized:
        window.setWindowState(state & ~Qt.WindowState.WindowMaximized)


def _enable_styled_background(widget):
    widget.setAttribute(
        Qt.WidgetAttribute.WA_StyledBackground,
        True,
    )


def _window_icon(name: str) -> QIcon:
    path = asset_path(
        "assets",
        "images",
        "icons",
        "window",
        f"{name}.svg",
    )
    return QIcon(str(path))


class _TitleBarControlButton(QPushButton):
    """Titelleisten-Button mit manuell zentriertem Icon (Windows-Style-Offset vermeiden)."""

    def __init__(
        self,
        object_name: str,
        icon_name: str,
        tooltip: str,
    ):
        super().__init__()
        self.setObjectName(object_name)
        self.setToolTip(tooltip)
        self.setFixedSize(_CONTROL_SIZE)
        self._button_icon = _window_icon(icon_name)
        self._icon_size = _ICON_SIZE
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAutoFillBackground(True)
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )
        _enable_styled_background(self)

    def set_icon_name(self, icon_name: str) -> None:
        self._button_icon = _window_icon(icon_name)
        self.update()

    def setIcon(self, icon: QIcon) -> None:  # noqa: N802 — Qt-API
        self._button_icon = icon
        self.update()

    def paintEvent(self, event):
        option = QStyleOptionButton()
        self.initStyleOption(option)
        option.icon = QIcon()
        option.text = ""

        painter = QStylePainter(self)
        painter.drawControl(QStyle.ControlElement.CE_PushButton, option)

        x = (self.width() - self._icon_size.width()) // 2
        y = (self.height() - self._icon_size.height()) // 2
        self._button_icon.paint(
            painter,
            QRect(
                x,
                y,
                self._icon_size.width(),
                self._icon_size.height(),
            ),
        )


def _make_control_button(
    object_name: str,
    icon_name: str,
    tooltip: str,
) -> QPushButton:
    return _TitleBarControlButton(object_name, icon_name, tooltip)


def _controls_panel_outer_size(button_count: int) -> QSize:
    if button_count <= 0:
        return QSize(0, 0)

    inner_width = (
        (_CONTROLS_H_MARGIN * 2)
        + (button_count * _CONTROL_SIZE.width())
        + (max(0, button_count - 1) * _CONTROLS_BUTTON_SPACING)
    )
    inner_height = (
        (_CONTROLS_V_MARGIN * 2)
        + _CONTROL_SIZE.height()
    )
    return QSize(
        inner_width + _CONTROLS_FRAME_BORDER,
        inner_height + _CONTROLS_FRAME_BORDER,
    )

_GRIP_SIZE = 8
_RESIZE_BORDER = _GRIP_SIZE
_HTCAPTION = 2
_HTLEFT = 10
_HTRIGHT = 11
_HTTOP = 12
_HTTOPLEFT = 13
_HTTOPRIGHT = 14
_HTBOTTOM = 15
_HTBOTTOMLEFT = 16
_HTBOTTOMRIGHT = 17
_WM_NCHITTEST = 0x0084
_WM_NCLBUTTONDOWN = 0x00A1
_GWL_STYLE = -16
_WS_THICKFRAME = 0x00040000
_WS_MINIMIZEBOX = 0x00020000
_WS_MAXIMIZEBOX = 0x00010000
_SWP_FRAMECHANGED = 0x0020
_SWP_NOMOVE = 0x0002
_SWP_NOSIZE = 0x0001
_SWP_NOZORDER = 0x0004
_SW_MINIMIZE = 6
_SW_RESTORE = 9
_RESIZE_HIT_CODES = frozenset(
    {
        _HTLEFT,
        _HTRIGHT,
        _HTTOP,
        _HTTOPLEFT,
        _HTTOPRIGHT,
        _HTBOTTOM,
        _HTBOTTOMLEFT,
        _HTBOTTOMRIGHT,
    }
)
_DRAG_THRESHOLD = 4


def _title_bar_caption_hit(
    window,
    global_x: int,
    global_y: int,
) -> bool:
    title_bar = getattr(window, "_mobiglas_title_bar", None)
    if title_bar is None or not title_bar.isVisible():
        return False

    title_local = title_bar.mapFromGlobal(QPoint(global_x, global_y))
    if not title_bar.rect().contains(title_local):
        return False

    controls = title_bar._controls_host
    if controls.isVisible():
        control_local = controls.mapFromGlobal(QPoint(global_x, global_y))
        if controls.rect().contains(control_local):
            return False

    actions = title_bar._actions_host
    if actions.isVisible():
        actions_local = actions.mapFromGlobal(QPoint(global_x, global_y))
        if actions.rect().contains(actions_local):
            return False

    return True


def _resize_border(window) -> int:
    ratio = window.devicePixelRatioF()
    if ratio <= 0:
        ratio = 1.0
    return max(_GRIP_SIZE, int(round(_GRIP_SIZE * ratio)))


def _qt_edges_from_ht(ht: int) -> Qt.Edge | None:
    mapping = {
        _HTLEFT: Qt.Edge.LeftEdge,
        _HTRIGHT: Qt.Edge.RightEdge,
        _HTTOP: Qt.Edge.TopEdge,
        _HTBOTTOM: Qt.Edge.BottomEdge,
        _HTTOPLEFT: Qt.Edge.LeftEdge | Qt.Edge.TopEdge,
        _HTTOPRIGHT: Qt.Edge.RightEdge | Qt.Edge.TopEdge,
        _HTBOTTOMLEFT: Qt.Edge.LeftEdge | Qt.Edge.BottomEdge,
        _HTBOTTOMRIGHT: Qt.Edge.RightEdge | Qt.Edge.BottomEdge,
    }
    return mapping.get(ht)


def _resize_hit_test(window, global_x: int, global_y: int) -> int | None:
    pos = window.mapFromGlobal(QPoint(global_x, global_y))
    rect = window.rect()
    border = _resize_border(window)

    on_left = 0 <= pos.x() < border
    on_right = rect.width() - border <= pos.x() <= rect.width()
    on_top = 0 <= pos.y() < border
    on_bottom = rect.height() - border <= pos.y() <= rect.height()

    if on_top and on_left:
        return _HTTOPLEFT
    if on_top and on_right:
        return _HTTOPRIGHT
    if on_bottom and on_left:
        return _HTBOTTOMLEFT
    if on_bottom and on_right:
        return _HTBOTTOMRIGHT
    if on_left:
        return _HTLEFT
    if on_right:
        return _HTRIGHT
    if on_top:
        return _HTTOP
    if on_bottom:
        return _HTBOTTOM

    if _title_bar_caption_hit(window, global_x, global_y):
        return _HTCAPTION

    return None


def _ht_from_qt_edges(edges: Qt.Edge) -> int:
    left = bool(edges & Qt.Edge.LeftEdge)
    right = bool(edges & Qt.Edge.RightEdge)
    top = bool(edges & Qt.Edge.TopEdge)
    bottom = bool(edges & Qt.Edge.BottomEdge)
    if top and left:
        return _HTTOPLEFT
    if top and right:
        return _HTTOPRIGHT
    if bottom and left:
        return _HTBOTTOMLEFT
    if bottom and right:
        return _HTBOTTOMRIGHT
    if left:
        return _HTLEFT
    if right:
        return _HTRIGHT
    if top:
        return _HTTOP
    if bottom:
        return _HTBOTTOM
    return 0


def _ensure_win32_thick_frame(window) -> None:
    """WS_THICKFRAME aktivieren — ohne diesen Stil reagiert Windows nicht auf HT*-Resize."""
    if sys.platform != "win32":
        return

    try:
        import ctypes

        hwnd = int(window.winId())
        if hwnd == 0:
            return

        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, _GWL_STYLE)
        style |= _WS_THICKFRAME | _WS_MINIMIZEBOX | _WS_MAXIMIZEBOX
        user32.SetWindowLongW(hwnd, _GWL_STYLE, style)
        user32.SetWindowPos(
            hwnd,
            0,
            0,
            0,
            0,
            0,
            _SWP_NOMOVE
            | _SWP_NOSIZE
            | _SWP_NOZORDER
            | _SWP_FRAMECHANGED,
        )
    except (AttributeError, OSError, ValueError):
        pass


class _ResizeGrip(QWidget):
    """Unsichtbarer Griff — liegt über Inhalt, damit alle Ränder erreichbar sind."""

    def __init__(
        self,
        window: QWidget,
        *,
        edges: Qt.Edge,
        cursor_shape: Qt.CursorShape,
    ):
        super().__init__(window)
        self._window = window
        self._edges = edges
        self.setCursor(cursor_shape)
        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            False,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setStyleSheet("background: transparent;")
        self.setMouseTracking(True)
        self.raise_()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        title_bar = getattr(self._window, "_mobiglas_title_bar", None)
        if (
            title_bar is not None
            and title_bar._is_window_maximized()
        ):
            if hasattr(event, "globalPosition"):
                global_pos = event.globalPosition().toPoint()
            else:
                global_pos = event.globalPos()
            title_bar._restore_for_edge_resize(
                global_pos,
                _ht_from_qt_edges(self._edges),
            )

        handle = self._window.windowHandle()
        if handle is not None and handle.startSystemResize(self._edges):
            event.accept()
            return
        super().mousePressEvent(event)


class _MobiglasResizeGrips(QObject):
    """Transparente Griffe an allen Fensterrändern."""

    def __init__(self, window: QWidget):
        super().__init__(window)
        self._grips = (
            _ResizeGrip(
                window,
                edges=Qt.Edge.LeftEdge,
                cursor_shape=Qt.CursorShape.SizeHorCursor,
            ),
            _ResizeGrip(
                window,
                edges=Qt.Edge.RightEdge,
                cursor_shape=Qt.CursorShape.SizeHorCursor,
            ),
            _ResizeGrip(
                window,
                edges=Qt.Edge.TopEdge,
                cursor_shape=Qt.CursorShape.SizeVerCursor,
            ),
            _ResizeGrip(
                window,
                edges=Qt.Edge.BottomEdge,
                cursor_shape=Qt.CursorShape.SizeVerCursor,
            ),
            _ResizeGrip(
                window,
                edges=Qt.Edge.LeftEdge | Qt.Edge.TopEdge,
                cursor_shape=Qt.CursorShape.SizeFDiagCursor,
            ),
            _ResizeGrip(
                window,
                edges=Qt.Edge.RightEdge | Qt.Edge.TopEdge,
                cursor_shape=Qt.CursorShape.SizeBDiagCursor,
            ),
            _ResizeGrip(
                window,
                edges=Qt.Edge.LeftEdge | Qt.Edge.BottomEdge,
                cursor_shape=Qt.CursorShape.SizeBDiagCursor,
            ),
            _ResizeGrip(
                window,
                edges=Qt.Edge.RightEdge | Qt.Edge.BottomEdge,
                cursor_shape=Qt.CursorShape.SizeFDiagCursor,
            ),
        )
        self.relayout()

    def _window_widget(self) -> QWidget | None:
        parent = self.parent()
        if isinstance(parent, QWidget):
            return parent
        return None

    def relayout(self):
        window = self._window_widget()
        if window is None:
            return

        try:
            width = max(window.width(), 1)
            height = max(window.height(), 1)
        except RuntimeError:
            return

        border = _resize_border(window)

        left, right, top, bottom, tl, tr, bl, br = self._grips
        left.setGeometry(0, 0, border, height)
        right.setGeometry(
            width - border,
            0,
            border,
            height,
        )
        top.setGeometry(
            border,
            0,
            max(width - 2 * border, border),
            border,
        )
        bottom.setGeometry(
            border,
            height - border,
            max(width - 2 * border, border),
            border,
        )
        tl.setGeometry(0, 0, border, border)
        tr.setGeometry(width - border, 0, border, border)
        bl.setGeometry(0, height - border, border, border)
        br.setGeometry(width - border, height - border, border, border)

        for grip in self._grips:
            grip.show()
            grip.raise_()


def _global_pos_from_msg_lparam(lparam: int) -> QPoint:
    import ctypes

    x = ctypes.c_short(lparam & 0xFFFF).value
    y = ctypes.c_short((lparam >> 16) & 0xFFFF).value
    return QPoint(x, y)


def _clamp_geometry_to_screen(window, rect: QRect) -> QRect:
    screen = window.screen()
    if screen is None:
        return rect

    available = screen.availableGeometry()
    min_size = window.minimumSize()
    width = min(
        max(rect.width(), min_size.width()),
        available.width(),
    )
    height = min(
        max(rect.height(), min_size.height()),
        available.height(),
    )

    left = max(
        available.left(),
        min(rect.left(), available.right() - width + 1),
    )
    top = max(
        available.top(),
        min(rect.top(), available.bottom() - height + 1),
    )
    return QRect(left, top, width, height)


class MobiglasFramelessMixin:
    """Rand-Resize für rahmenlose Fenster unter Windows."""

    def mobiglas_is_maximized(self) -> bool:
        title_bar = getattr(self, "_mobiglas_title_bar", None)
        if title_bar is not None and title_bar._custom_maximized:
            return True
        return self.isMaximized()

    def _sync_custom_maximized_state(self) -> None:
        title_bar = getattr(self, "_mobiglas_title_bar", None)
        if title_bar is None or not title_bar._custom_maximized:
            return

        screen = self.screen()
        if screen is None:
            return

        if self.geometry() != screen.availableGeometry():
            title_bar._custom_maximized = False
            title_bar._sync_maximize_button()

    def _maybe_mark_snapped_maximized(self) -> None:
        title_bar = getattr(self, "_mobiglas_title_bar", None)
        if title_bar is None or title_bar._custom_maximized:
            return

        screen = self.screen()
        if screen is None:
            return

        available = screen.availableGeometry()
        current = self.geometry()
        if current != available:
            return

        if (
            title_bar._normal_geometry is None
            or title_bar._is_full_screen_geometry(
                title_bar._normal_geometry
            )
        ):
            title_bar._normal_geometry = (
                title_bar._default_restore_geometry()
            )

        title_bar._custom_maximized = True
        title_bar._sync_maximize_button()

    def _relayout_resize_grips(self) -> None:
        grips = getattr(self, "_mobiglas_resize_grips", None)
        if grips is not None:
            grips.relayout()

    def moveEvent(self, event):
        self._sync_custom_maximized_state()
        if not self.mobiglas_is_maximized():
            title_bar = getattr(self, "_mobiglas_title_bar", None)
            if title_bar is not None:
                title_bar._normal_geometry = self.geometry()
        super().moveEvent(event)

    def resizeEvent(self, event):
        self._maybe_mark_snapped_maximized()
        self._sync_custom_maximized_state()
        if not self.mobiglas_is_maximized():
            title_bar = getattr(self, "_mobiglas_title_bar", None)
            if title_bar is not None:
                title_bar._normal_geometry = self.geometry()
        self._relayout_resize_grips()
        super().resizeEvent(event)

    def showEvent(self, event):
        _ensure_win32_thick_frame(self)
        if isinstance(self, QDialog):
            _finalize_mobiglas_dialog_size(self)
        self._sync_custom_maximized_state()
        self._relayout_resize_grips()
        super().showEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            title_bar = getattr(self, "_mobiglas_title_bar", None)
            if title_bar is not None:
                if self.isMaximized():
                    normal = self.normalGeometry()
                    if (
                        normal.width() > 0
                        and not title_bar._is_full_screen_geometry(normal)
                    ):
                        title_bar._normal_geometry = normal
                    title_bar._custom_maximized = True
                elif (
                    title_bar._custom_maximized
                    and not title_bar._is_full_screen_geometry(
                        self.geometry()
                    )
                ):
                    title_bar._custom_maximized = False
                title_bar._sync_maximize_button()
        super().changeEvent(event)

    def nativeEvent(self, eventType, message):
        if sys.platform == "win32" and eventType == b"windows_generic_MSG":
            try:
                import ctypes.wintypes as wintypes

                msg = wintypes.MSG.from_address(int(message))
            except (AttributeError, TypeError, ValueError):
                pass
            else:
                if msg.message == _WM_NCHITTEST:
                    global_pos = _global_pos_from_msg_lparam(msg.lParam)
                    ht = _resize_hit_test(
                        self,
                        global_pos.x(),
                        global_pos.y(),
                    )
                    if ht is not None:
                        return True, ht

                if msg.message == _WM_NCLBUTTONDOWN:
                    ht = int(msg.wParam)
                    if ht in _RESIZE_HIT_CODES:
                        title_bar = getattr(
                            self,
                            "_mobiglas_title_bar",
                            None,
                        )
                        if (
                            title_bar is not None
                            and title_bar._is_window_maximized()
                        ):
                            global_pos = _global_pos_from_msg_lparam(
                                msg.lParam
                            )
                            title_bar._restore_for_edge_resize(
                                global_pos,
                                ht,
                            )

        return super().nativeEvent(eventType, message)


class MobiglasTitleBar(QWidget):

    def __init__(
        self,
        window,
        *,
        title="",
        show_minimize=True,
        show_maximize=True,
        show_close=True,
    ):
        super().__init__(window)
        self._window = window
        self._drag_start = None
        self._drag_press_global = None
        self._pending_restore_press = None
        self._drag_moved = False
        self._custom_maximized = False
        self._normal_geometry = None
        self.setObjectName("mobiglasTitleBar")
        self.setFixedHeight(_TITLE_BAR_HEIGHT)
        _enable_styled_background(self)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._bevel_top = QFrame()
        self._bevel_top.setObjectName("mobiglasTitleBevelTop")
        self._bevel_top.setFixedHeight(_BEVEL_TOP_HEIGHT)
        _enable_styled_background(self._bevel_top)
        outer.addWidget(self._bevel_top)

        row_host = QWidget()
        row_host.setObjectName("mobiglasTitleRow")
        row_host.setFixedHeight(_ROW_HEIGHT)
        _enable_styled_background(row_host)
        row = QHBoxLayout(row_host)
        row.setContentsMargins(14, 0, 0, 0)
        row.setSpacing(10)
        row.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self._row_layout = row

        marker = QLabel("◆")
        marker.setObjectName("mobiglasTitleMarker")
        marker.setAlignment(
            Qt.AlignmentFlag.AlignVCenter
        )
        row.addWidget(marker, 0, Qt.AlignmentFlag.AlignVCenter)

        self._title_label = QLabel(title.upper())
        self._title_label.setObjectName("mobiglasTitleLabel")
        self._title_label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter
            | Qt.AlignmentFlag.AlignLeft
        )
        self._title_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        row.addWidget(self._title_label, 1, Qt.AlignmentFlag.AlignVCenter)

        self._actions_host = QWidget()
        self._actions_host.setObjectName("mobiglasTitleActions")
        _enable_styled_background(self._actions_host)
        self._actions_layout = QHBoxLayout(self._actions_host)
        self._actions_layout.setContentsMargins(0, 0, 0, 0)
        self._actions_layout.setSpacing(6)
        self._actions_layout.setAlignment(
            Qt.AlignmentFlag.AlignVCenter
        )
        self._actions_host.hide()
        row.addWidget(
            self._actions_host,
            0,
            Qt.AlignmentFlag.AlignVCenter,
        )

        controls_host = QWidget()
        controls_host.setObjectName("mobiglasTitleControls")
        _enable_styled_background(controls_host)
        controls_host.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )
        controls = QHBoxLayout(controls_host)
        controls.setContentsMargins(
            _CONTROLS_H_MARGIN,
            _CONTROLS_V_MARGIN,
            _CONTROLS_H_MARGIN,
            _CONTROLS_V_MARGIN,
        )
        controls.setSpacing(_CONTROLS_BUTTON_SPACING)
        controls.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._min_button = None
        self._max_button = None
        self._close_button = None

        if show_minimize:
            self._min_button = _make_control_button(
                "mobiglasTitleMin",
                "minimize",
                tr("common.minimize"),
            )
            self._min_button.clicked.connect(
                self._minimize_window
            )
            controls.addWidget(self._min_button)

        if show_maximize:
            self._max_button = _make_control_button(
                "mobiglasTitleMax",
                "maximize",
                tr("common.maximize"),
            )
            self._max_button.clicked.connect(
                self._toggle_maximize
            )
            controls.addWidget(self._max_button)

        if show_close:
            self._close_button = _make_control_button(
                "mobiglasTitleClose",
                "close",
                tr("common.close"),
            )
            if isinstance(self._window, QDialog):
                self._close_button.clicked.connect(
                    self._window.reject
                )
            else:
                self._close_button.clicked.connect(
                    self._window.close
                )
            controls.addWidget(self._close_button)

        visible_controls = sum(
            (
                show_minimize,
                show_maximize,
                show_close,
            )
        )
        self._controls_host = controls_host
        if visible_controls:
            controls_host.setFixedSize(
                _controls_panel_outer_size(visible_controls)
            )
            row.addWidget(
                controls_host,
                0,
                Qt.AlignmentFlag.AlignVCenter,
            )
        else:
            controls_host.hide()
        outer.addWidget(row_host)

        self._show_minimize = show_minimize
        self._show_maximize = show_maximize
        self._show_close = show_close

        self._row_host = row_host
        for widget in (
            self,
            self._bevel_top,
            row_host,
            marker,
            self._title_label,
            self._actions_host,
        ):
            widget.installEventFilter(self)

    def _register_drag_widget(self, widget: QWidget) -> None:
        widget.installEventFilter(self)

    def _is_drag_excluded_widget(self, widget: QWidget) -> bool:
        if widget in (
            self._min_button,
            self._max_button,
            self._close_button,
            self._controls_host,
        ):
            return True
        if self._controls_host.isAncestorOf(widget):
            return True
        if self._actions_host.isVisible() and self._actions_host.isAncestorOf(
            widget
        ):
            return True
        return widget.objectName() == "mobiglasTitleAction"

    def _global_pos_from_event(self, event) -> QPoint:
        if hasattr(event, "globalPosition"):
            return event.globalPosition().toPoint()
        return event.globalPos()

    def _try_begin_window_resize(self, event) -> bool:
        global_pos = self._global_pos_from_event(event)
        ht = _resize_hit_test(
            self._window,
            global_pos.x(),
            global_pos.y(),
        )
        if ht is None or ht == _HTCAPTION:
            return False

        if self._is_window_maximized():
            self._restore_for_edge_resize(global_pos, ht)

        edges = _qt_edges_from_ht(ht)
        if edges is None:
            return False

        handle = self._window.windowHandle()
        if handle is not None and handle.startSystemResize(edges):
            event.accept()
            return True
        return False

    def eventFilter(self, obj, event):
        if self._is_drag_excluded_widget(obj):
            return super().eventFilter(obj, event)

        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                if self._try_begin_window_resize(event):
                    return True
                self._begin_window_drag(event)
                return True
        if event.type() == QEvent.Type.MouseMove:
            if event.buttons() & Qt.MouseButton.LeftButton:
                self._continue_window_drag(event)
                return True
        if event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton:
                self._end_window_drag()
        if event.type() == QEvent.Type.MouseButtonDblClick:
            if (
                event.button() == Qt.MouseButton.LeftButton
                and self._show_maximize
                and not self._drag_moved
            ):
                self._toggle_maximize()
                return True
        return super().eventFilter(obj, event)

    def _event_pos_in_title_bar(self, event) -> QPoint:
        if hasattr(event, "globalPosition"):
            global_pos = event.globalPosition().toPoint()
        else:
            global_pos = event.globalPos()
        return self.mapFromGlobal(global_pos)

    def set_title(self, title: str):
        self._title_label.setText(title.upper())

    def set_leading_widget(self, widget: QWidget):
        """Widget links in der Titelleiste (direkt nach dem Marker)."""
        widget.setParent(self)
        self._row_layout.insertWidget(
            1,
            widget,
            0,
            Qt.AlignmentFlag.AlignVCenter,
        )
        self._register_drag_widget(widget)

    def add_action_button(self, text, callback):
        button = QPushButton(text)
        button.setObjectName("mobiglasTitleAction")
        button.setAutoFillBackground(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        _enable_styled_background(button)
        button.clicked.connect(callback)
        self._actions_layout.addWidget(button)
        self._actions_host.show()
        return button

    def _is_window_maximized(self) -> bool:
        window = self._window
        if window.isMaximized():
            return True
        return self._custom_maximized and self._is_full_screen_geometry()

    def _is_full_screen_geometry(self, geom: QRect | None = None) -> bool:
        window = self._window
        rect = geom if geom is not None else window.geometry()
        screen = window.screen()
        if screen is None:
            return False
        return rect == screen.availableGeometry()

    def _default_restore_geometry(self) -> QRect:
        window = self._window
        screen = window.screen()
        if screen is None:
            return QRect(100, 100, 1200, 800)

        available = screen.availableGeometry()
        width = min(
            max(960, window.minimumWidth()),
            max(available.width() * 4 // 5, window.minimumWidth()),
        )
        height = min(
            max(640, window.minimumHeight()),
            max(available.height() * 4 // 5, window.minimumHeight()),
        )
        return QRect(
            available.left() + (available.width() - width) // 2,
            available.top() + (available.height() - height) // 2,
            width,
            height,
        )

    def _sync_maximize_button(self):
        if self._max_button is None:
            return

        if self._is_window_maximized():
            self._max_button.setIcon(_window_icon("restore"))
            self._max_button.setToolTip(tr("common.restore"))
        else:
            self._max_button.setIcon(_window_icon("maximize"))
            self._max_button.setToolTip(tr("common.maximize"))

    def _ensure_normal_geometry_saved(self) -> None:
        window = self._window
        if self._is_window_maximized():
            return
        geom = window.geometry()
        if not self._is_full_screen_geometry(geom):
            self._normal_geometry = geom

    def _apply_custom_maximize(self) -> None:
        window = self._window
        screen = window.screen()
        if screen is None:
            return

        self._ensure_normal_geometry_saved()
        if (
            self._normal_geometry is None
            or self._is_full_screen_geometry(self._normal_geometry)
        ):
            self._normal_geometry = self._default_restore_geometry()

        _clear_native_window_maximize(window)
        window.setGeometry(screen.availableGeometry())
        self._custom_maximized = True
        self._sync_maximize_button()

    def _apply_custom_restore(self, target: QRect | None = None) -> None:
        window = self._window
        if target is None:
            target = self._fallback_normal_geometry()
        if (
            self._is_full_screen_geometry(target)
            or target.size() == window.geometry().size()
        ):
            target = self._default_restore_geometry()

        target = _clamp_geometry_to_screen(window, target)
        self._custom_maximized = False

        if sys.platform == "win32" and _win32_force_rect(window, target):
            self._normal_geometry = window.geometry()
            self._sync_maximize_button()
            return

        _clear_native_window_maximize(window)
        window.setGeometry(target)
        self._normal_geometry = window.geometry()
        self._sync_maximize_button()

    def _minimize_window(self):
        window = self._window
        self._end_window_drag()

        self._ensure_normal_geometry_saved()
        self._custom_maximized = False

        if sys.platform == "win32" and _win32_minimize(window):
            self._sync_maximize_button()
            return

        _clear_native_window_maximize(window)
        state = window.windowState() & ~Qt.WindowState.WindowMaximized
        window.setWindowState(state | Qt.WindowState.WindowMinimized)

    def _toggle_maximize(self):
        if self._max_button is None:
            return

        window = self._window
        self._end_window_drag()

        if self._is_window_maximized():
            self._apply_custom_restore()
            return

        self._apply_custom_maximize()

    def restore_from_maximize(self):
        if not self._is_window_maximized():
            return

        self._toggle_maximize()

    def _fallback_normal_geometry(self) -> QRect:
        window = self._window
        normal = self._normal_geometry
        if normal is not None and normal.width() > 0 and normal.height() > 0:
            return normal

        normal = window.normalGeometry()
        if normal.width() > 0 and normal.height() > 0:
            return normal

        screen = window.screen()
        if screen is not None:
            available = screen.availableGeometry()
            width = min(1200, available.width())
            height = min(800, available.height())
            return QRect(
                available.left() + (available.width() - width) // 2,
                available.top() + (available.height() - height) // 2,
                width,
                height,
            )

        return QRect(100, 100, 1200, 800)

    def _restore_for_edge_resize(
        self,
        global_pos: QPoint,
        ht_code: int,
    ) -> None:
        """Maximiertes Fenster wiederherstellen, wenn an einem Rand gezogen wird."""
        if not self._is_window_maximized():
            return

        window = self._window
        normal = self._fallback_normal_geometry()
        width = normal.width()
        height = normal.height()
        gx = global_pos.x()
        gy = global_pos.y()

        if ht_code in (_HTLEFT, _HTTOPLEFT, _HTBOTTOMLEFT):
            x = gx
        elif ht_code in (_HTRIGHT, _HTTOPRIGHT, _HTBOTTOMRIGHT):
            x = gx - width
        else:
            x = gx - width // 2

        if ht_code in (_HTTOP, _HTTOPLEFT, _HTTOPRIGHT):
            y = gy
        elif ht_code in (_HTBOTTOM, _HTBOTTOMLEFT, _HTBOTTOMRIGHT):
            y = gy - height
        else:
            y = gy - self.mapFromGlobal(global_pos).y()

        target = _clamp_geometry_to_screen(
            window,
            QRect(x, y, width, height),
        )
        self._custom_maximized = False
        if sys.platform == "win32" and _win32_force_rect(window, target):
            self._normal_geometry = window.geometry()
            self._sync_maximize_button()
            return

        _clear_native_window_maximize(window)
        window.setGeometry(target)
        self._normal_geometry = window.geometry()
        self._sync_maximize_button()

    def _restore_window_for_drag(self, event):
        """Maximiertes Fenster wiederherstellen, damit es gezogen werden kann."""
        window = self._window
        if not self._is_window_maximized():
            return

        normal = self._fallback_normal_geometry()
        local = self._event_pos_in_title_bar(event)
        ratio = local.x() / max(self.width(), 1)
        if hasattr(event, "globalPosition"):
            global_pos = event.globalPosition().toPoint()
        else:
            global_pos = event.globalPos()
        new_x = int(global_pos.x() - normal.width() * ratio)
        new_y = int(global_pos.y() - local.y())

        target = _clamp_geometry_to_screen(
            window,
            QRect(
                new_x,
                new_y,
                normal.width(),
                normal.height(),
            ),
        )
        self._custom_maximized = False
        if sys.platform == "win32" and _win32_force_rect(window, target):
            self._normal_geometry = window.geometry()
            self._sync_maximize_button()
            return

        _clear_native_window_maximize(window)
        window.setGeometry(target)
        self._normal_geometry = window.geometry()
        self._sync_maximize_button()

    def _try_start_system_move(self, event) -> bool:
        handle = self._window.windowHandle()
        if handle is None:
            return False
        if not handle.startSystemMove():
            return False
        self._end_window_drag()
        event.accept()
        return True

    def _begin_window_drag(self, event):
        self._drag_moved = False
        self._drag_press_global = self._global_pos_from_event(event)

        if self._is_window_maximized():
            self._pending_restore_press = event
            self._drag_start = None
            self.grabMouse()
            event.accept()
            return True

        if sys.platform == "win32" and self._try_start_system_move(event):
            return True

        self._pending_restore_press = None
        self._drag_start = (
            self._drag_press_global
            - self._window.frameGeometry().topLeft()
        )
        self.grabMouse()
        event.accept()
        return True

    def _continue_window_drag(self, event):
        if self._drag_press_global is None:
            return False

        global_pos = self._global_pos_from_event(event)
        if not self._drag_moved:
            delta = global_pos - self._drag_press_global
            if delta.manhattanLength() < _DRAG_THRESHOLD:
                return False
            self._drag_moved = True

            if self._pending_restore_press is not None:
                self._restore_window_for_drag(self._pending_restore_press)
                self._pending_restore_press = None
                if sys.platform == "win32" and self._try_start_system_move(event):
                    return True
                self._drag_start = (
                    global_pos - self._window.frameGeometry().topLeft()
                )

        if self._drag_start is not None:
            self._window.move(global_pos - self._drag_start)

        event.accept()
        return True

    def _end_window_drag(self):
        if self.mouseGrabber() is self:
            self.releaseMouse()
        self._drag_start = None
        self._drag_press_global = None
        self._pending_restore_press = None
        self._drag_moved = False

    def mousePressEvent(self, event):
        if (
            event.button() == Qt.MouseButton.LeftButton
            and (
                self._try_begin_window_resize(event)
                or self._begin_window_drag(event)
            )
        ):
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            event.buttons() & Qt.MouseButton.LeftButton
            and self._continue_window_drag(event)
        ):
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._end_window_drag()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._show_maximize
            and not self._drag_moved
        ):
            self._toggle_maximize()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


def _polish_title_bar(title_bar: MobiglasTitleBar):
    style = title_bar.style()
    if style is None:
        return

    for widget in (
        title_bar,
        title_bar._bevel_top,
        title_bar._controls_host,
        title_bar.findChild(QWidget, "mobiglasTitleRow"),
    ):
        if widget is None:
            continue
        style.unpolish(widget)
        style.polish(widget)
        widget.update()

    for button in (
        title_bar._min_button,
        title_bar._max_button,
        title_bar._close_button,
    ):
        if button is None:
            continue
        style.unpolish(button)
        style.polish(button)
        button.update()


def _finalize_mobiglas_dialog_size(window: QDialog) -> None:
    """Größe/Mindestgröße nach Titelleisten-Wrapper und Win32-Rahmen synchronisieren."""
    window.adjustSize()
    hint = window.minimumSizeHint()
    min_w = max(window.minimumWidth(), hint.width())
    min_h = hint.height()
    if min_w > 0 or min_h > 0:
        window.setMinimumSize(min_w, max(min_h, 0))

    target_w = max(window.width(), min_w)
    target_h = max(window.height(), min_h)
    if target_w != window.width() or target_h != window.height():
        window.resize(target_w, target_h)


def apply_mobiglas_window_frame(
    window,
    *,
    title=None,
    dialog=False,
    show_minimize=None,
    show_maximize=None,
    show_close=True,
) -> MobiglasTitleBar:
    if show_minimize is None:
        show_minimize = not dialog
    if show_maximize is None:
        show_maximize = not dialog

    window.setWindowFlag(
        Qt.WindowType.FramelessWindowHint,
        True,
    )
    window.setAttribute(
        Qt.WidgetAttribute.WA_TranslucentBackground,
        False,
    )

    title_text = title or window.windowTitle()
    title_bar = MobiglasTitleBar(
        window,
        title=title_text,
        show_minimize=show_minimize,
        show_maximize=show_maximize,
        show_close=show_close,
    )

    if isinstance(window, QMainWindow):
        _wrap_main_window(window, title_bar)
    else:
        _wrap_dialog(window, title_bar)

    _polish_title_bar(title_bar)
    window._mobiglas_title_bar = title_bar
    if isinstance(window, QDialog):
        _finalize_mobiglas_dialog_size(window)
    if sys.platform == "win32":
        window._mobiglas_resize_grips = _MobiglasResizeGrips(window)
        if window.isVisible():
            _ensure_win32_thick_frame(window)
            window._mobiglas_resize_grips.relayout()
    return title_bar


def _wrap_main_window(window: QMainWindow, title_bar: MobiglasTitleBar):
    central = window.centralWidget()

    root = QWidget()
    root.setObjectName("mobiglasWindowRoot")

    layout = QVBoxLayout(root)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    layout.addWidget(title_bar)

    if central is not None:
        layout.addWidget(central, 1)

    window.setCentralWidget(root)

    menu_bar = window.menuBar()
    if menu_bar is not None:
        menu_bar.hide()


def _wrap_dialog(window: QDialog, title_bar: MobiglasTitleBar):
    old_layout = window.layout()
    if old_layout is None:
        layout = QVBoxLayout(window)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(title_bar)
        return

    margins = old_layout.contentsMargins()
    spacing = old_layout.spacing()

    content = QWidget()
    content.setObjectName("mobiglasDialogContent")
    content.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Expanding,
    )
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(margins)
    content_layout.setSpacing(spacing)

    while old_layout.count():
        stretch = 0
        alignment = Qt.AlignmentFlag(0)

        if isinstance(old_layout, QBoxLayout):
            stretch = old_layout.stretch(0)
            layout_item = old_layout.itemAt(0)
            if layout_item is not None:
                alignment = layout_item.alignment()

        item = old_layout.takeAt(0)
        if item is None:
            continue
        if item.widget():
            content_layout.addWidget(
                item.widget(),
                stretch,
                alignment,
            )
        elif item.layout():
            content_layout.addLayout(item.layout())
        elif item.spacerItem():
            content_layout.addItem(item.spacerItem())

    old_layout.setContentsMargins(0, 0, 0, 0)
    old_layout.setSpacing(0)
    old_layout.addWidget(title_bar)
    old_layout.addWidget(content, 1)
