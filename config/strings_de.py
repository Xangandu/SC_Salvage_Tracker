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
