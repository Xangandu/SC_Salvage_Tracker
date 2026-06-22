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
)

from database.access import get_database
from config.dates import (
    format_date,
    normalize_date_input,
    today_display,
)
from config.materials import material_label
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
    subsection_title,
    add_form_field,
    info_panel,
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

        layout.addWidget(page_title("VERKÄUFE"))
        layout.addWidget(
            section_accent("◆ VERFÜGBARER LAGERBESTAND")
        )

        self.inventory_container = QVBoxLayout()
        inventory_host = QWidget()
        inventory_host.setLayout(self.inventory_container)
        layout.addWidget(inventory_host)

        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(2)
        self.inventory_table.setHorizontalHeaderLabels([
            "Material",
            "Verfügbar (SCU)",
        ])
        configure_mobiglas_table(
            self.inventory_table,
            "dataTable",
        )
        self.inventory_table.setMinimumHeight(160)

        self.inventory_empty_panel = empty_info_panel(
            "Kein verkaufbares Material im Lager.",
            "assets/images/icons/info.svg",
        )
        self.inventory_container.addWidget(
            self.inventory_table
        )
        self.inventory_container.addWidget(
            self.inventory_empty_panel
        )
        self.inventory_empty_panel.hide()

        form_panel, form_layout = info_panel()
        form_layout.addWidget(
            subsection_title("◆ NEUER VERKAUF")
        )

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText(
            "z.B. Area18"
        )

        self.sale_date_input = QLineEdit()
        self.sale_date_input.setPlaceholderText(
            "TT.MM.JJJJ"
        )
        self.sale_date_input.setText(today_display())

        self.material_combo = QComboBox()

        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText(
            "Menge in SCU"
        )

        self.unit_price_input = QLineEdit()
        self.unit_price_input.setPlaceholderText(
            "Preis pro SCU (aUEC)"
        )

        self.total_label = QLabel("Gesamt: 0 aUEC")
        self.total_label.setObjectName("profitLabel")

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText(
            "Notiz (optional)"
        )

        self.save_button = primary_button(
            "Verkauf speichern"
        )

        for label_text, widget in [
            ("Verkaufsort", self.location_input),
            ("Datum", self.sale_date_input),
            ("Material", self.material_combo),
            ("Menge (SCU)", self.quantity_input),
            ("Stückpreis (aUEC)", self.unit_price_input),
            ("Notiz", self.notes_input),
        ]:
            add_form_field(
                form_layout,
                label_text,
                widget,
            )

        form_layout.addWidget(self.total_label)
        form_layout.addWidget(self.save_button)
        layout.addWidget(form_panel)

        profit_panel = QFrame()
        profit_panel.setObjectName("financeSummaryPanel")
        profit_layout = QVBoxLayout(profit_panel)
        profit_layout.setSpacing(8)

        profit_layout.addWidget(
            subsection_title("◆ FINANZÜBERSICHT")
        )
        profit_layout.addLayout(hud_divider())

        self.revenue_summary_label = QLabel(
            "Gesamtumsatz (alle Verkäufe): 0 aUEC"
        )
        self.revenue_summary_label.setObjectName(
            "statValue"
        )

        self.costs_summary_label = QLabel(
            "Gesamtkosten: 0 aUEC"
        )
        self.costs_summary_label.setObjectName("statLabel")

        self.profit_summary_label = QLabel(
            "Gewinn: 0 aUEC"
        )
        self.profit_summary_label.setObjectName(
            "profitLabel"
        )

        profit_layout.addWidget(
            self.revenue_summary_label
        )
        profit_layout.addWidget(
            self.costs_summary_label
        )
        profit_layout.addWidget(
            self.profit_summary_label
        )
        layout.addWidget(profit_panel)

        layout.addWidget(
            section_accent("◆ VERKAUFSHISTORIE")
        )

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
            "historyTable",
        )
        self.history_table.setMinimumHeight(220)

        history_actions = QHBoxLayout()
        history_actions.setSpacing(12)
        self.void_sale_button = _secondary_button(
            "Verkauf stornieren"
        )
        self.void_sale_button.clicked.connect(
            self.void_selected_sale
        )
        history_actions.addWidget(self.void_sale_button)
        history_actions.addStretch()
        layout.addWidget(self.history_table)
        layout.addLayout(history_actions)

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
                        f"{quantity:,.1f}"
                    ),
                )

                combo_label = (
                    f"{label} — {quantity:,.1f} SCU"
                )
                self.material_combo.addItem(
                    combo_label,
                    code,
                )

            finalize_table_columns(
                self.inventory_table,
                stretch_column=0,
            )

        self.material_combo.blockSignals(False)

    def load_history(self):
        sales = self.db.get_sales_history()

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
                    f"{sale['total_amount']:,.0f} aUEC"
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

    def update_profit_summary(self):
        revenue = self.db.get_total_sales_value()
        costs = self.db.get_global_total_costs()
        profit = revenue - costs

        self.revenue_summary_label.setText(
            f"Gesamtumsatz (alle Verkäufe): "
            f"{revenue:,.0f} aUEC"
        )
        self.costs_summary_label.setText(
            f"Gesamtkosten: {costs:,.0f} aUEC"
        )
        self.profit_summary_label.setText(
            f"Gewinn: {profit:,.0f} aUEC"
        )

    def update_line_total(self):
        try:
            quantity = float(
                self.quantity_input.text() or 0
            )
            unit_price = float(
                self.unit_price_input.text() or 0
            )
        except ValueError:
            self.total_label.setText(
                "Gesamt: — aUEC"
            )
            return

        total = quantity * unit_price
        self.total_label.setText(
            f"Gesamt: {total:,.0f} aUEC"
        )

    def save_sale(self):
        location = self.location_input.text().strip()

        if not location:
            QMessageBox.warning(
                self,
                "Fehler",
                "Bitte einen Verkaufsort angeben.",
            )
            return

        try:
            sale_date = normalize_date_input(
                self.sale_date_input.text()
            )
        except ValueError as error:
            QMessageBox.warning(
                self,
                "Fehler",
                str(error),
            )
            return

        material_code = self.material_combo.currentData()

        if material_code is None:
            QMessageBox.warning(
                self,
                "Fehler",
                "Kein Material im Lager verfügbar.",
            )
            return

        try:
            quantity = float(
                self.quantity_input.text()
            )
            unit_price = float(
                self.unit_price_input.text()
            )
        except ValueError:
            QMessageBox.warning(
                self,
                "Fehler",
                "Bitte gültige Menge und Preis eingeben.",
            )
            return

        if quantity <= 0:
            QMessageBox.warning(
                self,
                "Fehler",
                "Die Verkaufsmenge muss größer als 0 sein.",
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
                "Verkauf nicht möglich",
                str(error),
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Verkauf konnte nicht gespeichert werden:\n\n{error}",
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
            "Verkauf gespeichert",
            "Der Verkauf wurde im Lager verbucht.",
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
                "Hinweis",
                "Bitte zuerst einen Verkauf in der "
                "Historie auswählen.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Verkauf stornieren",
            f"Verkauf #{sale_id} wirklich stornieren?\n\n"
            "Die verkaufte Menge wird dem Lager "
            "zurückgebucht. "
            "Nicht möglich, wenn bereits ausgezahlt.",
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
                "Nicht möglich",
                str(error),
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Stornierung fehlgeschlagen:\n\n{error}",
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
            "Storniert",
            f"Verkauf #{sale_id} wurde storniert.",
        )
