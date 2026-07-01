"""Dialog: Material zwischen Lager-Standorten verschieben (Pool-basiert)."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config.i18n import tr, format_number
from config.materials import material_label
from config.strings_de import parse_number_de
from database.access import get_database
from ui.mobiglas_window_frame import (
    MobiglasFramelessMixin,
    apply_mobiglas_window_frame,
)
from ui.page_layout import (
    add_form_field,
    form_label,
    hud_divider,
    page_panel,
    page_title,
    primary_button,
)
from ui.storage_pool_utils import build_pools_from_rows
from ui.system_location_picker import SystemLocationPicker


def _secondary_button(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("secondaryAction")
    return button


def _format_pool_row(pool: dict) -> str:
    if pool.get("pool_kind") == "SHIP":
        location = tr(
            "storage.location.ship",
            ship=pool.get("ship_name") or "—",
        )
    else:
        location = pool.get("location_label") or "—"
    return tr(
        "storage.transfer.pool_option",
        location=location,
        material=material_label(pool["material_code"]),
        quantity=format_number(pool["quantity_scu"], 0),
    )


class StorageTransferDialog(MobiglasFramelessMixin, QDialog):

    def __init__(
        self,
        parent,
        stockpile_rows: list[dict],
        *,
        initial_stockpile_id: int | None = None,
    ):
        super().__init__(parent)
        self.db = get_database()
        row_by_id = {
            row["id"]: row
            for row in stockpile_rows
            if row.get("id") is not None
        }
        self._pools = build_pools_from_rows(stockpile_rows)
        self._result_dest_id: int | None = None

        self.setObjectName("mobiglasDialog")
        self.setWindowTitle(tr("storage.transfer.title"))
        self.setModal(True)
        self.resize(560, 520)
        self.setMinimumWidth(480)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addWidget(page_title(tr("storage.transfer.title")))
        layout.addLayout(hud_divider())

        panel, panel_layout = page_panel()
        panel_layout.setContentsMargins(16, 16, 16, 16)
        panel_layout.setSpacing(10)

        hint = form_label(tr("storage.transfer.pool_hint"))
        hint.setWordWrap(True)
        panel_layout.addWidget(hint)

        self.source_combo = QComboBox()
        self.source_combo.setObjectName("locationCombo")
        self.source_combo.setMinimumContentsLength(28)
        initial_pool_index = 0
        for index, pool in enumerate(self._pools):
            self.source_combo.addItem(_format_pool_row(pool), pool)
            if initial_stockpile_id is not None:
                source_row = row_by_id.get(initial_stockpile_id)
                if source_row and pool_key_matches(source_row, pool):
                    initial_pool_index = index

        self.source_combo.setCurrentIndex(initial_pool_index)

        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText(
            tr("storage.label.quantity")
        )

        self.dest_type_combo = QComboBox()
        self.dest_type_combo.addItem(
            tr("storage.location_type.station"),
            "STATION",
        )
        self.dest_type_combo.addItem(
            tr("storage.location_type.ship"),
            "SHIP",
        )

        self.location_picker = SystemLocationPicker()
        self.ship_host = QWidget()
        ship_layout = QVBoxLayout(self.ship_host)
        ship_layout.setContentsMargins(0, 0, 0, 0)
        ship_layout.setSpacing(8)
        ship_layout.addWidget(form_label(tr("storage.label.ship")))
        self.ship_combo = QComboBox()
        self.ship_combo.setObjectName("locationCombo")
        self.ship_combo.setMinimumContentsLength(24)
        ship_layout.addWidget(self.ship_combo)
        self.ship_host.hide()

        add_form_field(
            panel_layout,
            tr("storage.transfer.label.source"),
            self.source_combo,
        )
        add_form_field(
            panel_layout,
            tr("storage.label.quantity"),
            self.quantity_input,
        )
        add_form_field(
            panel_layout,
            tr("storage.transfer.label.destination_type"),
            self.dest_type_combo,
        )
        panel_layout.addWidget(self.location_picker)
        panel_layout.addWidget(self.ship_host)

        layout.addWidget(panel)

        actions = QHBoxLayout()
        actions.addStretch()
        cancel_button = _secondary_button(tr("common.cancel"))
        cancel_button.clicked.connect(self.reject)
        self.confirm_button = primary_button(tr("storage.transfer.confirm"))
        self.confirm_button.clicked.connect(self._confirm)
        actions.addWidget(cancel_button)
        actions.addWidget(self.confirm_button)
        layout.addLayout(actions)

        self.setLayout(layout)
        apply_mobiglas_window_frame(
            self,
            title=tr("storage.transfer.title"),
        )

        self.source_combo.currentIndexChanged.connect(
            self._sync_quantity_default
        )
        self.dest_type_combo.currentIndexChanged.connect(
            self._on_dest_type_changed
        )

        self._load_ships()
        self._on_dest_type_changed()
        self._sync_quantity_default()

    @property
    def destination_stockpile_id(self) -> int | None:
        return self._result_dest_id

    def _selected_pool(self) -> dict | None:
        pool = self.source_combo.currentData()
        return pool if isinstance(pool, dict) else None

    def _load_ships(self):
        self.ship_combo.blockSignals(True)
        self.ship_combo.clear()
        for ship in self.db.list_stockpile_ships():
            self.ship_combo.addItem(
                ship["ship_name"],
                ship["id"],
            )
        self.ship_combo.blockSignals(False)

    def _sync_quantity_default(self):
        pool = self._selected_pool()
        if not pool:
            return
        self.quantity_input.setText(
            format_number(pool["quantity_scu"], 0)
        )

    def _on_dest_type_changed(self):
        kind = self.dest_type_combo.currentData()
        if kind == "SHIP":
            self.location_picker.hide()
            self.ship_host.show()
        else:
            self.ship_host.hide()
            self.location_picker.show()

    def _confirm(self):
        pool = self._selected_pool()
        if not pool:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("storage.transfer.msg.no_source"),
            )
            return

        quantity = parse_number_de(self.quantity_input.text())
        if quantity is None or quantity <= 0:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("error.storage.quantity_positive"),
            )
            return

        dest_kind = self.dest_type_combo.currentData()
        ship_id = None
        location_key = None
        location_label = ""

        if dest_kind == "SHIP":
            ship_id = self.ship_combo.currentData()
            if ship_id is None:
                QMessageBox.warning(
                    self,
                    tr("common.error"),
                    tr("error.storage.ship_required"),
                )
                return
            location_label = self.ship_combo.currentText().strip()
        else:
            selected = self.location_picker.selection()
            if not selected:
                QMessageBox.warning(
                    self,
                    tr("common.error"),
                    tr("error.location.not_selected"),
                )
                return
            dest_kind = selected.location_kind
            location_key = selected.location_key
            location_label = selected.location_label

        try:
            self._result_dest_id = self.db.transfer_from_material_pool(
                pool,
                quantity_scu=quantity,
                location_kind=dest_kind,
                location_key=location_key,
                location_label=location_label,
                ship_id=ship_id,
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

        self.accept()


def pool_key_matches(entry: dict, pool: dict) -> bool:
    if pool.get("pool_kind") == "SHIP":
        return (
            entry.get("ship_id") == pool.get("ship_id")
            and entry.get("material_code") == pool.get("material_code")
        )
    return (
        entry.get("location_kind") == pool.get("location_kind")
        and entry.get("location_key") == pool.get("location_key")
        and entry.get("material_code") == pool.get("material_code")
    )
