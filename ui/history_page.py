from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
)

from database.access import get_database
from config.dates import format_date
from config.materials import material_label
from config.strings_de import format_number_de
from config.permissions import apply_widget_permissions
from ui.table_utils import (
    configure_mobiglas_table,
    finalize_table_columns,
)
from ui.page_layout import (
    build_page_scroll,
    page_content_widget,
    page_title,
    section_accent,
    page_panel,
    empty_info_panel,
    hud_divider,
)


class HistoryPage(QWidget):

    def __init__(self):
        super().__init__()

        content, layout = page_content_widget()
        layout.addWidget(page_title("VERKAUFSHISTORIE"))
        layout.addWidget(
            section_accent("◆ ALLE VERKÄUFE")
        )
        layout.addLayout(hud_divider())

        table_panel, table_layout = page_panel()
        table_layout.setContentsMargins(12, 12, 12, 12)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Nr.",
            "Datum",
            "Ort",
            "Materialien",
            "Umsatz",
            "Verkäufer",
        ])
        configure_mobiglas_table(
            self.history_table,
            "dataTable",
        )
        self.history_table.setMinimumHeight(400)

        self.history_empty_panel = empty_info_panel(
            "Noch keine Verkäufe erfasst.",
            "assets/images/icons/info.svg",
        )

        table_layout.addWidget(self.history_table)
        table_layout.addWidget(self.history_empty_panel)
        self.history_empty_panel.hide()
        layout.addWidget(table_panel)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(build_page_scroll(content))

        self.load_history()

    def apply_permissions(self, user, page_name="history"):
        apply_widget_permissions(self, user, page_name)

    def refresh_history(self):
        self.load_history()

    def load_history(self):
        db = get_database()
        sales = db.get_sales_history()
        has_sales = len(sales) > 0

        self.history_table.setVisible(has_sales)
        self.history_empty_panel.setVisible(not has_sales)
        self.history_table.setRowCount(len(sales))

        for row, sale in enumerate(sales):
            items_text = ", ".join(
                f"{item['quantity']:g} SCU "
                f"{material_label(item['material_code'])}"
                for item in sale["items"]
            )

            self.history_table.setItem(
                row,
                0,
                QTableWidgetItem(f"#{sale['id']}"),
            )
            self.history_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    format_date(sale["sale_date"])
                ),
            )
            self.history_table.setItem(
                row,
                2,
                QTableWidgetItem(sale["location"]),
            )
            self.history_table.setItem(
                row,
                3,
                QTableWidgetItem(items_text or "—"),
            )
            self.history_table.setItem(
                row,
                4,
                QTableWidgetItem(
                    format_number_de(sale['total_amount'])
                ),
            )
            self.history_table.setItem(
                row,
                5,
                QTableWidgetItem(sale["created_by"]),
            )

        finalize_table_columns(
            self.history_table,
            stretch_column=3,
        )
