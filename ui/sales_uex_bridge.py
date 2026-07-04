"""Verbindet Verkaufsseite und UEX-Preisabruf (lokal, asynchron)."""

from __future__ import annotations

from shiboken6 import isValid

from PySide6.QtWidgets import QComboBox, QLabel, QLineEdit

from config.i18n import format_number, tr
from services.uex.price_worker import UexPriceFetchWorker
from ui.system_location_picker import SystemLocationPicker, SystemLocationSelection


class SalesUexBridge:
    """Lädt UEX-Preise bei Standortwechsel und füllt das Preisfeld."""

    def __init__(
        self,
        *,
        location_picker: SystemLocationPicker,
        unit_price_input: QLineEdit,
        material_combo: QComboBox,
        status_label: QLabel,
    ):
        self._location_picker = location_picker
        self._unit_price_input = unit_price_input
        self._material_combo = material_combo
        self._status_label = status_label
        self._worker: UexPriceFetchWorker | None = None
        self._price_cache: dict[str, float] = {}
        self._request_token = 0

        location_picker.location_changed.connect(
            self._on_location_changed
        )
        material_combo.currentIndexChanged.connect(
            self._apply_price_for_current_material
        )

    def _on_location_changed(
        self,
        selection: SystemLocationSelection | None,
    ) -> None:
        self._stop_worker()
        self._price_cache.clear()
        self._unit_price_input.clear()

        if selection is None:
            self._status_label.setText("")
            return

        self._request_token += 1
        token = self._request_token
        self._status_label.setText(tr("sales.uex.loading"))

        worker = UexPriceFetchWorker(
            system=selection.system,
            location_kind=selection.location_kind,
            location_key=selection.location_key,
            location_label=selection.location_label,
        )
        worker.prices_ready.connect(
            lambda prices, t=token: self._on_prices_ready(prices, t)
        )
        worker.fetch_failed.connect(
            lambda code, t=token: self._on_fetch_failed(code, t)
        )
        worker.finished.connect(
            lambda: self._release_worker(worker)
        )
        self._worker = worker
        worker.start()

    def _on_prices_ready(self, prices: dict, token: int) -> None:
        if token != self._request_token:
            return

        self._price_cache = dict(prices)
        self._apply_price_for_current_material()
        self._status_label.setText(tr("sales.uex.loaded"))

    def _on_fetch_failed(self, error_code: str, token: int) -> None:
        if token != self._request_token:
            return

        self._price_cache.clear()
        self._unit_price_input.clear()
        message_key = f"sales.uex.error.{error_code}"
        message = tr(message_key, default=tr("sales.uex.error.unknown"))
        self._status_label.setText(message)

    def _apply_price_for_current_material(self) -> None:
        material_code = self._material_combo.currentData()
        if not material_code:
            return

        price = self._price_cache.get(material_code)
        if price is None:
            return

        decimals = 0 if float(price).is_integer() else 2
        self._unit_price_input.setText(
            format_number(price, decimals)
        )

    def _release_worker(self, worker: UexPriceFetchWorker) -> None:
        if self._worker is worker:
            self._worker = None
        if isValid(worker):
            worker.deleteLater()

    def _stop_worker(self) -> None:
        worker = self._worker
        if worker is None:
            return
        if not isValid(worker):
            self._worker = None
            return

        self._worker = None
        if worker.isRunning():
            worker.requestInterruption()
            worker.wait(2000)
