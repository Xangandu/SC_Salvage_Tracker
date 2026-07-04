"""Zentrale Schrift-Kategorien — ein Stil pro Verwendungszweck in der gesamten App."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from config.font_families import (
    DEFAULT_FONT_FAMILY,
    FONT_FAMILY_LABELS,
    resolve_body_font,
    resolve_heading_font,
)

TYPOGRAPHY_SETTINGS_KEY = "typography_json"
TYPOGRAPHY_BASELINE_KEY = "typography_baseline_json"

FONT_WEIGHT_OPTIONS = (
    ("normal", 400),
    ("600", 600),
    ("bold", 700),
    ("700", 700),
)

INHERIT_FAMILY = ""


@dataclass(frozen=True)
class TypographyCategory:
    category_id: str
    qss_selector: str
    preview_object_name: str
    label_key: str
    description_key: str
    preview_key: str
    default_family_role: str  # "heading" | "body"
    default_size_px: int
    default_weight: int
    default_letter_spacing_px: float
    default_color: str
    italic: bool = False


TYPOGRAPHY_CATEGORIES: tuple[TypographyCategory, ...] = (
    TypographyCategory(
        "page_heading",
        "QLabel#pageTitle, QLabel#dashboardContextTitle",
        "pageTitle",
        "typography.category.page_heading",
        "typography.category.page_heading.desc",
        "typography.preview.page_heading",
        "heading",
        30,
        700,
        3.0,
        "#EDEDED",
    ),
    TypographyCategory(
        "section_heading",
        (
            "QLabel#sectionAccent,"
            " QLabel#subSectionTitle,"
            " QLabel#sectionTitle,"
            " QLabel#navTitlePrimary,"
            " QLabel#navTitleSecondary,"
            " QLabel#navUserHeading,"
            " QLabel#navLanguageHeading,"
            " QLabel#warningBannerTitle,"
            " QLabel#dashboardSection,"
            " QLabel#dashboardMaterialGroupTitle,"
            " QLabel#panelTitle"
        ),
        "sectionAccent",
        "typography.category.section_heading",
        "typography.category.section_heading.desc",
        "typography.preview.section_heading",
        "heading",
        18,
        700,
        2.0,
        "#D97732",
    ),
    TypographyCategory(
        "body",
        (
            "QLabel#formLabel,"
            " QLabel#displayValue,"
            " QLabel#mutedLabel,"
            " QLabel#hintLabel,"
            " QLabel#statLabel,"
            " QLabel#cardTitle,"
            " QLabel#navUserName,"
            " QLabel#navRoleBadge,"
            " QLabel#navNetworkBadge,"
            " QLabel#dashboardContextHelp,"
            " QLabel#dashboardTimelineWhen,"
            " QLabel#mobiglasTitleLabel,"
            " QLabel#cardDetailLabel,"
            " QLabel#hudMarker"
        ),
        "formLabel",
        "typography.category.body",
        "typography.category.body.desc",
        "typography.preview.body",
        "body",
        14,
        600,
        0.0,
        "#C5D6E6",
    ),
    TypographyCategory(
        "data",
        (
            "QLabel#cardValue,"
            " QLabel#statValue,"
            " QLabel#refineryCountdownValue"
        ),
        "cardValue",
        "typography.category.data",
        "typography.category.data.desc",
        "typography.preview.data",
        "body",
        22,
        700,
        0.0,
        "#FFFFFF",
    ),
    TypographyCategory(
        "profit",
        "QLabel#profitLabel",
        "profitLabel",
        "typography.category.profit",
        "typography.category.profit.desc",
        "typography.preview.profit",
        "heading",
        22,
        700,
        0.0,
        "#F0A848",
    ),
    TypographyCategory(
        "button",
        (
            "QPushButton#primaryAction,"
            " QPushButton#secondaryAction,"
            " QPushButton#mobiglasTitleAction,"
            " #navButton,"
            " QPushButton#navUpdateBadge,"
            " QPushButton#navStorageBadge,"
            " QToolButton#dashboardAlertBell"
        ),
        "primaryAction",
        "typography.category.button",
        "typography.category.button.desc",
        "typography.preview.button",
        "heading",
        12,
        700,
        2.0,
        "#FFF8F2",
    ),
    TypographyCategory(
        "table_header",
        (
            "QTableWidget#dataTable QHeaderView::section,"
            " QTableWidget#historyTable QHeaderView::section,"
            " QTableWidget#editableTable QHeaderView::section"
        ),
        "formLabel",
        "typography.category.table_header",
        "typography.category.table_header.desc",
        "typography.preview.table_header",
        "heading",
        10,
        700,
        2.0,
        "#8FA3B8",
    ),
    TypographyCategory(
        "table_cell",
        (
            "QTableWidget#dataTable,"
            " QTableWidget#historyTable,"
            " QTableWidget#editableTable"
        ),
        "displayValue",
        "typography.category.table_cell",
        "typography.category.table_cell.desc",
        "typography.preview.table_cell",
        "body",
        15,
        400,
        0.0,
        "#D8E4EF",
    ),
    TypographyCategory(
        "input",
        (
            "QLineEdit,"
            " QComboBox,"
            " QSpinBox,"
            " QDoubleSpinBox,"
            " QTextEdit,"
            " QPlainTextEdit"
        ),
        "formLabel",
        "typography.category.input",
        "typography.category.input.desc",
        "typography.preview.input",
        "body",
        14,
        400,
        0.0,
        "#D9F4FF",
    ),
    TypographyCategory(
        "status",
        (
            "QLabel#emptyInfo,"
            " QLabel#infoValue,"
            " QLabel#warningBanner"
        ),
        "emptyInfo",
        "typography.category.status",
        "typography.category.status.desc",
        "typography.preview.status",
        "body",
        14,
        400,
        0.0,
        "#848484",
        italic=True,
    ),
    TypographyCategory(
        "tooltip",
        "QToolTip",
        "hintLabel",
        "typography.category.tooltip",
        "typography.category.tooltip.desc",
        "typography.preview.tooltip",
        "body",
        12,
        600,
        0.0,
        "#E8F0F6",
    ),
)

TYPOGRAPHY_CATEGORY_BY_ID = {
    category.category_id: category for category in TYPOGRAPHY_CATEGORIES
}

# Alte Einzelrollen → neue Kategorie (Migration gespeicherter Einstellungen)
LEGACY_ROLE_TO_CATEGORY: dict[str, str] = {
    "page_title": "page_heading",
    "dashboard_context_title": "page_heading",
    "window_title": "body",
    "section_accent": "section_heading",
    "subsection_title": "section_heading",
    "nav_section_heading": "section_heading",
    "nav_title_primary": "section_heading",
    "form_label": "body",
    "display_value": "body",
    "muted_label": "body",
    "hint_label": "body",
    "nav_user_name": "body",
    "card_title": "body",
    "stat_label": "body",
    "dashboard_timeline_when": "body",
    "card_value": "data",
    "stat_value": "data",
    "profit_label": "profit",
    "dialog_info_value": "status",
    "empty_info": "status",
    "table_header": "table_header",
    "table_cell": "table_cell",
    "table": "table_cell",
}

# Abwärtskompatibilität (alte Import-Namen)
TypographyRole = TypographyCategory
TYPOGRAPHY_ROLES = TYPOGRAPHY_CATEGORIES
TYPOGRAPHY_ROLE_BY_ID = TYPOGRAPHY_CATEGORY_BY_ID
TYPOGRAPHY_GROUPS = tuple()

# Theme-Standard (Star Citizen = Kategorie-Defaults); Dark/Light nur Abweichungen
THEME_TYPOGRAPHY_PATCHES: dict[str, dict[str, dict[str, Any]]] = {
    "dark": {
        "body": {"color": "#C5D6E6"},
        "data": {"color": "#EDEDED"},
        "profit": {"color": "#D97732"},
        "input": {"color": "#E0E0E0"},
        "table_cell": {"color": "#EDEDED"},
        "table_header": {"color": "#848484"},
    },
    "light": {
        "body": {"color": "#4A5561"},
        "data": {"color": "#1C2530"},
        "profit": {"color": "#C45A12"},
        "input": {"color": "#2C3844"},
        "table_cell": {"color": "#1C2530"},
        "table_header": {"color": "#5C6773"},
    },
}


def theme_typography_defaults(
    theme_id: str,
    *,
    global_family_id: str,
) -> dict[str, dict[str, Any]]:
    patches = (
        {}
        if theme_id == "star_citizen"
        else THEME_TYPOGRAPHY_PATCHES.get(theme_id, {})
    )

    return {
        category.category_id: merge_category_style(
            category,
            patches.get(category.category_id),
            global_family_id=global_family_id,
        )
        for category in TYPOGRAPHY_CATEGORIES
    }


def resolve_typography_baseline(
    baseline_json: Any,
    *,
    theme_id: str,
    global_family_id: str,
) -> dict[str, dict[str, Any]]:
    saved = normalize_typography_settings(baseline_json)
    theme_defaults = theme_typography_defaults(
        theme_id,
        global_family_id=global_family_id,
    )
    if not saved:
        return theme_defaults
    return {
        category.category_id: (
            merge_category_style(
                category,
                saved[category.category_id],
                global_family_id=global_family_id,
            )
            if category.category_id in saved
            else theme_defaults[category.category_id]
        )
        for category in TYPOGRAPHY_CATEGORIES
    }


def resolve_typography_for_ui(
    active_json: Any,
    baseline_json: Any,
    *,
    theme_id: str,
    global_family_id: str,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Anzeige-Werte und Reset-Basis (eigenes Theme oder Theme-Standard)."""
    baseline = resolve_typography_baseline(
        baseline_json,
        theme_id=theme_id,
        global_family_id=global_family_id,
    )
    theme_defaults = theme_typography_defaults(
        theme_id,
        global_family_id=global_family_id,
    )
    active = normalize_typography_settings(active_json)
    if not active:
        return theme_defaults, baseline

    display = {
        category.category_id: (
            merge_category_style(
                category,
                active[category.category_id],
                global_family_id=global_family_id,
            )
            if category.category_id in active
            else theme_defaults[category.category_id]
        )
        for category in TYPOGRAPHY_CATEGORIES
    }
    return display, baseline


