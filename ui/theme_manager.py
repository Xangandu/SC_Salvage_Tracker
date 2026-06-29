"""Zentrales Theme-System — lädt, speichert und wendet UI-Themes an."""

from __future__ import annotations

import json
import re
from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QTableWidget,
    QWidget,
)

from config.debug import debug_log
from config.font_families import (
    DEFAULT_FONT_FAMILY,
    FONT_FAMILY_LABELS,
    apply_font_family_to_qss,
    dashboard_label_fonts,
    resolve_body_font,
    resolve_heading_font,
)

THEMES_DIR = Path(__file__).parent / "themes"
PALETTES_DIR = THEMES_DIR / "palettes"

THEME_IDS = ("dark", "star_citizen", "light")

THEME_LABELS = {
    "dark": "Dark",
    "star_citizen": "Star Citizen",
    "light": "Light",
}

FONT_SIZE_MAP = {
    "small": 14,
    "normal": 16,
    "large": 18,
}

FONT_SIZE_LABELS = {
    "small": "Klein",
    "normal": "Normal",
    "large": "Groß",
}

NAV_WIDTH_LABELS = {
    "narrow": "Schmal",
    "normal": "Normal",
    "wide": "Breit",
}

NAV_WIDTH_PX = {
    "narrow": (188, 208),
    "normal": (248, 268),
    "wide": (288, 308),
}

LAUNCHER_FONT_NAMES = ('"Rajdhani"', '"Orbitron"')
SYSTEM_FONT_NAME = '"Segoe UI"'

ANIMATION_LABELS = {
    "off": "Aus",
    "reduced": "Reduziert",
    "full": "Voll",
}

DASHBOARD_LAYOUT_LABELS = {
    "classic": "Classic",
    "operations": "Operations",
    "refinery": "Refinery",
    "storage": "Storage",
}

DEFAULT_DASHBOARD_FONT_SCALE = 100
DASHBOARD_FONT_SCALE_MIN = 50
DASHBOARD_FONT_SCALE_MAX = 250
DASHBOARD_FONT_BASE_PX = 14

DASHBOARD_FONT_LABEL_NAMES = frozenset({
    "pageTitle",
    "dashboardContextHelp",
    "dashboardTimelineWhen",
    "sectionAccent",
    "subSectionTitle",
    "formLabel",
    "displayValue",
    "mutedLabel",
    "cardTitle",
    "cardValue",
    "profitLabel",
    "statValue",
    "dashboardKpiDigit",
    "dashboardKpiDigitAccent",
    "dashboardCatalogTitle",
    "dashboardCatalogHint",
    "dashboardCatalogDropLabel",
    "dashboardCatalogLabel",
})

DASHBOARD_FONT_PREVIEW_RULES = (
    ("QFrame#dashboardFontPreviewCard QLabel", DASHBOARD_FONT_BASE_PX),
    ("QLabel#dashboardFontPreviewHint", DASHBOARD_FONT_BASE_PX),
)

TRANSPARENCY_OPTIONS = (0, 25, 50, 75, 100)
PANEL_TRANSPARENCY_OPTIONS = tuple(range(0, 101, 5))

TABLE_DENSITY_LABELS = {
    "compact": "Kompakt",
    "normal": "Normal",
    "spacious": "Geräumig",
}

TABLE_DENSITY_ROW_HEIGHT = {
    "compact": 28,
    "normal": 36,
    "spacious": 46,
}

TABLE_DENSITY_PADDING = {
    "compact": {
        "item_v": 4,
        "item_h": 6,
        "header_v": 6,
        "header_h": 8,
        "header_font": 9,
    },
    "normal": {
        "item_v": 8,
        "item_h": 10,
        "header_v": 10,
        "header_h": 12,
        "header_font": 10,
    },
    "spacious": {
        "item_v": 12,
        "item_h": 14,
        "header_v": 14,
        "header_h": 16,
        "header_font": 11,
    },
}

TABLE_OBJECT_NAMES = (
    "dataTable",
    "historyTable",
    "editableTable",
)

# Alle Akzent-/Highlight-Farben (Cyan, Blau, Orange, Gold) — für Benutzer-Akzent
ACCENT_REPLACE_COLORS = (
    "#FF8C00",
    "#00D9FF",
    "#55E8FF",
    "#0A9CC0",
    "#1E5167",
    "#1A4A61",
    "#4A90E2",
    "#6BA3E8",
    "#3A7BC8",
    "#0078D7",
    "#005A9E",
    "#C9A227",
    "#FFC857",
    "#FFE8A3",
    "#B8860B",
    "#CCE4F7",
    "#E8F4FC",
)

# Star-Citizen-Dunkelfarben → helle Grautöne (vollständige Ableitung)
_LIGHT_COLOR_MAP = {
    "#FFFFFF": "#FFFFFF",
    "#FFF8F2": "#FFFBF7",
    "#FFE8A3": "#EDE0B8",
    "#FFD4B0": "#F0D8BC",
    "#FFC857": "#C99214",
    "#FFC088": "#E0A868",
    "#FFB347": "#C97620",
    "#F4F8FC": "#1C2530",
    "#F2F7FB": "#1C2530",
    "#F0A848": "#B85A18",
    "#F0A060": "#C86218",
    "#F09848": "#D97828",
    "#E8F2FA": "#283440",
    "#E8F0F6": "#2C3844",
    "#E8893A": "#D06820",
    "#E6EEF5": "#1C2530",
    "#E07A2A": "#C45A12",
    "#D9F4FF": "#1A2838",
    "#D8E4EF": "#2A3440",
    "#D46E22": "#B85418",
    "#C9A227": "#96700A",
    "#C86218": "#A84E12",
    "#C5D6E6": "#4A5561",
    "#C42B1C": "#B52820",
    "#B89AFF": "#7C5AC8",
    "#A84E12": "#8F4210",
    "#9FB4C8": "#5C6773",
    "#9A2218": "#8A1E18",
    "#93A8BC": "#566170",
    "#8FA8BC": "#5A6573",
    "#8FA3B8": "#4A5561",
    "#7C92A8": "#526070",
    "#708696": "#5C6773",
    "#6F8599": "#4A5864",
    "#55E8FF": "#0E7490",
    "#506070": "#5A6573",
    "#4D6B78": "#5C6773",
    "#4AD4A0": "#20996A",
    "#4A6070": "#556070",
    "#42D4F5": "#0E7490",
    "#41D17A": "#1E8A52",
    "#3D2A00": "#FFF4E8",
    "#3A5168": "#98A8B8",
    "#33485C": "#A8B4C0",
    "#324558": "#B0BAC4",
    "#2A3848": "#B8C2CC",
    "#29414D": "#B0BCC8",
    "#263545": "#C0C8D0",
    "#243040": "#C4CAD2",
    "#1E5A72": "#0C5468",
    "#1E2A38": "#CED4DC",
    "#1B2A38": "#D8DEE6",
    "#1B2430": "#EEF1F5",
    "#1A3348": "#E0E8F0",
    "#1A2838": "#E8ECF0",
    "#1A2430": "#F5F6F8",
    "#171E28": "#FFFFFF",
    "#162433": "#E8EDF2",
    "#161C26": "#F5F7FA",
    "#151D28": "#F5F6F8",
    "#151D27": "#FAFBFC",
    "#141C26": "#FFFFFF",
    "#123042": "#D6E8F2",
    "#121E29": "#D8DCE2",
    "#121820": "#DCE1E7",
    "#111820": "#DEE2E8",
    "#101820": "#E0E4EA",
    "#101620": "#E2E6EB",
    "#10161E": "#E8EBEF",
    "#0F161E": "#EAECEF",
    "#0E1A25": "#EDF0F4",
    "#0E141C": "#FFFFFF",
    "#0E131A": "#E4E8ED",
    "#0D1218": "#E6E9EE",
    "#0C131A": "#E4E8ED",
    "#0C1016": "#E8EBF0",
    "#0A9CC0": "#0C6880",
    "#0A131C": "#F0F2F5",
    "#0A1016": "#E8EBF0",
    "#0A0D12": "#ECEEF2",
    "#08131C": "#F8F9FA",
    "#07090D": "#DDE1E6",
    "#030608": "#D0D4DA",
    "#030507": "#D4D8DE",
    "#00D9FF": "#0E7490",
}

