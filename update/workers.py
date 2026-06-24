"""Hintergrund-Threads für Update-Prüfung und Download."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from config.update import UpdateManifest
from update.service import download_update_file, fetch_update_manifest_online


class UpdateCheckWorker(QThread):
    check_done = Signal(object, object)

    def run(self):
        manifest, error = fetch_update_manifest_online()
        self.check_done.emit(manifest, error)


class UpdateDownloadWorker(QThread):
    progress = Signal(int, int)
    download_done = Signal(object, object)

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
            self.download_done.emit(None, str(error))
            return

        self.download_done.emit(path, None)
