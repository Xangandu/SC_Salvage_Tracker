"""Gruppierte Standort-Dropdowns (Stationen, Landeplaetze) — nicht editierbar."""

from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QComboBox

from config.i18n import tr

LocationEntryData = dict[str, str]


def _combo_model_item(combo: QComboBox, index: int):
    model = combo.model()
    if model is None:
        return None
    return model.item(index)


def _add_non_selectable_header(combo: QComboBox, label: str) -> None:
    combo.addItem(label, None)
    item = _combo_model_item(combo, combo.count() - 1)
    if item is None:
        return
    item.setEnabled(False)
    item.setSelectable(False)
    font = QFont(item.font())
    font.setBold(True)
    item.setFont(font)


def _add_location_item(
    combo: QComboBox,
    *,
    kind: str,
    location_id: str,
    name: str,
) -> None:
    combo.addItem(
        name,
        {"kind": kind, "key": location_id},
    )


def populate_station_city_location_combo(
    combo: QComboBox,
    stations: list[tuple[str, str]],
    cities: list[tuple[str, str]],
    *,
    placeholder: str = "",
) -> None:
    """Eine Combo: Überschriften (nicht wählbar) + Stationen + Städte."""
    combo.blockSignals(True)
    combo.clear()

    if placeholder:
        combo.addItem(placeholder, None)

    if stations:
        _add_non_selectable_header(
            combo,
            tr("location.group.stations"),
        )
        for location_id, name in stations:
            _add_location_item(
                combo,
                kind="STATION",
                location_id=location_id,
                name=name,
            )

    if cities:
        _add_non_selectable_header(
            combo,
            tr("location.group.cities"),
        )
        for location_id, name in cities:
            _add_location_item(
                combo,
                kind="CITY",
                location_id=location_id,
                name=name,
            )

    combo.setCurrentIndex(0)
    combo.blockSignals(False)


def station_city_combo_selection(
    combo: QComboBox,
) -> tuple[str, str, str] | None:
    """(kind, location_key, label) oder None."""
    data = combo.currentData()
    if not isinstance(data, dict):
        return None

    kind = data.get("kind")
    location_key = data.get("key")
    if kind not in {"STATION", "CITY"} or not location_key:
        return None

    return (
        str(kind),
        str(location_key),
        combo.currentText().strip(),
    )


def set_station_city_combo_selection(
    combo: QComboBox,
    *,
    kind: str,
    location_key: str,
) -> bool:
    for index in range(combo.count()):
        data = combo.itemData(index)
        if not isinstance(data, dict):
            continue
        if data.get("kind") == kind and data.get("key") == location_key:
            combo.setCurrentIndex(index)
            return True
    return False


def build_location_combo(
    groups: list[tuple[str, list[tuple[str, str]]]],
    *,
    placeholder: str = "",
) -> QComboBox:
    combo = QComboBox()
    combo.setObjectName("locationCombo")
    combo.setEditable(False)
    combo.setMinimumContentsLength(28)
    combo.setMaxVisibleItems(20)
    combo.setSizeAdjustPolicy(
        QComboBox.SizeAdjustPolicy.AdjustToContents,
    )
    populate_grouped_location_combo(
        combo,
        groups,
        placeholder=placeholder or tr("location.placeholder.select"),
    )
    return combo


def populate_grouped_location_combo(
    combo: QComboBox,
    groups: list[tuple[str, list[tuple[str, str]]]],
    *,
    placeholder: str = "",
) -> None:
    combo.blockSignals(True)
    combo.clear()

    if placeholder:
        combo.addItem(placeholder, "")

    has_items = False
    for _group_label, items in groups:
        if not items:
            continue
        if has_items:
            combo.insertSeparator(combo.count())
        for location_id, name in items:
            combo.addItem(name, location_id)
        has_items = True

    combo.setCurrentIndex(0)
    combo.blockSignals(False)


def location_combo_is_selected(combo: QComboBox) -> bool:
    return location_combo_key(combo) is not None


def location_combo_text(combo: QComboBox) -> str:
    if not location_combo_is_selected(combo):
        return ""
    return combo.currentText().strip()


def location_combo_key(combo: QComboBox) -> str | None:
    data = combo.currentData()
    if data in (None, ""):
        return None
    return str(data)


def set_location_combo_text(
    combo: QComboBox,
    location: str,
) -> None:
    location = (location or "").strip()
    if not location:
        combo.setCurrentIndex(0)
        return

    for index in range(combo.count()):
        if combo.itemData(index) in (None, ""):
            continue
        if combo.itemText(index).casefold() == location.casefold():
            combo.setCurrentIndex(index)
            return

    combo.setCurrentIndex(0)


def select_first_location(combo: QComboBox) -> None:
    for index in range(combo.count()):
        if combo.itemData(index) not in (None, ""):
            combo.setCurrentIndex(index)
            return