_LIGHT_RGBA_REPLACEMENTS = (
    ("rgba(255, 255, 255, 0.08)", "rgba(0, 0, 0, 0.05)"),
    ("rgba(255, 255, 255, 0.04)", "rgba(0, 0, 0, 0.03)"),
    ("rgba(224, 122, 42, 0.22)", "rgba(196, 90, 18, 0.18)"),
    ("rgba(224, 122, 42, 0.15)", "rgba(196, 90, 18, 0.12)"),
    ("rgba(201, 162, 39, 0.28)", "rgba(150, 112, 10, 0.35)"),
    ("rgba(201, 162, 39, 0.06)", "rgba(150, 112, 10, 0.10)"),
    ("rgba(20, 28, 38, 0.85)", "rgba(255, 255, 255, 0.98)"),
    ("rgba(14, 20, 28, 0.95)", "rgba(255, 255, 255, 0.98)"),
    ("rgba(14, 20, 28, 0.85)", "rgba(255, 255, 255, 0.96)"),
    ("rgba(10, 24, 36, 0.55)", "rgba(255, 255, 255, 0.92)"),
    ("rgba(85, 232, 255, 0.62)", "rgba(14, 116, 144, 0.75)"),
    ("rgba(10, 156, 192, 0.55)", "rgba(14, 116, 144, 0.22)"),
    ("rgba(0, 217, 255, 0.16)", "rgba(14, 116, 144, 0.14)"),
    ("rgba(0, 217, 255, 0.12)", "rgba(14, 116, 144, 0.10)"),
    ("rgba(0, 217, 255, 35)", "rgba(14, 116, 144, 0.35)"),
    ("rgba(0, 217, 255, 8)", "rgba(14, 116, 144, 0.10)"),
    ("rgba(66, 212, 245, 35)", "rgba(14, 116, 144, 0.30)"),
    ("rgba(66, 212, 245, 12)", "rgba(14, 116, 144, 0.10)"),
    ("rgba(255, 179, 71, 70)", "rgba(196, 90, 18, 0.45)"),
    ("rgba(255, 179, 71, 45)", "rgba(196, 90, 18, 0.30)"),
    ("rgba(255, 179, 71, 30)", "rgba(196, 90, 18, 0.22)"),
    ("rgba(255, 179, 71, 22)", "rgba(196, 90, 18, 0.18)"),
    ("rgba(255, 179, 71, 12)", "rgba(196, 90, 18, 0.12)"),
    ("rgba(224, 122, 42, 0.45)", "rgba(196, 90, 18, 0.35)"),
    ("rgba(0, 217, 255, 0.35)", "rgba(14, 116, 144, 0.30)"),
)


def _build_light_replacements() -> list[tuple[str, str]]:
    items = sorted(
        _LIGHT_COLOR_MAP.items(),
        key=lambda pair: len(pair[0]),
        reverse=True,
    )
    items.extend([
        ('"Rajdhani"', '"Segoe UI"'),
        ('"Orbitron"', '"Segoe UI"'),
    ])
    return items


# Star-Citizen-Farben → sehr dunkles Grau (vollständige Ableitung)
_DARK_COLOR_MAP = {
    "#FFFFFF": "#FFFFFF",
    "#FFF8F2": "#F0F0F0",
    "#FFE8A3": "#D8C888",
    "#FFD4B0": "#C8A890",
    "#FFC857": "#D4B048",
    "#FFC088": "#E0A868",
    "#FFB347": "#D89048",
    "#F4F8FC": "#EDEDED",
    "#F2F7FB": "#EDEDED",
    "#F0A848": "#D49040",
    "#F0A060": "#DC9848",
    "#F09848": "#E89450",
    "#E8F2FA": "#D0D0D0",
    "#E8F0F6": "#D0D0D0",
    "#E8893A": "#E08840",
    "#E6EEF5": "#E4E4E4",
    "#E07A2A": "#D97732",
    "#D9F4FF": "#E0E0E0",
    "#D8E4EF": "#C8C8C8",
    "#D46E22": "#C87028",
    "#C9A227": "#C4A035",
    "#C86218": "#C06820",
    "#C5D6E6": "#A8A8A8",
    "#C42B1C": "#D04038",
    "#B89AFF": "#A888E0",
    "#A84E12": "#A04810",
    "#9FB4C8": "#909090",
    "#9A2218": "#B83830",
    "#93A8BC": "#888888",
    "#8FA8BC": "#868686",
    "#8FA3B8": "#848484",
    "#7C92A8": "#808080",
    "#708696": "#787878",
    "#6F8599": "#787878",
    "#55E8FF": "#8FC4E0",
    "#506070": "#909090",
    "#4D6B78": "#989898",
    "#4AD4A0": "#50C090",
    "#4A6070": "#888888",
    "#42D4F5": "#7EB8DA",
    "#41D17A": "#4CB878",
    "#3D2A00": "#3A2E18",
    "#3A5168": "#484848",
    "#33485C": "#424242",
    "#324558": "#404040",
    "#2A3848": "#3C3C3C",
    "#29414D": "#3A3A3A",
    "#263545": "#383838",
    "#243040": "#363636",
    "#1E5A72": "#4A7888",
    "#1E2A38": "#323232",
    "#1B2A38": "#2E2E2E",
    "#1B2430": "#282828",
    "#1A3348": "#303030",
    "#1A2838": "#2C2C2C",
    "#1A2430": "#2A2A2A",
    "#171E28": "#282828",
    "#162433": "#262626",
    "#161C26": "#242424",
    "#151D28": "#262626",
    "#151D27": "#262626",
    "#141C26": "#242424",
    "#123042": "#2A3238",
    "#121E29": "#222222",
    "#121820": "#202020",
    "#111820": "#1E1E1E",
    "#101820": "#1E1E1E",
    "#101620": "#1C1C1C",
    "#10161E": "#1A1A1A",
    "#0F161E": "#1A1A1A",
    "#0E1A25": "#1C1C1C",
    "#0E141C": "#1A1A1A",
    "#0E131A": "#181818",
    "#0D1218": "#181818",
    "#0C131A": "#181818",
    "#0C1016": "#161616",
    "#0A9CC0": "#5A98B8",
    "#0A131C": "#181818",
    "#0A1016": "#161616",
    "#0A0D12": "#141414",
    "#08131C": "#161616",
    "#07090D": "#101010",
    "#030608": "#0E0E0E",
    "#030507": "#0C0C0C",
    "#00D9FF": "#7EB8DA",
}

