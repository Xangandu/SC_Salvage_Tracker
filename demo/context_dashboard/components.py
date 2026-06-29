"""Gemeinsame UI-Bausteine für die Kontext-Dashboard-Demo."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.dashboard_number_animation import AnimatedDashboardValue
from ui.page_layout import form_label, hud_divider, subsection_title


def field_column(label_text: str, value_widget: QWidget) -> QWidget:
    host = QWidget()
    host.setAutoFillBackground(False)
    col = QVBoxLayout(host)
    col.setContentsMargins(0, 0, 0, 0)
    col.setSpacing(2)
    col.addWidget(form_label(label_text))
    col.addWidget(value_widget)
    return host


def kpi_card(title: str, value: QWidget, *, accent=False) -> QFrame:
    card = QFrame()
    card.setObjectName("dashboardKpiCard")
    card.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Minimum,
    )
    layout = QVBoxLayout(card)
    layout.setContentsMargins(12, 10, 12, 10)
    layout.setSpacing(8)
    layout.addWidget(subsection_title(title.upper()))

    divider = QWidget()
    divider.setAutoFillBackground(False)
    divider.setLayout(hud_divider())
    layout.addWidget(divider)

    value.setObjectName("profitLabel" if accent else "cardValue")
    if hasattr(value, "setAlignment"):
        value.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
    layout.addWidget(value)
    return card


def dashboard_card() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("dashboardCard")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(10)
    return frame, layout


class GlobalAlertStrip(QFrame):
    """Dünner app-weiter Hinweis — Verbesserung aus dem Konzept."""

    clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("infoPanel")
        self._target = "overview"

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 8, 12, 8)
        row.setSpacing(10)

        self.icon_label = QLabel("◆")
        self.icon_label.setObjectName("hudMarker")
        row.addWidget(self.icon_label)

        self.message_label = QLabel()
        self.message_label.setObjectName("warningBannerTitle")
        self.message_label.setWordWrap(True)
        row.addWidget(self.message_label, 1)

        self.action_button = QPushButton()
        self.action_button.setObjectName("secondaryAction")
        self.action_button.clicked.connect(self._emit)
        row.addWidget(self.action_button)

    def _emit(self):
        self.clicked.emit(self._target)

    def set_alert(self, alert: dict | None):
        if not alert:
            self.hide()
            return
        self._target = alert.get("target_context", "overview")
        self.message_label.setText(alert.get("message", ""))
        self.action_button.setText(alert.get("action_label", "Anzeigen"))
        self.show()


class ContextHeader(QWidget):
    """Zeigt aktuellen Dashboard-Kontext + Pin/Folgen."""

    pin_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self.context_title = QLabel()
        self.context_title.setObjectName("pageTitle")
        self.context_subtitle = QLabel()
        self.context_subtitle.setObjectName("sectionAccent")
        text_col.addWidget(self.context_title)
        text_col.addWidget(self.context_subtitle)
        row.addLayout(text_col, 1)

        self.mode_label = QLabel()
        self.mode_label.setObjectName("mutedLabel")
        row.addWidget(self.mode_label)

        self.pin_button = QPushButton("Anheften")
        self.pin_button.setObjectName("secondaryAction")
        self.pin_button.setCheckable(True)
        self.pin_button.toggled.connect(self._on_pin)
        row.addWidget(self.pin_button)

    def _on_pin(self, pinned: bool):
        self._update_mode_label(pinned)
        self.pin_toggled.emit(pinned)

    def _update_mode_label(self, pinned: bool):
        if pinned:
            self.mode_label.setText("Modus: Angeheftet")
            self.pin_button.setText("Loslösen")
        else:
            self.mode_label.setText("Modus: Folgt Navigation")
            self.pin_button.setText("Anheften")

    def set_context(self, key: str, labels: tuple[str, str], *, pinned: bool):
        title, subtitle = labels
        self.context_title.setText(f"◆ {title}")
        self.context_subtitle.setText(subtitle)
        self.pin_button.blockSignals(True)
        self.pin_button.setChecked(pinned)
        self.pin_button.blockSignals(False)
        self._update_mode_label(pinned)


class ProgressBarRow(QWidget):
    """Einfache Fortschrittszeile für Material-Standorte."""

    def __init__(self, label: str, detail: str, percent: int, parent=None):
        super().__init__(parent)
        col = QVBoxLayout(self)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(4)

        head = QHBoxLayout()
        name = QLabel(label)
        name.setObjectName("formLabel")
        pct = QLabel(f"{percent} %")
        pct.setObjectName("mutedLabel")
        head.addWidget(name)
        head.addStretch()
        head.addWidget(pct)
        col.addLayout(head)

        track = QFrame()
        track.setObjectName("hudLine")
        track.setFixedHeight(6)
        col.addWidget(track)

        fill_host = QFrame()
        fill_host.setFixedHeight(6)
        fill_host.setStyleSheet("background: transparent;")
        fill_layout = QHBoxLayout(fill_host)
        fill_layout.setContentsMargins(0, 0, 0, 0)
        fill_layout.setSpacing(0)
        fill = QFrame()
        fill.setObjectName("hudMarker")
        fill.setFixedHeight(6)
        fill.setMinimumWidth(max(24, int(2.4 * percent)))
        fill_layout.addWidget(fill)
        fill_layout.addStretch()
        col.addWidget(fill_host)

        detail_label = QLabel(detail)
        detail_label.setObjectName("mutedLabel")
        detail_label.setWordWrap(True)
        col.addWidget(detail_label)


class TimelineRow(QWidget):
    def __init__(self, when: str, title: str, detail: str, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 4, 0, 4)
        row.setSpacing(12)

        when_label = QLabel(when)
        when_label.setObjectName("mutedLabel")
        when_label.setFixedWidth(72)
        row.addWidget(when_label)

        body = QVBoxLayout()
        body.setSpacing(2)
        t = QLabel(title)
        t.setObjectName("formLabel")
        d = QLabel(detail)
        d.setObjectName("displayValue")
        d.setWordWrap(True)
        body.addWidget(t)
        body.addWidget(d)
        row.addLayout(body, 1)


def animated_scu(initial: str = "0 SCU") -> AnimatedDashboardValue:
    widget = AnimatedDashboardValue(initial)
    widget.setObjectName("cardValue")
    return widget


def animate_scu(
    widget: AnimatedDashboardValue,
    value: float,
    *,
    duration=1200,
):
    widget.animate_to(
        value,
        suffix=" SCU",
        decimals=1,
        duration=duration,
    )


def animate_int(
    widget: AnimatedDashboardValue,
    value: float,
    *,
    suffix="",
    prefix="",
    duration=800,
):
    widget.animate_to(
        value,
        suffix=suffix,
        prefix=prefix,
        decimals=0,
        duration=duration,
    )


def animate_currency(widget: AnimatedDashboardValue, value: float):
    widget.animate_to(
        value,
        suffix=" aUEC",
        decimals=0,
        duration=1400,
    )
