"""Spalter-Positionen (Verkäufe / Auszahlung) zwischen Sitzungen speichern."""

from __future__ import annotations

import json

from PySide6.QtCore import QEvent, QObject, QTimer
from PySide6.QtWidgets import QApplication, QSplitter

SETTING_SALES_PAGE_SPLIT = "sales_page_split_sizes"
SETTING_PAYOUT_PAGE_SPLIT = "payout_page_split_sizes"
SETTING_STORAGE_PAGE_SPLIT = "storage_page_split_sizes"
SETTING_REFINERY_PAGE_SPLIT = "refinery_page_split_sizes"

_MIN_PANEL_WIDTH = 80
_RESTORE_DELAYS_MS = (0, 50, 150, 350, 600, 1000)
_STARTUP_PHASE_MS = 1500


def _parse_payload(raw: str) -> list[int] | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None

    if isinstance(data, list) and len(data) >= 2:
        try:
            left, right = int(data[0]), int(data[1])
        except (TypeError, ValueError):
            return None
        if left >= _MIN_PANEL_WIDTH and right >= _MIN_PANEL_WIDTH:
            return [left, right]

    if not isinstance(data, dict):
        return None

    sizes = data.get("sizes")
    if isinstance(sizes, list) and len(sizes) >= 2:
        try:
            left, right = int(sizes[0]), int(sizes[1])
        except (TypeError, ValueError):
            return None
        if left >= _MIN_PANEL_WIDTH and right >= _MIN_PANEL_WIDTH:
            return [left, right]

    ratio = data.get("ratio")
    if ratio is not None:
        try:
            ratio = float(ratio)
        except (TypeError, ValueError):
            return None
        if 0.15 <= ratio <= 0.85:
            return None

    return None


def _content_width(splitter: QSplitter) -> int:
    sizes = splitter.sizes()
    total = sum(sizes)
    if total >= _MIN_PANEL_WIDTH * 2:
        return total

    width = splitter.width()
    if width < _MIN_PANEL_WIDTH * 2:
        return 0

    handles = splitter.handleWidth() * max(0, splitter.count() - 1)
    return max(0, width - handles)


def _scale_sizes(stored_sizes: list[int], target_total: int) -> list[int]:
    stored_total = sum(stored_sizes)
    if stored_total <= 0 or target_total <= 0:
        return stored_sizes[:2]

    left = round(stored_sizes[0] * target_total / stored_total)
    left = max(
        _MIN_PANEL_WIDTH,
        min(left, target_total - _MIN_PANEL_WIDTH),
    )
    right = target_total - left
    return [left, right]


def _apply_saved_sizes(splitter: QSplitter, stored_sizes: list[int]) -> bool:
    target_total = _content_width(splitter)
    if target_total < _MIN_PANEL_WIDTH * 2:
        return False

    sizes = _scale_sizes(stored_sizes, target_total)
    splitter.blockSignals(True)
    splitter.setSizes(sizes)
    splitter.setStretchFactor(0, 0)
    splitter.setStretchFactor(1, 1)
    splitter.blockSignals(False)
    return True


class _PageSplitController(QObject):
    def __init__(
        self,
        splitter: QSplitter,
        db,
        setting_key: str,
        default_sizes: list[int],
    ) -> None:
        super().__init__(splitter)
        self._splitter = splitter
        self._db = db
        self._key = setting_key
        self._defaults = default_sizes[:2]
        self._restoring = False
        self._startup_phase = True

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(120)
        self._save_timer.timeout.connect(self._persist)

        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(60)
        self._resize_timer.timeout.connect(self._restore_once)

        splitter.splitterMoved.connect(self._on_moved)

        window = splitter.window()
        if window is not None:
            window.installEventFilter(self)
        splitter.installEventFilter(self)

        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._persist)

        for delay in _RESTORE_DELAYS_MS:
            QTimer.singleShot(delay, self._restore_once)

        QTimer.singleShot(
            _STARTUP_PHASE_MS,
            self._end_startup_phase,
        )

    def _end_startup_phase(self) -> None:
        self._startup_phase = False

    def _stored_sizes(self) -> list[int] | None:
        raw = self._db.settings.get_app_setting(self._key, "") or ""
        return _parse_payload(raw)

    def _restore_once(self) -> None:
        if self._restoring:
            return

        stored = self._stored_sizes() or self._defaults
        self._restoring = True
        try:
            _apply_saved_sizes(self._splitter, stored)
        finally:
            self._restoring = False

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.Show:
            QTimer.singleShot(0, self._restore_once)
        elif (
            event.type() == QEvent.Type.Resize
            and obj is self._splitter.window()
            and self._startup_phase
            and not self._restoring
        ):
            self._resize_timer.start()
        return False

    def _on_moved(self, _pos: int, _index: int) -> None:
        if self._restoring:
            return
        self._save_timer.stop()
        self._save_timer.start()

    def _persist(self) -> None:
        if self._restoring:
            return

        sizes = self._splitter.sizes()
        if len(sizes) < 2:
            return

        total = sum(sizes)
        if total <= 0:
            return

        self._db.settings.set_app_setting(
            self._key,
            json.dumps({"sizes": sizes[:2]}),
        )


def bind_page_split_persistence(
    splitter: QSplitter,
    db,
    setting_key: str,
    *,
    default_sizes: list[int],
) -> None:
    """Lädt gespeicherte Spalter-Breiten und speichert bei Verschieben."""

    _PageSplitController(
        splitter,
        db,
        setting_key,
        default_sizes,
    )
