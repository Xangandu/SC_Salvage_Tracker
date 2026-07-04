from __future__ import annotations

import math
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, Signal, QRectF
from PySide6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config.dates import format_datetime, parse_datetime
from config.i18n import tr, format_number
from config.materials import material_label
from config.refinery_methods import display_refinery_method
from ui.page_layout import primary_button, svg_icon_widget


def _parse_db_datetime(value):
    if not value:
        return datetime.now()

    try:
        return parse_datetime(value)
    except ValueError:
        return datetime.now()


def _format_countdown(total_seconds: int) -> str:
    total_seconds = max(0, int(total_seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def refinery_job_progress_state(job: dict) -> dict:
    ready_time = _parse_db_datetime(job.get("end_time"))
    start_time = _parse_db_datetime(job.get("start_time"))
    now = datetime.now()

    remaining_seconds = int((ready_time - now).total_seconds())
    total_seconds = max(1, int((ready_time - start_time).total_seconds()))
    elapsed_seconds = max(0, total_seconds - max(0, remaining_seconds))
    progress = min(100.0, elapsed_seconds / total_seconds * 100.0)

    job_status = job.get("status", "RUNNING")
    is_ready = job_status == "READY" or remaining_seconds <= 0
    if is_ready:
        progress = 100.0

    return {
        "progress": progress,
        "remaining_seconds": max(0, remaining_seconds),
        "is_ready": is_ready,
        "ready_time": ready_time,
    }


class RefineryJobProgressBar(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0.0
        self._pulse = 0.0
        self.setFixedHeight(12)
        self.setObjectName("refineryJobProgress")

        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(33)
        self._anim_timer.timeout.connect(self._tick_animation)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._anim_timer.isActive():
            self._anim_timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._anim_timer.stop()

    def set_progress(self, value: float) -> None:
        self._progress = max(0.0, min(100.0, float(value)))
        self.update()

    def _tick_animation(self):
        self._pulse = (self._pulse + 0.04) % (2 * math.pi)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        track = QRectF(0.5, 0.5, width - 1, height - 1)
        radius = max(3.0, height * 0.35)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(14, 20, 28))
        painter.drawRoundedRect(track, radius, radius)

        painter.setPen(QPen(QColor(38, 53, 69), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(track, radius, radius)

        inner = track.adjusted(1.5, 1.5, -1.5, -1.5)
        fill_w = inner.width() * self._progress / 100.0
        if fill_w > 1.0:
            fill_rect = QRectF(inner.x(), inner.y(), fill_w, inner.height())
            gradient = QLinearGradient(fill_rect.left(), 0, fill_rect.right(), 0)
            gradient.setColorAt(0.0, QColor(160, 90, 24))
            gradient.setColorAt(0.55, QColor(224, 122, 42))
            gradient.setColorAt(1.0, QColor(255, 168, 72))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(fill_rect, radius - 1, radius - 1)

            edge_x = fill_rect.right()
            glow = QLinearGradient(edge_x - 8, 0, edge_x + 4, 0)
            alpha = int(90 + 50 * math.sin(self._pulse))
            glow.setColorAt(0.0, QColor(66, 212, 245, 0))
            glow.setColorAt(1.0, QColor(66, 212, 245, alpha))
            painter.fillRect(
                QRectF(edge_x - 8, inner.y(), 12, inner.height()),
                glow,
            )

        painter.end()


def _secondary_button(text):
    button = QPushButton(text)
    button.setObjectName("secondaryAction")
    return button


def _detail_label(text):
    label = QLabel(text)
    label.setObjectName("cardDetailLabel")
    return label


class RefineryJobCard(QFrame):

    complete_requested = Signal(int)
    cancel_requested = Signal(int)

    def __init__(self, job: dict, parent=None):
        super().__init__(parent)

        self._job = dict(job)
        self._job_id = job["id"]
        self._collect_button = None
        self._card_ready_style = None

        self.setObjectName("jobCard")

        self._status_label = QLabel()
        self._status_label.setObjectName("jobStatusLabel")
        self._countdown_value = QLabel("00:00:00")
        self._countdown_value.setObjectName("refineryCountdownValue")
        self._ready_at_label = QLabel()
        self._ready_at_label.setObjectName("cardDetailLabel")
        self._remaining_label = QLabel()
        self._remaining_label.setObjectName("cardDetailLabel")
        self._progress_label = QLabel()
        self._progress_label.setObjectName("cardDetailLabel")
        self._progress_bar = RefineryJobProgressBar(self)

        self._details_layout = QVBoxLayout()
        self._details_layout.setContentsMargins(0, 0, 0, 0)
        self._details_layout.setSpacing(2)

        self._actions_layout = QVBoxLayout()
        self._actions_layout.setContentsMargins(0, 0, 0, 0)
        self._actions_layout.setSpacing(8)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        header_layout = QHBoxLayout()
        self._icon_widget = svg_icon_widget(
            "assets/images/icons/processing.svg",
            size=36,
            object_name="jobStatusIcon",
        )
        header_layout.addWidget(self._icon_widget)
        header_layout.addWidget(self._status_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        layout.addWidget(self._countdown_value)
        layout.addWidget(self._ready_at_label)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._progress_label)
        layout.addWidget(self._remaining_label)
        layout.addLayout(self._details_layout)
        layout.addLayout(self._actions_layout)

        cancel_button = _secondary_button(tr("refinery.button.cancel"))
        cancel_button.clicked.connect(
            lambda checked=False, jid=self._job_id:
            self.cancel_requested.emit(jid)
        )
        self._actions_layout.addWidget(cancel_button)

        self._rebuild_static_details()
        self.tick()

    def job_id(self) -> int:
        return self._job_id

    def set_job(self, job: dict) -> None:
        self._job = dict(job)
        self._rebuild_static_details()
        self.tick()

    def _rebuild_static_details(self):
        while self._details_layout.count():
            item = self._details_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        job = self._job
        job_id = job["id"]

        self._details_layout.addWidget(_detail_label(
            tr(
                "refinery.job.detail",
                job_id=job_id,
                name=job["refinery_name"],
            )
        ))

        method = display_refinery_method(
            (job.get("refinery_method") or "").strip()
        )
        if method:
            self._details_layout.addWidget(_detail_label(
                tr("refinery.job.method", method=method)
            ))

        cost = job.get("cost", 0) or 0
        payer = (job.get("cost_paid_by") or "").strip()
        if cost > 0 and payer:
            cost_line = tr(
                "refinery.job.cost_paid",
                cost=format_number(cost),
                payer=payer,
            )
        else:
            cost_line = tr(
                "refinery.job.cost",
                cost=format_number(cost),
            )
        self._details_layout.addWidget(_detail_label(cost_line))
        self._details_layout.addWidget(_detail_label(
            tr("refinery.job.created_by", name=job["created_by"])
        ))

        for item in job.get("items", []):
            self._details_layout.addWidget(_detail_label(
                tr(
                    "refinery.job.batch_line",
                    batch_id=item["batch_id"],
                    material=material_label(item["input_material"]),
                    quantity=format_number(item["input_quantity"], 0),
                )
            ))

    def _ensure_collect_button(self):
        if self._collect_button is not None:
            return

        self._collect_button = primary_button(
            tr("refinery.button.complete")
        )
        self._collect_button.clicked.connect(
            lambda checked=False, jid=self._job_id:
            self.complete_requested.emit(jid)
        )
        self._actions_layout.addWidget(self._collect_button)

    def _remove_collect_button(self):
        if self._collect_button is None:
            return

        self._actions_layout.removeWidget(self._collect_button)
        self._collect_button.deleteLater()
        self._collect_button = None

    def tick(self):
        job = self._job
        state = refinery_job_progress_state(job)
        progress = state["progress"]
        remaining_seconds = state["remaining_seconds"]
        is_ready = state["is_ready"]
        ready_time = state["ready_time"]

        if is_ready:
            self.setObjectName("jobCardReady")
            self._status_label.setObjectName("jobStatusLabelReady")
            self._status_label.setText(
                tr("refinery.status.ready_for_pickup")
            )
            self._countdown_value.setText("00:00:00")
            self._remaining_label.setText(
                tr(
                    "refinery.job.remaining",
                    remaining=tr("refinery.status.finished"),
                )
            )
            self._ensure_collect_button()
        else:
            self.setObjectName("jobCard")
            self._status_label.setObjectName("jobStatusLabel")
            if remaining_seconds <= 3600:
                self._status_label.setText(
                    tr("refinery.status.final_phase")
                )
            else:
                self._status_label.setText(
                    tr("refinery.status.in_progress")
                )
            self._countdown_value.setText(
                _format_countdown(remaining_seconds)
            )
            self._remaining_label.setText(
                tr(
                    "refinery.job.countdown",
                    countdown=_format_countdown(remaining_seconds),
                )
            )
            self._remove_collect_button()

        self._ready_at_label.setText(
            tr(
                "refinery.job.ready_at",
                time=format_datetime(ready_time),
            )
        )
        self._progress_label.setText(
            tr(
                "refinery.job.progress",
                percent=format_number(progress, 0),
            )
        )
        self._progress_bar.set_progress(progress)
        if self._card_ready_style != is_ready:
            self._card_ready_style = is_ready
            self.style().unpolish(self)
            self.style().polish(self)
