STATUS_LABELS = {
    "ACTIVE": "AKTIV",
    "WAITING_FOR_REFINERY": "WARTET AUF RAFFINERIE",
    "WAITING_FOR_SALE": "VERKAUFSBEREIT",
    "WAITING_FOR_PAYOUT": "AUSZAHLUNG",
    "REFINERY_COMPLETED": "VERKAUFSBEREIT",
    "SOLD": "VERKAUFT",
    "IDLE": "LEERLAUF",
}


def status_label(status):
    return STATUS_LABELS.get(status, status)


def format_number_de(value, decimals=0):
    """Deutsches Zahlenformat: 1.234,56 (Punkt = Tausender, Komma = Dezimal)."""
    formatted = f"{value:,.{decimals}f}"

    if decimals:
        return (
            formatted.replace(",", "§")
            .replace(".", ",")
            .replace("§", ".")
        )

    return formatted.replace(",", ".")


def parse_number_de(text, default=None):
    """Parst deutsche oder englische Zahleneingabe (1.234,56 · 12,5 · 12.5)."""
    if text is None:
        return default

    value = str(text).strip().replace("\u00a0", "").replace(" ", "")
    if not value:
        return default

    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    elif value.count(".") == 1:
        before, after = value.split(".")
        if len(after) == 3 and after.isdigit() and before.isdigit():
            value = before + after
    elif value.count(".") > 1:
        value = value.replace(".", "")

    try:
        return float(value)
    except ValueError:
        return default


def parse_int_de(text, default=None):
    """Ganzzahl aus deutscher oder englischer Eingabe."""
    number = parse_number_de(text, default=None)
    if number is None:
        return default

    try:
        return int(round(number))
    except (TypeError, ValueError):
        return default
