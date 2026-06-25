"""Partikelwolke für Dashboard-Statuswechsel."""

from __future__ import annotations

import math
import random

from PySide6.QtCore import (
    QEvent,
    QObject,
    QTimer,
    Qt,
    QRectF,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
)
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QWidget,
)

ANIMATION_MS = 1800
CYCLE_COMPLETE_MS = 10_000
CYCLE_COMPLETE_BLINK_MS = 500
_PARTICLE_COUNT = 42

_ORANGE_CARD_LIGHT = """
QFrame#dashboardKpiCard {
    background: rgba(255, 179, 71, 0.45);
    border: 1px solid rgba(255, 200, 120, 0.95);
    border-radius: 6px;
    padding: 6px 10px;
}
"""

_ORANGE_CARD_DARK = """
QFrame#dashboardKpiCard {
    background: rgba(153, 76, 0, 0.58);
    border: 1px solid rgba(204, 102, 0, 0.95);
    border-radius: 6px;
    padding: 6px 10px;
}
"""

_ORANGE_VALUE_LIGHT = """
QLabel#dashboardKpiStatusValue {
    color: #4A2800;
    font-weight: bold;
}
"""

_ORANGE_VALUE_DARK = """
QLabel#dashboardKpiStatusValue {
    color: #FFE8C8;
    font-weight: bold;
}
"""

_STATUS_GLOW = {
    "ACTIVE": (65, 209, 122),
    "WAITING_FOR_REFINERY": (230, 192, 74),
    "WAITING_FOR_SALE": (0, 170, 255),
    "REFINERY_COMPLETED": (0, 170, 255),
    "WAITING_FOR_PAYOUT": (0, 196, 220),
    "SOLD": (0, 229, 204),
    "IDLE": (120, 150, 165),
}


def _glow_rgb(status_code: str) -> tuple[int, int, int]:
    return _STATUS_GLOW.get(status_code, (0, 217, 255))


class _Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "ttl", "size", "color")

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        ttl: float,
        size: float,
        color: QColor,
    ):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = 0.0
        self.ttl = ttl
        self.size = size
        self.color = color


class _CardResizeFilter(QObject):
    def __init__(self, card: QFrame):
        super().__init__(card)
        self._card = card

    def eventFilter(self, watched, event):
        if watched is self._card and event.type() == QEvent.Type.Resize:
            overlay = getattr(self._card, "_status_effect_overlay", None)
            if overlay is not None:
                overlay.setGeometry(self._card.rect())
        return False


class StatusParticleOverlay(QWidget):
    def __init__(self, card: QFrame):
        super().__init__(card)
        self._card = card
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.hide()

        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

        self._particles: list[_Particle] = []
        self._elapsed_ms = 0

    def start(self, rgb: tuple[int, int, int]):
        self._elapsed_ms = 0

        width = max(self.width(), 40)
        height = max(self.height(), 40)
        center_x = width / 2
        center_y = height / 2

        base = QColor(*rgb)
        self._particles = []
        for _ in range(_PARTICLE_COUNT):
            angle = random.uniform(0.0, 2.0 * math.pi)
            speed = random.uniform(70.0, 220.0)
            ttl = random.uniform(0.55, 1.0)
            size = random.uniform(1.6, 4.2)
            tint = QColor(base)
            tint.setAlpha(random.randint(160, 255))
            self._particles.append(
                _Particle(
                    center_x,
                    center_y,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    ttl,
                    size,
                    tint,
                )
            )

        self.setGeometry(self._card.rect())
        self.show()
        self.raise_()
        self._timer.start()
        self.update()

    def stop(self):
        self._timer.stop()
        self._particles.clear()
        self.hide()
        self.update()

    def _tick(self):
        dt = self._timer.interval() / 1000.0
        self._elapsed_ms += self._timer.interval()

        alive_particles = []
        for particle in self._particles:
            particle.life += dt / particle.ttl
            if particle.life >= 1.0:
                continue
            particle.x += particle.vx * dt
            particle.y += particle.vy * dt
            particle.vy += 28.0 * dt
            particle.vx *= 0.985
            alive_particles.append(particle)
        self._particles = alive_particles

        self.update()

        if self._elapsed_ms >= ANIMATION_MS and not self._particles:
            self.stop()

    def paintEvent(self, _event):
        if not self._particles:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        for particle in self._particles:
            fade = 1.0 - particle.life
            if fade <= 0:
                continue
            color = QColor(particle.color)
            color.setAlpha(int(color.alpha() * fade))
            radius = particle.size * (0.6 + fade * 0.8)
            gradient = QLinearGradient(
                particle.x - radius,
                particle.y - radius,
                particle.x + radius,
                particle.y + radius,
            )
            gradient.setColorAt(0.0, color)
            inner = QColor(255, 255, 255, int(180 * fade))
            gradient.setColorAt(1.0, inner)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(
                QRectF(
                    particle.x - radius,
                    particle.y - radius,
                    radius * 2,
                    radius * 2,
                )
            )

        painter.end()


