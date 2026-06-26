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

DEFAULT_DASHBOARD_FONT_SCALE = 200
DASHBOARD_FONT_SCALE_MIN = 50
DASHBOARD_FONT_SCALE_MAX = 250

DASHBOARD_FONT_BASE_RULES = (
    ("QLabel#dashboardKpiTitle", 10),
    ("QLabel#dashboardKpiValue", 16),
    ("QLabel#dashboardKpiValueAccent", 16),
    ("QLabel#dashboardKpiStatusValue", 13),
    ("QLabel#dashboardKpiDigit", 16),
    ("QLabel#dashboardKpiDigitAccent", 16),
    ("QLabel#dashboardStatDigit", 12),
    ("QLabel#dashboardSessionHeading", 10),
    ("QLabel#dashboardStatLabel", 11),
    ("QLabel#dashboardStatValue", 12),
    ("QLabel#dashboardCatalogTitle", 12),
    ("QLabel#dashboardCatalogHint", 11),
    ("QLabel#dashboardCatalogDropLabel", 10),
    ("QLabel#dashboardCatalogLabel", 12),
    ("QWidget#dashboardCatalogPanel QLabel#hudMarker", 10),
    ("QWidget#dashboardPage QLabel#hudMarker", 18),
    ("QLabel#dashboardSection", 18),
)

