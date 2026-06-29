from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QApplication

from database.access import get_database


class RefineryLiveSync(QObject):

    jobs_updated = Signal()
    jobs_became_ready = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._notified_ready: set[int] = set()
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

    def start(self) -> None:
        if not self._timer.isActive():
            self._timer.start()
        self._tick()

    def stop(self) -> None:
        self._timer.stop()

    def clear_notified(self, job_id: int | None = None) -> None:
        if job_id is None:
            self._notified_ready.clear()
            return
        self._notified_ready.discard(job_id)

    def _tick(self) -> None:
        db = get_database()
        sync = getattr(db, "sync_expired_refinery_jobs", None)
        newly_ready: list[int] = []

        if callable(sync):
            try:
                newly_ready = list(sync() or [])
            except Exception:
                newly_ready = []

        self.jobs_updated.emit()

        fresh = [
            job_id
            for job_id in newly_ready
            if job_id not in self._notified_ready
        ]
        if not fresh:
            return

        self._notified_ready.update(fresh)
        self.jobs_became_ready.emit(fresh)
        QApplication.beep()
