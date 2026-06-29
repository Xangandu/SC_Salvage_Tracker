"""Star Citizen cargo units — Raffinerie-Terminal (cSCU) vs. Tracker (SCU)."""

# Ingame-Raffinerie arbeitet in centi-SCU; 1000 cSCU = 10 SCU.
CSCU_PER_SCU = 100


def scu_to_cscu(scu: float) -> int:
    """SCU → cSCU (Terminal-Anzeige)."""
    return round(float(scu) * CSCU_PER_SCU)


def cscu_to_scu(cscu: float) -> float:
    """cSCU → SCU (Tracker-Buchung)."""
    return float(cscu) / CSCU_PER_SCU


def format_scu_from_cscu_hint(cscu: float) -> str:
    """Kurzer Hinweistext: cSCU → SCU."""
    from config.i18n import format_number

    scu = cscu_to_scu(cscu)
    return f"{format_number(cscu, 0)} cSCU = {format_number(scu, 0)} SCU"
