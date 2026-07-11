"""Drei Layout-Varianten für die Auszahlungsseite."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from config.i18n import tr
from demo.payout_layout import components
from ui.page_layout import (
    hud_divider,
    page_content_widget,
    page_title,
    section_accent,
)


class VerticalReferenceLayout(QWidget):
    """A — Aktuell: vier Bereiche untereinander (wie Screenshot)."""

    VARIANT_ID = "vertical"
    VARIANT_TITLE = "A — Aktuell (vertikal)"
    VARIANT_HINT = (
        "Alle vier Blöcke untereinander. Übersichtlich bei wenig Inhalt, "
        "aber viel Leerraum wenn Tabellen leer sind."
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        content, layout = page_content_widget()
        layout.addWidget(page_title(tr("payout.title")))
        layout.addWidget(section_accent(tr("payout.section.main")))
        layout.addLayout(hud_divider())
        layout.addWidget(components.build_summary_block())
        layout.addWidget(section_accent(tr("payout.section.unpaid")))
        layout.addLayout(hud_divider())
        layout.addWidget(components.build_unpaid_block()[0])
        layout.addWidget(components.build_calculate_block())
        layout.addWidget(section_accent(tr("payout.section.crew_totals")))
        layout.addLayout(hud_divider())
        layout.addWidget(components.build_crew_totals_block())
        layout.addStretch()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(content)


class SplitColumnsLayout(QWidget):
    """B — Zweispaltig: KPI oben, links Workflow, rechts Historie."""

    VARIANT_ID = "split"
    VARIANT_TITLE = "B — Zweispaltig (empfohlen)"
    VARIANT_HINT = (
        "KPI-Karten oben in einer Zeile. Links: offene Verkäufe + Berechnung. "
        "Rechts: Crew-Historie. Nutzt die Breite besser, weniger Scrollen."
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        content, layout = page_content_widget()
        layout.addWidget(page_title(tr("payout.title")))
        layout.addWidget(section_accent(tr("payout.section.main")))
        layout.addLayout(hud_divider())
        layout.addWidget(components.build_kpi_row())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("contentStack")

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)
        left_layout.addWidget(components.build_unpaid_block(compact=True)[0])
        left_layout.addWidget(components.build_calculate_block())
        left_layout.addStretch()

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        right_layout.addWidget(components.build_crew_totals_block(compact=True))
        right_layout.addStretch()

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([620, 420])

        layout.addWidget(splitter, 1)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(content)


class WorkflowMasterDetailLayout(QWidget):
    """C — Workflow: schmale Verkaufsliste links, Formular + Historie rechts."""

    VARIANT_ID = "workflow"
    VARIANT_TITLE = "C — Workflow (Master-Detail)"
    VARIANT_HINT = (
        "Links nur die Verkaufsliste (Master). Rechts oben Berechnung, "
        "unten Historie — klarer Arbeitsfluss: wählen → berechnen → speichern."
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        content, layout = page_content_widget()
        layout.addWidget(page_title(tr("payout.title")))
        layout.addWidget(section_accent(tr("payout.section.main")))
        layout.addLayout(hud_divider())
        layout.addWidget(components.build_kpi_row())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("contentStack")

        master = QWidget()
        master.setMinimumWidth(280)
        master_layout = QVBoxLayout(master)
        master_layout.setContentsMargins(0, 0, 0, 0)
        master_layout.setSpacing(8)
        master_layout.addWidget(components.build_unpaid_block(compact=True)[0])
        master_layout.addStretch()

        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(12)
        detail_layout.addWidget(components.build_calculate_block())
        detail_layout.addWidget(components.build_crew_totals_block(compact=True))
        detail_layout.addStretch()

        splitter.addWidget(master)
        splitter.addWidget(detail)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 5)
        splitter.setSizes([340, 700])

        layout.addWidget(splitter, 1)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(content)


LAYOUT_VARIANTS = (
    VerticalReferenceLayout,
    SplitColumnsLayout,
    WorkflowMasterDetailLayout,
)
