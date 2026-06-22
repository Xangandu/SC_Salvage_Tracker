"""Interaktive Vorschau — Salvage Operations Base Alpha (0.15 Konzept).

Starten mit:
  py scripts/run_operations_base_preview.py
  py scripts/run_operations_base_preview.py --live

Keine Änderungen an der Produktions-App — nur Mockup / Art Direction.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontDatabase,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config.paths import asset_path


MATERIAL_COLORS = {
    "RMC": QColor(214, 178, 48),
    "CM": QColor(52, 118, 178),
    "CM Salvage": QColor(178, 108, 52),
    "CM_SALVAGE": QColor(178, 108, 52),
    "CM Rubble": QColor(118, 116, 112),
    "CM_RUBBLE": QColor(118, 116, 112),
    "CM Scraps": QColor(158, 98, 62),
    "CM_SCRAPS": QColor(158, 98, 62),
}


@dataclass
class BaseState:
    credits: int = 12_758_420
    total_profit: int = 8_420_000
    costs: int = 1_120_000
    net_profit: int = 7_300_000
    storage_fill: float = 0.63
    storage_scu: int = 15240
    storage_capacity: int = 24000
    materials: dict = field(default_factory=lambda: {
        "RMC": 4200,
        "CM": 3100,
        "CM Salvage": 2800,
        "CM Rubble": 1900,
        "CM Scraps": 3240,
    })
    refinery_status: str = "processing"
    refinery_progress: float = 0.65
    refinery_job_id: str = "R-21"
    refinery_input: str = "CM Rubble"
    refinery_output: str = "CM"
    session_active: bool = True
    session_ship: str = "Aegis Vulture"
    session_location: str = "ARC-L1 · Wreck Field Delta"
    session_hours: float = 2.4
    session_profit_est: int = 420_000
    hangar_vulture: str = "Mission Active"
    hangar_reclaimer: str = "Docked"
    events: list = field(default_factory=lambda: [
        "Refinery Job #R-21 — Fertig in 1h 24m",
        "Trade Terminal — 800 SCU CM verkaufsbereit",
        "Hangar — Vulture Rückkehr ETA 45 Min",
        "Storage — Block C bei 63 % Kapazität",
    ])
    comms: list = field(default_factory=lambda: [
        "08:41  Storage Deck — Containerblock C erweitert",
        "08:38  Refinery Complex — Charge 65 % verarbeitet",
        "08:22  Trade Terminal — Verkauf #47 abgeschlossen",
        "08:05  Operations — Tagesgewinn +142.000 aUEC",
        "07:50  Hangar — Reclaimer Docking abgeschlossen",
    ])


def _demo_state() -> BaseState:
    return BaseState()


def _live_state() -> BaseState:
    state = _demo_state()
    try:
        from database.access import get_database
        db = get_database()
    except Exception:
        return state

    try:
        revenue = int(db.get_total_sales_value() or 0)
        costs = int(db.get_global_total_costs() or 0)
        state.credits = revenue
        state.total_profit = revenue
        state.costs = costs
        state.net_profit = revenue - costs

        inventory = db.get_available_storage_inventory()
        total_scu = sum(int(i.get("quantity", 0)) for i in inventory)
        state.storage_scu = total_scu
        state.storage_capacity = max(24000, total_scu * 2 or 24000)
        state.storage_fill = min(
            1.0,
            total_scu / state.storage_capacity if state.storage_capacity else 0,
        )
        state.materials = {
            i["material_code"]: int(i["quantity"])
            for i in inventory
        } or state.materials

        jobs = db.get_active_refinery_jobs()
        if jobs:
            job = jobs[0]
            state.refinery_job_id = f"R-{job['id']}"
            state.refinery_status = (
                "complete" if job.get("status") == "READY"
                else "processing"
            )
            state.refinery_progress = (
                0.85 if job.get("status") == "READY" else 0.45
            )
        else:
            state.refinery_status = "idle"
            state.refinery_progress = 0.0

        session = db.get_active_session()
        if session:
            state.session_active = True
            state.session_ship = session[1] or "Aegis Vulture"
            state.hangar_vulture = "Mission Active"
        else:
            state.session_active = False
            state.hangar_vulture = "Docked"
    except Exception:
        pass

    return state


def _draw_ship_vulture(
    painter: QPainter,
    cx: float,
    cy: float,
    scale: float,
    *,
    lit: bool,
    alpha: int = 255,
):
    body = QColor(190, 198, 210, alpha) if lit else QColor(72, 78, 88, alpha)
    if lit and alpha > 200:
        body = QColor(220, 228, 238, alpha)

    path = QPainterPath()
    s = scale
    path.moveTo(cx, cy - 22 * s)
    path.lineTo(cx + 8 * s, cy - 6 * s)
    path.lineTo(cx + 28 * s, cy + 2 * s)
    path.lineTo(cx + 10 * s, cy + 4 * s)
    path.lineTo(cx + 6 * s, cy + 16 * s)
    path.lineTo(cx - 6 * s, cy + 16 * s)
    path.lineTo(cx - 10 * s, cy + 4 * s)
    path.lineTo(cx - 28 * s, cy + 2 * s)
    path.lineTo(cx - 8 * s, cy - 6 * s)
    path.closeSubpath()
    painter.fillPath(path, QBrush(body))
    painter.setPen(QPen(QColor(232, 160, 74, 120 if lit else 40), 1))
    painter.drawPath(path)


def _draw_ship_reclaimer(
    painter: QPainter,
    cx: float,
    cy: float,
    scale: float,
    *,
    lit: bool,
    alpha: int = 255,
):
    hull = QColor(130, 138, 148, alpha) if not lit else QColor(175, 182, 192, alpha)
    painter.setBrush(QBrush(hull))
    painter.setPen(QPen(QColor(60, 64, 72, alpha), 1))

    s = scale
    body = QRectF(cx - 42 * s, cy - 8 * s, 84 * s, 22 * s)
    painter.drawRoundedRect(body, 3, 3)

    bridge = QRectF(cx - 12 * s, cy - 18 * s, 24 * s, 12 * s)
    painter.drawRect(bridge)

    for side in (-1, 1):
        arm = QPainterPath()
        ax = cx + side * 38 * s
        arm.moveTo(ax, cy + 2 * s)
        arm.lineTo(ax + side * 18 * s, cy - 20 * s)
        arm.lineTo(ax + side * 24 * s, cy - 18 * s)
        arm.lineTo(ax + side * 8 * s, cy + 6 * s)
        arm.closeSubpath()
        painter.fillPath(arm, QBrush(hull.darker(115)))

    if lit:
        painter.setBrush(QColor(232, 140, 60, 160))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx - 30 * s, cy + 10 * s), 3 * s, 3 * s)
        painter.drawEllipse(QPointF(cx + 30 * s, cy + 10 * s), 3 * s, 3 * s)


class BaseSceneWidget(QWidget):
    zone_clicked = Signal(str)
    zone_hovered = Signal(str)

    ZONES = (
        ("operations", 1, "OPERATIONS CENTER"),
        ("hangar", 2, "HANGAR DECK"),
        ("storage", 3, "STORAGE DECK"),
        ("refinery", 4, "REFINERY COMPLEX"),
        ("trade", 5, "TRADE TERMINAL"),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(720, 480)
        self.setMouseTracking(True)
        self._state = _demo_state()
        self._hover_key = ""
        self._selected_key = ""
        self._zoom_key = ""
        self._zoom_amount = 0.0
        self._tick = 0
        self._stars = [
            (random.uniform(0, 1), random.uniform(0, 0.45), random.uniform(0.3, 1.0))
            for _ in range(80)
        ]
        self._smoke = [
            (random.uniform(0.62, 0.88), random.uniform(0.18, 0.42), random.random())
            for _ in range(18)
        ]
        self._sparks = [
            (random.uniform(0.08, 0.28), random.uniform(0.42, 0.62), random.random())
            for _ in range(6)
        ]
        self._drones = [
            (random.random(), i) for i in range(3)
        ]

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(40)

    def set_state(self, state: BaseState):
        self._state = state
        self.update()

    def _animate(self):
        self._tick += 1
        if self._zoom_amount > 0:
            self._zoom_amount = max(0.0, self._zoom_amount - 0.035)
        for i, (x, y, phase) in enumerate(self._smoke):
            self._smoke[i] = (x, y - 0.002, (phase + 0.025) % 1.0)
        for i, (pos, lane) in enumerate(self._drones):
            self._drones[i] = ((pos + 0.004) % 1.0, lane)
        self.update()

    def _zone_rects(self) -> dict[str, QRectF]:
        w, h = self.width(), self.height()
        return {
            "operations": QRectF(w * 0.34, h * 0.02, w * 0.32, h * 0.20),
            "hangar": QRectF(w * 0.02, h * 0.22, w * 0.30, h * 0.34),
            "storage": QRectF(w * 0.26, h * 0.38, w * 0.44, h * 0.32),
            "refinery": QRectF(w * 0.66, h * 0.18, w * 0.32, h * 0.38),
            "trade": QRectF(w * 0.52, h * 0.72, w * 0.30, h * 0.22),
        }

    def _hit_zone(self, pos) -> str:
        for key, rect in self._zone_rects().items():
            if rect.contains(pos):
                return key
        return ""

    def mouseMoveEvent(self, event):
        key = self._hit_zone(event.position())
        if key != self._hover_key:
            self._hover_key = key
            self.zone_hovered.emit(key)
            self.update()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            key = self._hit_zone(event.position())
            if key:
                self._selected_key = key
                self._zoom_key = key
                self._zoom_amount = 1.0
                self.zone_clicked.emit(key)
                self.update()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        key = self._hit_zone(event.position())
        if not key:
            return
        titles = {k: t for k, _i, t in self.ZONES}
        QMessageBox.information(
            self,
            "Detailansicht (Vorschau)",
            f"{titles.get(key, key)}\n\n"
            "In Version 0.15+ öffnet ein Doppelklick die "
            "passende Tracker-Seite.\n\n"
            "Diese Vorschau ändert die Produktions-App nicht.",
        )

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        self._draw_sky(painter, w, h)
        self._draw_asteroid_cavern(painter, w, h)
        self._draw_corridors(painter, w, h)
        self._draw_ambient_lights(painter, w, h)
        self._draw_drones(painter, w, h)

        rects = self._zone_rects()
        labels = {k: (i, t) for k, i, t in self.ZONES}
        draw_order = ("storage", "trade", "hangar", "refinery", "operations")

        for key in draw_order:
            rect = rects[key]
            index, title = labels[key]
            hover = key == self._hover_key
            selected = key == self._selected_key
            zoom = 1.05 if key == self._zoom_key and self._zoom_amount > 0 else 1.0
            self._draw_zone(painter, key, rect, index, title, hover, selected, zoom)

        painter.setPen(QColor(70, 80, 90, 140))
        painter.setFont(QFont("Rajdhani", 8))
        painter.drawText(
            10, h - 8,
            "Vorschau · Art Direction · Ziel-Engine: OpenGL 0.15",
        )
        painter.end()

    def _draw_sky(self, painter: QPainter, w: float, h: float):
        grad = QLinearGradient(0, 0, 0, h * 0.5)
        grad.setColorAt(0.0, QColor(4, 6, 14))
        grad.setColorAt(1.0, QColor(10, 12, 18))
        painter.fillRect(QRectF(0, 0, w, h * 0.5), grad)

        for sx, sy, br in self._stars:
            twinkle = 0.6 + 0.4 * abs((self._tick * 0.05 + sx * 10) % 1 - 0.5)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(
                QColor(200, 210, 230, int(180 * br * twinkle))
            )
            painter.drawEllipse(QPointF(sx * w, sy * h), 1.2, 1.2)

    def _draw_asteroid_cavern(self, painter: QPainter, w: float, h: float):
        floor = QPainterPath()
        floor.moveTo(0, h * 0.48)
        floor.cubicTo(w * 0.1, h * 0.38, w * 0.35, h * 0.32, w * 0.55, h * 0.36)
        floor.cubicTo(w * 0.75, h * 0.40, w * 0.92, h * 0.52, w, h * 0.58)
        floor.lineTo(w, h)
        floor.lineTo(0, h)
        floor.closeSubpath()

        rock = QLinearGradient(0, h * 0.3, 0, h)
        rock.setColorAt(0.0, QColor(38, 34, 30))
        rock.setColorAt(0.45, QColor(28, 26, 24))
        rock.setColorAt(1.0, QColor(14, 14, 16))
        painter.fillPath(floor, QBrush(rock))

        ceiling = QPainterPath()
        ceiling.moveTo(0, h * 0.12)
        ceiling.cubicTo(w * 0.2, h * 0.02, w * 0.55, 0, w * 0.85, h * 0.06)
        ceiling.lineTo(w, h * 0.22)
        ceiling.lineTo(0, h * 0.28)
        ceiling.closeSubpath()
        painter.fillPath(ceiling, QColor(18, 16, 14, 200))

        vignette = QRadialGradient(w * 0.5, h * 0.55, w * 0.65)
        vignette.setColorAt(0.0, QColor(0, 0, 0, 0))
        vignette.setColorAt(1.0, QColor(0, 0, 0, 180))
        painter.fillRect(self.rect(), QBrush(vignette))

    def _draw_corridors(self, painter: QPainter, w: float, h: float):
        painter.setPen(QPen(QColor(48, 52, 58, 100), 3))
        painter.drawLine(int(w * 0.32), int(h * 0.52), int(w * 0.38), int(h * 0.38))
        painter.drawLine(int(w * 0.58), int(h * 0.52), int(w * 0.68), int(h * 0.42))
        painter.setPen(QPen(QColor(232, 160, 74, 60), 1))
        for t in range(5):
            flicker = (self._tick // 18 + t) % 3 != 0
            if flicker:
                painter.drawLine(
                    int(w * (0.34 + t * 0.05)), int(h * 0.50),
                    int(w * (0.36 + t * 0.05)), int(h * 0.42),
                )

    def _draw_ambient_lights(self, painter: QPainter, w: float, h: float):
        for cx, cy, color, radius in (
            (0.18, 0.48, QColor(240, 160, 70, 45), 0.28),
            (0.78, 0.40, QColor(255, 120, 50, 50), 0.26),
            (0.50, 0.22, QColor(80, 180, 200, 30), 0.22),
            (0.62, 0.78, QColor(70, 160, 190, 35), 0.18),
        ):
            grad = QRadialGradient(w * cx, h * cy, w * radius)
            grad.setColorAt(0.0, color)
            grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.fillRect(self.rect(), QBrush(grad))

    def _draw_drones(self, painter: QPainter, w: float, h: float):
        lanes = (
            (0.12, 0.28, 0.48, 0.22),
            (0.55, 0.15, 0.72, 0.35),
            (0.40, 0.55, 0.58, 0.72),
        )
        painter.setBrush(QColor(94, 196, 216, 180))
        painter.setPen(Qt.PenStyle.NoPen)
        for progress, lane_id in self._drones:
            x1, y1, x2, y2 = lanes[lane_id % len(lanes)]
            px = x1 + (x2 - x1) * progress
            py = y1 + (y2 - y1) * progress
            painter.drawEllipse(QPointF(px * w, py * h), 3, 3)

    def _draw_iso_deck(
        self,
        painter: QPainter,
        rect: QRectF,
        *,
        hover: bool,
        selected: bool,
        depth: float = 14,
    ):
        cx, cy = rect.center().x(), rect.bottom() - depth * 0.5
        hw = rect.width() * 0.46
        hh = rect.height() * 0.22
        skew = hh * 0.85

        top = QPolygonF([
            QPointF(cx - hw, cy - skew * 0.3),
            QPointF(cx, cy - skew - hh * 0.2),
            QPointF(cx + hw, cy - skew * 0.3),
            QPointF(cx, cy + hh * 0.15),
        ])

        left = QPolygonF([
            top[3], top[0],
            QPointF(top[0].x(), top[0].y() + depth),
            QPointF(top[3].x(), top[3].y() + depth),
        ])
        right = QPolygonF([
            top[3], top[2],
            QPointF(top[2].x(), top[2].y() + depth),
            QPointF(top[3].x(), top[3].y() + depth),
        ])

        top_c = QColor(46, 52, 62)
        if hover:
            top_c = QColor(56, 66, 78)
        if selected:
            top_c = QColor(62, 72, 86)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(28, 32, 38))
        painter.drawPolygon(left)
        painter.setBrush(QColor(34, 38, 46))
        painter.drawPolygon(right)
        painter.setBrush(top_c)
        painter.drawPolygon(top)

        border_c = QColor(94, 196, 216, 220 if hover else 70)
        if selected:
            border_c = QColor(240, 168, 74, 240)
        painter.setPen(QPen(border_c, 2 if hover or selected else 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPolygon(top)

        return top.boundingRect()

    def _draw_zone(
        self,
        painter: QPainter,
        key: str,
        rect: QRectF,
        index: int,
        title: str,
        hover: bool,
        selected: bool,
        zoom: float,
    ):
        cx, cy = rect.center().x(), rect.center().y()
        scaled = QRectF(
            cx - rect.width() * zoom * 0.5,
            cy - rect.height() * zoom * 0.5,
            rect.width() * zoom,
            rect.height() * zoom,
        )

        deck = self._draw_iso_deck(
            painter, scaled, hover=hover, selected=selected
        )

        if key == "operations":
            self._draw_operations(painter, scaled, deck)
        elif key == "hangar":
            self._draw_hangar(painter, scaled, deck)
        elif key == "storage":
            self._draw_storage(painter, scaled, deck)
        elif key == "refinery":
            self._draw_refinery(painter, scaled, deck)
        elif key == "trade":
            self._draw_trade(painter, scaled, deck)

        badge = QRectF(scaled.left() + 10, scaled.top() + 6, 24, 24)
        painter.setBrush(QColor(232, 152, 58))
        painter.setPen(QPen(QColor(20, 16, 12), 1))
        painter.drawEllipse(badge)
        painter.setPen(QColor(16, 14, 12))
        painter.setFont(QFont("Orbitron", 11, QFont.Weight.Bold))
        painter.drawText(badge, Qt.AlignmentFlag.AlignCenter, str(index))

        painter.setPen(QColor(230, 234, 240))
        painter.setFont(QFont("Orbitron", 7, QFont.Weight.Bold))
        painter.drawText(
            QRectF(scaled.left() + 38, scaled.top() + 8, scaled.width() - 46, 20),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            title,
        )

    def _draw_operations(self, painter: QPainter, rect: QRectF, deck: QRectF):
        cx = deck.center().x()
        cy = deck.top() + deck.height() * 0.35

        for r, alpha in ((38, 40), (32, 70), (26, 110)):
            painter.setPen(QPen(QColor(94, 196, 216, alpha), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), r, r * 0.35)

        dome = QPainterPath()
        dome.addEllipse(QPointF(cx, cy), 28, 18)
        dome_grad = QRadialGradient(cx, cy, 30)
        dome_grad.setColorAt(0.0, QColor(80, 180, 200, 120))
        dome_grad.setColorAt(1.0, QColor(30, 40, 52, 200))
        painter.fillPath(dome, QBrush(dome_grad))
        painter.setPen(QPen(QColor(94, 196, 216, 160), 1))
        painter.drawPath(dome)

        blink = (self._tick // 22) % 2 == 0
        painter.setBrush(QColor(240, 180, 80, 200 if blink else 80))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy - 22), 4, 4)

    def _draw_hangar(self, painter: QPainter, rect: QRectF, deck: QRectF):
        pad = QRectF(
            deck.left() + deck.width() * 0.08,
            deck.center().y() - 8,
            deck.width() * 0.84,
            deck.height() * 0.55,
        )
        painter.fillRect(pad, QColor(36, 40, 48))
        for i in range(6):
            on = (self._tick // 12 + i) % 2 == 0
            painter.setBrush(QColor(240, 160, 60, 200 if on else 60))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                QPointF(pad.left() + 12 + i * (pad.width() - 24) / 5, pad.bottom() - 4),
                3, 3,
            )

        vulture_out = self._state.session_active
        _draw_ship_reclaimer(
            painter,
            pad.center().x(),
            pad.center().y() - 6,
            min(pad.width(), pad.height()) / 120,
            lit=not vulture_out,
        )
        if vulture_out:
            _draw_ship_vulture(
                painter,
                pad.right() + 20,
                pad.top() + 10,
                0.55,
                lit=True,
                alpha=140,
            )
            painter.setFont(QFont("Rajdhani", 7))
            painter.setPen(QColor(240, 180, 90, 180))
            painter.drawText(
                int(pad.right() + 4), int(pad.top() + 4),
                "Vulture → Einsatz",
            )

        for sx, sy, phase in self._sparks:
            if phase > 0.5:
                continue
            px = pad.left() + sx * pad.width()
            py = pad.top() + sy * pad.height()
            painter.setPen(QPen(QColor(255, 220, 120, 200), 1))
            painter.drawLine(int(px), int(py), int(px + 4), int(py - 6))

    def _draw_storage(self, painter: QPainter, rect: QRectF, deck: QRectF):
        yard = QRectF(
            deck.left() + deck.width() * 0.06,
            deck.top() + deck.height() * 0.15,
            deck.width() * 0.88,
            deck.height() * 0.75,
        )
        painter.fillRect(yard, QColor(32, 36, 42, 180))

        materials = self._state.materials
        total = max(1, sum(materials.values()))
        box_w = min(20, yard.width() / 10)
        box_h = box_w * 1.15
        col = 0
        row = 0
        max_cols = 8

        for name, qty in materials.items():
            color = MATERIAL_COLORS.get(name, QColor(100, 100, 100))
            count = max(1, int((qty / total) * self._state.storage_fill * 24))
            for _ in range(count):
                x = yard.left() + 8 + col * (box_w + 3)
                y = yard.bottom() - 8 - row * (box_h + 2)
                shade = 100 + (col + row) % 3 * 8
                painter.fillRect(QRectF(x, y - box_h, box_w, box_h), color.darker(shade))
                painter.setPen(QPen(color.lighter(120), 1))
                painter.drawRect(QRectF(x, y - box_h, box_w, box_h))
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

        belt_y = yard.bottom() - 2
        offset = (self._tick * 2) % 20
        painter.setPen(QPen(QColor(60, 64, 70), 2))
        painter.drawLine(int(yard.left()), int(belt_y), int(yard.right()), int(belt_y))
        for bx in range(int(yard.left()) - 20, int(yard.right()) + 20, 20):
            painter.fillRect(
                QRectF(bx + offset, belt_y - 2, 8, 4),
                QColor(80, 84, 90),
            )

    def _draw_refinery(self, painter: QPainter, rect: QRectF, deck: QRectF):
        cx = deck.center().x()
        base_y = deck.center().y() + 10

        for i, ox in enumerate((-48, -20, 8, 36)):
            stack_h = 40 + i * 8
            stack = QRectF(cx + ox - 10, base_y - stack_h, 20, stack_h)
            grad = QLinearGradient(stack.topLeft(), stack.bottomLeft())
            grad.setColorAt(0, QColor(70, 68, 64))
            grad.setColorAt(1, QColor(42, 40, 38))
            painter.fillRect(stack, grad)
            painter.setPen(QPen(QColor(90, 88, 84), 1))
            painter.drawRect(stack)

        status = self._state.refinery_status
        active = status in ("processing", "complete")

        if active:
            molten = QRectF(cx - 8, base_y - 18, 16, 10)
            pulse = 0.5 + 0.5 * ((self._tick % 30) / 30)
            painter.setBrush(QColor(255, 100, 30, int(160 + 80 * pulse)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(molten.center(), 12, 6)

            for x, y, phase in self._smoke:
                px = deck.left() + x * deck.width()
                py = deck.top() + y * deck.height()
                alpha = int(100 * (1 - phase))
                painter.setBrush(QColor(160, 160, 170, alpha))
                painter.drawEllipse(QPointF(px, py), 8 + phase * 14, 8 + phase * 10)

            blink = (self._tick // 10) % 2 == 0
            for lx in (deck.left() + 20, deck.right() - 28):
                painter.setBrush(
                    QColor(255, 60, 30, 220 if blink else 80)
                )
                painter.drawEllipse(QPointF(lx, deck.top() + 18), 5, 5)
        else:
            painter.setFont(QFont("Rajdhani", 9))
            painter.setPen(QColor(100, 108, 118))
            painter.drawText(deck, Qt.AlignmentFlag.AlignCenter, "IDLE")

    def _draw_trade(self, painter: QPainter, rect: QRectF, deck: QRectF):
        pad = QRectF(
            deck.left() + deck.width() * 0.12,
            deck.center().y() - 4,
            deck.width() * 0.76,
            deck.height() * 0.55,
        )
        painter.fillRect(pad, QColor(34, 40, 50))
        painter.setPen(QPen(QColor(94, 196, 216, 100), 1))
        painter.drawRect(pad)

        _draw_ship_vulture(
            painter,
            pad.center().x(),
            pad.center().y() - 4,
            min(pad.width(), 70) / 70,
            lit=True,
        )

        painter.setFont(QFont("Rajdhani", 8))
        painter.setPen(QColor(150, 190, 210))
        painter.drawText(
            QRectF(pad.left(), pad.bottom() - 14, pad.width(), 12),
            Qt.AlignmentFlag.AlignCenter,
            "TRADE DOCK",
        )


class OperationsBasePreviewWindow(QWidget):
    ZONE_DETAILS = {
        "operations": ("Operations Center", "Finanzen · Statistik · Status"),
        "hangar": ("Hangar Deck", "Vulture · Reclaimer · Flottenstatus"),
        "storage": ("Storage Deck", "Container · Materialbestände"),
        "refinery": ("Refinery Complex", "Verarbeitung · Ausgabe CM"),
        "trade": ("Trade Terminal", "Verkauf · Umsatz · Gewinn"),
    }

    def __init__(self, *, live: bool = False):
        super().__init__()
        self._state = _live_state() if live else _demo_state()
        self._live = live

        self.setObjectName("opsBaseRoot")
        self.setWindowTitle(
            "SC Salvage Tracker — Operations Base Alpha (Vorschau v2)"
        )
        self.resize(1440, 900)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 10)
        root.setSpacing(10)

        root.addLayout(self._build_top_bar())
        root.addLayout(self._build_main_row(), stretch=1)
        root.addLayout(self._build_bottom_row())

        banner = QLabel(
            "VORSCHAU v2 · Salvage Operations Base Alpha · "
            + ("Live-Daten" if live else "Demo-Daten")
            + " · Keine Produktionsänderung · "
            "Hover / Klick / Doppelklick auf Bereiche [1]–[5]"
        )
        banner.setObjectName("opsPreviewBanner")
        banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(banner)

        self._scene.zone_clicked.connect(self._on_zone_clicked)
        self._scene.zone_hovered.connect(self._on_zone_hovered)
        self._apply_state_to_panels()

    def _build_top_bar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        col = QVBoxLayout()
        col.setSpacing(2)
        title = QLabel("SALVAGE OPERATIONS BASE ALPHA")
        title.setObjectName("opsBaseTitle")
        sub = QLabel("BASISSTUFE 1 · ASTEROIDEN-HANGAR · INDUSTRIAL SALVAGE CORP")
        sub.setObjectName("opsBaseSubtitle")
        col.addWidget(title)
        col.addWidget(sub)
        row.addLayout(col)
        row.addStretch()
        meta = QLabel(
            f"{datetime.now():%H:%M}  ·  {datetime.now():%d.%m.%Y}  ·  "
            "v0.15 PREVIEW\nNOVA SALVAGE CORP · Rang: Operator · Rep: 847"
        )
        meta.setObjectName("opsBaseMeta")
        meta.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(meta)
        return row

    def _panel(self, title: str, *, warm: bool = False) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("opsPanelAccent" if warm else "opsPanel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        heading = QLabel(title)
        heading.setObjectName("opsPanelTitleWarm" if warm else "opsPanelTitle")
        layout.addWidget(heading)
        return frame, layout

    def _status_row(self, label: str, value: float) -> QWidget:
        row = QWidget()
        lay = QVBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        lay.addWidget(self._label(label, "opsPanelLabel"))
        bar_bg = QFrame()
        bar_bg.setObjectName("opsStatusBar")
        bar_lay = QHBoxLayout(bar_bg)
        bar_lay.setContentsMargins(0, 0, 0, 0)
        fill = QFrame()
        fill.setObjectName("opsStatusBarFill")
        fill.setFixedWidth(int(100 * value))
        bar_lay.addWidget(fill)
        bar_lay.addStretch()
        lay.addWidget(bar_bg)
        return row

    def _mat_bar(self, label: str, ratio: float, color: str) -> QWidget:
        row = QWidget()
        lay = QVBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        lay.addWidget(self._label(f"{label}  {ratio * 100:.0f} %", "opsPanelLabel"))
        bar_bg = QFrame()
        bar_bg.setObjectName("opsMatBar")
        bar_lay = QHBoxLayout(bar_bg)
        bar_lay.setContentsMargins(0, 0, 0, 0)
        fill = QFrame()
        fill.setObjectName("opsMatBarFill")
        fill.setFixedWidth(max(4, int(90 * ratio)))
        fill.setStyleSheet(f"background-color: {color};")
        bar_lay.addWidget(fill)
        bar_lay.addStretch()
        lay.addWidget(bar_bg)
        return row

    @staticmethod
    def _label(text: str, obj: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName(obj)
        return lbl

    def _build_main_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)

        left = QVBoxLayout()
        sys_p, sys_l = self._panel("SYSTEM STATUS")
        for name, val in (
            ("Power", 1.0), ("Life Support", 1.0), ("Security", 0.98),
            ("Comms", 1.0), ("Docking", 0.95),
        ):
            sys_l.addWidget(self._status_row(name, val))
        sys_l.addStretch()
        left.addWidget(sys_p)

        ev_p, ev_l = self._panel("NÄCHSTE EREIGNISSE")
        self._event_labels = []
        for _ in range(4):
            lbl = self._label("—", "opsEventRow")
            lbl.setWordWrap(True)
            ev_l.addWidget(lbl)
            self._event_labels.append(lbl)
        ev_l.addStretch()
        left.addWidget(ev_p)
        row.addLayout(left, stretch=2)

        center = QVBoxLayout()
        frame = QFrame()
        frame.setObjectName("opsSceneFrame")
        frame_l = QVBoxLayout(frame)
        frame_l.setContentsMargins(4, 4, 4, 4)
        self._scene = BaseSceneWidget()
        self._scene.set_state(self._state)
        frame_l.addWidget(self._scene)
        center.addWidget(frame, stretch=1)

        hint_row = QHBoxLayout()
        self._zone_hint = self._label(
            "Hover · Klick · Doppelklick auf Bereiche [1]–[5]",
            "opsZoneHint",
        )
        hint_row.addWidget(self._zone_hint, stretch=1)
        reset = QPushButton("Kamera zurücksetzen")
        reset.setObjectName("opsSceneButton")
        reset.clicked.connect(self._reset_scene)
        hint_row.addWidget(reset)
        center.addLayout(hint_row)
        row.addLayout(center, stretch=8)

        fin_p, fin_l = self._panel("FINANZÜBERSICHT", warm=True)
        self._lbl_credits = self._label("", "opsPanelValueAccent")
        self._lbl_profit = self._label("", "opsPanelValue")
        self._lbl_costs = self._label("", "opsPanelRow")
        self._lbl_net = self._label("", "opsPanelValue")
        fin_l.addWidget(self._label("Aktuelle Credits", "opsPanelLabel"))
        fin_l.addWidget(self._lbl_credits)
        fin_l.addWidget(self._label("Gesamtgewinn", "opsPanelLabel"))
        fin_l.addWidget(self._lbl_profit)
        fin_l.addWidget(self._lbl_costs)
        fin_l.addWidget(self._label("Nettogewinn", "opsPanelLabel"))
        fin_l.addWidget(self._lbl_net)
        fin_l.addStretch()
        row.addWidget(fin_p, stretch=2)

        return row

    def _build_bottom_row(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setSpacing(10)

        p1, l1 = self._panel("LAGERBESTAND")
        self._storage_summary = self._label("", "opsPanelRow")
        self._storage_summary.setWordWrap(True)
        l1.addWidget(self._storage_summary)
        self._mat_bars_host = QVBoxLayout()
        l1.addLayout(self._mat_bars_host)
        l1.addStretch()

        p2, l2 = self._panel("AKTIVE JOBS")
        self._lbl_jobs = self._label("", "opsPanelRow")
        self._lbl_jobs.setWordWrap(True)
        l2.addWidget(self._lbl_jobs)
        self._job_bar_bg = QFrame()
        self._job_bar_bg.setObjectName("opsJobProgress")
        job_lay = QHBoxLayout(self._job_bar_bg)
        job_lay.setContentsMargins(0, 0, 0, 0)
        self._job_bar_fill = QFrame()
        self._job_bar_fill.setObjectName("opsJobProgressFill")
        job_lay.addWidget(self._job_bar_fill)
        job_lay.addStretch()
        l2.addWidget(self._job_bar_bg)
        l2.addStretch()

        p3, l3 = self._panel("AKTIVE SESSION")
        self._lbl_session = self._label("", "opsPanelRow")
        self._lbl_session.setWordWrap(True)
        l3.addWidget(self._lbl_session)
        l3.addStretch()

        p4, l4 = self._panel("KOMMUNIKATIONEN")
        self._lbl_comms = self._label("", "opsPanelRow")
        self._lbl_comms.setWordWrap(True)
        l4.addWidget(self._lbl_comms)
        l4.addStretch()

        grid.addWidget(p1, 0, 0)
        grid.addWidget(p2, 0, 1)
        grid.addWidget(p3, 0, 2)
        grid.addWidget(p4, 0, 3)
        return grid

    def _apply_state_to_panels(self):
        s = self._state
        self._lbl_credits.setText(f"{s.credits:,.0f} aUEC")
        self._lbl_profit.setText(f"{s.total_profit:,.0f} aUEC")
        self._lbl_costs.setText(f"Kosten: {s.costs:,.0f} aUEC")
        self._lbl_net.setText(f"{s.net_profit:,.0f} aUEC")

        total_mat = max(1, sum(s.materials.values()))
        while self._mat_bars_host.count():
            item = self._mat_bars_host.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        bar_colors = {
            "RMC": "#d4aa38",
            "CM": "#3478b2",
            "CM Salvage": "#b26c34",
            "CM Rubble": "#787674",
            "CM Scraps": "#9e623e",
        }
        for name, qty in s.materials.items():
            self._mat_bars_host.addWidget(
                self._mat_bar(name, qty / total_mat, bar_colors.get(name, "#888"))
            )

        self._storage_summary.setText(
            f"Gesamt: {s.storage_scu:,} / {s.storage_capacity:,} SCU "
            f"({s.storage_fill * 100:.0f} % Auslastung)"
        )

        if s.refinery_status == "idle":
            self._lbl_jobs.setText("Kein aktiver Job · Raffinerie im Leerlauf")
            self._job_bar_fill.setFixedWidth(0)
        else:
            self._lbl_jobs.setText(
                f"#{s.refinery_job_id} · {s.refinery_input} → {s.refinery_output}\n"
                f"Status: {s.refinery_status.upper()}"
            )
            self._job_bar_fill.setFixedWidth(
                max(8, int(180 * s.refinery_progress))
            )

        if s.session_active:
            self._lbl_session.setText(
                f"◉ {s.session_ship}\n{s.session_location}\n"
                f"Dauer: {s.session_hours:.1f} h · "
                f"Est.: {s.session_profit_est:,} aUEC\n"
                f"Vulture: {s.hangar_vulture} · "
                f"Reclaimer: {s.hangar_reclaimer}"
            )
        else:
            self._lbl_session.setText(
                f"Keine aktive Session\n"
                f"Vulture: {s.hangar_vulture} · "
                f"Reclaimer: {s.hangar_reclaimer}"
            )

        self._lbl_comms.setText("\n".join(s.comms))
        for lbl, text in zip(self._event_labels, s.events):
            lbl.setText(f"▸ {text}")

    def _on_zone_clicked(self, key: str):
        if key in self.ZONE_DETAILS:
            title, detail = self.ZONE_DETAILS[key]
            self._zone_hint.setText(f"[{key.upper()}] {title} — {detail}")

    def _on_zone_hovered(self, key: str):
        if not key:
            self._zone_hint.setText(
                "Hover · Klick · Doppelklick auf Bereiche [1]–[5]"
            )
        elif key in self.ZONE_DETAILS:
            self._zone_hint.setText(f"→ {self.ZONE_DETAILS[key][0]}")

    def _reset_scene(self):
        self._scene._selected_key = ""
        self._scene._zoom_key = ""
        self._scene._zoom_amount = 0.0
        self._scene.update()
        self._zone_hint.setText(
            "Hover · Klick · Doppelklick auf Bereiche [1]–[5]"
        )


def load_preview_fonts() -> None:
    for font_file in (
        "assets/fonts/Orbitron-Bold.ttf",
        "assets/fonts/Rajdhani-Regular.ttf",
        "assets/fonts/Rajdhani-Bold.ttf",
    ):
        path = asset_path(font_file)
        if path.exists():
            QFontDatabase.addApplicationFont(str(path))


def load_preview_theme(app: QApplication) -> None:
    qss_path = asset_path("ui/themes/operations_base_preview.qss")
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))


def run_operations_base_preview(*, live: bool = False) -> int:
    app = QApplication([])
    load_preview_fonts()
    load_preview_theme(app)
    app.setFont(QFont("Rajdhani", 11))

    window = OperationsBasePreviewWindow(live=live)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run_operations_base_preview())
