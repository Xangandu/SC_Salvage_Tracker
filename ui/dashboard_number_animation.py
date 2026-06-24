"""Weiche Hoch-/Runterzähl-Animation für Dashboard-KPI-Zahlen."""

from PySide6.QtCore import (
    QEasingCurve,
    QVariantAnimation,
    QAbstractAnimation,
)
from PySide6.QtWidgets import QLabel

from config.strings_de import format_number_de

DEFAULT_DURATION_MS = 4000


class AnimatedDashboardValue(QLabel):
    """QLabel mit sanfter Zahlenanimation (Start → Ziel)."""

    def __init__(self, text="0", parent=None):
        super().__init__(text, parent)
        self._numeric_value = 0.0
        self._suffix = ""
        self._prefix = ""
        self._decimals = 0

        self._animation = QVariantAnimation(self)
        self._animation.setDuration(DEFAULT_DURATION_MS)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.valueChanged.connect(self._apply_display_value)
        self._animation.finished.connect(self._on_finished)

    def animate_to(
        self,
        target,
        *,
        suffix="",
        prefix="",
        decimals=0,
        duration=None,
    ):
        target = float(target)
        self._suffix = suffix
        self._prefix = prefix
        self._decimals = decimals

        if duration is not None:
            self._animation.setDuration(duration)

        if self._animation.state() == QAbstractAnimation.State.Running:
            start = float(self._animation.currentValue())
        else:
            start = self._numeric_value

        if abs(start - target) < 1e-9:
            self._animation.stop()
            self._numeric_value = target
            self._apply_display_value(target)
            return

        self._animation.stop()
        self._animation.setStartValue(start)
        self._animation.setEndValue(target)
        self._animation.start()

    def set_immediate(
        self,
        target,
        *,
        suffix="",
        prefix="",
        decimals=0,
    ):
        self._animation.stop()
        self._numeric_value = float(target)
        self._suffix = suffix
        self._prefix = prefix
        self._decimals = decimals
        self._apply_display_value(self._numeric_value)

    def _on_finished(self):
        self._numeric_value = float(self._animation.endValue())
        self._apply_display_value(self._numeric_value)

    def _apply_display_value(self, value):
        self._numeric_value = float(value)
        text = format_number_de(self._numeric_value, self._decimals)
        if self._prefix:
            text = f"{self._prefix}{text}"
        if self._suffix:
            text = f"{text}{self._suffix}"
        super().setText(text)