class _CycleCompleteBlink(QObject):
    def __init__(
        self,
        card: QFrame,
        value_label: QLabel,
        payout_text: str,
        complete_text: str,
        on_finished,
    ):
        super().__init__(card)
        self._card = card
        self._value_label = value_label
        self._payout_text = payout_text
        self._complete_text = complete_text
        self._on_finished = on_finished
        self._elapsed_ms = 0
        self._show_payout = True

        self._timer = QTimer(self)
        self._timer.setInterval(CYCLE_COMPLETE_BLINK_MS)
        self._timer.timeout.connect(self._tick)

    def start(self):
        self._elapsed_ms = 0
        self._show_payout = True
        self._apply_frame()
        self._timer.start()

    def stop(self):
        if self._timer.isActive():
            self._timer.stop()
        self._card.setStyleSheet("")
        self._card.setObjectName("dashboardKpiCard")
        card_style = self._card.style()
        card_style.unpolish(self._card)
        card_style.polish(self._card)
        self._card.update()

        self._value_label.setStyleSheet("")
        self._value_label.setObjectName("dashboardKpiStatusValue")
        style = self._value_label.style()
        style.unpolish(self._value_label)
        style.polish(self._value_label)
        self._value_label.update()

    def _apply_frame(self):
        if self._show_payout:
            self._card.setStyleSheet(_ORANGE_CARD_LIGHT)
            self._value_label.setStyleSheet(_ORANGE_VALUE_LIGHT)
            self._value_label.setText(self._payout_text)
        else:
            self._card.setStyleSheet(_ORANGE_CARD_DARK)
            self._value_label.setStyleSheet(_ORANGE_VALUE_DARK)
            self._value_label.setText(self._complete_text)

        self._value_label.setObjectName("dashboardKpiStatusValue")

    def _tick(self):
        self._elapsed_ms += CYCLE_COMPLETE_BLINK_MS
        self._show_payout = not self._show_payout
        self._apply_frame()

        if self._elapsed_ms >= CYCLE_COMPLETE_MS:
            self._timer.stop()
            self.stop()
            if self._on_finished is not None:
                self._on_finished()


class DashboardStatusAnimator:
    @classmethod
    def _overlay(cls, card: QFrame) -> StatusParticleOverlay:
        overlay = getattr(card, "_status_effect_overlay", None)
        if overlay is None:
            overlay = StatusParticleOverlay(card)
            card._status_effect_overlay = overlay
            resize_filter = _CardResizeFilter(card)
            card.installEventFilter(resize_filter)
            card._status_resize_filter = resize_filter
        overlay.setGeometry(card.rect())
        return overlay

    @classmethod
    def stop(cls, card: QFrame, value_label: QLabel | None = None):
        cls.stop_cycle_complete(card)

        overlay = getattr(card, "_status_effect_overlay", None)
        if overlay is not None:
            overlay.stop()

        if value_label is not None:
            value_label.setGraphicsEffect(None)

    @classmethod
    def stop_cycle_complete(cls, card: QFrame):
        blink = getattr(card, "_cycle_complete_blink", None)
        if blink is not None:
            blink.stop()
            card._cycle_complete_blink = None

    @classmethod
    def cycle_complete(
        cls,
        card: QFrame,
        value_label: QLabel,
        payout_text: str,
        complete_text: str,
        on_finished=None,
    ):
        cls.stop(card, value_label)
        blink = _CycleCompleteBlink(
            card,
            value_label,
            payout_text,
            complete_text,
            on_finished,
        )
        card._cycle_complete_blink = blink
        blink.start()

    @classmethod
    def is_cycle_complete_running(cls, card: QFrame) -> bool:
        blink = getattr(card, "_cycle_complete_blink", None)
        return blink is not None and blink._timer.isActive()

    @classmethod
    def pulse(
        cls,
        card: QFrame,
        value_label: QLabel,
        status_code: str,
        status_text: str,
    ):
        cls.stop(card, value_label)
        value_label.setText(status_text)
        overlay = cls._overlay(card)
        overlay.start(_glow_rgb(status_code))
