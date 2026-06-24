"""Small persistence helpers for update checks."""

from config.dates import now_db_timestamp


UPDATE_AUTO_CHECK_KEY = "update_auto_check"
UPDATE_LAST_CHECK_KEY = "update_last_check"


def is_auto_check_enabled(db) -> bool:
    value = db.settings.get_app_setting(
        UPDATE_AUTO_CHECK_KEY,
        "1",
    )
    return str(value) == "1"


def set_auto_check_enabled(db, enabled: bool):
    db.settings.set_app_setting(
        UPDATE_AUTO_CHECK_KEY,
        "1" if enabled else "0",
    )


def get_last_check(db):
    return db.settings.get_app_setting(
        UPDATE_LAST_CHECK_KEY,
        "",
    )


def record_last_check(db):
    checked_at = now_db_timestamp()
    db.settings.set_app_setting(
        UPDATE_LAST_CHECK_KEY,
        checked_at,
    )
    return checked_at
