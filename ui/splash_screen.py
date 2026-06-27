from pathlib import Path
import math
import random

from PySide6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    Signal,
    QEventLoop,
    QRect,
    QRectF,
    QElapsedTimer,
)
from PySide6.QtGui import (
    QPixmap,
    QPainter,
    QColor,
    QLinearGradient,
    QPen,
    QFont,
    QPainterPath,
    QBrush,
)
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QFrame,
    QApplication,
)

from config.paths import asset_path
from config.i18n import tr
from config.version import (
    DEVELOPER_NAME,
    DEVELOPER_ALIAS,
    format_version_splash,
)


SPLASH_IMAGE_PATH = asset_path(
    "assets/images/splash.png"
)

SPLASH_DURATION_MS = 8000
MIN_SPLASH_VISIBLE_MS = 2200
POST_INIT_FADE_DELAY_MS = 700

# Bildschirmanteil: 88 % Basis, davon 40 % kleiner → 52,8 %
SPLASH_SCREEN_RATIO = 0.88 * (1.0 - 0.40)

# Positionierung relativ zur Splash-Grafik (unter Icon-Beschriftungen)
STATUS_Y_RATIO = 0.845
BAR_WIDTH_RATIO = 0.46
BAR_HEIGHT_RATIO = 0.035
STATUS_TO_BAR_GAP = 6
BAR_DOWN_EXTRA_PX = 10
VERSION_X_RATIO = 0.034
SPLASH_EDGE_MARGIN = 10

SPLASH_PROGRESS_STYLE = """
QFrame#splashProgressPanel {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 rgba(23, 30, 40, 238),
        stop: 1 rgba(14, 20, 28, 248)
    );
    border: 1px solid #263545;
    border-top: 2px solid #E07A2A;
    border-radius: 6px;
}
QLabel#splashStatus {
    color: #42D4F5;
    font-family: "Rajdhani";
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 1px;
    background: transparent;
}
QLabel#splashPercent {
    color: #C9A227;
    font-family: "Rajdhani";
    font-size: 14px;
    font-weight: bold;
    letter-spacing: 0.6px;
    background: transparent;
}
QFrame#splashHudLine {
    color: #E07A2A;
    background-color: #E07A2A;
    max-height: 2px;
}
QLabel#splashHudMarker {
    color: #E07A2A;
    font-family: "Rajdhani";
    font-size: 14px;
    font-weight: bold;
    padding: 0 2px;
    background: transparent;
}
"""

_TRACK_BG = QColor(14, 20, 28)
_TRACK_BORDER = QColor(38, 53, 69)
_TRACK_INNER = QColor(10, 14, 20)
_FILL_START = QColor(160, 90, 24)
_FILL_MID = QColor(224, 122, 42)
_FILL_END = QColor(255, 168, 72)
_SEGMENT_COUNT = 10


class SplashHudRow(QWidget):

    def __init__(
        self,
        text,
        parent=None,
    ):
        super().__init__(parent)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        left_line = QFrame()
        left_line.setObjectName("splashHudLine")
        left_line.setFrameShape(QFrame.Shape.HLine)
        left_line.setFixedHeight(2)

        marker = QLabel("◆")
        marker.setObjectName("splashHudMarker")
        marker.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.label = QLabel(text)
        self.label.setObjectName("splashStatus")
        self.label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        marker_right = QLabel("◆")
        marker_right.setObjectName("splashHudMarker")
        marker_right.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        right_line = QFrame()
        right_line.setObjectName("splashHudLine")
        right_line.setFrameShape(QFrame.Shape.HLine)
        right_line.setFixedHeight(2)

        layout.addWidget(left_line, 1)
        layout.addWidget(marker)
        layout.addWidget(self.label)
        layout.addWidget(marker_right)
        layout.addWidget(right_line, 1)

        self.setLayout(layout)

    def set_text(self, text):
        self.label.setText(text)


