from pathlib import Path
import random

from PySide6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    Signal,
    QEventLoop,
    QRect,
    QElapsedTimer,
)
from PySide6.QtGui import (
    QPixmap,
    QPainter,
    QColor,
    QLinearGradient,
    QPen,
    QFont,
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
    background-color: rgba(8, 19, 28, 230);
    border: 1px solid #00D9FF;
    border-radius: 2px;
}
QLabel#splashStatus {
    color: #D9F4FF;
    font-family: "Rajdhani";
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 0.5px;
    background: transparent;
}
"""


class MobiglasLoadingBar(QWidget):

    def __init__(self, parent=None, bar_height=24):
        super().__init__(parent)

        self._progress = 0
        self._stripe_offset = 0
        self._stalled = False
        self.setFixedHeight(bar_height)
        self.setObjectName("mobiglasLoadingBar")

    def setProgress(self, value):
        self._progress = max(0, min(100, int(value)))
        self._stripe_offset = (self._stripe_offset + 2) % 7
        self.update()

    def setStalled(self, stalled):
        self._stalled = stalled
        self._stripe_offset = (self._stripe_offset + 3) % 7
        self.update()

    def progress(self):
        return self._progress

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        width = self.width()
        height = self.height()
        inner_width = max(0, width - 4)
        fill_width = int(
            inner_width * self._progress / 100
        )

        painter.fillRect(
            self.rect(),
            QColor(8, 19, 28, 210),
        )

        painter.setPen(
            QPen(QColor(0, 217, 255), 1)
        )
        painter.drawRect(0, 0, width - 1, height - 1)

        if fill_width > 0:
            gradient = QLinearGradient(0, 0, fill_width, 0)
            gradient.setColorAt(
                0.0,
                QColor(0, 90, 115, 220),
            )
            gradient.setColorAt(
                1.0,
                QColor(0, 217, 255, 230),
            )
            painter.fillRect(
                2,
                2,
                fill_width,
                height - 4,
                gradient,
            )

            painter.setPen(
                QPen(QColor(0, 217, 255, 70), 1)
            )
            stripe_step = 7
            start_x = -height + self._stripe_offset
            for x in range(start_x, fill_width, stripe_step):
                painter.drawLine(
                    x + 2,
                    height - 2,
                    x + height,
                    2,
                )

        painter.setPen(QColor(217, 244, 255))
        font = QFont("Rajdhani", 11)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            f"{self._progress}%",
        )

        painter.end()


class MobiglasLoadingPanel(QFrame):

    def __init__(
        self,
        status_text=None,
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName("splashProgressPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        if status_text is None:
            status_text = tr("splash.initializing")

        self.status_label = QLabel(status_text)
        self.status_label.setObjectName("splashStatus")
        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.status_label.setWordWrap(True)

        self.loading_bar = MobiglasLoadingBar(self)

        layout.addWidget(self.status_label)
        layout.addWidget(self.loading_bar)

    def set_status(self, text):
        self.status_label.setText(text)

    def set_progress(self, value):
        self.loading_bar.setProgress(value)

    def set_stalled(self, stalled):
        self.loading_bar.setStalled(stalled)


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

        QTimer.singleShot(delay, self._tick_progress)

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
        bar_height = max(16, int(height * BAR_HEIGHT_RATIO))
        status_height = max(22, int(height * 0.042))
        panel_height = (
            8
            + status_height
            + 6
            + bar_height
            + 8
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
        self._start_progress_timers()

    def _tick_progress(self):
        if self._closing:
            return

        elapsed_ms = self._progress_clock.elapsed()
        expected = min(
            100,
            int(elapsed_ms * 100 / self.duration_ms),
        )

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
