"""Standorte pro System: System → Station oder Stadt (eine Dropdown-Leiste)."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QComboBox,
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
from ui.location_combo import (
    populate_station_city_location_combo,
    set_station_city_combo_selection,
    station_city_combo_selection,
)


@dataclass(frozen=True)
class SystemLocationSelection:
    system: str
    location_kind: str
    location_key: str
    location_label: str


class SystemLocationPicker(QWidget):
    """System wählen, dann Station **oder** Stadt aus einer gemeinsamen Liste."""

    def __init__(
        self,
        parent=None,
        *,
        refinery_stations_only: bool = False,
    ):
        super().__init__(parent)
        self._refinery_stations_only = refinery_stations_only

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

        location_label = QLabel(tr("location.label.place"))
        location_label.setObjectName("formLabel")
        layout.addWidget(location_label)

        self.location_combo = QComboBox()
        self.location_combo.setObjectName("locationCombo")
        self.location_combo.setEditable(False)
        self.location_combo.setMinimumContentsLength(28)
        self.location_combo.setMaxVisibleItems(20)
        layout.addWidget(self.location_combo)

        self.system_combo.currentIndexChanged.connect(
            self._reload_for_system
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
        cities = cities_for_system(
            system,
            refinery_only=self._refinery_stations_only,
        )

        populate_station_city_location_combo(
            self.location_combo,
            stations,
            cities,
            placeholder=tr("location.placeholder.select"),
        )

    def is_selected(self) -> bool:
        return self.selection() is not None

    def selection(self) -> SystemLocationSelection | None:
        system = self.system_combo.currentData()
        if not system:
            return None

        picked = station_city_combo_selection(self.location_combo)
        if picked is None:
            return None

        kind, location_key, location_label = picked
        return SystemLocationSelection(
            system=system,
            location_kind=kind,
            location_key=location_key,
            location_label=location_label,
        )

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
                    self._select(sys_name, "STATION", loc_id)
                    return

            for loc_id, name in cities_for_system(
                sys_name,
                refinery_only=self._refinery_stations_only,
            ):
                if name.casefold() == location_label.casefold():
                    self._select(sys_name, "CITY", loc_id)
                    return

    def _select(
        self,
        system: str,
        kind: str,
        location_id: str,
    ) -> None:
        index = self.system_combo.findData(system)
        if index >= 0:
            self.system_combo.setCurrentIndex(index)

        self._reload_for_system()
        set_station_city_combo_selection(
            self.location_combo,
            kind=kind,
            location_key=location_id,
        )
