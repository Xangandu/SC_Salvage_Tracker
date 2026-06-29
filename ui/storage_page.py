from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QPushButton,
    QCheckBox,
    QFrame,
    QDialog,
)

from database.access import get_database
from database.stockpile_repository import StockpileRepository
from config.dates import format_datetime
from config.materials import (
    RAW_CM_MATERIAL_CODES,
    REFINED_SELLABLE_CODES,
    material_label,
)
from config.storage_idle import (
    DEFAULT_RESERVE_TAG,
    IDLE_WARNING_DAYS,
    format_relative_activity,
)
from config.i18n import tr, format_number, format_scu, format_scu_delta
from config.strings_de import parse_number_de
from config.permissions import apply_widget_permissions
from ui.system_location_picker import SystemLocationPicker
from ui.mobiglas_input_dialog import MobiglasTextInputDialog
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
    form_label,
    info_panel,
    primary_button,
    empty_info_panel,
)


STORAGE_MATERIAL_CODES = (
    *REFINED_SELLABLE_CODES,
    *RAW_CM_MATERIAL_CODES,
)


def _secondary_button(text):
    button = QPushButton(text)
    button.setObjectName("secondaryAction")
    return button


class StoragePage(QWidget):

    idle_warnings_changed = Signal(int)

    def __init__(self):
        super().__init__()

        self.db = get_database()
        self._stockpile_rows: list[dict] = []
        self._idle_banner_collapsed = False

        content, layout = page_content_widget()

        layout.addWidget(page_title(tr("storage.title")))

        self.idle_banner_host = QFrame()
        self.idle_banner_host.setObjectName("infoPanel")
        idle_banner_layout = QVBoxLayout(self.idle_banner_host)
        idle_banner_layout.setContentsMargins(12, 12, 12, 12)
        idle_banner_layout.setSpacing(8)

        idle_header = QHBoxLayout()
        idle_header.setSpacing(12)
        self.idle_banner_title = QLabel()
        self.idle_banner_title.setObjectName("warningBannerTitle")
        self.idle_banner_title.setWordWrap(True)
        idle_header.addWidget(self.idle_banner_title, 1)
        self.idle_banner_toggle = _secondary_button(
            tr("storage.idle.banner.collapse")
        )
        idle_header.addWidget(self.idle_banner_toggle)
        idle_banner_layout.addLayout(idle_header)

        self.idle_banner_body = QWidget()
        idle_body_layout = QVBoxLayout(self.idle_banner_body)
        idle_body_layout.setContentsMargins(0, 0, 0, 0)
        idle_body_layout.setSpacing(8)
        self.idle_banner_hint = QLabel(tr("storage.idle.banner.hint"))
        self.idle_banner_hint.setObjectName("warningBanner")
        self.idle_banner_hint.setWordWrap(True)
        idle_body_layout.addWidget(self.idle_banner_hint)
        idle_banner_layout.addWidget(self.idle_banner_body)
        self.idle_banner_host.hide()
        layout.addWidget(self.idle_banner_host)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)
        sort_label = QLabel(tr("storage.label.sort"))
        sort_label.setObjectName("formLabel")
        self.sort_combo = QComboBox()
        self.sort_combo.addItem(
            tr("storage.sort.location"),
            StockpileRepository.SORT_LOCATION,
        )
        self.sort_combo.addItem(
            tr("storage.sort.material"),
            StockpileRepository.SORT_MATERIAL,
        )
        self.sort_combo.addItem(
            tr("storage.sort.age"),
            StockpileRepository.SORT_AGE,
        )
        self.warnings_only_checkbox = QCheckBox(
            tr("storage.filter.warnings_only")
        )
        self.warnings_only_checkbox.setObjectName("formLabel")
        filter_row.addWidget(sort_label)
        filter_row.addWidget(self.sort_combo, 1)
        filter_row.addWidget(self.warnings_only_checkbox)
        layout.addLayout(filter_row)

        layout.addWidget(section_accent(tr("storage.section.list")))

        self.stockpile_table = QTableWidget()
        self.stockpile_table.setColumnCount(7)
        self.stockpile_table.setHorizontalHeaderLabels([
            tr("storage.table.location"),
            tr("storage.table.material"),
            tr("storage.table.quantity"),
            tr("storage.table.status"),
            tr("storage.table.ship"),
            tr("storage.table.activity"),
            tr("storage.table.reserve"),
        ])
        configure_mobiglas_table(
            self.stockpile_table,
            "dataTable",
        )
        self.stockpile_table.setMinimumHeight(200)
        self.stockpile_empty = empty_info_panel(
            tr("storage.empty"),
            "assets/images/icons/info.svg",
        )
        layout.addWidget(self.stockpile_table)
        layout.addWidget(self.stockpile_empty)

        list_actions = QHBoxLayout()
        list_actions.setSpacing(12)
        self.reminded_button = _secondary_button(
            tr("storage.button.reminded")
        )
        self.reserve_button = _secondary_button(
            tr("storage.button.set_reserve")
        )
        self.moved_button = _secondary_button(
            tr("storage.button.moved")
        )
        self.delete_stockpile_button = _secondary_button(
            tr("storage.button.delete")
        )
        list_actions.addWidget(self.reminded_button)
        list_actions.addWidget(self.reserve_button)
        list_actions.addWidget(self.moved_button)
        list_actions.addWidget(self.delete_stockpile_button)
        list_actions.addStretch()
        layout.addLayout(list_actions)

        layout.addWidget(
            section_accent(tr("storage.section.totals"))
        )
        self.totals_panel = QFrame()
        self.totals_panel.setObjectName("storageTotalsPanel")
        totals_panel_layout = QVBoxLayout(self.totals_panel)
        totals_panel_layout.setContentsMargins(0, 0, 0, 0)
        totals_panel_layout.setSpacing(0)

        self.totals_chips_host = QWidget()
        self.totals_chips_layout = QHBoxLayout(self.totals_chips_host)
        self.totals_chips_layout.setContentsMargins(0, 0, 0, 0)
        self.totals_chips_layout.setSpacing(12)
        totals_panel_layout.addWidget(self.totals_chips_host)

        self.totals_empty_label = QLabel(tr("storage.totals.none"))
        self.totals_empty_label.setObjectName("hintLabel")
        self.totals_empty_label.setWordWrap(True)
        totals_panel_layout.addWidget(self.totals_empty_label)
        self.totals_empty_label.hide()
        layout.addWidget(self.totals_panel)

        form_panel, form_layout = info_panel()
        form_layout.addWidget(
            subsection_title(tr("storage.section.add"))
        )

        self.location_type_combo = QComboBox()
        self.location_type_combo.addItem(
            tr("storage.location_type.station"),
            "STATION",
        )
        self.location_type_combo.addItem(
            tr("storage.location_type.ship"),
            "SHIP",
        )

        self.location_picker = SystemLocationPicker()
        self.ship_host = QWidget()
        ship_host_layout = QVBoxLayout(self.ship_host)
        ship_host_layout.setContentsMargins(0, 0, 0, 0)
        ship_host_layout.setSpacing(8)
        ship_host_layout.addWidget(form_label(tr("storage.label.ship")))
        self.ship_combo = QComboBox()
        self.ship_combo.setObjectName("locationCombo")
        self.ship_combo.setMinimumContentsLength(24)
        ship_host_layout.addWidget(self.ship_combo)
        self.ship_host.hide()

        self.material_combo = QComboBox()
        for code in STORAGE_MATERIAL_CODES:
            self.material_combo.addItem(
                material_label(code),
                code,
            )

        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText(
            tr("storage.label.quantity")
        )

        self.reserve_input = QLineEdit()
        self.reserve_input.setPlaceholderText(
            tr("storage.placeholder.reserve")
        )

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText(
            tr("storage.placeholder.notes")
        )

        self.save_button = primary_button(
            tr("storage.button.save")
        )

        add_form_field(
            form_layout,
            tr("storage.label.location_type"),
            self.location_type_combo,
        )
        form_layout.addWidget(self.location_picker)
        form_layout.addWidget(self.ship_host)
        add_form_field(
            form_layout,
            tr("storage.label.material"),
            self.material_combo,
        )
        add_form_field(
            form_layout,
            tr("storage.label.quantity"),
            self.quantity_input,
        )
        add_form_field(
            form_layout,
            tr("storage.label.reserve"),
            self.reserve_input,
        )
        add_form_field(
            form_layout,
            tr("storage.label.notes"),
            self.notes_input,
        )
        form_layout.addWidget(self.save_button)
        layout.addWidget(form_panel)

        layout.addWidget(
            section_accent(tr("storage.section.history"))
        )

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            tr("storage.history.when"),
            tr("storage.history.type"),
            tr("storage.table.location"),
            tr("storage.table.material"),
            tr("storage.history.delta"),
        ])
        configure_mobiglas_table(
            self.history_table,
            "historyTable",
        )
        self.history_table.setMinimumHeight(160)

        history_actions = QHBoxLayout()
        history_actions.setSpacing(12)
        self.delete_event_button = _secondary_button(
            tr("storage.button.delete_event")
        )
        history_actions.addWidget(self.delete_event_button)
        history_actions.addStretch()
        layout.addWidget(self.history_table)
        layout.addLayout(history_actions)

        layout.addStretch()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(build_page_scroll(content))

        self.sort_combo.currentIndexChanged.connect(
            self.load_data
        )
        self.warnings_only_checkbox.toggled.connect(
            self.load_data
        )
        self.idle_banner_toggle.clicked.connect(
            self._toggle_idle_banner
        )
        self.location_type_combo.currentIndexChanged.connect(
            self._on_location_type_changed
        )
        self.save_button.clicked.connect(self.save_entry)
        self.reminded_button.clicked.connect(
            self.acknowledge_selected_idle
        )
        self.reserve_button.clicked.connect(
            self.set_reserve_on_selected
        )
        self.moved_button.clicked.connect(
            self.mark_selected_moved
        )
        self.delete_stockpile_button.clicked.connect(
            self.delete_selected_stockpile
        )
        self.delete_event_button.clicked.connect(
            self.delete_selected_event
        )

        self._on_location_type_changed()
        self.load_data()

    def apply_permissions(
        self,
        user,
        page_name="storage",
    ):
        apply_widget_permissions(
            self,
            user,
            page_name,
        )

    def _on_location_type_changed(self):
        kind = self.location_type_combo.currentData()
        if kind == "SHIP":
            self.location_picker.hide()
            self.ship_host.show()
        else:
            self.ship_host.hide()
            self.location_picker.show()

    def _load_ships(self):
        self.ship_combo.blockSignals(True)
        self.ship_combo.clear()
        ships = self.db.list_stockpile_ships()
        for ship in ships:
            self.ship_combo.addItem(
                ship["ship_name"],
                ship["id"],
            )
        self.ship_combo.blockSignals(False)

    def _status_label(self, status: str) -> str:
        return tr(
            f"storage.status.{status}",
            default=status,
        )

    def _location_display(self, entry: dict) -> str:
        if entry.get("ship_name"):
            return tr(
                "storage.location.ship",
                ship=entry["ship_name"],
            )
        return entry.get("location_label") or "—"

    def _event_type_label(self, event_type: str) -> str:
        return tr(
            f"storage.history.type.{event_type}",
            default=event_type,
        )

    def _toggle_idle_banner(self):
        self._idle_banner_collapsed = not self._idle_banner_collapsed
        self.idle_banner_body.setVisible(
            not self._idle_banner_collapsed
        )
        self.idle_banner_toggle.setText(
            tr("storage.idle.banner.expand")
            if self._idle_banner_collapsed
            else tr("storage.idle.banner.collapse")
        )

    def _update_idle_banner(self, count: int):
        if count <= 0:
            self.idle_banner_host.hide()
            return

        self.idle_banner_title.setText(
            tr(
                "storage.idle.banner.title",
                count=count,
                days=IDLE_WARNING_DAYS,
            )
        )
        self.idle_banner_host.show()
        self.idle_banner_body.setVisible(
            not self._idle_banner_collapsed
        )

    def _activity_display(self, entry: dict) -> str:
        text = format_relative_activity(entry.get("last_activity_at"))
        if entry.get("idle_warning"):
            return tr("storage.activity.warning_prefix") + text
        return text

    def load_data(self):
        self._load_ships()
        sort_by = self.sort_combo.currentData()
        warnings_only = self.warnings_only_checkbox.isChecked()
        self._stockpile_rows = self.db.list_material_stockpiles(
            sort_by=sort_by,
            warnings_only=warnings_only,
        )

        idle_count = self.db.count_stockpile_idle_warnings()
        self._update_idle_banner(idle_count)
        self.idle_warnings_changed.emit(idle_count)

        has_rows = len(self._stockpile_rows) > 0
        self.stockpile_table.setVisible(has_rows)
        self.stockpile_empty.setVisible(not has_rows)
        self.stockpile_table.setRowCount(len(self._stockpile_rows))

        for row, entry in enumerate(self._stockpile_rows):
            self.stockpile_table.setItem(
                row,
                0,
                QTableWidgetItem(
                    self._location_display(entry)
                ),
            )
            self.stockpile_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    material_label(entry["material_code"])
                ),
            )
            self.stockpile_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    format_number(entry["quantity_scu"], 0)
                ),
            )
            self.stockpile_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    self._status_label(entry["status"])
                ),
            )
            self.stockpile_table.setItem(
                row,
                4,
                QTableWidgetItem(entry.get("ship_name") or "—"),
            )
            self.stockpile_table.setItem(
                row,
                5,
                QTableWidgetItem(
                    self._activity_display(entry)
                ),
            )
            self.stockpile_table.setItem(
                row,
                6,
                QTableWidgetItem(entry.get("reserve_tag") or "—"),
            )

        if has_rows:
            finalize_table_columns(
                self.stockpile_table,
                stretch_column=0,
            )

        self._update_totals(self.db.get_stockpile_totals())

        self._load_history()

    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _build_total_chip(
        self,
        material_code: str,
        quantity_scu: float,
    ) -> QFrame:
        chip = QFrame()
        chip.setObjectName("storageTotalChip")
        chip_layout = QVBoxLayout(chip)
        chip_layout.setContentsMargins(16, 12, 16, 12)
        chip_layout.setSpacing(2)

        name = QLabel(material_label(material_code))
        name.setObjectName("statLabel")
        qty = QLabel(format_scu(quantity_scu))
        qty.setObjectName("statValue")

        chip_layout.addWidget(name)
        chip_layout.addWidget(qty)
        return chip

    def _update_totals(self, totals):
        self._clear_layout(self.totals_chips_layout)

        if not totals:
            self.totals_empty_label.show()
            self.totals_chips_host.hide()
            return

        self.totals_empty_label.hide()
        self.totals_chips_host.show()

        for item in totals:
            self.totals_chips_layout.addWidget(
                self._build_total_chip(
                    item["material_code"],
                    float(item.get("quantity_scu") or 0),
                )
            )
        self.totals_chips_layout.addStretch()

    def _load_history(self):
        events = self.db.list_stockpile_events()
        self.history_table.setRowCount(len(events))

        for row, event in enumerate(events):
            delta = event.get("quantity_delta")
            delta_text = "—"
            if delta is not None:
                delta_text = format_scu_delta(delta)

            location = event.get("location_label") or event.get(
                "to_label"
            ) or "—"
            material = material_label(
                event.get("material_code") or "—"
            )

            self.history_table.setItem(
                row,
                0,
                QTableWidgetItem(
                    format_datetime(event["created_at"])
                ),
            )
            self.history_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    self._event_type_label(event["event_type"])
                ),
            )
            self.history_table.setItem(
                row,
                2,
                QTableWidgetItem(location),
            )
            self.history_table.setItem(
                row,
                3,
                QTableWidgetItem(material),
            )
            self.history_table.setItem(
                row,
                4,
                QTableWidgetItem(delta_text),
            )

        finalize_table_columns(
            self.history_table,
            stretch_column=2,
        )

    def _selected_stockpile(self) -> dict | None:
        row = self.stockpile_table.currentRow()
        if row < 0 or row >= len(self._stockpile_rows):
            return None
        return self._stockpile_rows[row]

    def save_entry(self):
        material_code = self.material_combo.currentData()
        quantity = parse_number_de(self.quantity_input.text())
        if quantity is None or quantity <= 0:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("error.storage.quantity_positive"),
            )
            return

        reserve_tag = self.reserve_input.text().strip() or None
        notes = self.notes_input.text().strip() or None
        location_kind = self.location_type_combo.currentData()

        try:
            if location_kind == "SHIP":
                ship_id = self.ship_combo.currentData()
                if ship_id is None:
                    QMessageBox.warning(
                        self,
                        tr("common.error"),
                        tr("error.storage.ship_required"),
                    )
                    return

                ship_name = self.ship_combo.currentText().strip()
                self.db.create_material_stockpile(
                    material_code=material_code,
                    quantity_scu=quantity,
                    location_kind="SHIP",
                    location_key=str(ship_id),
                    location_label=ship_name,
                    ship_id=ship_id,
                    reserve_tag=reserve_tag,
                    notes=notes,
                )
            else:
                selected = self.location_picker.selection()
                if not selected:
                    QMessageBox.warning(
                        self,
                        tr("common.error"),
                        tr("error.location.not_selected"),
                    )
                    return

                self.db.create_material_stockpile(
                    material_code=material_code,
                    quantity_scu=quantity,
                    location_kind=selected.location_kind,
                    location_key=selected.location_key,
                    location_label=selected.location_label,
                    reserve_tag=reserve_tag,
                    notes=notes,
                )
        except ValueError as error:
            QMessageBox.warning(
                self,
                tr("common.error"),
                str(error),
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                tr("common.error"),
                str(error),
            )
            return

        self.quantity_input.clear()
        self.reserve_input.clear()
        self.notes_input.clear()
        QMessageBox.information(
            self,
            tr("common.success"),
            tr("storage.msg.saved"),
        )
        self.load_data()

    def acknowledge_selected_idle(self):
        entry = self._selected_stockpile()
        if not entry:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("storage.msg.no_selection"),
            )
            return

        try:
            self.db.acknowledge_stockpile_idle(entry["id"])
        except ValueError as error:
            QMessageBox.warning(
                self,
                tr("common.error"),
                str(error),
            )
            return

        QMessageBox.information(
            self,
            tr("common.success"),
            tr("storage.msg.reminded"),
        )
        self.load_data()

    def set_reserve_on_selected(self):
        entry = self._selected_stockpile()
        if not entry:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("storage.msg.no_selection"),
            )
            return

        dialog = MobiglasTextInputDialog(
            self,
            tr("storage.msg.reserve_prompt.title"),
            tr("storage.msg.reserve_prompt.label"),
            text=entry.get("reserve_tag") or DEFAULT_RESERVE_TAG,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        reserve_tag = dialog.text().strip()
        if not reserve_tag:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("error.storage.reserve_required"),
            )
            return

        try:
            self.db.set_stockpile_reserve(
                entry["id"],
                reserve_tag,
            )
        except ValueError as error:
            QMessageBox.warning(
                self,
                tr("common.error"),
                str(error),
            )
            return

        QMessageBox.information(
            self,
            tr("common.success"),
            tr("storage.msg.reserve_set"),
        )
        self.load_data()

    def mark_selected_moved(self):
        entry = self._selected_stockpile()
        if not entry:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("storage.msg.no_selection"),
            )
            return

        try:
            self.db.mark_stockpile_moved(entry["id"])
        except ValueError as error:
            QMessageBox.warning(
                self,
                tr("common.error"),
                str(error),
            )
            return

        QMessageBox.information(
            self,
            tr("common.success"),
            tr("storage.msg.moved"),
        )
        self.load_data()

    def delete_selected_stockpile(self):
        entry = self._selected_stockpile()
        if not entry:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("storage.msg.no_selection"),
            )
            return

        answer = QMessageBox.question(
            self,
            tr("storage.msg.delete_confirm.title"),
            tr(
                "storage.msg.delete_confirm.message",
                location=self._location_display(entry),
                material=material_label(entry["material_code"]),
                quantity=format_number(entry["quantity_scu"], 0),
            ),
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.db.delete_material_stockpile(entry["id"])
        except ValueError as error:
            QMessageBox.warning(
                self,
                tr("common.error"),
                str(error),
            )
            return

        QMessageBox.information(
            self,
            tr("common.success"),
            tr("storage.msg.deleted"),
        )
        self.load_data()

    def delete_selected_event(self):
        row = self.history_table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("storage.msg.no_selection"),
            )
            return

        events = self.db.list_stockpile_events()
        if row >= len(events):
            return

        event_id = events[row]["id"]

        answer = QMessageBox.question(
            self,
            tr("storage.msg.delete_event_confirm.title"),
            tr("storage.msg.delete_event_confirm.message"),
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.db.delete_stockpile_event(event_id)
        except ValueError as error:
            QMessageBox.warning(
                self,
                tr("common.error"),
                str(error),
            )
            return

        self.load_data()
