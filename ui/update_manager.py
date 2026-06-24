"""Update-Manager (rekonstruiert).

Siehe ``update/__init__.py`` für den Hintergrund: Diese Datei fehlte im
Repository, wird aber von ``ui/main_window.py`` (``from ui.update_manager
import UpdateManager``) beim Start importiert.

Die Implementierung ist bewusst minimal und ohne Netzwerkzugriff. Sie erfüllt
exakt die von den Aufrufern erwartete Schnittstelle:

* ``UpdateManager(db, parent)``
* Signal ``check_completed``
* ``run_startup_check()``
* ``set_auto_check(enabled)``
* ``check_for_updates(silent=False)``
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox

from config.version import APP_NAME, format_version_subtitle
from update.service import (
    is_auto_check_enabled,
    record_check,
    set_auto_check_enabled,
)


class UpdateManager(QObject):
    """Verwaltet die (lokale) Update-Prüfung des Programms."""

    check_completed = Signal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._parent_widget = parent

    def set_auto_check(self, enabled: bool) -> None:
        set_auto_check_enabled(self.db, bool(enabled))

    def run_startup_check(self) -> None:
        """Beim Start aufgerufen; prüft nur, wenn aktiviert."""
        if is_auto_check_enabled(self.db):
            self.check_for_updates(silent=True)

    def check_for_updates(self, silent: bool = False) -> None:
        """Prüfung durchführen (lokal) und Zeitpunkt vermerken.

        Online-Update-Prüfung über GitHub Releases ist in dieser
        rekonstruierten Fassung nicht enthalten; die aktuell installierte
        Version gilt als aktuell.
        """
        record_check(self.db)

        if not silent:
            QMessageBox.information(
                self._parent_widget,
                APP_NAME,
                "Es wird die aktuelle Version verwendet:\n"
                f"{format_version_subtitle()}",
            )

        self.check_completed.emit()
