"""Deutsche Datums-/Zeitformate für UI und Eingabe.

Alle Zeitstempel nutzen die lokale Systemzeit (Windows-Zeitzone des
jeweiligen Rechners) — z. B. MESZ in Deutschland oder EST in den USA.
"""

from datetime import date, datetime

# SQLite: datetime('now') ist UTC — immer localtime für Speicherung.
SQLITE_LOCAL_NOW = "datetime('now', 'localtime')"
SQLITE_LOCAL_DATE = "date('now', 'localtime')"

DISPLAY_DATE_FMT = "%d.%m.%Y"
DISPLAY_DATETIME_FMT = "%d.%m.%Y %H:%M"
DISPLAY_DATETIME_SECONDS_FMT = "%d.%m.%Y %H:%M:%S"

DB_DATE_FMT = "%Y-%m-%d"
DB_DATETIME_FMT = "%Y-%m-%d %H:%M:%S"
DB_DATETIME_MS_FMT = "%Y-%m-%d %H:%M:%S.%f"

_DATE_INPUT_FORMATS = (
    DISPLAY_DATE_FMT,
    "%d.%m.%y",
    DB_DATE_FMT,
)

_DATETIME_INPUT_FORMATS = (
    DISPLAY_DATETIME_SECONDS_FMT,
    DISPLAY_DATETIME_FMT,
    DB_DATETIME_MS_FMT,
    DB_DATETIME_FMT,
    "%Y-%m-%d %H:%M",
)


def today_display():
    return datetime.now().strftime(DISPLAY_DATE_FMT)


def now_db_timestamp():
    return datetime.now().strftime(DB_DATETIME_FMT)


def parse_date(value):
    text = (value or "").strip()

    if not text:
        raise ValueError("Bitte ein Datum angeben.")

    for fmt in _DATE_INPUT_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    raise ValueError(
        "Ungültiges Datum. Bitte TT.MM.JJJJ verwenden."
    )


def parse_datetime(value):
    text = (value or "").strip()

    if not text:
        raise ValueError("Ungültiger Zeitstempel.")

    for fmt in _DATETIME_INPUT_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    raise ValueError("Ungültiges Datum oder Uhrzeit.")


def normalize_date_input(value):
    return parse_date(value).strftime(DISPLAY_DATE_FMT)


def format_date(value):
    if value is None:
        return "—"

    if isinstance(value, datetime):
        return value.strftime(DISPLAY_DATE_FMT)

    if isinstance(value, date):
        return value.strftime(DISPLAY_DATE_FMT)

    text = str(value).strip()

    if not text:
        return "—"

    try:
        return parse_date(text).strftime(DISPLAY_DATE_FMT)
    except ValueError:
        pass

    try:
        return parse_datetime(text).strftime(DISPLAY_DATE_FMT)
    except ValueError:
        return text


def _parse_iso_datetime(text: str) -> datetime | None:
    """ISO-8601 (z. B. alte UTC-Speicherung) in lokale Anzeigezeit."""
    cleaned = text.strip()
    if not cleaned or "T" not in cleaned:
        return None
    try:
        parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def format_datetime(value, with_seconds=False):
    if value is None:
        return "—"

    if isinstance(value, datetime):
        fmt = (
            DISPLAY_DATETIME_SECONDS_FMT
            if with_seconds
            else DISPLAY_DATETIME_FMT
        )
        return value.strftime(fmt)

    text = str(value).strip()

    if not text:
        return "—"

    try:
        parsed = parse_datetime(text)
    except ValueError:
        parsed = _parse_iso_datetime(text)
        if parsed is None:
            return format_date(text)

    fmt = (
        DISPLAY_DATETIME_SECONDS_FMT
        if with_seconds
        else DISPLAY_DATETIME_FMT
    )
    return parsed.strftime(fmt)
