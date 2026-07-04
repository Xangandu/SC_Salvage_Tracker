"""Hintergrund-Abruf von UEX-Verkaufspreisen (lokal, nicht blockierend)."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from services.uex.api_client import UexApiClient
from services.uex.models import UexApiError


class UexPriceFetchWorker(QThread):
    prices_ready = Signal(dict)
    fetch_failed = Signal(str)

    def __init__(
        self,
        *,
        system: str,
        location_kind: str,
        location_key: str,
        location_label: str,
        parent=None,
    ):
        super().__init__(parent)
        self._system = system
        self._location_kind = location_kind
        self._location_key = location_key
        self._location_label = location_label
        self._client = UexApiClient()

    def run(self):
        if self.isInterruptionRequested():
            return

        try:
            result = self._client.fetch_sale_prices(
                system=self._system,
                location_kind=self._location_kind,
                location_key=self._location_key,
                location_label=self._location_label,
            )
        except UexApiError as error:
            if not self.isInterruptionRequested():
                self.fetch_failed.emit(str(error))
            return
        except Exception:
            if not self.isInterruptionRequested():
                self.fetch_failed.emit("unknown")
            return

        if self.isInterruptionRequested():
            return

        if not result.prices_by_tracker_code:
            self.fetch_failed.emit("no_prices")
            return

        self.prices_ready.emit(result.prices_by_tracker_code)
