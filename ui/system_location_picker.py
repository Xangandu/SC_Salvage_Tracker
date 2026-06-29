"""Standorte pro System: System → Station | Stadt (zwei Dropdowns in einer Zeile)."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from config.i18n import tr
from config.locations.catalog import (
    SYSTEM_ORDER,
    cities_for_system,
    stations_for_system,
)


@dataclass(frozen=True)
class SystemLocationSelection:
    system: str
    location_kind: str
    location_key: str
    location_label: str


def _populate_choice_combo(
    combo: QComboBox,
    items: list[tuple[str, str]],
    placeholder: str,
) -> None:
    combo.blockSignals(True)
    combo.clear()
    combo.addItem(placeholder, "")
    for location_id, name in items:
        combo.addItem(name, location_id)
    combo.setCurrentIndex(0)
    combo.blockSignals(False)


def _combo_has_selection(combo: QComboBox) -> bool:
    data = combo.currentData()
    return data not in (None, "")


class SystemLocationPicker(QWidget):
    """System wählen, dann Station **oder** Stadt aus dem gewählten System."""

    def __init__(
        self,
        parent=None,
        *,
        refinery_stations_only: bool = False,
    ):
        super().__init__(parent)
        self._refinery_stations_only = refinery_stations_only
        self._updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        system_label = QLabel(tr("location.label.system"))
        system_label.setObjectName("formLabel")
        layout.addWidget(system_label)

        self.system_combo = QComboBox()
        self.system_combo.setObjectName("locationCombo")
        self.system_combo.setEditable(False)
        self.system_combo.setMinimumContentsLength(16)
        for system in SYSTEM_ORDER:
            self.system_combo.addItem(system, system)
        layout.addWidget(self.system_combo)

        row = QHBoxLayout()
        row.setSpacing(12)

        station_col = QVBoxLayout()
        station_col.setSpacing(4)
        station_label = QLabel(tr("location.label.station"))
        station_label.setObjectName("formLabel")
        station_col.addWidget(station_label)
        self.station_combo = QComboBox()
        self.station_combo.setObjectName("locationCombo")
        self.station_combo.setEditable(False)
        self.station_combo.setMinimumContentsLength(20)
        self.station_combo.setMaxVisibleItems(18)
        station_col.addWidget(self.station_combo)

        city_col = QVBoxLayout()
        city_col.setSpacing(4)
        city_label = QLabel(tr("location.label.city"))
        city_label.setObjectName("formLabel")
        city_col.addWidget(city_label)
        self.city_combo = QComboBox()
        self.city_combo.setObjectName("locationCombo")
        self.city_combo.setEditable(False)
        self.city_combo.setMinimumContentsLength(20)
        self.city_combo.setMaxVisibleItems(18)
        city_col.addWidget(self.city_combo)

        row.addLayout(station_col, 1)
        row.addLayout(city_col, 1)
        layout.addLayout(row)

        self.system_combo.currentIndexChanged.connect(
            self._reload_for_system
        )
        self.station_combo.currentIndexChanged.connect(
            self._on_station_changed
        )
        self.city_combo.currentIndexChanged.connect(
            self._on_city_changed
        )

        self._reload_for_system()

    def _reload_for_system(self) -> None:
        system = self.system_combo.currentData()
        if not system:
            return

        stations = stations_for_system(
            system,
            refinery_only=self._refinery_stations_only,
        )
        cities = cities_for_system(system)

        _populate_choice_combo(
            self.station_combo,
            stations,
            tr("location.placeholder.station"),
        )
        _populate_choice_combo(
            self.city_combo,
            cities,
            tr("location.placeholder.city"),
        )

    def _on_station_changed(self) -> None:
        if self._updating:
            return
        if not _combo_has_selection(self.station_combo):
            return
        self._updating = True
        self.city_combo.setCurrentIndex(0)
        self._updating = False

    def _on_city_changed(self) -> None:
        if self._updating:
            return
        if not _combo_has_selection(self.city_combo):
            return
        self._updating = True
        self.station_combo.setCurrentIndex(0)
        self._updating = False

    def is_selected(self) -> bool:
        return self.selection() is not None

    def selection(self) -> SystemLocationSelection | None:
        system = self.system_combo.currentData()
        if not system:
            return None

        if _combo_has_selection(self.station_combo):
            return SystemLocationSelection(
                system=system,
                location_kind="STATION",
                location_key=str(self.station_combo.currentData()),
                location_label=self.station_combo.currentText().strip(),
            )

        if _combo_has_selection(self.city_combo):
            return SystemLocationSelection(
                system=system,
                location_kind="CITY",
                location_key=str(self.city_combo.currentData()),
                location_label=self.city_combo.currentText().strip(),
            )

        return None

    def location_label(self) -> str:
        selected = self.selection()
        if not selected:
            return ""
        return selected.location_label

    def set_location(
        self,
        location_label: str,
        *,
        system: str | None = None,
    ) -> None:
        location_label = (location_label or "").strip()
        if not location_label:
            return

        systems = [system] if system else list(SYSTEM_ORDER)
        for sys_name in systems:
            if not sys_name:
                continue

            for loc_id, name in stations_for_system(
                sys_name,
                refinery_only=self._refinery_stations_only,
            ):
                if name.casefold() == location_label.casefold():
                    self._select(sys_name, self.station_combo, loc_id)
                    return

            for loc_id, name in cities_for_system(sys_name):
                if name.casefold() == location_label.casefold():
                    self._select(sys_name, self.city_combo, loc_id)
                    return

    def _select(
        self,
        system: str,
        combo: QComboBox,
        location_id: str,
    ) -> None:
        index = self.system_combo.findData(system)
        if index >= 0:
            self.system_combo.setCurrentIndex(index)

        self._reload_for_system()

        for row in range(combo.count()):
            if combo.itemData(row) == location_id:
                combo.setCurrentIndex(row)
                return
