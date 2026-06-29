"""Gruppierte Standort-Dropdowns (Stationen, Landeplaetze) — nicht editierbar."""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox

from config.i18n import tr


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
