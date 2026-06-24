"""Persistenz der Update-Einstellungen (rekonstruiert).

Siehe ``update/__init__.py`` für den Hintergrund. Die Funktionen lesen und
schreiben ausschließlich die App-Einstellungen, die bereits in
``database/settings_repository.py`` (``DEFAULT_APP_SETTINGS``) definiert sind:

* ``update_auto_check``  — "1"/"0", ob beim Start geprüft werden soll
* ``update_last_check``  — Zeitstempel der letzten Prüfung (DB-Format)

Bewusst ohne Netzwerkzugriff, damit der Programmstart in jeder Umgebung
funktioniert.
"""

from __future__ import annotations

from config.dates import now_db_timestamp

AUTO_CHECK_KEY = "update_auto_check"
LAST_CHECK_KEY = "update_last_check"


def is_auto_check_enabled(db) -> bool:
    """True, wenn beim Start automatisch nach Updates gesucht werden soll."""
    return db.settings.get_app_setting(AUTO_CHECK_KEY, "1") == "1"


def set_auto_check_enabled(db, enabled: bool) -> None:
    db.settings.set_app_setting(
        AUTO_CHECK_KEY,
        "1" if enabled else "0",
    )


def get_last_check(db):
    """Zeitstempel der letzten Update-Prüfung oder ``None``."""
    value = db.settings.get_app_setting(LAST_CHECK_KEY, "")
    return value or None


def record_check(db) -> str:
    """Aktuellen Zeitpunkt als letzte Prüfung speichern und zurückgeben."""
    timestamp = now_db_timestamp()
    db.settings.set_app_setting(LAST_CHECK_KEY, timestamp)
    return timestamp
