from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
)

from database.access import get_database
from config.dates import (
    format_date,
    normalize_date_input,
    today_display,
)
from config.materials import material_label
from config.i18n import tr, format_number
from config.strings_de import parse_number_de
from config.permissions import apply_widget_permissions
from ui.sales_uex_bridge import SalesUexBridge
from ui.system_location_picker import SystemLocationPicker
from ui.table_utils import (
    configure_mobiglas_table,
    finalize_system_list_table,
)
from ui.page_split_persistence import (
    SETTING_SALES_PAGE_SPLIT,
    bind_page_split_persistence,
)
from ui.page_layout import (
    build_page_scroll,
    page_content_widget,
    page_title,
    section_accent,
    subsection_title,
    add_form_field,
    info_panel,
    page_panel,
    primary_button,
    empty_info_panel,
    hud_divider,
)


def _secondary_button(text):
    button = QPushButton(text)
    button.setObjectName("secondaryAction")
    return button


class SalesPage(QWidget):

    def __init__(self):
        super().__init__()

        self.db = get_database()

        content, layout = page_content_widget()

        layout.addWidget(page_title(tr("sales.title")))
        layout.addWidget(
            section_accent(tr("sales.section.main"))
        )
        layout.addLayout(hud_divider())

        kpi_row = QWidget()
        kpi_layout = QHBoxLayout(kpi_row)
        kpi_layout.setContentsMargins(0, 0, 0, 0)
        kpi_layout.setSpacing(12)

        revenue_panel = QFrame()
        revenue_panel.setObjectName("financeSummaryPanel")
        revenue_layout = QVBoxLayout(revenue_panel)
        revenue_layout.setContentsMargins(14, 10, 14, 10)
        revenue_layout.setSpacing(4)
        revenue_layout.addWidget(QLabel(tr("sales.kpi.revenue")))
        self.revenue_summary_label = QLabel(
            f"{format_number(0)} aUEC"
        )
        self.revenue_summary_label.setObjectName("statValue")
        revenue_layout.addWidget(self.revenue_summary_label)

        costs_panel = QFrame()
        costs_panel.setObjectName("financeSummaryPanel")
        costs_layout = QVBoxLayout(costs_panel)
        costs_layout.setContentsMargins(14, 10, 14, 10)
        costs_layout.setSpacing(4)
        costs_layout.addWidget(QLabel(tr("sales.kpi.costs")))
        self.costs_summary_label = QLabel(
            f"{format_number(0)} aUEC"
        )
        self.costs_summary_label.setObjectName("statLabel")
        costs_layout.addWidget(self.costs_summary_label)

        profit_panel = QFrame()
        profit_panel.setObjectName("financeSummaryPanel")
        profit_layout = QVBoxLayout(profit_panel)
        profit_layout.setContentsMargins(14, 10, 14, 10)
        profit_layout.setSpacing(4)
        profit_layout.addWidget(QLabel(tr("sales.kpi.profit")))
        self.profit_summary_label = QLabel(
            f"{format_number(0)} aUEC"
        )
        self.profit_summary_label.setObjectName("profitLabel")
        profit_layout.addWidget(self.profit_summary_label)

        kpi_layout.addWidget(revenue_panel, 1)
        kpi_layout.addWidget(costs_panel, 1)
        kpi_layout.addWidget(profit_panel, 1)
        layout.addWidget(kpi_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("pageSplit")
        splitter.setHandleWidth(14)
        splitter.setChildrenCollapsible(False)

        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 16, 0)
        left_layout.setSpacing(12)

        inventory_panel, inventory_layout = page_panel()
        inventory_layout.setContentsMargins(12, 12, 12, 12)
        inventory_layout.setSpacing(8)
        inventory_layout.addWidget(
            subsection_title(tr("sales.section.inventory"))
        )
        inventory_layout.addLayout(hud_divider())

        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(2)
        self.inventory_table.setHorizontalHeaderLabels([
            tr("sales.table.material"),
            tr("sales.table.available_scu"),
        ])
        configure_mobiglas_table(
            self.inventory_table,
            "dataTable",
        )
        self.inventory_empty_panel = empty_info_panel(
            tr("sales.inventory.empty"),
            "assets/images/icons/info.svg",
        )
        inventory_layout.addWidget(self.inventory_table)
        inventory_layout.addWidget(self.inventory_empty_panel)
        self.inventory_empty_panel.hide()
        left_layout.addWidget(inventory_panel)

        form_panel, form_layout = info_panel()
        form_layout.addWidget(
            subsection_title(tr("sales.section.new"))
        )
        form_layout.addLayout(hud_divider())

        self.location_picker = SystemLocationPicker()
        form_layout.addWidget(self.location_picker)

        self.uex_status_label = QLabel("")
        self.uex_status_label.setObjectName("mutedLabel")
        self.uex_status_label.setWordWrap(True)
        form_layout.addWidget(self.uex_status_label)

        self.sale_date_input = QLineEdit()
        self.sale_date_input.setPlaceholderText(
            tr("sales.placeholder.date")
        )
        self.sale_date_input.setText(today_display())

        self.material_combo = QComboBox()

        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText(
            tr("sales.placeholder.quantity")
        )

        self.unit_price_input = QLineEdit()
        self.unit_price_input.setPlaceholderText(
            tr("sales.placeholder.unit_price")
        )

        self.total_label = QLabel(
            tr("sales.line_total", total=format_number(0))
        )
        self.total_label.setObjectName("profitLabel")

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText(
            tr("sales.placeholder.notes")
        )

        self.save_button = primary_button(
            tr("sales.button.save")
        )

        for label_text, widget in [
            (tr("sales.label.date"), self.sale_date_input),
            (tr("sales.label.material"), self.material_combo),
            (tr("sales.label.quantity"), self.quantity_input),
            (tr("sales.label.unit_price"), self.unit_price_input),
            (tr("sales.label.notes"), self.notes_input),
        ]:
            add_form_field(
                form_layout,
                label_text,
                widget,
            )

        form_layout.addWidget(self.total_label)
        form_layout.addWidget(self.save_button)
        left_layout.addWidget(form_panel)
        left_layout.addStretch()

        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(16, 0, 0, 0)
        right_layout.setSpacing(12)

        history_panel, history_layout = page_panel()
        history_layout.setContentsMargins(12, 12, 12, 12)
        history_layout.setSpacing(8)
        history_layout.addWidget(
            subsection_title(tr("sales.section.history"))
        )
        history_layout.addLayout(hud_divider())

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            tr("sales.history.no"),
            tr("sales.history.date"),
            tr("sales.history.location"),
            tr("sales.history.materials"),
            tr("sales.history.revenue"),
            tr("sales.history.seller"),
        ])
        configure_mobiglas_table(
            self.history_table,
            "historyTable",
        )

        self.void_sale_button = _secondary_button(
            tr("sales.button.void")
        )
        self.void_sale_button.clicked.connect(
            self.void_selected_sale
        )

        history_actions = QHBoxLayout()
        history_actions.setSpacing(12)
        history_actions.addWidget(self.void_sale_button)
        history_actions.addStretch()

        history_layout.addWidget(self.history_table)
        history_layout.addLayout(history_actions)
        right_layout.addWidget(history_panel)
        right_layout.addStretch()

        splitter.addWidget(left_column)
        splitter.addWidget(right_column)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([620, 420])
        layout.addWidget(splitter, 1)

        bind_page_split_persistence(
            splitter,
            self.db,
            SETTING_SALES_PAGE_SPLIT,
            default_sizes=[620, 420],
        )

        layout.addStretch()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(build_page_scroll(content))

        self.quantity_input.textChanged.connect(
            self.update_line_total
        )
        self.unit_price_input.textChanged.connect(
            self.update_line_total
        )
        self.save_button.clicked.connect(
            self.save_sale
        )

        self._uex_bridge = SalesUexBridge(
            location_picker=self.location_picker,
            unit_price_input=self.unit_price_input,
            material_combo=self.material_combo,
            status_label=self.uex_status_label,
        )

        self.load_data()

    def apply_permissions(
        self,
        user,
        page_name="sales",
    ):
        apply_widget_permissions(
            self,
            user,
            page_name,
        )

    def load_data(self):
        self.load_inventory()
        self.load_history()
        self.update_profit_summary()
        self.update_line_total()

    def load_inventory(self):
        inventory = (
            self.db.get_available_storage_inventory()
        )

        self.material_combo.blockSignals(True)
        self.material_combo.clear()

        if not inventory:
            self.inventory_table.hide()
            self.inventory_empty_panel.show()
        else:
            self.inventory_empty_panel.hide()
            self.inventory_table.show()
            self.inventory_table.setRowCount(
                len(inventory)
            )

            for row, entry in enumerate(inventory):
                code = entry["material_code"]
                label = material_label(code)
                quantity = entry["quantity"]

                self.inventory_table.setItem(
                    row,
                    0,
                    QTableWidgetItem(label),
                )
                self.inventory_table.setItem(
                    row,
                    1,
                    QTableWidgetItem(
                        format_number(quantity, 0)
                    ),
                )

                combo_label = tr(
                    "sales.material.combo",
                    material=label,
                    quantity=format_number(quantity, 0),
                )
                self.material_combo.addItem(
                    combo_label,
                    code,
                )

            finalize_system_list_table(
                self.inventory_table,
                stretch_column=0,
                max_visible_rows=5,
            )

        self.material_combo.blockSignals(False)

    def load_history(self):
        sales = self.db.get_sales_history()

        self.history_table.setRowCount(len(sales))

        for row, sale in enumerate(sales):
            items_text = ", ".join(
                tr(
                    "sales.history.item_line",
                    quantity=format_number(item["quantity"], 0),
                    material=material_label(item["material_code"]),
                )
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
                    f"{format_number(sale['total_amount'])} aUEC"
                ),
            )
            self.history_table.setItem(
                row,
                5,
                QTableWidgetItem(sale["created_by"]),
            )

        finalize_system_list_table(
            self.history_table,
            stretch_column=3,
            max_visible_rows=10,
        )

    def update_profit_summary(self):
        revenue = self.db.get_total_sales_value()
        costs = self.db.get_global_total_costs()
        profit = revenue - costs

        self.revenue_summary_label.setText(
            f"{format_number(revenue)} aUEC"
        )
        self.costs_summary_label.setText(
            f"{format_number(costs)} aUEC"
        )
        self.profit_summary_label.setText(
            f"{format_number(profit)} aUEC"
        )

    def update_line_total(self):
        quantity = parse_number_de(self.quantity_input.text(), default=0)
        unit_price = parse_number_de(self.unit_price_input.text(), default=0)
        if quantity is None or unit_price is None:
            self.total_label.setText(
                tr("sales.line_total.invalid")
            )
            return

        total = quantity * unit_price
        self.total_label.setText(
            tr(
                "sales.line_total",
                total=format_number(total),
            )
        )

    def save_sale(self):
        location = self.location_picker.location_label()

        if not self.location_picker.is_selected():
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("error.location.not_selected"),
            )
            return

        try:
            sale_date = normalize_date_input(
                self.sale_date_input.text()
            )
        except ValueError as error:
            QMessageBox.warning(
                self,
                tr("common.error"),
                str(error),
            )
            return

        material_code = self.material_combo.currentData()

        if material_code is None:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("sales.msg.no_material"),
            )
            return

        quantity = parse_number_de(self.quantity_input.text())
        unit_price = parse_number_de(self.unit_price_input.text())
        if quantity is None or unit_price is None:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("sales.msg.invalid_quantity_price"),
            )
            return

        if quantity <= 0:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("sales.msg.quantity_positive"),
            )
            return

        notes = self.notes_input.text().strip() or None

        try:
            self.db.record_storage_sale(
                location,
                sale_date,
                material_code,
                quantity,
                unit_price,
                notes=notes,
            )
        except ValueError as error:
            QMessageBox.warning(
                self,
                tr("sales.msg.not_possible.title"),
                str(error),
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                tr("common.error"),
                tr("sales.msg.save_failed", error=error),
            )
            return

        self.quantity_input.clear()
        self.unit_price_input.clear()
        self.notes_input.clear()
        self.update_line_total()

        self.load_data()

        main_window = self.window()

        if hasattr(
            main_window,
            "dashboard_page"
        ):
            main_window.dashboard_page.refresh_dashboard()

        QMessageBox.information(
            self,
            tr("sales.msg.saved.title"),
            tr("sales.msg.saved.message"),
        )

    def _selected_history_sale_id(self):
        row = self.history_table.currentRow()

        if row < 0:
            return None

        item = self.history_table.item(row, 0)

        if not item:
            return None

        return int(item.text().lstrip("#"))

    def void_selected_sale(self):
        sale_id = self._selected_history_sale_id()

        if sale_id is None:
            QMessageBox.warning(
                self,
                tr("common.hint"),
                tr("sales.msg.no_selection"),
            )
            return

        answer = QMessageBox.question(
            self,
            tr("sales.msg.void_confirm.title"),
            tr(
                "sales.msg.void_confirm.message",
                sale_id=sale_id,
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        try:
            self.db.void_sale(sale_id)
        except ValueError as error:
            QMessageBox.warning(
                self,
                tr("common.not_possible"),
                str(error),
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                tr("common.error"),
                tr("sales.msg.void_failed", error=error),
            )
            return

        self.load_data()

        main_window = self.window()

        if hasattr(main_window, "refresh_all"):
            main_window.refresh_all()
        elif hasattr(main_window, "dashboard_page"):
            main_window.dashboard_page.refresh_dashboard()

        QMessageBox.information(
            self,
            tr("sales.msg.voided.title"),
            tr(
                "sales.msg.voided.message",
                sale_id=sale_id,
            ),
        )
