"""Dashboard-Label mit automatischer Schriftanpassung an die Panelbreite."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget


class DashboardFitLabel(QLabel):
    """Skaliert Text per Umbruch und kleinerer Schrift, damit er ins Panel passt."""

    def __init__(
        self,
        text: str = "",
        *,
        min_px: int = 8,
        max_lines: int = 3,
        parent: QWidget | None = None,
    ):
        super().__init__(text, parent)
        self._base_px = 13
        self._min_px = min_px
        self._max_lines = max_lines
        self._fitted_px = self._base_px
        self._last_fit_width = -1
        self._in_refit = False

        self.setWordWrap(True)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

    def apply_theme_font(self, font: QFont):
        """Dashboard-Schrift aus ThemeManager (Basisschrift für Auto-Layout)."""
        px = font.pixelSize()
        if px <= 0:
            px = font.pointSize()
        if px > 0:
            self._base_px = px
            self._fitted_px = px
        self._last_fit_width = -1
        super().setFont(font)
        self._refit()

    def setFont(self, font: QFont):
        if self._in_refit:
            super().setFont(font)
            return
        px = font.pixelSize()
        if px <= 0:
            px = font.pointSize()
        if px > 0:
            self._base_px = px
            self._fitted_px = px
        self._last_fit_width = -1
        super().setFont(font)
        self._refit()

    def setText(self, text: str):
        super().setText(text or "")
        self._last_fit_width = -1
        self._refit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refit()

    def heightForWidth(self, width: int) -> int:
        if width <= 0 or not self.text():
            return super().heightForWidth(width)
        return self._content_height_for_width(width)

    def hasHeightForWidth(self) -> bool:
        return True

    def _metrics_for(self, px: int) -> QFontMetrics:
        font = QFont(self.font())
        if font.pixelSize() > 0:
            font.setPixelSize(px)
        else:
            font.setPointSize(px)
        return QFontMetrics(font)

    def _content_height_for_width(self, width: int) -> int:
        px = self._pick_font_size(width)
        metrics = self._metrics_for(px)
        rect = metrics.boundingRect(
            0,
            0,
            width,
            10000,
            int(Qt.TextFlag.TextWordWrap),
            self.text(),
        )
        line_h = metrics.height()
        line_count = max(1, (rect.height() + line_h - 1) // line_h)
        line_count = min(line_count, self._max_lines)
        return line_count * line_h

    def text_fits_at_width(self, width: int) -> bool:
        """Prüft, ob der Text bei Dashboard-Basisschrift in die Breite passt."""
        if width <= 0 or not self.text():
            return True
        return self._text_fits_at_px(width, self._base_px)

    def _text_fits_at_px(self, width: int, px: int) -> bool:
        metrics = self._metrics_for(px)
        rect = metrics.boundingRect(
            0,
            0,
            width,
            10000,
            int(Qt.TextFlag.TextWordWrap),
            self.text(),
        )
        line_h = metrics.height()
        line_count = max(1, (rect.height() + line_h - 1) // line_h)
        if line_count > self._max_lines:
            return False
        return rect.width() <= width + 1

    def _pick_font_size(self, width: int) -> int:
        text = self.text()
        if width <= 0 or not text:
            return self._base_px

        for px in range(self._base_px, self._min_px - 1, -1):
            metrics = self._metrics_for(px)
            rect = metrics.boundingRect(
                0,
                0,
                width,
                10000,
                int(Qt.TextFlag.TextWordWrap),
                text,
            )
            line_h = metrics.height()
            line_count = max(1, (rect.height() + line_h - 1) // line_h)
            if line_count <= self._max_lines and rect.width() <= width + 1:
                return px

        return self._min_px

    def _refit(self):
        if self._in_refit:
            return

        width = self.width()
        if width <= 0:
            return

        fitted_px = self._pick_font_size(width)
        if width == self._last_fit_width and fitted_px == self._fitted_px:
            return

        self._in_refit = True
        try:
            if fitted_px != self._fitted_px:
                font = QFont(self.font())
                if font.pixelSize() > 0:
                    font.setPixelSize(fitted_px)
                else:
                    font.setPointSize(fitted_px)
                super().setFont(font)
                self._fitted_px = fitted_px

            self._last_fit_width = width

            if self._fitted_px < self._base_px:
                self.setToolTip(self.text())
            else:
                self.setToolTip("")
        finally:
            self._in_refit = False
