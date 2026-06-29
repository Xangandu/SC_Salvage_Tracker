"""Raffinerie-Verfahren (Star Citizen) — Reihenfolge wie ingame / UEX."""

REFINERY_METHODS = (
    "Cormack",
    "Dinyx Solventation",
    "Electrostarolysis",
    "Ferron Exchange",
    "Gaskin Process",
    "Kazen Winnowing",
    "Pyrometric Chromalysis",
    "Thermonatic Deposition",
    "XCR Reaction",
)

# Alte Tracker-Einträge (Kurznamen vor 0.16)
LEGACY_REFINERY_METHOD_ALIASES = {
    "Ferron": "Ferron Exchange",
    "Dinyx": "Dinyx Solventation",
    "Pyrometric": "Pyrometric Chromalysis",
    "So-Hon": "Thermonatic Deposition",
    "Koben": "Kazen Winnowing",
    "Lyon": "Electrostarolysis",
    "Timberline": "Ferron Exchange",
    "Thermite": "Pyrometric Chromalysis",
    "Crown": "Cormack",
}


def display_refinery_method(method: str) -> str:
    if not method:
        return ""
    return LEGACY_REFINERY_METHOD_ALIASES.get(method, method)


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