def serialize_typography_form(
    form_values: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    saved: dict[str, dict[str, Any]] = {}
    for category in TYPOGRAPHY_CATEGORIES:
        style = form_values.get(category.category_id)
        if not isinstance(style, dict):
            continue
        saved[category.category_id] = {
            "family_id": style.get("family_id", INHERIT_FAMILY),
            "size_px": int(style.get("size_px", category.default_size_px)),
            "weight": int(style.get("weight", category.default_weight)),
            "letter_spacing_px": float(
                style.get(
                    "letter_spacing_px",
                    category.default_letter_spacing_px,
                )
                or 0
            ),
            "color": str(style.get("color", category.default_color)).upper(),
            "italic": bool(style.get("italic", category.italic)),
        }
    return saved


def typography_category_ids() -> tuple[str, ...]:
    return tuple(category.category_id for category in TYPOGRAPHY_CATEGORIES)


def resolve_category_family(
    category: TypographyCategory,
    *,
    family_id: str,
    override_family_id: str = "",
    theme_id: str = "star_citizen",
) -> str:
    chosen = (override_family_id or "").strip()
    if chosen and chosen in FONT_FAMILY_LABELS:
        effective_id = chosen
    elif family_id in FONT_FAMILY_LABELS:
        effective_id = family_id
    else:
        effective_id = DEFAULT_FONT_FAMILY

    if category.default_family_role == "heading":
        return resolve_heading_font(effective_id)
    return resolve_body_font(effective_id, theme_id=theme_id)


def category_default_style(
    category: TypographyCategory,
    *,
    family_id: str,
) -> dict[str, Any]:
    del family_id
    return {
        "family_id": INHERIT_FAMILY,
        "size_px": category.default_size_px,
        "weight": category.default_weight,
        "letter_spacing_px": category.default_letter_spacing_px,
        "color": category.default_color,
        "italic": category.italic,
    }


role_default_style = category_default_style


def merge_category_style(
    category: TypographyCategory,
    override: dict[str, Any] | None,
    *,
    global_family_id: str,
) -> dict[str, Any]:
    del global_family_id
    base = category_default_style(category, family_id=DEFAULT_FONT_FAMILY)
    if not override:
        return base
    merged = dict(base)
    for key in (
        "family_id",
        "size_px",
        "weight",
        "letter_spacing_px",
        "color",
        "italic",
    ):
        if key not in override:
            continue
        value = override[key]
        if value is None:
            continue
        if key == "family_id" and value == INHERIT_FAMILY:
            merged[key] = INHERIT_FAMILY
            continue
        if key == "color" and not str(value).strip():
            continue
        merged[key] = value
    return merged


merge_role_style = merge_category_style


def _clean_category_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: payload[key]
        for key in (
            "family_id",
            "size_px",
            "weight",
            "letter_spacing_px",
            "color",
            "italic",
        )
        if key in payload
    }


