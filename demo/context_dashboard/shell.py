"""Kontext-Dashboard-Shell: Alert, Header, View-Stack."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from demo.context_dashboard import mock_data
from demo.context_dashboard.components import ContextHeader, GlobalAlertStrip
from demo.context_dashboard.views import CONTEXT_VIEWS


class ContextDashboardShell(QWidget):
    """Demo-Shell mit globaler Alert-Zeile und Kontext-Wechsel."""

    context_change_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboardPage")
        self._pinned = False
        self._pinned_context = "overview"
        self._active_context = "overview"
        self._views: dict[str, QWidget] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 16)
        root.setSpacing(12)

        self.demo_banner = QFrame()
        self.demo_banner.setObjectName("infoPanel")
        banner_layout = QVBoxLayout(self.demo_banner)
        banner_layout.setContentsMargins(10, 8, 10, 8)
        from PySide6.QtWidgets import QLabel

        banner_title = QLabel("DEMO — Kontext-Dashboard")
        banner_title.setObjectName("warningBannerTitle")
        banner_hint = QLabel(
            "Keine echten Daten. Navigation links wechselt das Dashboard "
            "(außer bei „Anheften“). Verbesserungen: globaler Alert, "
            "Übersicht-Modus, Pin/Folgen."
        )
        banner_hint.setObjectName("mutedLabel")
        banner_hint.setWordWrap(True)
        banner_layout.addWidget(banner_title)
        banner_layout.addWidget(banner_hint)
        root.addWidget(self.demo_banner)

        self.alert_strip = GlobalAlertStrip()
        self.alert_strip.clicked.connect(self._on_alert_clicked)
        root.addWidget(self.alert_strip)

        self.context_header = ContextHeader()
        self.context_header.pin_toggled.connect(self._on_pin_toggled)
        root.addWidget(self.context_header)

        self.stack = QStackedWidget()
        self.stack.setObjectName("dashboardContent")
        root.addWidget(self.stack, 1)

        for key, view_cls in CONTEXT_VIEWS.items():
            view = view_cls()
            self._views[key] = view
            self.stack.addWidget(view)

        self.set_context("overview", force=True)

    def _on_pin_toggled(self, pinned: bool):
        self._pinned = pinned
        if pinned:
            self._pinned_context = self._active_context
        self._update_header()

    def _on_alert_clicked(self, target: str):
        self.context_change_requested.emit(target)
        self.set_context(target, force=True)

    def set_context(self, key: str, *, force: bool = False):
        if key not in self._views:
            return

        if self._pinned and not force:
            self._update_header(nav_context=key)
            return

        self._active_context = key
        if self._pinned:
            self._pinned_context = key

        self.stack.setCurrentWidget(self._views[key])
        self._views[key].refresh()
        self._update_header(nav_context=key)

    def refresh_current(self):
        view = self._views.get(self._display_context())
        if view is not None:
            view.refresh()

    def _display_context(self) -> str:
        if self._pinned:
            return self._pinned_context
        return self._active_context

    def _update_header(self, nav_context: str | None = None):
        display = self._display_context()
        labels = mock_data.CONTEXT_META.get(
            display,
            ("DASHBOARD", ""),
        )
        self.context_header.set_context(
            display,
            labels,
            pinned=self._pinned,
        )
        self.alert_strip.set_alert(mock_data.GLOBAL_ALERT)

        if self._pinned and nav_context and nav_context != display:
            nav_label = mock_data.CONTEXT_META.get(nav_context, ("", ""))[0]
            self.context_header.context_subtitle.setText(
                f"{labels[1]}  ·  Nav: {nav_label} (angeheftet)"
            )

    def simulate_live_tick(self):
        """Demo: leichte Zahlenänderung für Animation."""
        import random

        from demo.context_dashboard import mock_data as md

        delta = random.uniform(-0.3, 0.8)
        md.SESSION["session_scu_total"] = max(
            0,
            md.SESSION["session_scu_total"] + delta,
        )
        md.SESSION["materials"]["RMC"] = max(
            0,
            md.SESSION["materials"]["RMC"] + delta * 0.2,
        )
        if self._display_context() == "session":
            self._views["session"].refresh()