_DARK_RGBA_REPLACEMENTS = (
    ("rgba(255, 255, 255, 0.08)", "rgba(255, 255, 255, 0.06)"),
    ("rgba(255, 255, 255, 0.04)", "rgba(255, 255, 255, 0.03)"),
    ("rgba(224, 122, 42, 0.22)", "rgba(217, 119, 50, 0.20)"),
    ("rgba(224, 122, 42, 0.15)", "rgba(217, 119, 50, 0.14)"),
    ("rgba(201, 162, 39, 0.28)", "rgba(196, 160, 53, 0.35)"),
    ("rgba(201, 162, 39, 0.06)", "rgba(196, 160, 53, 0.10)"),
    ("rgba(23, 30, 40, 0.85)", "rgba(36, 36, 36, 0.92)"),
    ("rgba(20, 28, 38, 0.85)", "rgba(36, 36, 36, 0.95)"),
    ("rgba(14, 20, 28, 0.95)", "rgba(30, 30, 30, 0.98)"),
    ("rgba(14, 20, 28, 0.85)", "rgba(36, 36, 36, 0.92)"),
    ("rgba(10, 24, 36, 0.55)", "rgba(30, 30, 30, 0.85)"),
    ("rgba(85, 232, 255, 0.62)", "rgba(142, 184, 218, 0.75)"),
    ("rgba(10, 156, 192, 0.55)", "rgba(126, 184, 218, 0.22)"),
    ("rgba(0, 217, 255, 0.16)", "rgba(126, 184, 218, 0.14)"),
    ("rgba(0, 217, 255, 0.12)", "rgba(126, 184, 218, 0.10)"),
    ("rgba(0, 217, 255, 35)", "rgba(126, 184, 218, 0.30)"),
    ("rgba(0, 217, 255, 8)", "rgba(126, 184, 218, 0.10)"),
    ("rgba(66, 212, 245, 35)", "rgba(126, 184, 218, 0.28)"),
    ("rgba(66, 212, 245, 12)", "rgba(126, 184, 218, 0.10)"),
    ("rgba(255, 179, 71, 70)", "rgba(217, 119, 50, 0.40)"),
    ("rgba(255, 179, 71, 45)", "rgba(217, 119, 50, 0.28)"),
    ("rgba(255, 179, 71, 30)", "rgba(217, 119, 50, 0.20)"),
    ("rgba(255, 179, 71, 22)", "rgba(217, 119, 50, 0.16)"),
    ("rgba(255, 179, 71, 12)", "rgba(217, 119, 50, 0.12)"),
    ("rgba(224, 122, 42, 0.45)", "rgba(217, 119, 50, 0.32)"),
    ("rgba(0, 217, 255, 0.35)", "rgba(126, 184, 218, 0.28)"),
)


def _build_dark_replacements() -> list[tuple[str, str]]:
    items = sorted(
        _DARK_COLOR_MAP.items(),
        key=lambda pair: len(pair[0]),
        reverse=True,
    )
    items.extend([
        ('"Rajdhani"', '"Segoe UI"'),
        ('"Orbitron"', '"Segoe UI"'),
    ])
    return items


# Star-Citizen-Basis → abgeleitete Themes (Reihenfolge beachten)
_DERIVED_REPLACEMENTS = {
    "dark": _build_dark_replacements(),
    "light": _build_light_replacements(),
}

_LIGHT_THEME_PATCH = """
/* ==========================================================
   LIGHT THEME — Feinjustierung (Star-Citizen-Struktur, helle Töne)
   ========================================================== */

QMainWindow {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #F4F5F7,
        stop: 0.45 #ECEEF2,
        stop: 1 #E2E5EA
    );
}

QWidget {
    color: #1C2530;
    font-family: "Segoe UI";
}

#navPanel {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #E4E7EC,
        stop: 1 #ECEEF2
    );
    border-right: 1px solid #C4CAD2;
}

QFrame#navBrandCard {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #FFFFFF,
        stop: 1 #F5F6F8
    );
    border: 1px solid #C4CAD2;
    border-left: 3px solid #C45A12;
}

QLabel#navTitlePrimary {
    color: #1C2530;
}

QLabel#navTitleSecondary {
    color: #0E7490;
}

QLabel#navEditionBadge {
    color: #0E7490;
}

QFrame#navEditionBadgeHost,
QFrame#navEditionBadgeHost[edition="solo"],
QFrame#navEditionBadgeHost[edition="crew"],
QFrame#navEditionBadgeHost[edition="orga"] {
    background-color: #F0F2F5;
}

#navButton {
    background-color: #FFFFFF;
    color: #1C2530;
    border: 1px solid #C4CAD2;
    font-family: "Segoe UI";
    font-size: 15px;
    font-weight: 600;
    letter-spacing: 0.5px;
    min-height: 44px;
}

#navButton:hover {
    background-color: #F0F4F8;
    color: #1C2530;
    border-color: #0E7490;
}

#navButton:pressed {
    background-color: #E4EBF2;
    color: #1C2530;
}

#navButton[active=true] {
    background-color: #C45A12;
    color: #FFFFFF;
    border: 2px solid #A84E12;
}

QLabel#pageTitle {
    color: #1C2530;
}

QLabel#sectionAccent {
    color: #C45A12;
}

QLabel#subSectionTitle {
    color: #C45A12;
}

QLabel#formLabel {
    color: #5C6773;
}

QLabel#sectionTitle {
    color: #1C2530;
}

QLabel#displayValue {
    color: #1C2530;
}

QLabel#mutedLabel {
    color: #5C6773;
}

QLabel#hintLabel {
    color: #5C6773;
}

QLabel#statLabel {
    color: #5C6773;
}

QLabel#statValue {
    color: #1C2530;
}

QLabel#profitLabel {
    color: #C45A12;
}

QLabel#cardTitle {
    color: #5C6773;
}

QLabel#cardValue {
    color: #1C2530;
}

QPushButton#primaryAction {
    background-color: #C45A12;
    color: #FFFFFF;
    border: 2px solid #A84E12;
}

QPushButton#primaryAction:hover {
    background-color: #A84E12;
    color: #FFFFFF;
}

QPushButton#secondaryAction {
    background-color: #FFFFFF;
    color: #1C2530;
    border: 1px solid #C4CAD2;
}

QPushButton#secondaryAction:hover {
    background-color: #F0F4F8;
    color: #1C2530;
    border-color: #0E7490;
}

QFrame#pagePanel,
QFrame#infoPanel {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #FFFFFF,
        stop: 1 #F5F6F8
    );
    border: 1px solid #C4CAD2;
}

QFrame#financeSummaryPanel,
QFrame#storageTotalsPanel {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #FFFFFF,
        stop: 1 #F5F6F8
    );
    border: 1px solid #C4CAD2;
    border-top: 2px solid #C45A12;
}

QFrame#financeSummaryPanel QLabel#statValue,
QFrame#financeSummaryPanel QLabel#profitLabel,
QFrame#storageTotalsPanel QLabel#statValue {
    color: #1C2530;
}

QFrame#storageTotalChip {
    background: #FFFFFF;
    border: 1px solid #C4CAD2;
}

QFrame#storageTotalsPanel QLabel#statLabel {
    color: #5C6773;
}

QLineEdit,
QComboBox,
QTextEdit,
QSpinBox,
QDoubleSpinBox {
    background-color: #FFFFFF;
    color: #1C2530;
    border: 1px solid #B8C0CA;
    selection-background-color: #0E7490;
    selection-color: #FFFFFF;
}

QLineEdit:disabled,
QComboBox:disabled {
    background-color: #ECEEF2;
    color: #8A939E;
    border: 1px solid #D0D5DC;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #1C2530;
    border: 1px solid #C4CAD2;
    selection-background-color: #0E7490;
    selection-color: #FFFFFF;
}

QTableWidget#dataTable,
QTableWidget#historyTable,
QTableWidget#editableTable {
    background-color: #FFFFFF;
    color: #1C2530;
    border: 1px solid #C4CAD2;
    gridline-color: #D8DCE2;
    selection-background-color: #0E7490;
    selection-color: #FFFFFF;
    alternate-background-color: #F5F6F8;
}

QTableWidget#dataTable QHeaderView::section,
QTableWidget#historyTable QHeaderView::section,
QTableWidget#editableTable QHeaderView::section {
    background-color: #E4E7EC;
    color: #1C2530;
    border: 1px solid #C4CAD2;
}

QTabWidget#settingsTabs::pane {
    background-color: #FFFFFF;
    border: 1px solid #C4CAD2;
}

QTabWidget#settingsTabs QTabBar::tab {
    background-color: #ECEEF2;
    color: #5C6773;
    border: 1px solid #C4CAD2;
    border-bottom: none;
}

QTabWidget#settingsTabs QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #1C2530;
    border-top: 2px solid #C45A12;
}

QTabWidget#settingsTabs QTabBar::tab:hover {
    background-color: #F5F6F8;
    color: #1C2530;
}

QScrollBar:vertical {
    background: #E4E7EC;
}

QScrollBar::handle:vertical {
    background: #0E7490;
}

QScrollBar:horizontal {
    background: #E4E7EC;
}

QScrollBar::handle:horizontal {
    background: #0E7490;
}

QDialog#mobiglasDialog {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #F8F9FA,
        stop: 0.45 #ECEEF2,
        stop: 1 #E2E5EA
    );
    border: 1px solid #C4CAD2;
    color: #1C2530;
}

QDialog#mobiglasDialog QWidget {
    color: #1C2530;
}

QDialog#mobiglasDialog QLabel {
    color: #1C2530;
}

QDialog#mobiglasDialog QLabel#pageTitle {
    color: #1C2530;
}

QDialog#mobiglasDialog QLabel#subSectionTitle {
    color: #C45A12;
}

QDialog#mobiglasDialog QLabel#mutedLabel {
    color: #5C6773;
}

QDialog#mobiglasDialog QFrame#rolePermissionGroup QCheckBox,
QDialog#mobiglasDialog QFrame#pagePanel QCheckBox {
    color: #1C2530;
}

QDialog#mobiglasDialog QFrame#rolePermissionGroup QLabel#subSectionTitle,
QDialog#mobiglasDialog QFrame#pagePanel QLabel#subSectionTitle {
    color: #0E7490;
}

QDialog#mobiglasDialog QFrame#pagePanel QLineEdit,
QDialog#mobiglasDialog QFrame#pagePanel QComboBox {
    background-color: #FFFFFF;
    color: #1C2530;
    border: 1px solid #B8C0CA;
}

QWidget#mobiglasDialogContent {
    color: #1C2530;
}

QMessageBox {
    background-color: #FFFFFF;
    color: #1C2530;
}

QMessageBox QLabel {
    color: #1C2530;
}

QLabel#warningBanner {
    background-color: #FFF8E8;
    color: #1C2530;
    border: 2px solid #96700A;
}

QLabel#warningBannerTitle {
    color: #96700A;
}

#versionLabel {
    color: #5C6773;
}

QCheckBox {
    color: #1C2530;
}

QCheckBox::indicator {
    border: 1px solid #B8C0CA;
    background: #FFFFFF;
}

QCheckBox::indicator:checked {
    background: #0E7490;
    border-color: #0C6880;
}
"""