DASHBOARD_FONT_PREVIEW_RULES = (
    ("QLabel#dashboardFontPreviewTitle", 10),
    ("QLabel#dashboardFontPreviewValue", 16),
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

# Star-Citizen-Basis → abgeleitete Themes (Reihenfolge beachten)
_DERIVED_REPLACEMENTS = {
    "dark": [
        ("#00D9FF", "#4A90E2"),
        ("#55E8FF", "#6BA3E8"),
        ("#0A9CC0", "#3A7BC8"),
        ("#D9F4FF", "#FFFFFF"),
        ("#08131C", "#1E1E1E"),
        ("#0D1A24", "#2D2D2D"),
        ("#152532", "#2D2D2D"),
        ("#0A121A", "#252525"),
        ("#1B2A38", "#1E1E1E"),
        ("#121E29", "#1E1E1E"),
        ("#0A131C", "#1E1E1E"),
        ("#030608", "#181818"),
        ("#162433", "#252525"),
        ("#0E1822", "#222222"),
        ("#060B10", "#1A1A1A"),
        ("#0B1721", "#2D2D2D"),
        ("#123042", "#3A3A3A"),
        ("#1E5167", "#4A4A4A"),
        ("#4D6B78", "#AAAAAA"),
        ('"Rajdhani"', '"Segoe UI"'),
        ('"Orbitron"', '"Segoe UI"'),
    ],
    "light": [
        ("#00D9FF", "#0078D7"),
        ("#55E8FF", "#0078D7"),
        ("#0A9CC0", "#005A9E"),
        ("#D9F4FF", "#222222"),
        ("#08131C", "#FFFFFF"),
        ("#0D1A24", "#F5F5F5"),
        ("#152532", "#FFFFFF"),
        ("#0A121A", "#F0F0F0"),
        ("#1B2A38", "#F0F0F0"),
        ("#121E29", "#F0F0F0"),
        ("#0A131C", "#F0F0F0"),
        ("#030608", "#E0E0E0"),
        ("#162433", "#E8E8E8"),
        ("#0E1822", "#F0F0F0"),
        ("#060B10", "#E0E0E0"),
        ("#0B1721", "#FFFFFF"),
        ("#123042", "#E8F4FC"),
        ("#1E5167", "#CCE4F7"),
        ("#1A4A61", "#B3D7F2"),
        ("#4D6B78", "#666666"),
        ("#29414D", "#CCCCCC"),
        ("#C9A227", "#B8860B"),
        ('"Rajdhani"', '"Segoe UI"'),
        ('"Orbitron"', '"Segoe UI"'),
    ],
}

_LIGHT_THEME_PATCH = """
/* ==========================================================
   LIGHT THEME — Feinjustierung
   ========================================================== */

#navButton {
    background-color: #FFFFFF;
    color: #222222;
    border: 1px solid #0078D7;
    font-family: "Rajdhani";
    font-size: 17px;
    font-weight: bold;
    letter-spacing: 0.5px;
    min-height: 44px;
}

#navButton:hover {
    background-color: #E8F4FC;
    color: #222222;
}

#navButton:pressed {
    background-color: #CCE4F7;
    color: #222222;
}

#navButton[active=true] {
    background-color: #0078D7;
    color: #FFFFFF;
    border: 2px solid #005A9E;
}

QLabel#subSectionTitle {
    color: #B85A18;
}

QLabel#sectionAccent {
    color: #B85A18;
}

QLabel#formLabel {
    color: #B85A18;
}

QLabel#sectionTitle {
    color: #222222;
}

QPushButton#primaryAction {
    background-color: #0078D7;
    color: #FFFFFF;
    border: 2px solid #005A9E;
}

QPushButton#primaryAction:hover {
    background-color: #005A9E;
    color: #FFFFFF;
}

QPushButton#secondaryAction {
    background-color: #FFFFFF;
    color: #222222;
    border: 1px solid #0078D7;
}

QPushButton#secondaryAction:hover {
    background-color: #E8F4FC;
    color: #222222;
}

QDialog#mobiglasDialog {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #FFFFFF,
        stop: 0.35 #F5F5F5,
        stop: 1 #E8E8E8
    );
}

QFrame#pagePanel,
QFrame#infoPanel {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #FFFFFF,
        stop: 1 #F5F5F5
    );
    border: 1px solid #0078D7;
}

QLineEdit,
QComboBox,
QTextEdit {
    background-color: #FFFFFF;
    color: #222222;
    border: 1px solid #0078D7;
}

QLineEdit:disabled {
    background-color: #F0F0F0;
    color: #888888;
    border: 1px solid #CCCCCC;
}

QTableWidget#dataTable,
QTableWidget#historyTable,
QTableWidget#editableTable {
    background-color: #FFFFFF;
    color: #222222;
    border: 1px solid #0078D7;
    gridline-color: #DDDDDD;
    selection-background-color: #0078D7;
    selection-color: #FFFFFF;
    alternate-background-color: #F5F5F5;
}

QTableWidget#dataTable QHeaderView::section,
QTableWidget#historyTable QHeaderView::section,
QTableWidget#editableTable QHeaderView::section {
    background-color: #E8E8E8;
    color: #222222;
    border: 1px solid #CCCCCC;
}

QMessageBox {
    background-color: #FFFFFF;
    color: #222222;
}

QLabel#warningBanner {
    background-color: #FFF8E1;
    color: #222222;
    border: 2px solid #B8860B;
}

QLabel#warningBannerTitle {
    color: #B8860B;
}

QLabel#mutedLabel {
    color: #666666;
}

QTabWidget#settingsTabs::pane {
    background-color: #FFFFFF;
    border: 1px solid #33485C;
}

QTabWidget#settingsTabs QTabBar::tab {
    background-color: #F0F2F5;
    color: #506070;
}

QTabWidget#settingsTabs QTabBar::tab:selected {
    background-color: #141C26;
    color: #F4F8FC;
    border-top: 2px solid #E07A2A;
}

QScrollBar:vertical {
    background: #E0E0E0;
}

QScrollBar::handle:vertical {
    background: #0078D7;
}

#versionLabel {
    color: #666666;
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
            qss += _LIGHT_THEME_PATCH

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
        pad_v = max(3, round(3 * scale / 100))
        pad_h = max(6, round(6 * scale / 100))
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
        lines = [
            "/* ThemeManager: Dashboard-Schrift */",
            cls._build_font_rules_qss(
                DASHBOARD_FONT_BASE_RULES,
                widget_scale,
            ),
            cls._build_font_rules_qss(
                (("QWidget#dashboardHeader QLabel#pageTitle", 42),),
                title_scale,
            ),
        ]
        button_px = cls._scaled_dashboard_px(16, button_scale)
        button_h = max(44, round(button_px * 1.6))
        lines.append(
            "QWidget#dashboardHeader QPushButton#secondaryAction,\n"
            "QWidget#dashboardHeader QPushButton#primaryAction {\n"
            f"    font-size: {button_px}px;\n"
            f"    min-height: {button_h}px;\n"
            "    padding: 8px 20px;\n"
            "}"
        )
        pad_v = max(3, round(3 * widget_scale / 100))
        pad_h = max(6, round(6 * widget_scale / 100))
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
        pad_v = max(3, round(3 * scale / 100))
        pad_h = max(6, round(6 * scale / 100))
        family_id = cls._current_font_family_id()
        heading = resolve_heading_font(family_id)
        body = resolve_body_font(family_id)
        return (
            "QFrame#dashboardFontPreviewHost {\n"
            "    background: transparent;\n"
            "    border: none;\n"
            "}\n"
            "QFrame#dashboardFontPreviewCard {\n"
            "    background: rgba(8, 16, 24, 0.68);\n"
            "    border: 1px solid rgba(0, 217, 255, 0.22);\n"
            "    border-radius: 6px;\n"
            f"    padding: {pad_v}px {pad_h}px;\n"
            "}\n"
            "QLabel#dashboardFontPreviewTitle {\n"
            "    color: rgba(0, 217, 255, 0.68);\n"
            f'    font-family: "{heading}";\n'
            "    font-weight: bold;\n"
            "}\n"
            "QLabel#dashboardFontPreviewValue {\n"
            "    color: #E6F2F8;\n"
            f'    font-family: "{body}";\n'
            "    font-weight: bold;\n"
            "}\n"
            "QLabel#dashboardFontPreviewHint {\n"
            "    color: rgba(85, 232, 255, 0.55);\n"
            f'    font-family: "{body}";\n'
            "    font-size: 11px;\n"
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
            if name == "pageTitle":
                font = QFont(
                    heading_font,
                    cls._scaled_dashboard_px(42, title_scale),
                )
                font.setBold(True)
                label.setFont(font)
                continue

            spec = label_fonts.get(name)
            if spec is None:
                continue
            family, base_px = spec
            font = QFont(
                family,
                cls._scaled_dashboard_px(base_px, widget_scale),
            )
            font.setBold(True)
            if isinstance(label, DashboardFitLabel):
                label.apply_theme_font(font)
            else:
                label.setFont(font)

        button_px = cls._scaled_dashboard_px(16, button_scale)
        for button in root_widget.findChildren(QPushButton):
            if button.objectName() not in (
                "secondaryAction",
                "primaryAction",
            ):
                continue
            font = QFont(body_font, button_px)
            font.setBold(True)
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