def migrate_typography_settings(raw: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if not raw:
        return {}

    migrated: dict[str, dict[str, Any]] = {}
    for key, payload in raw.items():
        if not isinstance(payload, dict):
            continue
        if key in TYPOGRAPHY_CATEGORY_BY_ID:
            migrated[key] = _clean_category_payload(payload)
            continue
        category_id = LEGACY_ROLE_TO_CATEGORY.get(key)
        if category_id is None:
            continue
        migrated[category_id] = _clean_category_payload(payload)

    combined_table = raw.get("table")
    if isinstance(combined_table, dict):
        cleaned = _clean_category_payload(combined_table)
        if "table_header" not in migrated:
            migrated["table_header"] = dict(cleaned)
        if "table_cell" not in migrated:
            migrated["table_cell"] = dict(cleaned)

    return migrated


def normalize_typography_settings(raw: Any) -> dict[str, dict[str, Any]]:
    if not raw:
        return {}
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return {}
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return {}
    if not isinstance(raw, dict):
        return {}
    return migrate_typography_settings(raw)


def serialize_typography_settings(settings: dict[str, dict[str, Any]]) -> str:
    return json.dumps(
        normalize_typography_settings(settings),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def category_has_custom_override(
    category: TypographyCategory,
    override: dict[str, Any] | None,
) -> bool:
    if not override:
        return False
    defaults = category_default_style(category, family_id=DEFAULT_FONT_FAMILY)
    for key, default_value in defaults.items():
        if key not in override:
            continue
        value = override[key]
        if key == "family_id":
            if value not in (None, "", INHERIT_FAMILY):
                return True
            continue
        if key == "color":
            if str(value or "").strip() and str(value).upper() != str(
                default_value
            ).upper():
                return True
            continue
        if value != default_value:
            return True
    return False


role_has_custom_override = category_has_custom_override


def collect_effective_typography(
    overrides: dict[str, dict[str, Any]] | None,
    *,
    global_family_id: str,
) -> dict[str, dict[str, Any]]:
    normalized = normalize_typography_settings(overrides)
    return {
        category.category_id: merge_category_style(
            category,
            normalized.get(category.category_id),
            global_family_id=global_family_id,
        )
        for category in TYPOGRAPHY_CATEGORIES
    }


def typography_role_ids() -> tuple[str, ...]:
    return typography_category_ids()
