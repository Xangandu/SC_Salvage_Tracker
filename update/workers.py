"""Hintergrund-Threads für Update-Prüfung und Download."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from config.update import UpdateManifest
from update.service import check_for_update, download_update_file


class UpdateCheckWorker(QThread):
    finished = Signal(object, object)

    def __init__(self, db):
        super().__init__()
        self.db = db

    def run(self):
        manifest, error = check_for_update(self.db)
        self.finished.emit(manifest, error)


class UpdateDownloadWorker(QThread):
    progress = Signal(int, int)
    finished = Signal(object, object)

    def __init__(self, manifest: UpdateManifest):
        super().__init__()
        self.manifest = manifest

    def run(self):
        try:
            path = download_update_file(
                self.manifest,
                progress_callback=self.progress.emit,
            )
        except RuntimeError as error:
            self.finished.emit(None, str(error))
            return

        self.finished.emit(path, None)
