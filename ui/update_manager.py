"""Koordination von Update-Prüfung, Dialog und Installation."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QMessageBox

from config.update import UpdateManifest
from config.i18n import tr
from config.version import APP_EDITION, format_version_subtitle
from ui.mobiglas_message_box import question as mobiglas_question
from ui.update_dialog import (
    UpdateAvailableDialog,
    UpdateDialogResult,
    UpdateDownloadDialog,
    UpdateInstallConfirmDialog,
)
from update.service import (
    can_launch_installer,
    get_network_update_warning,
    install_path_source_label,
    is_auto_check_enabled,
    is_install_path_known,
    launch_installer,
    record_last_check,
    resolve_update_install_dir,
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
                    tr("update.manager.dialog.title"),
                    tr("update.manager.check_running"),
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
                    tr("update.manager.dialog.title"),
                    tr("update.manager.check_failed", error=error),
                )
            return

        if manifest is None:
            if not silent:
                QMessageBox.warning(
                    self.parent,
                    tr("update.manager.dialog.title"),
                    tr("update.manager.manifest_failed"),
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
                tr("update.manager.dialog.title"),
                tr(
                    "update.manager.up_to_date",
                    version=format_version_subtitle(),
                ),
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
            tr("update.manager.notify.title"),
            tr(
                "update.manager.notify.message",
                version=manifest.version_display,
                build=manifest.build,
            ),
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

    def _resolve_install_target(self) -> tuple[str, str] | None:
        edition = APP_EDITION or "solo"
        install_dir, source = resolve_update_install_dir(edition)
        source_label = install_path_source_label(source)
        return str(install_dir), source_label

    def _start_install(self, manifest):
        if not can_launch_installer():
            QMessageBox.information(
                self.parent,
                tr("update.manager.dialog.title"),
                tr(
                    "update.manager.installer_unavailable",
                    url=manifest.download.url,
                ),
            )
            return

        warning = get_network_update_warning()
        if warning:
            answer = QMessageBox.question(
                self.parent,
                tr("update.manager.network_active.title"),
                tr(
                    "update.manager.network_active.continue",
                    warning=warning,
                ),
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        target = self._resolve_install_target()
        if target is None:
            return
        install_dir, source_label = target

        edition = APP_EDITION or "solo"
        resolved_dir, source = resolve_update_install_dir(edition)
        if not is_install_path_known(source):
            answer = QMessageBox.warning(
                self.parent,
                tr("update.manager.install_confirm.title"),
                tr(
                    "update.manager.install_path.unknown",
                    install_dir=str(resolved_dir),
                ),
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        confirm = QMessageBox.question(
            self.parent,
            tr("update.manager.install_confirm.title"),
            tr(
                "update.manager.install_confirm.message",
                install_dir=install_dir,
                source_label=source_label,
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self._download_and_install(manifest, install_dir, source_label)

    def _download_and_install(
        self,
        manifest: UpdateManifest,
        install_dir: str,
        source_label: str,
    ):
        if (
            self._download_worker
            and self._download_worker.isRunning()
        ):
            return

        progress_dialog = UpdateDownloadDialog(
            manifest,
            self.parent,
            install_dir=install_dir,
            install_source_label=source_label,
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
                manifest,
                install_dir,
                source_label,
            )
        )
        self._download_worker.start()

    def _on_download_finished(
        self,
        path,
        error,
        progress_dialog,
        manifest,
        install_dir,
        source_label,
    ):
        progress_dialog.close()

        if error:
            QMessageBox.warning(
                self.parent,
                tr("update.manager.download.title"),
                tr("update.manager.download.failed", error=error),
            )
            return

        confirm_dialog = UpdateInstallConfirmDialog(
            manifest,
            install_dir,
            source_label,
            self.parent,
        )
        if confirm_dialog.exec() != confirm_dialog.DialogCode.Accepted:
            return

        try:
            launch_installer(path)
        except RuntimeError as launch_error:
            QMessageBox.warning(
                self.parent,
                tr("update.manager.install.title"),
                str(launch_error),
            )
            return

        QApplication.instance().quit()
