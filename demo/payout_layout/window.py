"""Demo-Fenster zum Vergleich der Auszahlungs-Layouts."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from demo.payout_layout.layouts import LAYOUT_VARIANTS
from ui.page_layout import hud_divider


class PayoutLayoutDemoWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowTitle("SC Salvage Tracker — Auszahlung Layout DEMO")
        self.resize(1320, 900)

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

        banner_title = QLabel("DEMO — Auszahlung übersichtlicher aufteilen")
        banner_title.setObjectName("warningBannerTitle")
        banner_hint = QLabel(
            "Keine echten Daten. Oben die Variante wählen und vergleichen. "
            "Variante B oder C nutzen die Bildschirmbreite besser als die "
            "aktuelle vertikale Anordnung."
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

        self._variant_hint = QLabel()
        self._variant_hint.setObjectName("mutedLabel")
        self._variant_hint.setWordWrap(True)

        self._buttons: list[QPushButton] = []
        self._stack = QStackedWidget()
        self._stack.setObjectName("pageContent")

        for index, variant_cls in enumerate(LAYOUT_VARIANTS):
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
        root.addWidget(self._variant_hint)
        root.addLayout(hud_divider())

        scroll = QScrollArea()
        scroll.setObjectName("pageScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(self._stack)
        root.addWidget(scroll, 1)

        self._show_variant(1)

    def _show_variant(self, index: int):
        self._stack.setCurrentIndex(index)
        variant = LAYOUT_VARIANTS[index]
        self._variant_hint.setText(variant.VARIANT_HINT)
        for button_index, button in enumerate(self._buttons):
            active = button_index == index
            button.setProperty("active", active)
            button.style().unpolish(button)
            button.style().polish(button)
