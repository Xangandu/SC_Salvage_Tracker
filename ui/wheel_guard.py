"""Verhindert Mausrad-Änderungen in Formularfeldern ohne Fokus."""

from PySide6.QtCore import QObject, QEvent
from PySide6.QtWidgets import (
    QApplication,
    QAbstractSpinBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QLineEdit,
    QScrollArea,
    QSlider,
    QTextEdit,
    QTimeEdit,
    QWidget,
)

_WHEEL_BLOCK_TYPES = (
    QComboBox,
    QAbstractSpinBox,
    QDateEdit,
    QTimeEdit,
    QDateTimeEdit,
    QSlider,
    QTextEdit,
)


class WheelGuardFilter(QObject):
    """Blockiert Wheel-Events auf Eingabewidgets ohne Fokus."""

    def eventFilter(self, watched, event):
        if event.type() != QEvent.Type.Wheel:
            return False

        if not isinstance(watched, QWidget):
            return False

        host = _wheel_block_host(watched)
        if host is None:
            return False

        if not _should_block_wheel(host):
            return False

        scroll_target = _scroll_viewport(host)
        if scroll_target is not None:
            QApplication.sendEvent(scroll_target, event)
            return True

        event.ignore()
        return True


def _wheel_block_host(widget):
    if not isinstance(widget, QWidget):
        return None

    if isinstance(widget, _WHEEL_BLOCK_TYPES):
        return widget

    if isinstance(widget, QLineEdit):
        parent = widget.parentWidget()
        if isinstance(parent, (QComboBox, QAbstractSpinBox)):
            return parent

    parent = widget.parentWidget()
    while isinstance(parent, QWidget):
        if isinstance(parent, _WHEEL_BLOCK_TYPES):
            return parent
        parent = parent.parentWidget()
    return None


def _has_effective_focus(host):
    focus = QApplication.focusWidget()
    if not isinstance(focus, QWidget):
        return False

    current = focus
    while isinstance(current, QWidget):
        if current is host:
            return True
        current = current.parentWidget()
    return False


def _combo_popup_open(combo):
    view = combo.view()
    if view is None:
        return False
    return view.isVisible()


def _should_block_wheel(host):
    if isinstance(host, QComboBox):
        return not _combo_popup_open(host)
    return not _has_effective_focus(host)


def _scroll_viewport(widget):
    parent = widget.parentWidget()
    while isinstance(parent, QWidget):
        if isinstance(parent, QScrollArea):
            return parent.viewport()
        parent = parent.parentWidget()
    return None


def install_wheel_guard(app):
    guard = WheelGuardFilter(app)
    app.installEventFilter(guard)
    return guard
