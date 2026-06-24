from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox

from update.service import (
    is_auto_check_enabled,
    record_last_check,
    set_auto_check_enabled,
)


class UpdateManager(QObject):
    check_completed = Signal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.parent = parent

    def set_auto_check(self, enabled: bool):
        set_auto_check_enabled(self.db, enabled)
        self.check_completed.emit()

    def run_startup_check(self):
        if is_auto_check_enabled(self.db):
            self.check_for_updates(silent=True)

    def check_for_updates(self, *, silent: bool = False):
        record_last_check(self.db)

        if not silent:
            QMessageBox.information(
                self.parent,
                "Updates",
                "Die Update-Prüfung wurde abgeschlossen.\n\n"
                "Es ist noch keine Update-Quelle konfiguriert.",
            )

        self.check_completed.emit()
