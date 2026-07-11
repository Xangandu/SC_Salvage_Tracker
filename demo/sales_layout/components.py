"""Wiederverwendbare Demo-Bausteine für die Verkaufsseite."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.i18n import format_number, tr
from demo.sales_layout import mock_data
from ui.page_layout import (
    add_form_field,
    empty_info_panel,
    hud_divider,
    info_panel,
    page_panel,
    primary_button,
    subsection_title,
)
from ui.system_location_picker import SystemLocationPicker
from ui.table_utils import (
    configure_mobiglas_table,
    finalize_system_list_table,
)


def _secondary_button(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("secondaryAction")
    return button


def build_kpi_row() -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(12)

    for title_key, value, object_name in (
        ("sales.kpi.revenue", mock_data.REVENUE_TOTAL, "statValue"),
        ("sales.kpi.costs", mock_data.COSTS_TOTAL, "statLabel"),
        ("sales.kpi.profit", mock_data.PROFIT_TOTAL, "profitLabel"),
    ):
        panel = QFrame()
        panel.setObjectName("financeSummaryPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(14, 10, 14, 10)
        panel_layout.setSpacing(4)
        panel_layout.addWidget(QLabel(tr(title_key)))
        value_label = QLabel(f"{format_number(value)} aUEC")
        value_label.setObjectName(object_name)
        panel_layout.addWidget(value_label)
        layout.addWidget(panel, 1)

    return row


def build_finance_block() -> QWidget:
    panel = QFrame()
    panel.setObjectName("financeSummaryPanel")
    layout = QVBoxLayout(panel)
    layout.setSpacing(8)
    layout.addWidget(subsection_title(tr("sales.section.finance")))
    layout.addLayout(hud_divider())

    for title_key, value, object_name in (
        ("sales.summary.revenue", mock_data.REVENUE_TOTAL, "statValue"),
        ("sales.summary.costs", mock_data.COSTS_TOTAL, "statLabel"),
        ("sales.summary.profit", mock_data.PROFIT_TOTAL, "profitLabel"),
    ):
        label = QLabel(
            tr(title_key, amount=format_number(value))
        )
        label.setObjectName(object_name)
        layout.addWidget(label)

    return panel


def build_inventory_block(*, compact: bool = False) -> QWidget:
    panel, panel_layout = page_panel()
    panel_layout.setContentsMargins(12, 12, 12, 12)
    panel_layout.setSpacing(8)
    panel_layout.addWidget(
        subsection_title(tr("sales.section.inventory"))
    )
    panel_layout.addLayout(hud_divider())

    table = QTableWidget()
    table.setColumnCount(2)
    table.setHorizontalHeaderLabels([
        tr("sales.table.material"),
        tr("sales.table.available_scu"),
    ])
    configure_mobiglas_table(table, "dataTable")

    if mock_data.INVENTORY:
        table.setRowCount(len(mock_data.INVENTORY))
        for row, entry in enumerate(mock_data.INVENTORY):
            table.setItem(row, 0, QTableWidgetItem(entry.material))
            table.setItem(
                row,
                1,
                QTableWidgetItem(format_number(entry.quantity, 0)),
            )
        finalize_system_list_table(
            table,
            stretch_column=0,
            max_visible_rows=4 if compact else 6,
        )
        panel_layout.addWidget(table)
    else:
        panel_layout.addWidget(
            empty_info_panel(
                tr("sales.inventory.empty"),
                "assets/images/icons/info.svg",
            )
        )

    return panel


def build_sale_form_block() -> QWidget:
    panel, panel_layout = info_panel()
    panel_layout.addWidget(
        subsection_title(tr("sales.section.new"))
    )
    panel_layout.addLayout(hud_divider())

    location_picker = SystemLocationPicker()
    panel_layout.addWidget(location_picker)

    uex_status = QLabel(tr("sales.uex.loaded"))
    uex_status.setObjectName("mutedLabel")
    uex_status.setWordWrap(True)
    panel_layout.addWidget(uex_status)

    material_combo = QComboBox()
    for entry in mock_data.INVENTORY:
        material_combo.addItem(
            tr(
                "sales.material.combo",
                material=entry.material,
                quantity=format_number(entry.quantity, 0),
            )
        )

    total_label = QLabel(
        tr("sales.line_total", total=format_number(0))
    )
    total_label.setObjectName("profitLabel")

    for label_text, widget in [
        (tr("sales.label.date"), QLineEdit()),
        (tr("sales.label.material"), material_combo),
        (tr("sales.label.quantity"), QLineEdit()),
        (tr("sales.label.unit_price"), QLineEdit()),
        (tr("sales.label.notes"), QLineEdit()),
    ]:
        add_form_field(panel_layout, label_text, widget)

    panel_layout.addWidget(total_label)
    panel_layout.addWidget(primary_button(tr("sales.button.save")))
    return panel


def build_history_block(*, compact: bool = False) -> QWidget:
    panel, panel_layout = page_panel()
    panel_layout.setContentsMargins(12, 12, 12, 12)
    panel_layout.setSpacing(8)
    panel_layout.addWidget(
        subsection_title(tr("sales.section.history"))
    )
    panel_layout.addLayout(hud_divider())

    table = QTableWidget()
    table.setColumnCount(6)
    table.setHorizontalHeaderLabels([
        tr("sales.history.no"),
        tr("sales.history.date"),
        tr("sales.history.location"),
        tr("sales.history.materials"),
        tr("sales.history.revenue"),
        tr("sales.history.seller"),
    ])
    configure_mobiglas_table(table, "historyTable")
    table.setRowCount(len(mock_data.HISTORY))

    for row, sale in enumerate(mock_data.HISTORY):
        values = (
            f"#{sale.number}",
            sale.date,
            sale.location,
            sale.materials,
            f"{format_number(sale.revenue)} aUEC",
            sale.seller,
        )
        for col, value in enumerate(values):
            table.setItem(row, col, QTableWidgetItem(value))

    panel_layout.addWidget(table)
    finalize_system_list_table(
        table,
        stretch_column=3,
        max_visible_rows=8 if compact else 10,
    )

    actions = QHBoxLayout()
    actions.setSpacing(12)
    actions.addWidget(_secondary_button(tr("sales.button.void")))
    actions.addStretch()
    panel_layout.addLayout(actions)
    return panel
