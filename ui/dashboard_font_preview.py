"""Live-Vorschau für die Dashboard-Schriftgröße."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel

from config.i18n import tr
from ui.page_layout import subsection_title, form_label
from ui.theme_manager import ThemeManager


class DashboardFontPreviewWidget(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboardFontPreviewHost")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)
        outer.addWidget(
            subsection_title(tr("dashboard.font_preview.section"))
        )

        self._card = QFrame()
        self._card.setObjectName("dashboardFontPreviewCard")

        layout = QVBoxLayout(self._card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._title = form_label(tr("dashboard.font_preview.demo_title"))

        self._value = QLabel(tr("dashboard.font_preview.demo_value"))
        self._value.setObjectName("displayValue")
        self._value.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        layout.addWidget(self._title)
        layout.addWidget(self._value)
        outer.addWidget(self._card)

        hint = QLabel(tr("dashboard.font_preview.hint"))
        hint.setObjectName("dashboardFontPreviewHint")
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(hint)

        self.set_scale(ThemeManager.default_dashboard_font_scale())

    def set_scale(self, scale_percent: int):
        self.setStyleSheet(
            ThemeManager.build_dashboard_font_preview_qss(
                scale_percent
            )
        )
