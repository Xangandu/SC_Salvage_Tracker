"""Kontext-Dashboard-Shell für das detached Dashboard-Fenster."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QStackedWidget, QVBoxLayout, QWidget

from config.i18n import tr
from database.dashboard_operations_repository import (
    DashboardOperationsRepository,
)
from ui.context_dashboard.components import ContextHeader, GlobalAlertStrip
from ui.context_dashboard.views import CONTEXT_VIEWS
from ui.dashboard_status_animation import DashboardStatusAnimator


CONTEXT_LABELS = {
    "overview": (
        "dashboard.context.overview.title",
        "dashboard.context.overview.subtitle",
    ),
    "session": (
        "dashboard.context.session.title",
        "dashboard.context.session.subtitle",
    ),
    "refinery": (
        "dashboard.context.refinery.title",
        "dashboard.context.refinery.subtitle",
    ),
    "storage": (
        "dashboard.context.storage.title",
        "dashboard.context.storage.subtitle",
    ),
    "sales": (
        "dashboard.context.sales.title",
        "dashboard.context.sales.subtitle",
    ),
    "payout": (
        "dashboard.context.payout.title",
        "dashboard.context.payout.subtitle",
    ),
    "history": (
        "dashboard.context.history.title",
        "dashboard.context.history.subtitle",
    ),
}


class ContextDashboardShell(QWidget):
    """Stacked context views + header + global alert strip."""

    context_change_requested = Signal(str)

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboardPage")
        self.setAutoFillBackground(False)

        self.db = db
        self._repo = DashboardOperationsRepository(db)
        self._views: dict[str, QWidget] = {}
        self._pinned = False
        self._pinned_context = "overview"
        self._active_context = "overview"
        self._nav_context = "overview"
        self._last_session_status = None

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 16)
        root.setSpacing(12)

        self.context_header = ContextHeader()
        self.context_header.pin_toggled.connect(self._on_pin_toggled)
        self.context_header.alert_bell.expansion_changed.connect(
            self._on_alert_expansion_changed
        )
        root.addWidget(self.context_header)

        self.alert_strip = GlobalAlertStrip()
        self.alert_strip.clicked.connect(self._on_alert_action)
        root.addWidget(self.alert_strip)

        self.context_help = QLabel()
        self.context_help.setObjectName("dashboardContextHelp")
        self.context_help.setWordWrap(True)
        root.addWidget(self.context_help)

        self.stack = QStackedWidget()
        self.stack.setObjectName("dashboardContent")
        root.addWidget(self.stack, 1)

        for key, view_cls in CONTEXT_VIEWS.items():
            view = view_cls()
            self._views[key] = view
            self.stack.addWidget(view)

        self.set_context("overview", force=True)

    @property
    def status_card(self):
        session_view = self._views.get("session")
        return getattr(session_view, "status_card", None)

    @property
    def status_kpi_value(self):
        session_view = self._views.get("session")
        return getattr(session_view, "status_kpi_value", None)

    @property
    def session_status_label(self):
        session_view = self._views.get("session")
        return getattr(session_view, "session_status_label", None)

    def _on_pin_toggled(self, pinned: bool):
        self._pinned = pinned
        if pinned:
            self._pinned_context = self._active_context
        self._update_header()

    def _on_alert_expansion_changed(self, expanded: bool):
        self.alert_strip.set_expanded(expanded)

    def _on_alert_action(self, target: str):
        self.context_change_requested.emit(target)
        self.set_context(target, force=True)

    def set_context(self, key: str, *, force: bool = False):
        if key not in self._views:
            return

        self._nav_context = key

        if self._pinned and not force:
            self._update_header()
            return

        previous = self._active_context
        self._active_context = key
        if self._pinned:
            self._pinned_context = key

        self.stack.setCurrentWidget(self._views[key])
        self.refresh()
        self._update_header()

    def refresh(self):
        display = self._display_context()
        data = self._repo.build_context(display)
        view = self._views.get(display)
        if view is not None:
            view.apply_data(data)

        if display == "session":
            self._sync_session_status_animation(data)

        alert = self._repo.build_global_alert()
        has_alert = bool(alert and alert.get("message"))
        self.context_header.alert_bell.set_has_alert(has_alert)
        self.alert_strip.set_alert(
            alert,
            expanded=self.context_header.alert_bell.isChecked(),
        )

    def _display_context(self) -> str:
        if self._pinned:
            return self._pinned_context
        return self._active_context

    def _update_header(self):
        display = self._display_context()
        title_key, subtitle_key = CONTEXT_LABELS.get(
            display,
            CONTEXT_LABELS["overview"],
        )
        nav_hint = ""
        if self._pinned and self._nav_context != display:
            nav_title_key = CONTEXT_LABELS.get(
                self._nav_context,
                CONTEXT_LABELS["overview"],
            )[0]
            nav_hint = tr("dashboard.context.nav_pinned", nav=tr(nav_title_key))

        self.context_header.set_context(
            tr(title_key),
            tr(subtitle_key),
            pinned=self._pinned,
            nav_hint=nav_hint,
        )

        help_key = f"dashboard.context.{display}.help"
        help_text = tr(help_key)
        if help_text == help_key:
            self.context_help.hide()
        else:
            self.context_help.setText(help_text)
            self.context_help.show()

    def _sync_session_status_animation(self, data: dict):
        status_code = data.get("status") or "IDLE"
        status_text = data.get("status_label") or status_code
        previous = self._last_session_status

        if (
            previous is not None
            and previous != status_code
            and self.status_card is not None
            and self.status_kpi_value is not None
        ):
            DashboardStatusAnimator.pulse(
                self.status_card,
                self.status_kpi_value,
                status_code,
                status_text,
            )

        self._last_session_status = status_code
