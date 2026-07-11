"""Drei Layout-Varianten für die Verkaufsseite."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from config.i18n import tr
from demo.sales_layout import components
from ui.page_layout import (
    hud_divider,
    page_content_widget,
    page_title,
    section_accent,
)


class VerticalReferenceLayout(QWidget):
    VARIANT_ID = "vertical"
    VARIANT_TITLE = "A — Aktuell (vertikal)"
    VARIANT_HINT = (
        "Lagerbestand, Formular, Finanzübersicht und Historie untereinander — "
        "viel vertikales Scrollen."
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        content, layout = page_content_widget()
        layout.addWidget(page_title(tr("sales.title")))
        layout.addWidget(section_accent(tr("sales.section.main")))
        layout.addWidget(components.build_inventory_block())
        layout.addWidget(components.build_sale_form_block())
        layout.addWidget(components.build_finance_block())
        layout.addWidget(section_accent(tr("sales.section.history")))
        layout.addLayout(hud_divider())
        layout.addWidget(components.build_history_block())
        layout.addStretch()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(content)


class SplitColumnsLayout(QWidget):
    VARIANT_ID = "split"
    VARIANT_TITLE = "B — Zweispaltig (empfohlen)"
    VARIANT_HINT = (
        "Finanz-KPIs oben in drei Karten. Links: Lager + neuer Verkauf. "
        "Rechts: Verkaufshistorie. Weniger Scrollen, klarer Workflow."
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        content, layout = page_content_widget()
        layout.addWidget(page_title(tr("sales.title")))
        layout.addWidget(section_accent(tr("sales.section.main")))
        layout.addLayout(hud_divider())
        layout.addWidget(components.build_kpi_row())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("pageSplit")
        splitter.setHandleWidth(14)
        splitter.setChildrenCollapsible(False)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 16, 0)
        left_layout.setSpacing(12)
        left_layout.addWidget(components.build_inventory_block(compact=True))
        left_layout.addWidget(components.build_sale_form_block())
        left_layout.addStretch()

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 0, 0, 0)
        right_layout.setSpacing(12)
        right_layout.addWidget(components.build_history_block(compact=True))
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
    VARIANT_ID = "workflow"
    VARIANT_TITLE = "C — Workflow (Master-Detail)"
    VARIANT_HINT = (
        "Schmale Lagerliste links. Rechts oben Verkaufsformular, "
        "unten Historie — Fokus auf Auswahl → Verkauf → Historie."
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        content, layout = page_content_widget()
        layout.addWidget(page_title(tr("sales.title")))
        layout.addWidget(section_accent(tr("sales.section.main")))
        layout.addLayout(hud_divider())
        layout.addWidget(components.build_kpi_row())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("pageSplit")
        splitter.setHandleWidth(14)
        splitter.setChildrenCollapsible(False)

        master = QWidget()
        master.setMinimumWidth(280)
        master_layout = QVBoxLayout(master)
        master_layout.setContentsMargins(0, 0, 16, 0)
        master_layout.setSpacing(8)
        master_layout.addWidget(components.build_inventory_block(compact=True))
        master_layout.addStretch()

        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(16, 0, 0, 0)
        detail_layout.setSpacing(12)
        detail_layout.addWidget(components.build_sale_form_block())
        detail_layout.addWidget(components.build_history_block(compact=True))
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
