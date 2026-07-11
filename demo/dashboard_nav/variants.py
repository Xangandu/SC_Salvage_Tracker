"""Mock-Navigationsbutton für Übersicht-Darstellungs-Demos."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config.i18n import tr
from ui.nav_button_icons import configure_nav_button


class DashboardNavVariant(QWidget):
    VARIANT_ID = "base"
    VARIANT_TITLE = ""
    VARIANT_HINT = ""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._window_open = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        hint = QLabel(self.VARIANT_HINT)
        hint.setObjectName("mutedLabel")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        nav_host = QFrame()
        nav_host.setObjectName("navPanel")
        nav_host.setFixedWidth(220)
        nav_layout = QVBoxLayout(nav_host)
        nav_layout.setContentsMargins(8, 12, 8, 12)
        nav_layout.setSpacing(8)

        self._button_host = QWidget()
        self._button_layout = QVBoxLayout(self._button_host)
        self._button_layout.setContentsMargins(0, 0, 0, 0)
        self._button_layout.setSpacing(8)
        nav_layout.addWidget(self._button_host)
        nav_layout.addStretch()

        layout.addWidget(nav_host, alignment=Qt.AlignmentFlag.AlignLeft)

        self._toggle = QPushButton("Fenster öffnen (simuliert)")
        self._toggle.setObjectName("secondaryAction")
        self._toggle.clicked.connect(self._toggle_window)
        layout.addWidget(self._toggle, alignment=Qt.AlignmentFlag.AlignLeft)

        self._state_label = QLabel()
        self._state_label.setObjectName("hintLabel")
        layout.addWidget(self._state_label)

        layout.addStretch()
        self._rebuild_button()

    def _toggle_window(self):
        self._window_open = not self._window_open
        self._rebuild_button()

    def _rebuild_button(self):
        while self._button_layout.count():
            item = self._button_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._button_layout.addWidget(self._build_control())
        self._toggle.setText(
            "Fenster schließen (simuliert)"
            if self._window_open
            else "Fenster öffnen (simuliert)"
        )
        self._state_label.setText(
            "Zustand: Übersicht-Fenster ist "
            + ("geöffnet" if self._window_open else "geschlossen")
        )

    def _build_control(self) -> QWidget:
        raise NotImplementedError


class VariantA_Current(DashboardNavVariant):
    VARIANT_ID = "current"
    VARIANT_TITLE = "A — Aktuell (Fix)"
    VARIANT_HINT = (
        "Rot = geschlossen („Übersicht ⧉“), Grün = geöffnet („Übersicht ●“). "
        "Nach dem Fix bleibt der Zustand auch beim Schließen per X korrekt."
    )

    def _build_control(self) -> QWidget:
        button = QPushButton(
            tr("dashboard.nav.detached")
            if self._window_open
            else tr("dashboard.nav.embedded")
        )
        configure_nav_button(button, "dashboard")
        button.setProperty(
            "dashboardWindowVisible",
            "true" if self._window_open else "false",
        )
        style = button.style()
        if style is not None:
            style.unpolish(button)
            style.polish(button)
        return button


class VariantB_StatusBadge(DashboardNavVariant):
    VARIANT_ID = "badge"
    VARIANT_TITLE = "B — Fester Text + Status-Punkt"
    VARIANT_HINT = (
        "Label bleibt „Übersicht“. Separater Punkt zeigt offen (grün) "
        "oder geschlossen (rot) — weniger Textflackern."
    )

    def _build_control(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("navButton")
        if self._window_open:
            frame.setProperty("dashboardWindowVisible", "true")
        else:
            frame.setProperty("dashboardWindowVisible", "false")

        row = QHBoxLayout(frame)
        row.setContentsMargins(10, 8, 10, 8)
        row.setSpacing(8)

        icon_btn = QPushButton()
        configure_nav_button(icon_btn, "dashboard")
        icon_btn.setFlat(True)
        icon_btn.setFixedSize(28, 28)
        icon_btn.setEnabled(False)
        row.addWidget(icon_btn)

        label = QLabel(tr("nav.dashboard"))
        label.setObjectName("formLabel")
        row.addWidget(label, 1)

        dot = QLabel("●")
        dot.setObjectName(
            "profitLabel" if self._window_open else "warningBannerTitle"
        )
        row.addWidget(dot)

        style = frame.style()
        if style is not None:
            style.unpolish(frame)
            style.polish(frame)
        return frame


class VariantC_AccentBar(DashboardNavVariant):
    VARIANT_ID = "accent"
    VARIANT_TITLE = "C — Akzentstreifen links"
    VARIANT_HINT = (
        "Farbiger Streifen links statt Vollfläche: rot = zu, grün = offen. "
        "Symbole ●/⧉ bleiben im Text."
    )

    def _build_control(self) -> QWidget:
        button = QPushButton(
            tr("dashboard.nav.detached")
            if self._window_open
            else tr("dashboard.nav.embedded")
        )
        configure_nav_button(button, "dashboard")
        accent = "#3DDC84" if self._window_open else "#FF6060"
        button.setStyleSheet(
            f"QPushButton#navButton {{"
            f"border-left: 6px solid {accent};"
            f"background-color: #141C26;"
            f"}}"
        )
        return button


VARIANTS = [
    VariantA_Current,
    VariantB_StatusBadge,
    VariantC_AccentBar,
]
