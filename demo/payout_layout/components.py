"""Wiederverwendbare Demo-Bausteine für die Auszahlungsseite."""

from __future__ import annotations

from PySide6.QtCore import Qt
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
from demo.payout_layout import mock_data
from ui.page_layout import (
    add_form_field,
    empty_info_panel,
    hud_divider,
    info_panel,
    page_panel,
    primary_button,
    subsection_title,
)
from ui.table_utils import (
    configure_editable_table,
    configure_mobiglas_table,
    finalize_system_list_table,
    finalize_table_columns,
)


def build_kpi_row() -> QWidget:
    """Kompakte KPI-Zeile statt großem Summary-Block."""
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(12)

    pending = QFrame()
    pending.setObjectName("financeSummaryPanel")
    pending_layout = QVBoxLayout(pending)
    pending_layout.setContentsMargins(14, 10, 14, 10)
    pending_layout.setSpacing(4)
    pending_layout.addWidget(QLabel("Ausstehende Verkäufe"))
    pending_value = QLabel(str(mock_data.PENDING_COUNT))
    pending_value.setObjectName("statValue")
    pending_layout.addWidget(pending_value)

    paid = QFrame()
    paid.setObjectName("financeSummaryPanel")
    paid_layout = QVBoxLayout(paid)
    paid_layout.setContentsMargins(14, 10, 14, 10)
    paid_layout.setSpacing(4)
    paid_layout.addWidget(QLabel("Ausgezahlt gesamt"))
    paid_value = QLabel(f"{format_number(mock_data.PAID_TOTAL)} aUEC")
    paid_value.setObjectName("statValue")
    paid_layout.addWidget(paid_value)

    layout.addWidget(pending, 1)
    layout.addWidget(paid, 1)
    return row


def build_unpaid_block(*, compact: bool = False) -> tuple[QWidget, QTableWidget]:
    panel, panel_layout = page_panel()
    panel_layout.setContentsMargins(12, 12, 12, 12)
    panel_layout.setSpacing(8)
    panel_layout.addWidget(
        subsection_title(tr("payout.section.unpaid"))
    )
    panel_layout.addLayout(hud_divider())

    table = QTableWidget()
    table.setColumnCount(5)
    table.setHorizontalHeaderLabels([
        tr("payout.table.no"),
        tr("payout.table.date"),
        tr("payout.table.location"),
        tr("payout.table.revenue"),
        tr("payout.table.seller"),
    ])
    configure_mobiglas_table(table, "dataTable")

    empty_panel = empty_info_panel(
        tr("payout.unpaid.empty"),
        "assets/images/icons/info.svg",
    )

    if mock_data.UNPAID_SALES:
        table.setRowCount(len(mock_data.UNPAID_SALES))
        for row, sale in enumerate(mock_data.UNPAID_SALES):
            values = (
                str(sale.number),
                sale.date,
                sale.location,
                sale.revenue,
                sale.seller,
            )
            for col, value in enumerate(values):
                table.setItem(row, col, QTableWidgetItem(value))
        finalize_table_columns(table, stretch_column=2)
        empty_panel.hide()
    else:
        table.hide()
        empty_panel.show()

    panel_layout.addWidget(table)
    panel_layout.addWidget(empty_panel)

    if compact:
        finalize_system_list_table(
            table,
            stretch_column=2,
            max_visible_rows=4,
        )

    return panel, table


def build_calculate_block() -> QWidget:
    panel, panel_layout = info_panel()
    panel_layout.addWidget(
        subsection_title(tr("payout.section.calculate"))
    )
    panel_layout.addLayout(hud_divider())

    sale_combo = QComboBox()
    sale_combo.addItem(tr("payout.sale.placeholder"))

    notes_input = QLineEdit()
    notes_input.setPlaceholderText(tr("payout.placeholder.notes"))

    calc_info = QLabel(tr("payout.calc.placeholder"))
    calc_info.setObjectName("payoutStatusPanel")
    calc_info.setWordWrap(True)

    payout_table = QTableWidget()
    payout_table.setColumnCount(2)
    payout_table.setHorizontalHeaderLabels([
        tr("payout.table.crew_member"),
        tr("payout.table.amount"),
    ])
    configure_editable_table(payout_table, "editableTable")
    payout_table.setRowCount(len(mock_data.CREW_MEMBERS))
    for row, member in enumerate(mock_data.CREW_MEMBERS):
        payout_table.setItem(row, 0, QTableWidgetItem(member))
        payout_table.setItem(row, 1, QTableWidgetItem(""))
    finalize_table_columns(payout_table, stretch_column=1)
    finalize_system_list_table(
        payout_table,
        stretch_column=1,
        max_visible_rows=5,
    )

    add_form_field(panel_layout, tr("payout.label.sale"), sale_combo)
    add_form_field(panel_layout, tr("payout.label.notes"), notes_input)
    panel_layout.addWidget(calc_info)
    panel_layout.addWidget(payout_table)

    button_row = QHBoxLayout()
    button_row.setSpacing(12)
    button_row.addWidget(primary_button(tr("payout.button.save")))
    button_row.addStretch()
    panel_layout.addLayout(button_row)

    return panel


def build_crew_totals_block(*, compact: bool = False) -> QWidget:
    panel, panel_layout = page_panel()
    panel_layout.setContentsMargins(12, 12, 12, 12)
    panel_layout.setSpacing(8)
    panel_layout.addWidget(
        subsection_title(tr("payout.section.crew_totals"))
    )
    panel_layout.addLayout(hud_divider())

    table = QTableWidget()
    table.setColumnCount(2)
    table.setHorizontalHeaderLabels([
        tr("payout.table.date_or_crew"),
        tr("payout.table.amount"),
    ])
    configure_mobiglas_table(table, "dataTable", selectable=False)
    table.setRowCount(len(mock_data.CREW_PAYOUTS))

    for row, payout in enumerate(mock_data.CREW_PAYOUTS):
        label = f"> {payout.date} {payout.location}"
        table.setItem(row, 0, QTableWidgetItem(label))
        amount_item = QTableWidgetItem(
            f"{format_number(payout.amount)} aUEC"
        )
        amount_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        table.setItem(row, 1, amount_item)

    panel_layout.addWidget(table)
    finalize_table_columns(table, stretch_column=0)
    finalize_system_list_table(
        table,
        stretch_column=0,
        max_visible_rows=6 if compact else 8,
    )
    return panel


def build_summary_block() -> QWidget:
    """Original: ein breiter Summary-Block wie in der Live-Seite."""
    panel = QFrame()
    panel.setObjectName("financeSummaryPanel")
    layout = QVBoxLayout(panel)
    layout.setSpacing(8)
    layout.addWidget(subsection_title(tr("payout.section.summary")))
    layout.addLayout(hud_divider())
    summary = QLabel(
        tr(
            "payout.summary",
            count=mock_data.PENDING_COUNT,
            total=format_number(mock_data.PAID_TOTAL),
        )
    )
    summary.setObjectName("statValue")
    layout.addWidget(summary)
    return panel
