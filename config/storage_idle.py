"""Idle-Erkennung für Lagerbestände (Phase C)."""

from __future__ import annotations

from datetime import datetime

from config.dates import parse_datetime
from config.i18n import tr

IDLE_WARNING_DAYS = 10
DEFAULT_RESERVE_TAG = "Reserve"


def _parse_timestamp(value) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    text = str(value).strip()
    if not text:
        return None

    try:
        return parse_datetime(text)
    except ValueError:
        return None


def days_since(value, *, now: datetime | None = None) -> int | None:
    parsed = _parse_timestamp(value)
    if parsed is None:
        return None

    reference = now or datetime.now()
    return max(0, (reference - parsed).days)


def has_reserve_tag(entry: dict) -> bool:
    return bool((entry.get("reserve_tag") or "").strip())


def is_idle_candidate(
    entry: dict,
    *,
    now: datetime | None = None,
) -> bool:
    if entry.get("status") != "STORED":
        return False

    if float(entry.get("quantity_scu") or 0) <= 0:
        return False

    if has_reserve_tag(entry):
        return False

    idle_days = days_since(entry.get("last_activity_at"), now=now)
    if idle_days is None:
        return False

    return idle_days >= IDLE_WARNING_DAYS


def should_show_idle_warning(
    entry: dict,
    *,
    now: datetime | None = None,
) -> bool:
    if not is_idle_candidate(entry, now=now):
        return False

    reminded_at = entry.get("idle_reminded_at")
    if not (reminded_at or "").strip():
        return True

    reminded_days = days_since(reminded_at, now=now)
    if reminded_days is None:
        return True

    return reminded_days >= IDLE_WARNING_DAYS


def format_relative_activity(value, *, now: datetime | None = None) -> str:
    parsed = _parse_timestamp(value)
    if parsed is None:
        return "—"

    reference = now or datetime.now()
    delta = reference - parsed
    days = max(0, delta.days)

    if days == 0:
        return tr("storage.activity.today")
    if days == 1:
        return tr("storage.activity.yesterday")

    return tr("storage.activity.days_ago", days=days)
