"""MobiGlas-Fensterrahmen mit eigener Titelleiste."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt, QPoint, QSize, QEvent
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
)

from config.paths import asset_path

_CONTROL_SIZE = QSize(26, 22)
_ICON_SIZE = QSize(12, 12)
_TITLE_BAR_HEIGHT = 38
_BEVEL_TOP_HEIGHT = 2
_ROW_HEIGHT = _TITLE_BAR_HEIGHT - _BEVEL_TOP_HEIGHT
_CONTROLS_H_MARGIN = 5
_CONTROLS_V_MARGIN = 2
_CONTROLS_BUTTON_SPACING = 4
_CONTROLS_FRAME_BORDER = 2


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


def _make_control_button(
    object_name: str,
    icon_name: str,
    tooltip: str,
) -> QPushButton:
    button = QPushButton()
    button.setObjectName(object_name)
    button.setToolTip(tooltip)
    button.setFixedSize(_CONTROL_SIZE)
    button.setIcon(_window_icon(icon_name))
    button.setIconSize(_ICON_SIZE)
    button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setAutoFillBackground(True)
    button.setSizePolicy(
        QSizePolicy.Policy.Fixed,
        QSizePolicy.Policy.Fixed,
    )
    _enable_styled_background(button)
    return button


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

_RESIZE_BORDER = 8
_HTLEFT = 10
_HTRIGHT = 11
_HTTOP = 12
_HTTOPLEFT = 13
_HTTOPRIGHT = 14
_HTBOTTOM = 15
_HTBOTTOMLEFT = 16
_HTBOTTOMRIGHT = 17


class MobiglasFramelessMixin:
    """Rand-Resize für rahmenlose Fenster unter Windows."""

    def mobiglas_is_maximized(self) -> bool:
        title_bar = getattr(self, "_mobiglas_title_bar", None)
        if title_bar is not None and title_bar._custom_maximized:
            return True
        return self.isMaximized()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            title_bar = getattr(self, "_mobiglas_title_bar", None)
            if title_bar is not None:
                title_bar._sync_maximize_button()
        super().changeEvent(event)

    def nativeEvent(self, eventType, message):
        result = super().nativeEvent(eventType, message)
        if sys.platform != "win32":
            return result
        if eventType != b"windows_generic_MSG":
            return result

        try:
            import ctypes
            import ctypes.wintypes as wintypes

            msg = wintypes.MSG.from_address(int(message))
        except (AttributeError, TypeError, ValueError):
            return result

        if msg.message != 0x0084:  # WM_NCHITTEST
            return result

        if self.mobiglas_is_maximized():
            return result

        x = ctypes.c_short(msg.lParam & 0xFFFF).value
        y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
        pos = self.mapFromGlobal(QPoint(x, y))
        rect = self.rect()

        on_left = 0 <= pos.x() <= _RESIZE_BORDER
        on_right = rect.width() - _RESIZE_BORDER <= pos.x() <= rect.width()
        on_top = 0 <= pos.y() <= _RESIZE_BORDER
        on_bottom = rect.height() - _RESIZE_BORDER <= pos.y() <= rect.height()

        if on_top and on_left:
            return True, _HTTOPLEFT
        if on_top and on_right:
            return True, _HTTOPRIGHT
        if on_bottom and on_left:
            return True, _HTBOTTOMLEFT
        if on_bottom and on_right:
            return True, _HTBOTTOMRIGHT
        if on_left:
            return True, _HTLEFT
        if on_right:
            return True, _HTRIGHT
        if on_top:
            return True, _HTTOP
        if on_bottom:
            return True, _HTBOTTOM

        return result


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
        row.setContentsMargins(12, 0, 8, 0)
        row.setSpacing(10)
        row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

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

        controls_host = QFrame()
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
                "Minimieren",
            )
            self._min_button.clicked.connect(
                self._window.showMinimized
            )
            controls.addWidget(self._min_button)

        if show_maximize:
            self._max_button = _make_control_button(
                "mobiglasTitleMax",
                "maximize",
                "Maximieren",
            )
            self._max_button.clicked.connect(
                self._toggle_maximize
            )
            controls.addWidget(self._max_button)

        if show_close:
            self._close_button = _make_control_button(
                "mobiglasTitleClose",
                "close",
                "Schließen",
            )
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

    def set_title(self, title: str):
        self._title_label.setText(title.upper())

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
        if self._custom_maximized:
            return True
        return self._window.isMaximized()

    def _sync_maximize_button(self):
        if self._max_button is None:
            return

        if self._is_window_maximized():
            self._max_button.setIcon(_window_icon("restore"))
            self._max_button.setToolTip("Wiederherstellen")
        else:
            self._custom_maximized = False
            self._max_button.setIcon(_window_icon("maximize"))
            self._max_button.setToolTip("Maximieren")

    def _toggle_maximize(self):
        if self._max_button is None:
            return

        window = self._window

        if self._is_window_maximized():
            if self._normal_geometry is not None:
                window.setGeometry(self._normal_geometry)
            else:
                window.showNormal()
            self._custom_maximized = False
            self._sync_maximize_button()
            return

        self._normal_geometry = window.geometry()
        screen = window.screen()
        if screen is not None:
            window.setGeometry(screen.availableGeometry())
            self._custom_maximized = True
        else:
            window.showMaximized()
            self._custom_maximized = window.isMaximized()

        self._sync_maximize_button()

    def restore_from_maximize(self):
        if not self._is_window_maximized():
            return

        self._toggle_maximize()

    def mousePressEvent(self, event):
        if (
            event.button() == Qt.MouseButton.LeftButton
            and not self._is_window_maximized()
        ):
            self._drag_start = (
                event.globalPosition().toPoint()
                - self._window.frameGeometry().topLeft()
            )
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            event.buttons() & Qt.MouseButton.LeftButton
            and self._drag_start is not None
            and not self._is_window_maximized()
        ):
            self._window.move(
                event.globalPosition().toPoint() - self._drag_start
            )
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_start = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._show_maximize
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
    ):
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
