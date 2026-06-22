"""
Star Citizen salvage materials (English UI labels).

Material flow:
  Session salvage -> RMC (sellable) + raw CM (Rubble / Scraps / Salvage)
  Raw CM -> Refinery -> CM (refined Construction Material, sellable)

CM is NEVER raw salvage input — only refinery output.
"""

# Directly sellable in Star Citizen
REFINED_SELLABLE_CODES = (
    "RMC",
    "CM",
)

# Raw CM — must be refined before sale
RAW_CM_MATERIAL_CODES = (
    "CM_RUBBLE",
    "CM_SCRAPS",
    "CM_SALVAGE",
)

REFINERY_INPUT_CODES = RAW_CM_MATERIAL_CODES
REFINERY_OUTPUT_CODE = "CM"

MATERIAL_LABELS = {
    "RMC": "RMC",
    "CM": "CM",
    "CM_RUBBLE": "CM Rubble",
    "CM_SCRAPS": "CM Scraps",
    "CM_SALVAGE": "CM Salvage",
}

CM_REFINERY_INPUTS = (
    "CM Rubble",
    "CM Scraps",
    "CM Salvage",
)

MATERIAL_UI_TO_CODE = {
    "CM Rubble": "CM_RUBBLE",
    "CM Scraps": "CM_SCRAPS",
    "CM Salvage": "CM_SALVAGE",
}

LEGACY_MATERIAL_UI_TO_CODE = {
    "CM-Schutt": "CM_RUBBLE",
    "CM-Schrott": "CM_SCRAPS",
    "CM-Salvage": "CM_SALVAGE",
}


def material_label(material_code):
    return MATERIAL_LABELS.get(
        material_code,
        material_code,
    )


def material_total_label(material_code):
    return f"{material_label(material_code)} TOTAL"


def is_raw_cm(material_code):
    return material_code in RAW_CM_MATERIAL_CODES


def is_refinery_output(material_code):
    return material_code == REFINERY_OUTPUT_CODE


def material_code_from_ui(label):
    if label in MATERIAL_UI_TO_CODE:
        return MATERIAL_UI_TO_CODE[label]

    if label in LEGACY_MATERIAL_UI_TO_CODE:
        return LEGACY_MATERIAL_UI_TO_CODE[label]

    return label


def resolve_material_label(name_or_code):
    if name_or_code in MATERIAL_LABELS:
        return material_label(name_or_code)

    if name_or_code in MATERIAL_UI_TO_CODE:
        return name_or_code

    if name_or_code in LEGACY_MATERIAL_UI_TO_CODE:
        return material_label(
            LEGACY_MATERIAL_UI_TO_CODE[name_or_code]
        )

    return name_or_code


# Welche Materialfelder pro Schiff bei der Erfassung aktiv sind
SHIP_MATERIAL_CODES = {
    "RSI Salvation": ("RMC", "CM_RUBBLE"),
    "Aegis Reclaimer": ("RMC", "CM_SALVAGE"),
    "Drake Vulture": ("CM_RUBBLE",),
    "MISC Fortune": ("CM_RUBBLE",),
    "ARGO MOTH": ("CM_SCRAPS",),
}


def material_codes_for_ship(ship_name: str) -> tuple[str, ...]:
    return SHIP_MATERIAL_CODES.get(
        ship_name,
        ("RMC", "CM_RUBBLE"),
    )
