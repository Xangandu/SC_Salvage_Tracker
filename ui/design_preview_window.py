"""Interaktive Design-Vorschau — Star-Citizen-Launcher-Stil.

Starten mit:
  py scripts/run_design_preview.py           (Classic · Orbitron / Rajdhani)
  py scripts/run_design_preview.py --scifi   (Alternative Sci-Fi Typografie)

Keine Funktionsänderungen — nur visuelle Mockups zum Abstimmen.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.paths import asset_path

PREVIEW_VARIANTS = {
    "classic": {
        "theme": "ui/themes/sc_launcher_next.qss",
        "title": "DESIGN PREVIEW · RSI LAUNCHER",
        "window_title": "SC Salvage Tracker — Design-Vorschau (Classic)",
        "footer": (
            "VORSCHAU · Orbitron / Rajdhani · Keine echten Daten"
        ),
        "login_hint": (
            "Schlankes Login-Panel · Orange als Primär-Aktion "
            "(wie RSI „Launch Game“) · dezente Cyan-Akzente"
        ),
        "fonts": (
            "assets/fonts/Orbitron-Bold.ttf",
            "assets/fonts/Rajdhani-Regular.ttf",
            "assets/fonts/Rajdhani-Bold.ttf",
        ),
    },
    "scifi": {
        "theme": "ui/themes/sc_launcher_scifi.qss",
        "title": "DESIGN PREVIEW · SCI-FI TYPOGRAPHY",
        "window_title": (
            "SC Salvage Tracker — Design-Vorschau (Sci-Fi)"
        ),
        "footer": (
            "VORSCHAU · Audiowide / Michroma / Exo 2 / "
            "Share Tech Mono · Keine echten Daten"
        ),
        "login_hint": (
            "Sci-Fi Typografie · Display: Audiowide · "
            "Labels: Michroma · UI: Exo 2 · Daten: Share Tech Mono"
        ),
        "fonts": (
            "assets/fonts/scifi/Audiowide-Regular.ttf",
            "assets/fonts/scifi/Michroma-Regular.ttf",
            "assets/fonts/scifi/Exo2-Variable.ttf",
            "assets/fonts/scifi/ShareTechMono-Regular.ttf",
            "assets/fonts/Orbitron-Bold.ttf",
            "assets/fonts/Rajdhani-Regular.ttf",
        ),
    },
}


def _divider():
    line = QWidget()
    line.setObjectName("scNextNavDivider")
    return line


def _scene_tab(text: str, active: bool = False) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("scNextSceneTab")
    button.setProperty("active", active)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    return button


def _nav_item(text: str, active: bool = False) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("scNextNavItem")
    button.setProperty("active", active)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    return button


def _kpi_card(label: str, value: str, *, accent: bool = False) -> QFrame:
    card = QFrame()
    card.setObjectName("scNextKpiCard")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 16, 18, 16)
    layout.setSpacing(6)

    title = QLabel(label)
    title.setObjectName("scNextKpiLabel")

    amount = QLabel(value)
    amount.setObjectName(
        "scNextKpiAccent" if accent else "scNextKpiValue"
    )

    layout.addWidget(title)
    layout.addWidget(amount)
    return card


class DesignPreviewWindow(QWidget):

    SCENES = ("LOGIN", "HAUPTFENSTER", "KOMPONENTEN")

    def __init__(self, variant: str = "classic"):
        super().__init__()
        self.variant = variant
        self._config = PREVIEW_VARIANTS[variant]

        self.setObjectName("scNextRoot")
        self.setWindowTitle(self._config["window_title"])
        self.resize(1280, 820)
        self._scene_buttons: list[QPushButton] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_title_bar())
        root.addWidget(self._build_scene_tabs())

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_login_scene())
        self.stack.addWidget(self._build_main_scene())
        self.stack.addWidget(self._build_components_scene())
        root.addWidget(self.stack, 1)

        note = QLabel(self._config["footer"])
        note.setObjectName("scNextPreviewNote")
        note.setAlignment(Qt.AlignCenter)
        note.setContentsMargins(0, 8, 0, 10)
        root.addWidget(note)

        self._select_scene(0)

    def _build_title_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("scNextTitleBar")

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 0, 12, 0)
        layout.setSpacing(12)

        brand = QLabel("MOBIGLAS")
        brand.setObjectName("scNextTitleBarBrand")

        sub = QLabel(self._config["title"])
        sub.setObjectName("scNextTitleBarSub")

        layout.addWidget(brand)
        layout.addWidget(sub)
        layout.addStretch()

        for name, obj_suffix in (
            ("—", "Min"),
            ("□", "Max"),
            ("✕", "Close"),
        ):
            btn = QPushButton(name)
            btn.setObjectName("scNextTitleBtn")
            if obj_suffix == "Close":
                btn.setObjectName("scNextTitleClose")
            btn.setEnabled(False)
            layout.addWidget(btn)

        return bar

    def _build_scene_tabs(self) -> QWidget:
        wrap = QWidget()
        wrap.setObjectName("scNextSceneTabs")
        layout = QHBoxLayout(wrap)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(0)

        for index, label in enumerate(self.SCENES):
            button = _scene_tab(label, active=index == 0)
            button.clicked.connect(
                lambda _checked=False, i=index: self._select_scene(i)
            )
            self._scene_buttons.append(button)
            layout.addWidget(button)

        layout.addStretch()
        return wrap

    def _select_scene(self, index: int):
        self.stack.setCurrentIndex(index)

        for i, button in enumerate(self._scene_buttons):
            button.setProperty("active", i == index)
            button.style().unpolish(button)
            button.style().polish(button)

    def _build_login_scene(self) -> QWidget:
        page = QWidget()
        page.setObjectName("scNextLoginBackdrop")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(1)

        card = QFrame()
        card.setObjectName("scNextLoginCard")
        card.setFixedWidth(440)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 36, 36, 32)
        card_layout.setSpacing(14)

        logo = QLabel("MOBIGLAS")
        logo.setObjectName("scNextLoginLogo")
        logo.setAlignment(Qt.AlignCenter)

        tagline = QLabel("BERGUNGS-TRACKER")
        tagline.setObjectName("scNextLoginTagline")
        tagline.setAlignment(Qt.AlignCenter)

        card_layout.addWidget(logo)
        card_layout.addWidget(tagline)
        card_layout.addSpacing(8)

        user_label = QLabel("BENUTZERNAME")
        user_label.setObjectName("scNextFieldLabel")
        user_input = QLineEdit()
        user_input.setObjectName("scNextInput")
        user_input.setPlaceholderText("Benutzername eingeben")
        user_input.setText("admin")

        pass_label = QLabel("PASSWORT")
        pass_label.setObjectName("scNextFieldLabel")
        pass_input = QLineEdit()
        pass_input.setObjectName("scNextInput")
        pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        pass_input.setPlaceholderText("••••••••")

        card_layout.addWidget(user_label)
        card_layout.addWidget(user_input)
        card_layout.addWidget(pass_label)
        card_layout.addWidget(pass_input)
        card_layout.addSpacing(6)

        login_btn = QPushButton("ANMELDEN")
        login_btn.setObjectName("scNextPrimary")
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        card_layout.addWidget(login_btn)

        hint = QLabel(self._config["login_hint"])
        hint.setObjectName("scNextLoginHint")
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(hint)

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(card)
        row.addStretch()
        outer.addLayout(row)
        outer.addStretch(1)
        return page

    def _build_main_scene(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        nav = QWidget()
        nav.setObjectName("scNextNavRail")
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(0, 24, 0, 20)
        nav_layout.setSpacing(4)

        brand = QLabel("MOBIGLAS")
        brand.setObjectName("scNextNavBrand")
        brand.setAlignment(Qt.AlignCenter)

        user = QLabel("captain_reclaimer")
        user.setObjectName("scNextNavUser")
        user.setAlignment(Qt.AlignCenter)

        role = QLabel("ADMINISTRATOR")
        role.setObjectName("scNextNavRole")
        role.setAlignment(Qt.AlignCenter)

        nav_layout.addWidget(brand)
        nav_layout.addSpacing(4)
        nav_layout.addWidget(user)
        nav_layout.addWidget(role)
        nav_layout.addSpacing(12)
        nav_layout.addWidget(_divider())
        nav_layout.addSpacing(8)

        items = [
            ("▸  Übersicht", True),
            ("   Sitzung", False),
            ("   Raffinerie", False),
            ("   Verkäufe", False),
            ("   Auszahlung", False),
            ("   Historie", False),
            ("   Einstellungen", False),
        ]
        for text, active in items:
            nav_layout.addWidget(_nav_item(text, active=active))

        nav_layout.addStretch()

        logout = QPushButton("Abmelden")
        logout.setObjectName("scNextGhost")
        logout.setCursor(Qt.CursorShape.PointingHandCursor)
        nav_layout.addWidget(logout)

        content = QWidget()
        content.setObjectName("scNextContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(32, 28, 32, 24)
        content_layout.setSpacing(18)

        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("ÜBERSICHT")
        title.setObjectName("scNextPageTitle")
        subtitle = QLabel(
            "Aktive Bergungssitzung · Stanton · Grid TDD"
        )
        subtitle.setObjectName("scNextPageSubtitle")
        header.addWidget(title)
        header.addWidget(subtitle)
        content_layout.addLayout(header)

        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(14)
        kpi_row.addWidget(
            _kpi_card("ROHMATERIAL", "14.280 SCU")
        )
        kpi_row.addWidget(
            _kpi_card("RAFFINIERT", "6.420 SCu", accent=True)
        )
        kpi_row.addWidget(
            _kpi_card("UMSATZ", "2.847.500 aUEC", accent=True)
        )
        kpi_row.addWidget(
            _kpi_card("CREW ONLINE", "4 / 6")
        )
        content_layout.addLayout(kpi_row)

        section = QLabel("LETZTE AKTIVITÄT")
        section.setObjectName("scNextSectionLabel")
        content_layout.addWidget(section)

        panel = QFrame()
        panel.setObjectName("scNextPanelElevated")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 16, 20, 16)
        panel_layout.setSpacing(12)

        chips = QHBoxLayout()
        chips.addWidget(self._chip("Session aktiv", ok=True))
        chips.addWidget(self._chip("Raffinerie · 68 %"))
        chips.addWidget(self._chip("Netzwerk · Host", warn=True))
        chips.addStretch()
        panel_layout.addLayout(chips)

        table = QTableWidget(4, 4)
        table.setObjectName("scNextTable")
        table.setHorizontalHeaderLabels(
            ["ZEIT", "EREIGNIS", "MATERIAL", "WERT"]
        )
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        rows = [
            ("21:14", "Verkauf abgeschlossen", "Quantanium", "412.000"),
            ("20:52", "Raffinerie gestartet", "Bexalite", "—"),
            ("20:31", "Material eingelagert", "Hephaestanite", "88 SCU"),
            ("19:58", "Session eröffnet", "Reclaimer", "—"),
        ]
        for row_index, row in enumerate(rows):
            for col_index, value in enumerate(row):
                table.setItem(
                    row_index,
                    col_index,
                    QTableWidgetItem(value),
                )
        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)
        panel_layout.addWidget(table)
        content_layout.addWidget(panel, 1)

        layout.addWidget(nav)
        layout.addWidget(content, 1)
        return page

    def _chip(
        self,
        text: str,
        *,
        ok: bool = False,
        warn: bool = False,
    ) -> QLabel:
        label = QLabel(text)
        if ok:
            label.setObjectName("scNextChipOk")
        elif warn:
            label.setObjectName("scNextChipWarn")
        else:
            label.setObjectName("scNextChip")
        return label

    def _build_components_scene(self) -> QWidget:
        page = QWidget()
        page.setObjectName("scNextContent")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(20)

        title = QLabel("KOMPONENTEN")
        title.setObjectName("scNextPageTitle")
        subtitle = QLabel(
            "Buttons · Eingaben · Panels · Status — einheitliches "
            "Design-System für die spätere Umstellung"
        )
        subtitle.setObjectName("scNextPageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setSpacing(16)

        buttons_panel, buttons_layout = self._panel("Buttons")
        btn_row = QHBoxLayout()
        for text, obj in (
            ("Primär", "scNextPrimary"),
            ("Sekundär", "scNextSecondary"),
            ("Ghost", "scNextGhost"),
        ):
            btn = QPushButton(text.upper())
            btn.setObjectName(obj)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_row.addWidget(btn)
        buttons_layout.addLayout(btn_row)
        grid.addWidget(buttons_panel, 0, 0)

        inputs_panel, inputs_layout = self._panel("Eingaben")
        for label_text in ("Benutzername", "Passwort"):
            lbl = QLabel(label_text.upper())
            lbl.setObjectName("scNextFieldLabel")
            field = QLineEdit()
            field.setObjectName("scNextInput")
            field.setPlaceholderText(f"{label_text} …")
            inputs_layout.addWidget(lbl)
            inputs_layout.addWidget(field)
        grid.addWidget(inputs_panel, 0, 1)

        status_panel, status_layout = self._panel("Status")
        chip_row = QHBoxLayout()
        chip_row.addWidget(self._chip("Bereit", ok=True))
        chip_row.addWidget(self._chip("Warnung", warn=True))
        chip_row.addWidget(self._chip("Info"))
        chip_row.addStretch()
        status_layout.addLayout(chip_row)
        grid.addWidget(status_panel, 1, 0)

        palette_panel, palette_layout = self._panel("Farben")
        colors = [
            ("#E07A2A", "Primär / RSI-Orange"),
            ("#42D4F5", "Akzent / Cyan"),
            ("#121820", "Panel"),
            ("#0A0D12", "Hintergrund"),
            ("#E6EEF5", "Text"),
            ("#708696", "Muted"),
        ]
        for hex_color, name in colors:
            row = QHBoxLayout()
            swatch = QFrame()
            swatch.setFixedSize(28, 28)
            swatch.setStyleSheet(
                f"background:{hex_color};"
                "border:1px solid #334155;border-radius:4px;"
            )
            lbl = QLabel(f"{name}  ·  {hex_color}")
            lbl.setObjectName("scNextPageSubtitle")
            row.addWidget(swatch)
            row.addWidget(lbl)
            row.addStretch()
            palette_layout.addLayout(row)
        grid.addWidget(palette_panel, 1, 1)

        if self.variant == "scifi":
            typo_panel, typo_layout = self._panel("Typografie")
            samples = (
                ("scNextFontDisplay", "Audiowide — MOBIGLAS"),
                ("scNextFontHeading", "Michroma — SECTION LABEL"),
                (
                    "scNextFontBody",
                    "Exo 2 — Navigation, Beschreibungen, UI-Text",
                ),
                (
                    "scNextFontMono",
                    "Share Tech Mono — 14.280 SCU · 21:14 · aUEC",
                ),
            )
            for obj_name, text in samples:
                label = QLabel(text)
                label.setObjectName(obj_name)
                label.setWordWrap(True)
                typo_layout.addWidget(label)
            grid.addWidget(typo_panel, 2, 0, 1, 2)

        layout.addLayout(grid)
        layout.addStretch()
        return page

    def _panel(self, title: str):
        panel = QFrame()
        panel.setObjectName("scNextPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        heading = QLabel(title.upper())
        heading.setObjectName("scNextSectionLabel")
        layout.addWidget(heading)
        return panel, layout


def load_preview_theme(app: QApplication, variant: str = "classic") -> None:
    config = PREVIEW_VARIANTS[variant]
    qss_path = asset_path(config["theme"])
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))


def load_preview_fonts(variant: str = "classic") -> None:
    seen: set[str] = set()

    for font_file in PREVIEW_VARIANTS[variant]["fonts"]:
        path = asset_path(font_file)
        if not path.exists() or str(path) in seen:
            continue

        seen.add(str(path))
        QFontDatabase.addApplicationFont(str(path))


def run_design_preview(variant: str = "classic") -> int:
    if variant not in PREVIEW_VARIANTS:
        variant = "classic"

    app = QApplication([])
    load_preview_fonts(variant)
    load_preview_theme(app, variant)

    if variant == "scifi":
        body = QFont("Exo 2", 14)
        body.setWeight(QFont.Weight.DemiBold)
        app.setFont(body)

    window = DesignPreviewWindow(variant=variant)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run_design_preview())
