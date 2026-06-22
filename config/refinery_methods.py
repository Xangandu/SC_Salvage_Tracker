"""Raffinerie-Verfahren (Star Citizen) — keine festen Ausbeute-Faktoren."""

REFINERY_METHODS = (
    "Ferron",
    "Dinyx",
    "Pyrometric",
    "So-Hon",
    "Koben",
    "Lyon",
    "Timberline",
    "Thermite",
    "Crown",
)


def calc_refinery_efficiency(
    output_scu: float,
    input_scu: float,
) -> float | None:
    """Ausbeute in % — nur berechnen, nicht speichern."""
    if input_scu is None or input_scu <= 0:
        return None
    if output_scu is None or output_scu < 0:
        return None
    return (float(output_scu) / float(input_scu)) * 100.0
