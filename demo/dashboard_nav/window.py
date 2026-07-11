"""Demo-Fenster für Übersicht-Nav-Darstellung."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from demo.dashboard_nav.variants import VARIANTS
from ui.page_layout import hud_divider


class DashboardNavDemoWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowTitle(
            "SC Salvage Tracker — Übersicht Nav DEMO"
        )
        self.resize(960, 640)

        central = QWidget()
        central.setObjectName("mainCentral")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        banner = QFrame()
        banner.setObjectName("infoPanel")
        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(16, 12, 16, 12)
        banner_layout.setSpacing(6)

        banner_title = QLabel(
            "DEMO — Übersicht-Schaltfläche: Fenster offen/geschlossen"
        )
        banner_title.setObjectName("warningBannerTitle")
        banner_hint = QLabel(
            "Simuliert Öffnen und Schließen des Übersicht-Fensters. "
            "Variante A entspricht dem Fix in der App. B und C sind "
            "alternative Darstellungen zum Vergleich."
        )
        banner_hint.setObjectName("mutedLabel")
        banner_hint.setWordWrap(True)
        banner_layout.addWidget(banner_title)
        banner_layout.addWidget(banner_hint)
        root.addWidget(banner)

        picker_row = QWidget()
        picker_layout = QHBoxLayout(picker_row)
        picker_layout.setContentsMargins(16, 10, 16, 6)
        picker_layout.setSpacing(8)

        self._buttons: list[QPushButton] = []
        self._stack = QStackedWidget()
        self._stack.setObjectName("pageContent")

        for index, variant_cls in enumerate(VARIANTS):
            button = QPushButton(variant_cls.VARIANT_TITLE)
            button.setObjectName("secondaryAction")
            button.setCheckable(True)
            button.clicked.connect(
                lambda checked=False, i=index: self._show_variant(i)
            )
            self._buttons.append(button)
            picker_layout.addWidget(button)
            self._stack.addWidget(variant_cls())

        picker_layout.addStretch()
        root.addWidget(picker_row)
        root.addLayout(hud_divider())
        root.addWidget(self._stack, 1)

        if self._buttons:
            self._show_variant(0)

    def _show_variant(self, index: int):
        for i, button in enumerate(self._buttons):
            button.setChecked(i == index)
        self._stack.setCurrentIndex(index)
