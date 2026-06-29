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
    "Drake Vulture": ("RMC", "CM_RUBBLE"),
    "MISC Fortune": ("CM_RUBBLE",),
    "Argo Moth": ("RMC", "CM_SCRAPS"),
}

# Anzeigereihenfolge: Solo → kleine Crew → Reclaimer
SALVAGE_SHIP_SORT_ORDER = (
    "RSI Salvation",
    "MISC Fortune",
    "Drake Vulture",
    "Argo Moth",
    "Aegis Reclaimer",
)

# Kurzname → voller Sitzungsname (Legacy / Tests)
SHIP_NAME_ALIASES = {
    "Vulture": "Drake Vulture",
    "Salvation": "RSI Salvation",
    "Fortune": "MISC Fortune",
    "MOTH": "Argo Moth",
    "ARGO MOTH": "Argo Moth",
    "ARGO Moth": "Argo Moth",
    "Argo MOTH": "Argo Moth",
    "Reclaimer": "Aegis Reclaimer",
}


def normalize_ship_name(ship_name: str) -> str:
    name = (ship_name or "").strip()
    return SHIP_NAME_ALIASES.get(name, name)


def ship_sort_key(ship_name: str) -> tuple[int, str]:
    normalized = normalize_ship_name(ship_name)
    try:
        return (
            SALVAGE_SHIP_SORT_ORDER.index(normalized),
            normalized.casefold(),
        )
    except ValueError:
        return (len(SALVAGE_SHIP_SORT_ORDER), normalized.casefold())


def material_codes_for_ship(ship_name: str) -> tuple[str, ...]:
    normalized = normalize_ship_name(ship_name)
    return SHIP_MATERIAL_CODES.get(
        normalized,
        ("RMC", "CM_RUBBLE"),
    )


def ship_supports_material(
    ship_name: str,
    material_code: str,
) -> bool:
    return material_code in material_codes_for_ship(ship_name)


def materials_summary_for_ship(ship_name: str) -> str:
    codes = material_codes_for_ship(ship_name)
    if not ship_name:
        return "—"
    return ", ".join(material_label(code) for code in codes)
