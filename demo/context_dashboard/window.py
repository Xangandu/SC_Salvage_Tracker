"""Demo-Hauptfenster: Navigation + Platzhalter-Seite + Kontext-Dashboard."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from demo.context_dashboard import mock_data
from demo.context_dashboard.shell import ContextDashboardShell
from ui.nav_button_icons import configure_nav_button
from ui.page_layout import hud_divider, page_title, section_accent


NAV_ITEMS = (
    ("overview", "nav.dashboard", "dashboard"),
    ("session", "nav.session", "session"),
    ("refinery", "nav.refinery", "refinery"),
    ("storage", "nav.storage", "storage"),
    ("sales", "nav.sales", "sales"),
    ("payout", "nav.payout", "payout"),
    ("history", "nav.history", "history"),
)

PAGE_BLURBS = {
    "overview": (
        "Übersicht",
        "Globale KPIs und nächste Aktionen — expliziter Dashboard-Modus.",
    ),
    "session": (
        "Session-Seite",
        "Hier arbeitest du an der aktiven Sitzung (Platzhalter).",
    ),
    "refinery": (
        "Raffinerie-Seite",
        "Jobs anlegen, Status verfolgen (Platzhalter).",
    ),
    "storage": (
        "Lager-Seite",
        "Bestand, Standorte, Warnungen (Platzhalter).",
    ),
    "sales": (
        "Verkauf-Seite",
        "Material verkaufen (Platzhalter).",
    ),
    "payout": (
        "Auszahlung-Seite",
        "Payouts erfassen (Platzhalter).",
    ),
    "history": (
        "Historie-Seite",
        "Verlauf und Statistik (Platzhalter).",
    ),
}


class DemoMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowTitle("SC Salvage Tracker — Kontext-Dashboard DEMO")
        self.resize(1480, 920)

        central = QWidget()
        central.setObjectName("mainCentral")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        nav = QWidget()
        nav.setObjectName("navPanel")
        nav.setFixedWidth(248)
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(0, 20, 0, 20)
        nav_layout.setSpacing(4)

        brand = QFrame()
        brand.setObjectName("navBrandCard")
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(14, 14, 14, 12)
        t1 = QLabel("SALVAGE")
        t1.setObjectName("navTitlePrimary")
        t2 = QLabel("TRACKER DEMO")
        t2.setObjectName("navTitleSecondary")
        brand_layout.addWidget(t1)
        brand_layout.addWidget(t2)
        nav_layout.addWidget(brand)
        nav_layout.addLayout(hud_divider())

        from config.i18n import tr

        self._nav_buttons: dict[str, QPushButton] = {}
        for key, label_key, icon_key in NAV_ITEMS:
            btn = QPushButton(tr(label_key))
            configure_nav_button(btn, icon_key)
            btn.clicked.connect(
                lambda checked=False, k=key: self._on_nav(k)
            )
            self._nav_buttons[key] = btn
            nav_layout.addWidget(btn)

        nav_layout.addStretch()
        root.addWidget(nav)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("contentStack")

        page_host = QWidget()
        page_host.setObjectName("pageContent")
        page_layout = QVBoxLayout(page_host)
        page_layout.setContentsMargins(24, 20, 24, 20)
        page_layout.setSpacing(12)

        self.page_title = page_title("Session")
        self.page_subtitle = section_accent("Platzhalter")
        page_layout.addWidget(self.page_title)
        page_layout.addWidget(self.page_subtitle)
        page_layout.addLayout(hud_divider())

        self.page_blurb = QLabel()
        self.page_blurb.setObjectName("displayValue")
        self.page_blurb.setWordWrap(True)
        page_layout.addWidget(self.page_blurb)

        hint = QLabel(
            "← Navigation wechselt die Fachseite und (im Modus „Folgen“) "
            "das Kontext-Dashboard rechts.\n"
            "„Anheften“ im Dashboard hält die Ansicht, während du "
            "andere Seiten öffnest."
        )
        hint.setObjectName("mutedLabel")
        hint.setWordWrap(True)
        page_layout.addWidget(hint)
        page_layout.addStretch()

        self.dashboard = ContextDashboardShell()
        self.dashboard.context_change_requested.connect(self._on_nav)

        splitter.addWidget(page_host)
        splitter.addWidget(self.dashboard)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 4)
        splitter.setSizes([520, 680])
        root.addWidget(splitter, 1)

        self._live_timer = QTimer(self)
        self._live_timer.setInterval(5000)
        self._live_timer.timeout.connect(
            self.dashboard.simulate_live_tick
        )
        self._live_timer.start()

        self._on_nav("session")

    def _set_active_button(self, key: str):
        for nav_key, btn in self._nav_buttons.items():
            active = nav_key == key
            btn.setProperty("active", active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_nav(self, key: str):
        self._set_active_button(key)
        title, blurb = PAGE_BLURBS.get(key, ("Seite", ""))
        self.page_title.setText(title)
        self.page_subtitle.setText(
            mock_data.CONTEXT_META.get(key, ("", ""))[1]
        )
        self.page_blurb.setText(blurb)
        self.dashboard.set_context(key)
