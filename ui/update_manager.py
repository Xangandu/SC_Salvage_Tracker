"""Koordination von Update-Prüfung, Dialog und Installation."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QMessageBox

from config.update import UpdateManifest
from config.version import format_version_subtitle
from ui.mobiglas_message_box import question as mobiglas_question
from ui.update_dialog import (
    UpdateAvailableDialog,
    UpdateDialogResult,
    UpdateDownloadDialog,
)
from update.service import (
    can_launch_installer,
    get_network_update_warning,
    is_auto_check_enabled,
    launch_installer,
    record_last_check,
    set_auto_check_enabled,
    set_skipped_version,
    should_offer_update,
)
from update.workers import UpdateCheckWorker, UpdateDownloadWorker


class UpdateManager(QObject):

    check_completed = Signal()
    update_available = Signal(object)
    update_cleared = Signal()

    def __init__(self, db, parent_widget):
        super().__init__(parent_widget)
        self.db = db
        self.parent = parent_widget
        self._check_worker = None
        self._download_worker = None
        self._startup_check_done = False
        self._pending_manifest: UpdateManifest | None = None

    @property
    def pending_update(self) -> UpdateManifest | None:
        return self._pending_manifest

    def show_pending_update(self):
        if self._pending_manifest is None:
            return
        self._show_update_dialog(self._pending_manifest)

    def run_startup_check(self):
        if self._startup_check_done:
            return
        self._startup_check_done = True

        if not is_auto_check_enabled(self.db):
            return

        self.check_for_updates(silent=True)

    def set_auto_check(self, enabled: bool):
        set_auto_check_enabled(self.db, enabled)

    def check_for_updates(self, *, silent: bool = False):
        if self._check_worker and self._check_worker.isRunning():
            if not silent:
                QMessageBox.information(
                    self.parent,
                    "Updates",
                    "Es läuft bereits eine Update-Prüfung.",
                )
            return

        self._check_worker = UpdateCheckWorker()
        self._check_worker.check_done.connect(
            lambda manifest, error: self._on_check_finished(
                manifest,
                error,
                silent=silent,
            )
        )
        self._check_worker.start()

    def _on_check_finished(self, manifest, error, *, silent: bool):
        self.check_completed.emit()

        if error:
            if not silent:
                QMessageBox.warning(
                    self.parent,
                    "Updates",
                    f"Update-Prüfung fehlgeschlagen:\n\n{error}",
                )
            return

        if manifest is None:
            if not silent:
                QMessageBox.warning(
                    self.parent,
                    "Updates",
                    "Update-Manifest konnte nicht gelesen werden.",
                )
            return

        record_last_check(self.db)

        if should_offer_update(self.db, manifest):
            self._set_pending_update(manifest)
            if silent:
                self._notify_update_available(manifest)
            else:
                self._show_update_dialog(manifest)
            return

        self._clear_pending_update()

        if not silent:
            QMessageBox.information(
                self.parent,
                "Updates",
                "Sie verwenden bereits die neueste Version.\n\n"
                f"{format_version_subtitle()}",
            )

    def _set_pending_update(self, manifest: UpdateManifest):
        self._pending_manifest = manifest
        self.update_available.emit(manifest)

    def _clear_pending_update(self):
        if self._pending_manifest is None:
            return
        self._pending_manifest = None
        self.update_cleared.emit()

    def _notify_update_available(self, manifest: UpdateManifest):
        answer = mobiglas_question(
            self.parent,
            "Neues Update verfügbar",
            f"Version {manifest.version_display} "
            f"(Build {manifest.build}) ist auf GitHub verfügbar.\n\n"
            "Möchten Sie die Update-Details anzeigen?",
            buttons=QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            default_button=QMessageBox.StandardButton.Yes,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._show_update_dialog(manifest)

    def _show_update_dialog(self, manifest):
        dialog = UpdateAvailableDialog(manifest, self.parent)
        dialog.exec()

        if dialog.result_action == UpdateDialogResult.INSTALL:
            self._start_install(manifest)
        elif dialog.result_action == UpdateDialogResult.SKIP:
            set_skipped_version(self.db, manifest.version)
            self._clear_pending_update()

    def _start_install(self, manifest):
        if not can_launch_installer():
            QMessageBox.information(
                self.parent,
                "Updates",
                "Die automatische Installation ist nur in der "
                "installierten Windows-Version verfügbar.\n\n"
                f"Laden Sie das Update manuell herunter:\n"
                f"{manifest.download.url}",
            )
            return

        warning = get_network_update_warning()
        if warning:
            answer = QMessageBox.question(
                self.parent,
                "Netzwerk aktiv",
                f"{warning}\n\nTrotzdem fortfahren?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        confirm = QMessageBox.question(
            self.parent,
            "Update installieren",
            "Die App wird geschlossen und das Update im Hintergrund "
            "installiert.\n\nFortfahren?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self._download_and_install(manifest)

    def _download_and_install(self, manifest):
        if (
            self._download_worker
            and self._download_worker.isRunning()
        ):
            return

        progress_dialog = UpdateDownloadDialog(
            manifest,
            self.parent,
        )
        progress_dialog.show()

        self._download_worker = UpdateDownloadWorker(manifest)
        self._download_worker.progress.connect(
            progress_dialog.set_progress
        )
        self._download_worker.download_done.connect(
            lambda path, error: self._on_download_finished(
                path,
                error,
                progress_dialog,
            )
        )
        self._download_worker.start()

    def _on_download_finished(self, path, error, progress_dialog):
        progress_dialog.close()

        if error:
            QMessageBox.warning(
                self.parent,
                "Download",
                f"Das Update konnte nicht heruntergeladen werden:\n\n"
                f"{error}",
            )
            return

        try:
            launch_installer(path)
        except RuntimeError as launch_error:
            QMessageBox.warning(
                self.parent,
                "Installation",
                str(launch_error),
            )
            return

        QApplication.instance().quit()