_DARK_THEME_PATCH = """
/* ==========================================================
   DARK THEME — Feinjustierung (Star-Citizen-Struktur, dunkles Grau)
   ========================================================== */

QMainWindow {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #141414,
        stop: 0.45 #1A1A1A,
        stop: 1 #101010
    );
}

QWidget {
    color: #E4E4E4;
    font-family: "Segoe UI";
}

#navPanel {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #181818,
        stop: 1 #1E1E1E
    );
    border-right: 1px solid #3A3A3A;
}

QFrame#navBrandCard {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #262626,
        stop: 1 #1E1E1E
    );
    border: 1px solid #3A3A3A;
    border-left: 3px solid #D97732;
}

QLabel#navTitlePrimary {
    color: #EDEDED;
}

QLabel#navTitleSecondary {
    color: #7EB8DA;
}

QLabel#navEditionBadge {
    color: #7EB8DA;
}

QFrame#navEditionBadgeHost,
QFrame#navEditionBadgeHost[edition="solo"],
QFrame#navEditionBadgeHost[edition="crew"],
QFrame#navEditionBadgeHost[edition="orga"] {
    background-color: #242424;
}

#navButton {
    background-color: #242424;
    color: #E4E4E4;
    border: 1px solid #3A3A3A;
    font-family: "Segoe UI";
    font-size: 15px;
    font-weight: 600;
    letter-spacing: 0.5px;
    min-height: 44px;
}

#navButton:hover {
    background-color: #2A2A2A;
    color: #EDEDED;
    border-color: #7EB8DA;
}

#navButton:pressed {
    background-color: #323232;
    color: #EDEDED;
}

#navButton[active=true] {
    background-color: #D97732;
    color: #FFFFFF;
    border: 2px solid #C06820;
}

QLabel#pageTitle {
    color: #EDEDED;
}

QLabel#sectionAccent {
    color: #D97732;
}

QLabel#subSectionTitle {
    color: #D97732;
}

QLabel#formLabel {
    color: #A0A0A0;
}

QLabel#sectionTitle {
    color: #E4E4E4;
}

QLabel#displayValue {
    color: #E0E0E0;
}

QLabel#mutedLabel {
    color: #909090;
}

QLabel#hintLabel {
    color: #888888;
}

QLabel#statLabel {
    color: #A0A0A0;
}

QLabel#statValue {
    color: #EDEDED;
}

QLabel#profitLabel {
    color: #D97732;
}

QLabel#cardTitle {
    color: #A0A0A0;
}

QLabel#cardValue {
    color: #E4E4E4;
}

QLabel#emptyInfo {
    color: #909090;
}

QWidget#emptyInfoPanel {
    background-color: #242424;
    border: 1px solid #3A3A3A;
    border-radius: 6px;
}

QLabel#warningBanner {
    color: #D8C888;
    background-color: #3A2E18;
    border: 2px solid #C4A035;
}

QLabel#warningBannerTitle {
    color: #D4B048;
}

QPushButton#primaryAction {
    background-color: #D97732;
    color: #FFFFFF;
    border: 2px solid #C06820;
}

QPushButton#primaryAction:hover {
    background-color: #C06820;
    color: #FFFFFF;
}

QPushButton#secondaryAction {
    background-color: #242424;
    color: #E4E4E4;
    border: 1px solid #3A3A3A;
}

QPushButton#secondaryAction:hover {
    background-color: #2A2A2A;
    color: #EDEDED;
    border-color: #7EB8DA;
}

QFrame#pagePanel,
QFrame#infoPanel {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #242424,
        stop: 1 #1E1E1E
    );
    border: 1px solid #3A3A3A;
}

QFrame#financeSummaryPanel,
QFrame#storageTotalsPanel {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #282828,
        stop: 1 #1E1E1E
    );
    border: 1px solid #3A3A3A;
    border-top: 2px solid #D97732;
}

QFrame#financeSummaryPanel QLabel#statValue,
QFrame#financeSummaryPanel QLabel#profitLabel,
QFrame#storageTotalsPanel QLabel#statValue {
    color: #EDEDED;
}

QFrame#storageTotalChip {
    background: #2A2A2A;
    border: 1px solid #404040;
}

QFrame#storageTotalsPanel QLabel#statLabel {
    color: #A0A0A0;
}

QFrame#dashboardAlertStrip {
    background: rgba(36, 36, 36, 0.95);
    border: 1px solid #424242;
}

QFrame#dashboardAlertStrip QLabel,
QFrame#dashboardAlertStrip QLabel#warningBannerTitle {
    color: #E4E4E4;
}

QToolButton#dashboardAlertBell {
    border: 1px solid #424242;
}

QToolButton#dashboardAlertBell:hover,
QToolButton#dashboardAlertBell:checked {
    border-color: #D97732;
}

QLineEdit,
QComboBox,
QTextEdit,
QSpinBox,
QDoubleSpinBox {
    background-color: #2A2A2A;
    color: #E4E4E4;
    border: 1px solid #404040;
    selection-background-color: #7EB8DA;
    selection-color: #101010;
}

QLineEdit:disabled,
QComboBox:disabled {
    background-color: #1E1E1E;
    color: #707070;
    border: 1px solid #323232;
}

QComboBox QAbstractItemView {
    background-color: #2A2A2A;
    color: #E4E4E4;
    border: 1px solid #404040;
    selection-background-color: #7EB8DA;
    selection-color: #101010;
}

QTableWidget#dataTable,
QTableWidget#historyTable,
QTableWidget#editableTable {
    background-color: #1A1A1A;
    color: #E4E4E4;
    border: 1px solid #3A3A3A;
    gridline-color: #323232;
    selection-background-color: #7EB8DA;
    selection-color: #101010;
    alternate-background-color: #222222;
}

QTableWidget#dataTable QHeaderView::section,
QTableWidget#historyTable QHeaderView::section,
QTableWidget#editableTable QHeaderView::section {
    background-color: #2A2A2A;
    color: #E4E4E4;
    border: 1px solid #3A3A3A;
}

QTabWidget#settingsTabs::pane {
    background-color: #242424;
    border: 1px solid #3A3A3A;
}

QTabWidget#settingsTabs QTabBar::tab {
    background-color: #1E1E1E;
    color: #909090;
    border: 1px solid #3A3A3A;
    border-bottom: none;
}

QTabWidget#settingsTabs QTabBar::tab:selected {
    background-color: #2A2A2A;
    color: #E4E4E4;
    border-top: 2px solid #D97732;
}

QTabWidget#settingsTabs QTabBar::tab:hover {
    background-color: #262626;
    color: #E4E4E4;
}

QScrollBar:vertical,
QScrollBar:horizontal {
    background: #1E1E1E;
}

QScrollBar::handle:vertical,
QScrollBar::handle:horizontal {
    background: #505050;
}

QScrollBar::handle:vertical:hover,
QScrollBar::handle:horizontal:hover {
    background: #7EB8DA;
}

QDialog#mobiglasDialog {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #1A1A1A,
        stop: 0.45 #161616,
        stop: 1 #101010
    );
    border: 1px solid #3A3A3A;
    color: #E4E4E4;
}

QDialog#mobiglasDialog QWidget {
    color: #E4E4E4;
}

QDialog#mobiglasDialog QLabel {
    color: #E4E4E4;
}

QDialog#mobiglasDialog QLabel#pageTitle {
    color: #EDEDED;
}

QDialog#mobiglasDialog QLabel#subSectionTitle {
    color: #D97732;
}

QDialog#mobiglasDialog QLabel#mutedLabel {
    color: #909090;
}

QDialog#mobiglasDialog QFrame#rolePermissionGroup QCheckBox,
QDialog#mobiglasDialog QFrame#pagePanel QCheckBox {
    color: #E4E4E4;
}

QDialog#mobiglasDialog QFrame#rolePermissionGroup QLabel#subSectionTitle,
QDialog#mobiglasDialog QFrame#pagePanel QLabel#subSectionTitle {
    color: #7EB8DA;
}

QDialog#mobiglasDialog QFrame#pagePanel QLineEdit,
QDialog#mobiglasDialog QFrame#pagePanel QComboBox {
    background-color: #2A2A2A;
    color: #E4E4E4;
    border: 1px solid #404040;
}

QWidget#mobiglasDialogContent {
    color: #E4E4E4;
}

QMessageBox {
    background-color: #242424;
    color: #E4E4E4;
}

QMessageBox QLabel {
    color: #E4E4E4;
}

#versionLabel {
    color: #888888;
}

QCheckBox {
    color: #E4E4E4;
}

QCheckBox::indicator {
    border: 1px solid #505050;
    background: #2A2A2A;
}

QCheckBox::indicator:checked {
    background: #7EB8DA;
    border-color: #5A98B8;
}
"""