class TrackerLoadingBar(QWidget):

    display_progress_changed = Signal(float)

    def __init__(self, parent=None, bar_height=24):
        super().__init__(parent)

        self._target_progress = 0.0
        self._display_progress = 0.0
        self._anim_phase = 0.0
        self._stalled = False
        self._pulse = 0.0
        self.setFixedHeight(bar_height)
        self.setObjectName("trackerLoadingBar")

        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)
        self._anim_timer.timeout.connect(self._tick_animation)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._anim_timer.isActive():
            self._anim_timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._anim_timer.stop()

    def reset(self) -> None:
        self._target_progress = 0.0
        self._display_progress = 0.0
        self._anim_phase = 0.0
        self._stalled = False
        self._pulse = 0.0
        self.display_progress_changed.emit(0.0)
        self.update()

    def setProgress(self, value):
        value = max(0.0, min(100.0, float(value)))
        if value <= 0.0:
            self.reset()
            return
        if value < self._display_progress - 25.0:
            self._display_progress = value
        self._target_progress = value

    def setStalled(self, stalled):
        self._stalled = stalled

    def progress(self):
        return int(round(self._display_progress))

    def _tick_animation(self):
        speed = 0.045 if self._stalled else 0.14
        delta = self._target_progress - self._display_progress
        if abs(delta) > 0.05:
            self._display_progress += delta * speed
        else:
            self._display_progress = self._target_progress

        anim_speed = 0.004 if self._stalled else 0.018
        self._anim_phase = (self._anim_phase + anim_speed) % 1.0
        self._pulse = (self._pulse + (0.035 if self._stalled else 0.02)) % (
            2 * math.pi
        )
        self.display_progress_changed.emit(self._display_progress)
        self.update()

    def _draw_hud_brackets(self, painter, rect, color, arm=5):
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        painter.setPen(QPen(color, 1.2))
        for sx, sy, dx, dy in (
            (x, y, arm, 0),
            (x, y, 0, arm),
            (x + w, y, -arm, 0),
            (x + w, y, 0, arm),
            (x, y + h, arm, 0),
            (x, y + h, 0, -arm),
            (x + w, y + h, -arm, 0),
            (x + w, y + h, 0, -arm),
        ):
            painter.drawLine(int(sx), int(sy), int(sx + dx), int(sy + dy))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        inset = 1
        track = QRectF(
            inset,
            inset,
            width - 2 * inset,
            height - 2 * inset,
        )
        radius = max(3.0, height * 0.22)

        pulse_alpha = int(90 + 50 * math.sin(self._pulse))
        border_color = QColor(_TRACK_BORDER)
        if self._stalled:
            border_color = QColor(224, 122, 42, pulse_alpha + 80)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(_TRACK_BG)
        painter.drawRoundedRect(track, radius, radius)

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(track, radius, radius)

        inner = track.adjusted(2, 2, -2, -2)
        inner_radius = max(2.0, radius - 1)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(_TRACK_INNER)
        painter.drawRoundedRect(inner, inner_radius, inner_radius)

        segment_pen = QPen(QColor(38, 53, 69, 120), 1)
        painter.setPen(segment_pen)
        for i in range(1, _SEGMENT_COUNT):
            sx = inner.x() + inner.width() * i / _SEGMENT_COUNT
            painter.drawLine(
                int(sx),
                int(inner.y() + 2),
                int(sx),
                int(inner.bottom() - 2),
            )

        inner_w = inner.width()
        fill_w = inner_w * self._display_progress / 100.0
        if fill_w > 1.5:
            fill_rect = QRectF(
                inner.x(),
                inner.y(),
                fill_w,
                inner.height(),
            )

            fill_grad = QLinearGradient(
                fill_rect.left(),
                0,
                fill_rect.right(),
                0,
            )
            fill_grad.setColorAt(0.0, _FILL_START)
            fill_grad.setColorAt(0.55, _FILL_MID)
            fill_grad.setColorAt(1.0, _FILL_END)
            painter.setBrush(QBrush(fill_grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(
                fill_rect,
                inner_radius,
                inner_radius,
            )

            shimmer_w = max(18.0, inner.height() * 1.8)
            shimmer_x = (
                inner.x()
                + (inner_w + shimmer_w) * self._anim_phase
                - shimmer_w
            )
            if shimmer_x < fill_rect.right():
                shimmer = QLinearGradient(
                    shimmer_x,
                    0,
                    shimmer_x + shimmer_w,
                    0,
                )
                shimmer.setColorAt(0.0, QColor(255, 255, 255, 0))
                shimmer.setColorAt(0.45, QColor(255, 220, 170, 55))
                shimmer.setColorAt(0.55, QColor(255, 255, 255, 90))
                shimmer.setColorAt(1.0, QColor(255, 255, 255, 0))
                clip = QPainterPath()
                clip.addRoundedRect(
                    fill_rect,
                    inner_radius,
                    inner_radius,
                )
                painter.setClipPath(clip)
                painter.fillRect(
                    QRectF(
                        shimmer_x,
                        inner.y(),
                        shimmer_w,
                        inner.height(),
                    ),
                    shimmer,
                )
                painter.setClipping(False)

            edge_x = inner.x() + fill_w
            edge_glow = QLinearGradient(edge_x - 10, 0, edge_x + 6, 0)
            edge_alpha = int(120 + 80 * math.sin(self._pulse * 1.4))
            edge_glow.setColorAt(0.0, QColor(66, 212, 245, 0))
            edge_glow.setColorAt(0.55, QColor(66, 212, 245, edge_alpha))
            edge_glow.setColorAt(1.0, QColor(255, 210, 140, edge_alpha // 2))
            painter.fillRect(
                QRectF(edge_x - 10, inner.y(), 16, inner.height()),
                edge_glow,
            )

        bracket_color = QColor(224, 122, 42, 180)
        if self._stalled:
            bracket_color = QColor(
                66,
                212,
                245,
                int(140 + 60 * math.sin(self._pulse)),
            )
        self._draw_hud_brackets(
            painter,
            track.adjusted(0.5, 0.5, -0.5, -0.5),
            bracket_color,
            arm=max(4, int(height * 0.22)),
        )

        scan_y = inner.y() + inner.height() * (
            0.35 + 0.3 * math.sin(self._pulse * 0.8)
        )
        scan_alpha = int(35 + 25 * math.sin(self._pulse * 1.2))
        painter.setPen(QPen(QColor(66, 212, 245, scan_alpha), 1))
        painter.drawLine(
            int(inner.x() + 3),
            int(scan_y),
            int(inner.right() - 3),
            int(scan_y),
        )

        painter.end()


class TrackerLoadingPanel(QFrame):

    def __init__(
        self,
        status_text=None,
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName("splashProgressPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        if status_text is None:
            status_text = tr("splash.initializing")

        self.status_row = SplashHudRow(status_text, self)

        bar_row = QHBoxLayout()
        bar_row.setContentsMargins(0, 0, 0, 0)
        bar_row.setSpacing(8)

        self.loading_bar = TrackerLoadingBar(self)
        self.percent_label = QLabel("0%")
        self.percent_label.setObjectName("splashPercent")
        self.percent_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter,
        )
        self.percent_label.setFixedWidth(48)
        self.loading_bar.display_progress_changed.connect(
            self._sync_percent_label,
        )

        bar_row.addWidget(self.loading_bar, 1)
        bar_row.addWidget(self.percent_label)

        layout.addWidget(self.status_row)
        layout.addLayout(bar_row)

    def _sync_percent_label(self, value: float) -> None:
        self.percent_label.setText(f"{int(round(value))}%")

    def reset(self) -> None:
        self.loading_bar.reset()
        self.percent_label.setText("0%")

    def set_status(self, text):
        self.status_row.set_text(text)

    def set_progress(self, value):
        self.loading_bar.setProgress(value)

    def set_stalled(self, stalled):
        self.loading_bar.setStalled(stalled)


MobiglasLoadingBar = TrackerLoadingBar
MobiglasLoadingPanel = TrackerLoadingPanel


class SplashScreen(QWidget):

    finished = Signal()

    def __init__(
        self,
        duration_ms=SPLASH_DURATION_MS,
        parent=None,
    ):
        super().__init__(parent)

        self.duration_ms = duration_ms
        self._progress_value = 0
        self._closing = False
        self._timers_started = False
        self._progress_clock = QElapsedTimer()
        self._show_clock = QElapsedTimer()
        self._init_complete = False
        self._fade_out_scheduled = False
        self._custom_status_active = False
        self._source_pixmap = None
        self._pixmap = None
        self._progress_generation = 0

        self.setObjectName("splashScreen")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            False,
        )

        self.image_label = QLabel(self)
        self.image_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.image_label.setObjectName("splashImage")
        self.image_label.setScaledContents(False)

        self.progress_panel = MobiglasLoadingPanel(
            parent=self,
        )

        self.version_label = QLabel(
            format_version_splash(),
            self,
        )
        self.version_label.setObjectName("splashVersion")
        self.version_label.setWordWrap(True)
        self.version_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )
        self.version_label.setAutoFillBackground(False)

        self.developer_label = QLabel(
            tr(
                "splash.created_by",
                name=DEVELOPER_NAME,
                alias=DEVELOPER_ALIAS,
            ),
            self,
        )
        self.developer_label.setObjectName("splashDeveloper")
        self.developer_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )
        self.developer_label.setAutoFillBackground(False)

        self.setStyleSheet(SPLASH_PROGRESS_STYLE)

        self.setWindowOpacity(0.0)

        self._fade_in = QPropertyAnimation(
            self,
            b"windowOpacity",
            self,
        )
        self._fade_in.setDuration(400)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )
        self._fade_in.finished.connect(
            self._start_progress_timers
        )

        self._fade_out = QPropertyAnimation(
            self,
            b"windowOpacity",
            self,
        )
        self._fade_out.setDuration(400)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.setEasingCurve(
            QEasingCurve.Type.InCubic
        )
        self._fade_out.finished.connect(self._emit_finished)

        self._load_image()
        self._raise_overlay_widgets()

    def set_status(self, text):
        self._custom_status_active = True
        self.progress_panel.set_status(text)
        QApplication.processEvents()

    def notify_init_complete(self):
        self._init_complete = True
        self._custom_status_active = True
        self.progress_panel.set_status(tr("splash.complete"))
        self.progress_panel.set_progress(
            max(self._progress_value, 92)
        )
        self._schedule_fade_out_when_ready()

    def _schedule_fade_out_when_ready(self):
        if self._fade_out_scheduled or self._closing:
            return

        if not self._init_complete:
            return

        self._fade_out_scheduled = True
        elapsed = self._show_clock.elapsed()
        remaining_visible = max(
            0,
            MIN_SPLASH_VISIBLE_MS - elapsed,
        )
        delay = remaining_visible + POST_INIT_FADE_DELAY_MS
        QTimer.singleShot(delay, self._start_fade_out)

    def _raise_overlay_widgets(self):
        self.image_label.lower()
        for widget in (
            self.progress_panel,
            self.version_label,
            self.developer_label,
        ):
            widget.raise_()
        self.developer_label.raise_()

    def _start_progress_timers(self):
        if self._timers_started:
            return

        self._timers_started = True
        self._progress_clock.invalidate()
        self._progress_clock.start()
        self._schedule_next_progress_tick()

        if self._init_complete:
            self._schedule_fade_out_when_ready()

    def _schedule_next_progress_tick(self):
        if self._closing or self._progress_value >= 100:
            return

        if random.random() < 0.2:
            delay = random.randint(170, 340)
        else:
            delay = random.randint(45, 115)

        generation = self._progress_generation

        def tick():
            if generation != self._progress_generation:
                return
            self._tick_progress()

        QTimer.singleShot(delay, tick)

    def _reset_progress_state(self):
        self._progress_generation += 1
        self._progress_value = 0
        self._closing = False
        self._fade_out_scheduled = False
        self._init_complete = False
        self._custom_status_active = False
        self._timers_started = False
        self._progress_clock.invalidate()
        self.progress_panel.reset()
        self.progress_panel.set_stalled(False)

    def _create_display_pixmap(self):
        source = self._source_pixmap
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry()
        device_ratio = screen.devicePixelRatio()

        max_logical_w = int(
            available.width() * SPLASH_SCREEN_RATIO
        )
        max_logical_h = int(
            available.height() * SPLASH_SCREEN_RATIO
        )

        source_w = source.width()
        source_h = source.height()

        # Nie über die Originalauflösung hinaus hochskalieren
        scale = min(
            max_logical_w / source_w,
            max_logical_h / source_h,
            1.0,
        )
        logical_w = max(1, int(source_w * scale))
        logical_h = max(1, int(source_h * scale))

        physical_w = min(
            max(1, int(logical_w * device_ratio)),
            source_w,
        )
        physical_h = min(
            max(1, int(logical_h * device_ratio)),
            source_h,
        )

        if physical_w == source_w and physical_h == source_h:
            display = QPixmap(source)
        else:
            display = source.scaled(
                physical_w,
                physical_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        if device_ratio > 1.0:
            display.setDevicePixelRatio(device_ratio)

        return display

    def _load_image(self):
        if SPLASH_IMAGE_PATH.exists():
            pixmap = QPixmap(str(SPLASH_IMAGE_PATH))
            if not pixmap.isNull():
                self._source_pixmap = pixmap

        if self._source_pixmap is None:
            self.resize(960, 540)
            self.image_label.setText("SC Salvage Tracker")
            return

        scaled = self._create_display_pixmap()
        self._pixmap = scaled
        self.image_label.setPixmap(scaled)

        logical_w = int(scaled.width() / scaled.devicePixelRatio())
        logical_h = int(scaled.height() / scaled.devicePixelRatio())
        self.resize(logical_w, logical_h)
        self._layout_overlay_elements(logical_w, logical_h)

    def _layout_overlay_elements(
        self,
        width,
        height,
    ):
        panel_width = int(width * 0.62)
        bar_height = max(18, int(height * BAR_HEIGHT_RATIO))
        status_height = max(26, int(height * 0.048))
        panel_height = (
            10
            + status_height
            + 8
            + bar_height
            + 10
        )
        panel_x = (width - panel_width) // 2
        panel_y = int(height * STATUS_Y_RATIO)

        version_width = int(width * 0.42)
        version_height = max(36, int(height * 0.055))
        version_x = SPLASH_EDGE_MARGIN
        version_y = height - version_height - SPLASH_EDGE_MARGIN

        developer_width = min(
            int(width * 0.52),
            width - (2 * SPLASH_EDGE_MARGIN),
        )
        developer_height = max(28, int(height * 0.042))
        developer_x = width - developer_width - SPLASH_EDGE_MARGIN
        developer_y = (
            height
            - developer_height
            - SPLASH_EDGE_MARGIN
        )

        self.developer_label.setFixedHeight(developer_height)

        self.progress_panel.setGeometry(
            QRect(
                panel_x,
                panel_y,
                panel_width,
                panel_height,
            )
        )

        self.version_label.setGeometry(
            QRect(
                version_x,
                version_y,
                version_width,
                version_height,
            )
        )

        self.developer_label.setGeometry(
            QRect(
                developer_x,
                developer_y,
                developer_width,
                developer_height,
            )
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)

        width = self.width()
        height = self.height()

        self.image_label.setGeometry(0, 0, width, height)
        self._layout_overlay_elements(width, height)
        self._raise_overlay_widgets()

    def show_splash(self):
        self._reset_progress_state()

        screen = QApplication.primaryScreen()
        available = screen.availableGeometry()
        self.move(
            available.x()
            + (available.width() - self.width()) // 2,
            available.y()
            + (available.height() - self.height()) // 2,
        )

        self.show()
        self._show_clock.start()
        QApplication.processEvents()

        self._fade_in.start()

    def _tick_progress(self):
        if self._closing:
            return

        if not self._progress_clock.isValid():
            self._schedule_next_progress_tick()
            return

        elapsed_ms = self._progress_clock.elapsed()
        expected = min(
            100,
            int(elapsed_ms * 100 / self.duration_ms),
        )

        if elapsed_ms < 250:
            expected = min(expected, 2)

        if elapsed_ms >= self.duration_ms - 450:
            step = random.randint(2, 5)
            self._progress_value = min(
                100,
                self._progress_value + step,
            )
            self.progress_panel.set_stalled(False)
        elif random.random() < 0.19:
            self.progress_panel.set_progress(
                self._progress_value
            )
            self.progress_panel.set_stalled(True)
        else:
            step = random.choice([1, 1, 1, 2])
            ceiling = min(
                expected + random.randint(0, 2),
                100,
            )
            self._progress_value = min(
                ceiling,
                self._progress_value + step,
            )
            self.progress_panel.set_stalled(False)

        self._progress_value = max(
            0,
            min(100, self._progress_value),
        )
        self.progress_panel.set_progress(self._progress_value)

        if (
            self._progress_value >= 100
            and not self._custom_status_active
        ):
            self.progress_panel.set_status(
                tr("splash.complete")
            )

        if self._progress_value >= 100:
            self.progress_panel.set_progress(100)
            return

        self._schedule_next_progress_tick()

    def _start_fade_out(self):
        if self._closing:
            return

        self._closing = True
        self.progress_panel.set_progress(100)
        self.progress_panel.set_stalled(False)
        self._fade_out.start()

    def _emit_finished(self):
        self.close()
        self.finished.emit()


def run_startup_splash(init_fn):
    """Splash sofort anzeigen, dann schwere Initialisierung ausführen."""
    splash = SplashScreen()
    splash.show_splash()

    try:
        init_fn(splash)
    finally:
        splash.notify_init_complete()

    loop = QEventLoop()
    splash.finished.connect(loop.quit)
    loop.exec()


def show_startup_splash(
    duration_ms=SPLASH_DURATION_MS,
):
    """Legacy-Helfer — nur noch Animation ohne Backend-Init."""
    splash = SplashScreen(duration_ms=duration_ms)
    splash.show_splash()
    splash.notify_init_complete()

    loop = QEventLoop()
    splash.finished.connect(loop.quit)
    loop.exec()