class ThemeManager:
    """Lädt Themes, wendet sie global an und stellt Farb-Tokens bereit."""

    _current_theme_id = "star_citizen"
    _current_palette: dict = {}
    _current_settings: dict = {}
    _base_qss_cache: str | None = None

    @classmethod
    def themes_dir(cls) -> Path:
        return THEMES_DIR

    @classmethod
    def available_themes(cls) -> list[tuple[str, str]]:
        from config.i18n import theme_option_label

        return [
            (
                theme_id,
                theme_option_label(
                    "palette",
                    theme_id,
                    THEME_LABELS[theme_id],
                ),
            )
            for theme_id in THEME_IDS
        ]

    @classmethod
    def load_palette(cls, theme_id: str) -> dict:
        path = PALETTES_DIR / f"{theme_id}.json"
        if not path.exists():
            raise FileNotFoundError(
                f"Palette nicht gefunden: {path}"
            )
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    @classmethod
    def _load_base_qss(cls) -> str:
        if cls._base_qss_cache is not None:
            return cls._base_qss_cache

        base_path = THEMES_DIR / "star_citizen.qss"
        if not base_path.exists():
            raise FileNotFoundError(
                f"Basis-QSS nicht gefunden: {base_path}"
            )

        cls._base_qss_cache = base_path.read_text(
            encoding="utf-8"
        )
        return cls._base_qss_cache

    @classmethod
    def _derive_qss(cls, theme_id: str, *, force: bool = False) -> str:
        qss_path = THEMES_DIR / f"{theme_id}.qss"

        if (
            theme_id == "star_citizen"
            and qss_path.exists()
            and not force
        ):
            return qss_path.read_text(encoding="utf-8")

        if theme_id not in _DERIVED_REPLACEMENTS:
            if qss_path.exists():
                return qss_path.read_text(encoding="utf-8")
            theme_id = "star_citizen"
            qss_path = THEMES_DIR / f"{theme_id}.qss"
            return qss_path.read_text(encoding="utf-8")

        base = cls._load_base_qss()
        qss = base
        for old, new in _DERIVED_REPLACEMENTS[theme_id]:
            qss = qss.replace(old, new)

        if theme_id == "light":
            for old, new in _LIGHT_RGBA_REPLACEMENTS:
                qss = qss.replace(old, new)
            qss += _LIGHT_THEME_PATCH

        if theme_id == "dark":
            for old, new in _DARK_RGBA_REPLACEMENTS:
                qss = qss.replace(old, new)
            qss += _DARK_THEME_PATCH

        qss_path.write_text(qss, encoding="utf-8")
        debug_log(f"Theme-QSS erzeugt: {qss_path.name}")
        return qss

    @classmethod
    def _accent_colors_to_replace(cls, theme_id: str) -> tuple[str, ...]:
        colors = set(ACCENT_REPLACE_COLORS)
        palette = cls.load_palette(theme_id)
        for key in (
            "primary",
            "secondary",
            "panel_border",
            "nav_border",
            "text_accent",
            "table_highlight",
            "scrollbar_handle",
            "gold",
        ):
            value = palette.get(key)
            if value:
                colors.add(value.upper())
                colors.add(value.lower())
        return tuple(sorted(colors, key=len, reverse=True))

    @classmethod
    def _apply_accent_override(
        cls,
        qss: str,
        accent_color: str,
        theme_id: str,
    ) -> str:
        if not accent_color or not re.match(
            r"^#[0-9A-Fa-f]{6}$",
            accent_color,
        ):
            return qss

        accent_color = accent_color.upper()

        for old_color in cls._accent_colors_to_replace(
            theme_id,
        ):
            qss = re.sub(
                re.escape(old_color),
                accent_color,
                qss,
                flags=re.IGNORECASE,
            )

        cls._current_palette["primary"] = accent_color
        cls._current_palette["secondary"] = accent_color
        cls._current_palette["panel_border"] = accent_color
        cls._current_palette["nav_border"] = accent_color
        cls._current_palette["text_accent"] = accent_color
        cls._current_palette["table_highlight"] = accent_color
        cls._current_palette["scrollbar_handle"] = accent_color
        cls._current_palette["gold"] = accent_color
        return qss

    @staticmethod
    def _normalize_hex(color: str) -> str | None:
        if not color or not re.match(
            r"^#[0-9A-Fa-f]{6}$",
            color,
        ):
            return None
        return color.upper()

    @staticmethod
    def _parse_hex_color(hex_color: str) -> tuple[int, int, int]:
        value = hex_color.lstrip("#")
        return (
            int(value[0:2], 16),
            int(value[2:4], 16),
            int(value[4:6], 16),
        )

    @classmethod
    def _format_hex_color(cls, red: int, green: int, blue: int) -> str:
        return (
            f"#{max(0, min(255, red)):02X}"
            f"{max(0, min(255, green)):02X}"
            f"{max(0, min(255, blue)):02X}"
        )

    @classmethod
    def _shade_hex(cls, hex_color: str, factor: float) -> str:
        red, green, blue = cls._parse_hex_color(hex_color)
        if factor >= 1:
            red = round(red + (255 - red) * (factor - 1))
            green = round(green + (255 - green) * (factor - 1))
            blue = round(blue + (255 - blue) * (factor - 1))
        else:
            red = round(red * factor)
            green = round(green * factor)
            blue = round(blue * factor)
        return cls._format_hex_color(red, green, blue)

    @classmethod
    def _append_ui_color_overrides(
        cls,
        qss: str,
        *,
        label_color: str = "",
        primary_button_color: str = "",
        secondary_button_color: str = "",
    ) -> str:
        blocks: list[str] = []

        label = cls._normalize_hex(label_color)
        if label:
            blocks.append(
                f"QLabel#formLabel {{ color: {label}; }}"
            )

        primary = cls._normalize_hex(primary_button_color)
        if primary:
            light = cls._shade_hex(primary, 1.12)
            dark = cls._shade_hex(primary, 0.82)
            border = cls._shade_hex(primary, 1.18)
            hover_light = cls._shade_hex(primary, 1.22)
            hover_dark = cls._shade_hex(primary, 0.88)
            hover_border = cls._shade_hex(primary, 1.28)
            pressed = cls._shade_hex(primary, 0.65)
            blocks.append(
                "\n".join(
                    (
                        "QPushButton#primaryAction {",
                        "    background: qlineargradient(",
                        "        x1: 0, y1: 0, x2: 0, y2: 1,",
                        f"        stop: 0 {light},",
                        f"        stop: 1 {dark}",
                        "    );",
                        f"    border: 1px solid {border};",
                        "    color: #FFF8F2;",
                        "}",
                        "QPushButton#primaryAction:hover {",
                        "    background: qlineargradient(",
                        "        x1: 0, y1: 0, x2: 0, y2: 1,",
                        f"        stop: 0 {hover_light},",
                        f"        stop: 1 {hover_dark}",
                        "    );",
                        f"    border: 1px solid {hover_border};",
                        "}",
                        f"QPushButton#primaryAction:pressed {{ background: {pressed}; }}",
                    )
                )
            )

        secondary = cls._normalize_hex(secondary_button_color)
        if secondary:
            hover_bg = cls._shade_hex(secondary, 1.15)
            border = cls._shade_hex(secondary, 1.35)
            blocks.append(
                "\n".join(
                    (
                        "QPushButton#secondaryAction {",
                        f"    background-color: {secondary};",
                        f"    border: 1px solid {border};",
                        "    color: #C5D6E6;",
                        "}",
                        "QPushButton#secondaryAction:hover {",
                        f"    background-color: {hover_bg};",
                        "    border-color: #42D4F5;",
                        "    color: #E8F2FA;",
                        "}",
                    )
                )
            )

        if not blocks:
            return qss

        return (
            qss
            + "\n\n/* UI color overrides */\n"
            + "\n\n".join(blocks)
        )

    @classmethod
    def default_dashboard_font_scale(cls) -> int:
        return DEFAULT_DASHBOARD_FONT_SCALE

    @classmethod
    def dashboard_card_padding(cls, scales=None) -> tuple[int, int]:
        scale = cls.resolve_dashboard_scales(scales)[
            "dashboard_font_scale"
        ]
        pad_v = max(6, round(10 * scale / 100))
        pad_h = max(8, round(14 * scale / 100))
        return pad_v, pad_h

    @classmethod
    def effective_row_unit_px(cls, scales=None) -> int:
        from ui.dashboard_widget_registry import ROW_UNIT_PX

        scale = cls.resolve_dashboard_scales(scales)[
            "dashboard_font_scale"
        ]
        return max(16, round(ROW_UNIT_PX * scale / 100))

    @classmethod
    def normalize_dashboard_font_scale(cls, value) -> int:
        try:
            scale = int(value)
        except (TypeError, ValueError):
            scale = DEFAULT_DASHBOARD_FONT_SCALE
        return max(
            DASHBOARD_FONT_SCALE_MIN,
            min(DASHBOARD_FONT_SCALE_MAX, scale),
        )

    @classmethod
    def _scaled_dashboard_px(cls, base_px: int, scale_percent: int) -> int:
        return max(8, round(base_px * scale_percent / 100))

    @classmethod
    def _build_font_rules_qss(
        cls,
        rules,
        scale_percent: int,
    ) -> str:
        lines = []
        for selector, base_px in rules:
            px = cls._scaled_dashboard_px(base_px, scale_percent)
            lines.append(f"{selector} {{ font-size: {px}px; }}")
        return "\n".join(lines)

    @classmethod
    def resolve_dashboard_scales(cls, settings=None) -> dict:
        src = settings if settings is not None else cls._current_settings
        widget_scale = cls.normalize_dashboard_font_scale(
            src.get(
                "dashboard_font_scale",
                DEFAULT_DASHBOARD_FONT_SCALE,
            )
        )
        title_scale = cls.normalize_dashboard_font_scale(
            src.get("dashboard_title_font_scale", widget_scale)
        )
        button_scale = cls.normalize_dashboard_font_scale(
            src.get("dashboard_button_font_scale", widget_scale)
        )
        return {
            "dashboard_font_scale": widget_scale,
            "dashboard_title_font_scale": title_scale,
            "dashboard_button_font_scale": button_scale,
        }

    @classmethod
    def build_dashboard_font_qss(
        cls,
        widget_scale: int,
        title_scale: int | None = None,
        button_scale: int | None = None,
    ) -> str:
        widget_scale = cls.normalize_dashboard_font_scale(
            widget_scale
        )
        if title_scale is None:
            title_scale = widget_scale
        if button_scale is None:
            button_scale = widget_scale
        title_scale = cls.normalize_dashboard_font_scale(title_scale)
        button_scale = cls.normalize_dashboard_font_scale(
            button_scale
        )

        widget_px = cls._scaled_dashboard_px(
            DASHBOARD_FONT_BASE_PX,
            widget_scale,
        )
        title_px = cls._scaled_dashboard_px(
            DASHBOARD_FONT_BASE_PX,
            title_scale,
        )
        button_px = cls._scaled_dashboard_px(
            DASHBOARD_FONT_BASE_PX,
            button_scale,
        )
        lines = [
            "/* ThemeManager: Dashboard-Schrift */",
            f"QWidget#dashboardPage QLabel {{\n"
            f"    font-size: {widget_px}px;\n"
            "}",
            "QWidget#dashboardHeader QLabel#pageTitle,\n"
            "QWidget#dashboardHeader QLabel#sectionAccent {\n"
            f"    font-size: {title_px}px;\n"
            "}",
            "QWidget#dashboardHeader QPushButton#secondaryAction,\n"
            "QWidget#dashboardHeader QPushButton#primaryAction {\n"
            f"    font-size: {button_px}px;\n"
            "}",
        ]
        button_h = max(32, round(button_px * 2.2))
        lines.append(
            "QWidget#dashboardHeader QPushButton#secondaryAction,\n"
            "QWidget#dashboardHeader QPushButton#primaryAction {\n"
            f"    min-height: {button_h}px;\n"
            "    padding: 8px 20px;\n"
            "}"
        )
        pad_v = max(6, round(10 * widget_scale / 100))
        pad_h = max(8, round(14 * widget_scale / 100))
        lines.append(
            "QFrame#dashboardKpiCard,\n"
            "QFrame#dashboardSessionPanel {\n"
            f"    padding: {pad_v}px {pad_h}px;\n"
            "}"
        )
        return "\n".join(lines)

    @classmethod
    def _current_font_family_id(cls) -> str:
        family_id = cls._current_settings.get(
            "font_family",
            DEFAULT_FONT_FAMILY,
        )
        if family_id not in FONT_FAMILY_LABELS:
            return DEFAULT_FONT_FAMILY
        return family_id

    @classmethod
    def build_dashboard_font_preview_qss(cls, scale_percent: int) -> str:
        scale = cls.normalize_dashboard_font_scale(scale_percent)
        pad_v = max(6, round(10 * scale / 100))
        pad_h = max(8, round(14 * scale / 100))
        family_id = cls._current_font_family_id()
        heading = resolve_heading_font(family_id)
        body = resolve_body_font(family_id)
        return (
            "QFrame#dashboardFontPreviewHost {\n"
            "    background: transparent;\n"
            "    border: none;\n"
            "}\n"
            "QFrame#dashboardFontPreviewCard {\n"
            "    background: qlineargradient(\n"
            "        x1: 0, y1: 0, x2: 0, y2: 1,\n"
            "        stop: 0 #171E28,\n"
            "        stop: 1 #121820\n"
            "    );\n"
            "    border: 1px solid #263545;\n"
            "    border-radius: 8px;\n"
            f"    padding: {pad_v}px {pad_h}px;\n"
            "}\n"
            "QLabel#dashboardFontPreviewHint {\n"
            "    color: #6F8599;\n"
            f'    font-family: "{body}";\n'
            "    font-weight: bold;\n"
            "}\n"
            + cls._build_font_rules_qss(
                DASHBOARD_FONT_PREVIEW_RULES,
                scale,
            )
        )

    @classmethod
    def apply_dashboard_fonts(
        cls,
        root_widget: QWidget,
        scales=None,
    ) -> None:
        resolved = cls.resolve_dashboard_scales(scales)
        widget_scale = resolved["dashboard_font_scale"]
        title_scale = resolved["dashboard_title_font_scale"]
        button_scale = resolved["dashboard_button_font_scale"]
        widget_px = cls._scaled_dashboard_px(
            DASHBOARD_FONT_BASE_PX,
            widget_scale,
        )
        title_px = cls._scaled_dashboard_px(
            DASHBOARD_FONT_BASE_PX,
            title_scale,
        )
        button_px = cls._scaled_dashboard_px(
            DASHBOARD_FONT_BASE_PX,
            button_scale,
        )

        root_widget.setStyleSheet(
            cls.build_dashboard_font_qss(
                widget_scale,
                title_scale,
                button_scale,
            )
        )

        family_id = cls._current_font_family_id()
        heading_font = resolve_heading_font(family_id)
        body_font = resolve_body_font(family_id)
        label_fonts = dashboard_label_fonts(family_id)

        from ui.dashboard_fit_label import DashboardFitLabel

        for label in root_widget.findChildren(QLabel):
            name = label.objectName()
            if name not in DASHBOARD_FONT_LABEL_NAMES:
                continue
            spec = label_fonts.get(name)
            if spec is not None:
                family = spec[0]
            elif name in ("pageTitle", "sectionAccent"):
                family = heading_font
            else:
                family = body_font
            if name in ("pageTitle", "sectionAccent"):
                label_px = title_px
            else:
                label_px = widget_px
            font = QFont(family, label_px)
            font.setBold(True)
            if isinstance(label, DashboardFitLabel):
                label.apply_theme_font(font)
            else:
                label.setFont(font)

        font = QFont(body_font, button_px)
        font.setBold(True)
        for button in root_widget.findChildren(QPushButton):
            if button.objectName() not in (
                "secondaryAction",
                "primaryAction",
            ):
                continue
            button.setFont(font)

        root_widget.style().unpolish(root_widget)
        root_widget.style().polish(root_widget)
        root_widget.update()

        page = root_widget
        if page.objectName() != "dashboardPage":
            return
        canvas = getattr(page, "canvas", None)
        if canvas is not None and hasattr(
            canvas,
            "reflow_content_sizes",
        ):
            canvas.reflow_content_sizes()

    @classmethod
    def refresh_dashboard_font_scale(cls, scales=None) -> None:
        app = QApplication.instance()
        if app is None:
            return

        if scales is None:
            scales = cls._current_settings

        for widget in app.allWidgets():
            if widget.objectName() == "dashboardPage":
                cls.apply_dashboard_fonts(widget, scales)

    @classmethod
    def _append_dashboard_font_scale(
        cls,
        qss: str,
        scales: dict,
    ) -> str:
        resolved = cls.resolve_dashboard_scales(scales)
        block = cls.build_dashboard_font_qss(
            resolved["dashboard_font_scale"],
            resolved["dashboard_title_font_scale"],
            resolved["dashboard_button_font_scale"],
        )
        return qss + "\n\n" + block

    @classmethod
    def _append_font_size(cls, qss: str, font_size: str) -> str:
        px = FONT_SIZE_MAP.get(font_size, 16)
        return (
            qss
            + f"\n\n/* ThemeManager: Schriftgröße */\n"
            + f"QWidget {{ font-size: {px}px; }}\n"
        )

    @classmethod
    def _append_font_family(
        cls,
        qss: str,
        font_family: str,
    ) -> str:
        family_id = (
            font_family
            if font_family in FONT_FAMILY_LABELS
            else DEFAULT_FONT_FAMILY
        )
        return apply_font_family_to_qss(qss, family_id)

    @classmethod
    def _alpha_from_percent(cls, percent: int) -> int:
        return max(0, min(255, int(255 * percent / 100)))

    @classmethod
    def _append_window_transparency(
        cls,
        qss: str,
        transparency: int,
    ) -> str:
        if transparency >= 100:
            return qss

        alpha = cls._alpha_from_percent(transparency)
        window_bg = cls._current_palette.get(
            "background",
            "#0A0D12",
        )
        nav_bg = cls._current_palette.get(
            "background_dark",
            "#07090D",
        )
        return (
            qss
            + f"\n\n/* ThemeManager: Fenster-Transparenz {transparency}% */\n"
            + "QMainWindow#mainWindow,\n"
            + "QMainWindow#dashboardWindow {\n"
            + f"    background-color: rgba({cls._hex_to_rgb(window_bg)}, {alpha});\n"
            + "}\n"
            + "#navPanel {\n"
            + f"    background-color: rgba({cls._hex_to_rgb(nav_bg)}, {alpha});\n"
            + "}\n"
        )

    @classmethod
    def _append_panel_transparency(
        cls,
        qss: str,
        panel_transparency: int,
    ) -> str:
        if panel_transparency >= 100:
            return qss

        alpha = cls._alpha_from_percent(panel_transparency)
        panel = cls._current_palette.get("panel", "#152532")
        return (
            qss
            + f"\n\n/* ThemeManager: Panel-Transparenz {panel_transparency}% */\n"
            + "QFrame#pagePanel,\n"
            + "QFrame#infoPanel {\n"
            + f"    background-color: rgba({cls._hex_to_rgb(panel)}, {alpha});\n"
            + "}\n"
        )

    @classmethod
    def _append_table_density(
        cls,
        qss: str,
        table_density: str,
    ) -> str:
        density = (
            table_density
            if table_density in TABLE_DENSITY_LABELS
            else "normal"
        )
        if density == "normal":
            return qss

        spec = TABLE_DENSITY_PADDING[density]
        selectors = ",\n".join(
            f"QTableWidget#{name}" for name in TABLE_OBJECT_NAMES
        )
        item_selectors = ",\n".join(
            f"QTableWidget#{name}::item"
            for name in TABLE_OBJECT_NAMES
        )
        header_selectors = ",\n".join(
            f"QTableWidget#{name} QHeaderView::section"
            for name in TABLE_OBJECT_NAMES
        )
        return (
            qss
            + f"\n\n/* ThemeManager: Tabellen-Dichte {density} */\n"
            + f"{item_selectors} {{\n"
            + f"    padding: {spec['item_v']}px {spec['item_h']}px;\n"
            + "}\n"
            + f"{header_selectors} {{\n"
            + f"    padding: {spec['header_v']}px {spec['header_h']}px;\n"
            + f"    font-size: {spec['header_font']}px;\n"
            + "}\n"
            + f"{selectors} {{\n"
            + "    outline: none;\n"
            + "}\n"
        )

    @classmethod
    def apply_table_row_height(
        cls,
        table,
        table_density: str | None = None,
    ) -> None:
        density = table_density or cls._current_settings.get(
            "table_density",
            "normal",
        )
        if density not in TABLE_DENSITY_ROW_HEIGHT:
            density = "normal"

        row_height = TABLE_DENSITY_ROW_HEIGHT[density]
        header = table.verticalHeader()
        header.setDefaultSectionSize(row_height)
        header.setMinimumSectionSize(max(20, row_height - 6))

    @classmethod
    def refresh_table_density(cls, table_density: str | None = None) -> None:
        app = QApplication.instance()
        if app is None:
            return

        density = table_density or cls._current_settings.get(
            "table_density",
            "normal",
        )
        for widget in app.allWidgets():
            if not isinstance(widget, QTableWidget):
                continue
            if widget.objectName() not in TABLE_OBJECT_NAMES:
                continue
            cls.apply_table_row_height(widget, density)
            widget.resizeRowsToContents()

    @classmethod
    def _hex_to_rgb(cls, hex_color: str) -> str:
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            return "13, 26, 36"
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r}, {g}, {b}"

    @classmethod
    def get_color(cls, key: str, fallback: str = "#FFFFFF") -> str:
        return cls._current_palette.get(key, fallback)

    @classmethod
    def current_theme_id(cls) -> str:
        return cls._current_theme_id

    @classmethod
    def current_settings(cls) -> dict:
        return dict(cls._current_settings)

    @classmethod
    def animations_enabled(cls, level: str = "full") -> bool:
        mode = cls._current_settings.get(
            "animations",
            level,
        )
        return mode != "off"

    @classmethod
    def animations_reduced(cls) -> bool:
        return (
            cls._current_settings.get("animations") == "reduced"
        )

    @classmethod
    def load_theme(
        cls,
        theme_id: str,
        *,
        accent_color: str = "",
        label_color: str = "",
        primary_button_color: str = "",
        secondary_button_color: str = "",
        font_size: str = "normal",
        font_family: str = DEFAULT_FONT_FAMILY,
        transparency: int = 100,
        panel_transparency: int = 100,
        table_density: str = "normal",
        animations: str = "full",
        dashboard_layout: str = "classic",
        dashboard_font_scale: int = DEFAULT_DASHBOARD_FONT_SCALE,
        dashboard_title_font_scale: int | None = None,
        dashboard_button_font_scale: int | None = None,
        persist: bool = False,
    ) -> None:
        if theme_id not in THEME_IDS:
            theme_id = "star_citizen"

        scales = cls.resolve_dashboard_scales(
            {
                "dashboard_font_scale": dashboard_font_scale,
                "dashboard_title_font_scale": (
                    dashboard_title_font_scale
                    if dashboard_title_font_scale is not None
                    else dashboard_font_scale
                ),
                "dashboard_button_font_scale": (
                    dashboard_button_font_scale
                    if dashboard_button_font_scale is not None
                    else dashboard_font_scale
                ),
            }
        )

        if font_family not in FONT_FAMILY_LABELS:
            font_family = DEFAULT_FONT_FAMILY

        if table_density not in TABLE_DENSITY_LABELS:
            table_density = "normal"

        panel_transparency = max(
            0,
            min(100, int(panel_transparency or 100)),
        )
        transparency = max(
            0,
            min(100, int(transparency or 100)),
        )

        cls._current_theme_id = theme_id
        cls._current_palette = cls.load_palette(theme_id)
        cls._current_settings = {
            "theme": theme_id,
            "accent_color": accent_color,
            "label_color": label_color,
            "primary_button_color": primary_button_color,
            "secondary_button_color": secondary_button_color,
            "font_size": font_size,
            "font_family": font_family,
            "transparency": transparency,
            "panel_transparency": panel_transparency,
            "table_density": table_density,
            "animations": animations,
            "dashboard_layout": dashboard_layout,
            **scales,
        }

        qss = cls._derive_qss(theme_id)
        qss = cls._apply_accent_override(
            qss,
            accent_color,
            theme_id,
        )
        qss = cls._append_ui_color_overrides(
            qss,
            label_color=label_color,
            primary_button_color=primary_button_color,
            secondary_button_color=secondary_button_color,
        )
        qss = cls._append_font_size(qss, font_size)
        qss = cls._append_font_family(
            qss,
            cls._current_settings.get(
                "font_family",
                DEFAULT_FONT_FAMILY,
            ),
        )
        qss = cls._append_window_transparency(qss, transparency)
        qss = cls._append_panel_transparency(
            qss,
            panel_transparency,
        )
        qss = cls._append_table_density(qss, table_density)

        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(qss)
            cls._apply_application_font(
                font_size,
                theme_id,
                font_family,
            )
            cls.refresh_dashboard_font_scale(scales)
            cls.refresh_table_density(table_density)

        debug_log(
            "Theme geladen:",
            theme_id,
            f"font={font_size}",
            f"window_transparency={transparency}%",
            f"panel_transparency={panel_transparency}%",
            f"table_density={table_density}",
            f"dashboard_widget={scales['dashboard_font_scale']}%",
            f"dashboard_title={scales['dashboard_title_font_scale']}%",
            f"dashboard_button={scales['dashboard_button_font_scale']}%",
        )

        if persist:
            cls.save_theme_preference(theme_id)

    @classmethod
    def _apply_application_font(
        cls,
        font_size: str,
        theme_id: str,
        font_family: str = DEFAULT_FONT_FAMILY,
    ) -> None:
        app = QApplication.instance()
        if app is None:
            return

        family_id = (
            font_family
            if font_family in FONT_FAMILY_LABELS
            else DEFAULT_FONT_FAMILY
        )
        palette = cls.load_palette(theme_id)
        family = resolve_body_font(
            family_id,
            theme_id=theme_id,
            palette=palette,
        )

        px = FONT_SIZE_MAP.get(font_size, 16)
        app.setFont(QFont(family, px))

    @classmethod
    def apply_settings(cls, settings: dict) -> None:
        scales = cls.resolve_dashboard_scales(settings)
        cls.load_theme(
            settings.get("theme", "star_citizen"),
            accent_color=settings.get("accent_color", ""),
            label_color=settings.get("label_color", ""),
            primary_button_color=settings.get(
                "primary_button_color",
                "",
            ),
            secondary_button_color=settings.get(
                "secondary_button_color",
                "",
            ),
            font_size=settings.get("font_size", "normal"),
            font_family=settings.get(
                "font_family",
                DEFAULT_FONT_FAMILY,
            ),
            transparency=int(
                settings.get("transparency", 100) or 100
            ),
            panel_transparency=int(
                settings.get("panel_transparency", 100) or 100
            ),
            table_density=settings.get(
                "table_density",
                "normal",
            ),
            animations=settings.get("animations", "full"),
            dashboard_layout=settings.get(
                "dashboard_layout",
                "classic",
            ),
            dashboard_font_scale=scales["dashboard_font_scale"],
            dashboard_title_font_scale=scales[
                "dashboard_title_font_scale"
            ],
            dashboard_button_font_scale=scales[
                "dashboard_button_font_scale"
            ],
        )

    @classmethod
    def apply_for_user(cls, database, user_id: int) -> dict:
        settings = database.settings.resolve_effective_settings(
            user_id
        )
        cls.apply_settings(settings)
        return settings

    @classmethod
    def save_theme_preference(cls, theme_id: str) -> None:
        cls._current_theme_id = theme_id

    @classmethod
    def ensure_derived_themes(cls) -> None:
        cls._derive_qss("dark", force=True)
        cls._derive_qss("light", force=True)
