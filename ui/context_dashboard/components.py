"""Gemeinsame Bausteine für kontextbezogene Dashboards."""

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from config.i18n import tr
from config.paths import asset_path
from ui.dashboard_number_animation import AnimatedDashboardValue
from ui.page_layout import form_label, hud_divider, subsection_title


MATERIAL_TILE_HEIGHT = 112
MATERIAL_TITLE_HEIGHT = 28
MATERIAL_GRID_COLUMNS = 3


def material_group_heading(text: str) -> QLabel:
    """Gruppen-Zwischenüberschrift (Verkaufsfähig / Rohstoffe)."""
    label = QLabel(text.upper())
    label.setObjectName("dashboardMaterialGroupTitle")
    return label


def _material_section_header(text: str, *, top_spacing: bool = False) -> QWidget:
    host = QWidget()
    host.setAutoFillBackground(False)
    col = QVBoxLayout(host)
    col.setContentsMargins(0, 16 if top_spacing else 0, 0, 0)
    col.setSpacing(6)
    col.addWidget(material_group_heading(text))
    divider = QWidget()
    divider.setAutoFillBackground(False)
    divider.setLayout(hud_divider())
    col.addWidget(divider)
    return host


def _hud_divider_widget() -> QWidget:
    host = QWidget()
    host.setAutoFillBackground(False)
    host.setLayout(hud_divider())
    return host


def material_kpi_card(title: str, value: QWidget) -> QFrame:
    """Material-Kachel mit fester Höhe und einheitlicher Aufteilung."""
    card = QFrame()
    card.setObjectName("dashboardMaterialKpiCard")
    card.setFixedHeight(MATERIAL_TILE_HEIGHT)
    card.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Fixed,
    )
    card.setMinimumWidth(0)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(10, 8, 10, 8)
    layout.setSpacing(4)

    title_label = QLabel(title.upper())
    title_label.setObjectName("cardTitle")
    title_label.setWordWrap(True)
    title_label.setFixedHeight(MATERIAL_TITLE_HEIGHT)
    title_label.setAlignment(
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
    )
    layout.addWidget(title_label)

    divider = _hud_divider_widget()
    layout.addWidget(divider)

    value.setObjectName("cardValue")
    value.setAlignment(
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
    )
    value.setMinimumHeight(28)
    layout.addWidget(value, 1)

    return card


def _material_grid_placeholder() -> QFrame:
    placeholder = QFrame()
    placeholder.setObjectName("dashboardMaterialKpiPlaceholder")
    placeholder.setFixedHeight(MATERIAL_TILE_HEIGHT)
    placeholder.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Fixed,
    )
    placeholder.setMinimumWidth(0)
    return placeholder


def build_session_materials_grid(
    sellable_codes: tuple[str, ...] | list[str],
    raw_codes: tuple[str, ...] | list[str],
    mat_widgets: dict[str, AnimatedDashboardValue],
    *,
    sellable_heading: str,
    raw_heading: str,
) -> QGridLayout:
    """Ein Raster (4×3): Überschriften + Kacheln mit identischen Spaltenbreiten."""
    from config.materials import material_label

    grid = QGridLayout()
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(10)
    grid.setVerticalSpacing(10)

    for col in range(MATERIAL_GRID_COLUMNS):
        grid.setColumnStretch(col, 1)

    sellable_header = _material_section_header(sellable_heading)
    grid.addWidget(sellable_header, 0, 0, 1, MATERIAL_GRID_COLUMNS)

    for col, code in enumerate(sellable_codes):
        widget = animated_scu()
        mat_widgets[code] = widget
        grid.addWidget(
            material_kpi_card(material_label(code), widget),
            1,
            col,
        )

    for col in range(len(sellable_codes), MATERIAL_GRID_COLUMNS):
        grid.addWidget(_material_grid_placeholder(), 1, col)

    raw_header = _material_section_header(raw_heading, top_spacing=True)
    grid.addWidget(raw_header, 2, 0, 1, MATERIAL_GRID_COLUMNS)

    for col, code in enumerate(raw_codes):
        widget = animated_scu()
        mat_widgets[code] = widget
        grid.addWidget(
            material_kpi_card(material_label(code), widget),
            3,
            col,
        )

    return grid


def kpi_card(
    title: str,
    value: QWidget,
    *,
    accent=False,
    uniform=False,
) -> QFrame:
    card = QFrame()
    card.setObjectName("dashboardKpiCard")
    card.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Preferred if uniform else QSizePolicy.Policy.Minimum,
    )
    if uniform:
        card.setMinimumHeight(96)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(12, 10, 12, 10)
    layout.setSpacing(8)
    title_label = subsection_title(title.upper())
    if uniform:
        title_label.setWordWrap(True)
    layout.addWidget(title_label)

    divider = QWidget()
    divider.setAutoFillBackground(False)
    divider.setLayout(hud_divider())
    layout.addWidget(divider)

    value.setObjectName("profitLabel" if accent else "cardValue")
    if hasattr(value, "setAlignment"):
        value.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
    layout.addWidget(value, 1 if uniform else 0)
    return card


def dashboard_card() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("dashboardCard")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(10)
    return frame, layout


def field_column(label_text: str, value_widget: QWidget) -> QWidget:
    host = QWidget()
    host.setAutoFillBackground(False)
    col = QVBoxLayout(host)
    col.setContentsMargins(0, 0, 0, 0)
    col.setSpacing(2)
    col.addWidget(form_label(label_text))
    col.addWidget(value_widget)
    return host


class ProgressBarRow(QWidget):
    """Fortschrittszeile — Balkenhöhe 11 px."""

    BAR_HEIGHT_PX = 11

    def __init__(
        self,
        label: str,
        detail: str,
        percent: int,
        parent=None,
        *,
        badge_text: str | None = None,
    ):
        super().__init__(parent)
        bar_h = self.BAR_HEIGHT_PX
        col = QVBoxLayout(self)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(4)

        head = QHBoxLayout()
        name = QLabel(label)
        name.setObjectName("formLabel")
        pct = QLabel(badge_text if badge_text is not None else f"{percent} %")
        pct.setObjectName("mutedLabel")
        head.addWidget(name)
        head.addStretch()
        if badge_text is not None or percent > 0:
            head.addWidget(pct)
        col.addLayout(head)

        fill_host = QFrame()
        fill_host.setFixedHeight(bar_h)
        fill_host.setStyleSheet(
            f"background: #263545; border-radius: {bar_h // 2}px;"
        )
        fill_layout = QHBoxLayout(fill_host)
        fill_layout.setContentsMargins(0, 0, 0, 0)
        fill_layout.setSpacing(0)
        fill = QFrame()
        fill.setStyleSheet(
            f"background: #E07A2A; border-radius: {bar_h // 2}px; "
            f"min-height: {bar_h}px;"
        )
        fill.setFixedHeight(bar_h)
        fill.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        clamped = max(0, min(100, int(percent)))
        if clamped <= 0:
            fill_layout.addStretch(1)
        else:
            fill_layout.addWidget(fill, clamped)
            if clamped < 100:
                fill_layout.addStretch(100 - clamped)
        col.addWidget(fill_host)

        detail_label = QLabel(detail)
        detail_label.setObjectName("mutedLabel")
        detail_label.setWordWrap(True)
        col.addWidget(detail_label)


class SessionRefineryProcessRow(QWidget):
    """Kompakte Raffinerie-Prozesszeile mit Live-Fortschritt."""

    def __init__(
        self,
        job: dict,
        title: str,
        detail: str,
        parent=None,
    ):
        super().__init__(parent)
        from ui.refinery_job_card import (
            RefineryJobProgressBar,
            refinery_job_progress_state,
            _format_countdown,
        )

        self._job = dict(job)
        self._title_text = title
        self._base_detail = detail
        self._progress_state = refinery_job_progress_state
        self._format_countdown = _format_countdown

        col = QVBoxLayout(self)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(4)

        head = QHBoxLayout()
        self._name = QLabel(title)
        self._name.setObjectName("formLabel")
        self._pct = QLabel("0 %")
        self._pct.setObjectName("mutedLabel")
        head.addWidget(self._name)
        head.addStretch()
        head.addWidget(self._pct)
        col.addLayout(head)

        self._progress_bar = RefineryJobProgressBar(self)
        col.addWidget(self._progress_bar)

        self._detail_label = QLabel(detail)
        self._detail_label.setObjectName("mutedLabel")
        self._detail_label.setWordWrap(True)
        col.addWidget(self._detail_label)

        self.tick()

    def job_id(self) -> int | None:
        return self._job.get("id")

    def set_process(self, job: dict, title: str, detail: str) -> None:
        self._job = dict(job)
        self._title_text = title
        self._base_detail = detail
        self._name.setText(title)
        self.tick()

    def tick(self) -> None:
        from config.i18n import format_number

        state = self._progress_state(self._job)
        progress = state["progress"]
        remaining_seconds = state["remaining_seconds"]
        is_ready = state["is_ready"]

        self._pct.setText(f"{format_number(progress, 0)} %")
        self._progress_bar.set_progress(progress)

        if is_ready:
            status_note = tr("refinery.status.ready_for_pickup")
        else:
            status_note = self._format_countdown(remaining_seconds)
        self._detail_label.setText(
            f"{self._base_detail} · {status_note}"
        )


class _TimelineDividerWidget(QWidget):
    """Vertikaler HUD-Trenner — Linie und Punkt auf derselben Achse gezeichnet."""

    LINE_COLOR = QColor("#33485C")
    MARKER_COLOR = QColor("#E07A2A")
    MARKER_SIZE = 4
    MARKER_GAP = 6
    MARKER_X_OFFSET = 1
    MARKER_Y_OFFSET = 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboardTimelineDivider")
        self.setFixedWidth(10)
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Expanding,
        )

    def paintEvent(self, _event):
        painter = QPainter(self)
        center_x = self.width() // 2
        height = self.height()
        mid_y = height // 2
        half = self.MARKER_SIZE // 2
        line_end = half + self.MARKER_GAP

        painter.setPen(QPen(self.LINE_COLOR, 1))
        painter.drawLine(center_x, 0, center_x, mid_y - line_end)
        painter.drawLine(center_x, mid_y + line_end, center_x, height)

        painter.fillRect(
            center_x - half + self.MARKER_X_OFFSET,
            mid_y - half + self.MARKER_Y_OFFSET,
            self.MARKER_SIZE,
            self.MARKER_SIZE,
            self.MARKER_COLOR,
        )
        painter.end()


def _timeline_divider() -> QWidget:
    return _TimelineDividerWidget()


class TimelineRow(QWidget):

    ICON_COLUMN_PX = 20
    TEXT_AFTER_DIVIDER_MARGIN = 12
    COLUMN_SPACING = 8
    WHEN_COLUMN_SAMPLES = (
        "31.12.2026 23:59:59",
        "31.12.2026 23:59",
        "—",
    )

    @classmethod
    def _timeline_when_font_metrics(cls, scales=None) -> QFontMetrics:
        """Gleiche Schrift wie ThemeManager.apply_dashboard_fonts für Datum/Uhrzeit."""
        from config.font_families import resolve_body_font
        from ui.theme_manager import (
            DASHBOARD_FONT_BASE_PX,
            ThemeManager,
        )

        settings = (
            scales
            if scales is not None
            else ThemeManager.current_settings()
        )
        resolved = ThemeManager.resolve_dashboard_scales(settings)
        widget_px = ThemeManager._scaled_dashboard_px(
            DASHBOARD_FONT_BASE_PX,
            resolved["dashboard_font_scale"],
        )
        font = QFont(
            resolve_body_font(ThemeManager._current_font_family_id()),
            widget_px,
        )
        font.setBold(True)
        return QFontMetrics(font)

    @classmethod
    def _timeline_when_column_width(
        cls,
        *,
        extra_text: str = "",
        scales=None,
    ) -> int:
        """Spaltenbreite inkl. Dashboard-Widget-Skalierung — Trenner bleiben bündig."""
        metrics = cls._timeline_when_font_metrics(scales)
        samples = cls.WHEN_COLUMN_SAMPLES
        if extra_text:
            samples = (*samples, extra_text)
        return max(metrics.horizontalAdvance(sample) for sample in samples)

    @classmethod
    def refresh_when_columns(
        cls,
        root: QWidget,
        scales=None,
        *,
        rows=None,
    ) -> None:
        """Nach Dashboard-Schrift-Slider Spaltenbreite aller Timeline-Zeilen anpassen."""
        if rows is None:
            rows = [
                widget
                for widget in root.findChildren(QWidget)
                if widget.objectName() == "dashboardTimelineRow"
                and getattr(widget, "_when_label", None) is not None
            ]
        if not rows:
            return

        metrics = cls._timeline_when_font_metrics(scales)
        width = cls._timeline_when_column_width(scales=scales)
        for row in rows:
            width = max(
                width,
                metrics.horizontalAdvance(row._when_label.text()),
            )

        for row in rows:
            row._apply_when_column_width(width)

    def _apply_when_column_width(self, when_width: int) -> None:
        when_label = getattr(self, "_when_label", None)
        grid = getattr(self, "_grid", None)
        if when_label is None:
            return
        when_label.setFixedWidth(when_width)
        if grid is not None:
            grid.setColumnMinimumWidth(0, when_width)

    def __init__(
        self,
        when: str,
        title: str,
        detail: str,
        *,
        compact: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("dashboardTimelineRow")
        compact = compact or len(when.strip()) <= 2

        title_label = QLabel(title)
        title_label.setObjectName("formLabel")
        title_label.setWordWrap(True)
        detail_label = QLabel(detail)
        detail_label.setObjectName("mutedLabel")
        detail_label.setWordWrap(True)

        if compact:
            row = QHBoxLayout(self)
            row.setContentsMargins(0, 1, 0, 1)
            row.setSpacing(6)

            when_label = QLabel(when)
            when_label.setObjectName("hudMarker")
            when_label.setFixedWidth(self.ICON_COLUMN_PX)
            when_label.setAlignment(
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
            )
            row.addWidget(
                when_label,
                0,
                Qt.AlignmentFlag.AlignTop,
            )

            body = QVBoxLayout()
            body.setSpacing(0)
            body.setContentsMargins(0, 0, 0, 0)
            body.addWidget(title_label)
            body.addWidget(detail_label)
            row.addLayout(body, 1)
            return

        grid = QGridLayout(self)
        grid.setContentsMargins(0, 1, 0, 1)
        grid.setHorizontalSpacing(self.COLUMN_SPACING)
        grid.setVerticalSpacing(0)

        when_label = QLabel(when)
        when_label.setObjectName("dashboardTimelineWhen")
        when_label.setWordWrap(False)
        when_width = self._timeline_when_column_width(extra_text=when)
        self._when_label = when_label
        self._grid = grid
        self._apply_when_column_width(when_width)
        when_label.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Preferred,
        )
        when_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        divider = _timeline_divider()

        grid.addWidget(
            when_label,
            0,
            0,
            2,
            1,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
        )
        grid.addWidget(divider, 0, 1, 2, 1)

        text_host = QWidget()
        text_layout = QVBoxLayout(text_host)
        text_layout.setContentsMargins(
            self.TEXT_AFTER_DIVIDER_MARGIN,
            0,
            0,
            0,
        )
        text_layout.setSpacing(0)
        text_layout.addWidget(title_label)
        text_layout.addWidget(detail_label)
        grid.addWidget(text_host, 0, 2, 2, 1)
        grid.setColumnStretch(2, 1)


def animated_scu(initial: str = "0 SCU") -> AnimatedDashboardValue:
    widget = AnimatedDashboardValue(initial)
    widget.setObjectName("cardValue")
    return widget


def animate_scu(widget: AnimatedDashboardValue, value, *, duration=1200):
    widget.animate_to(value or 0, suffix=" SCU", decimals=0, duration=duration)


def animate_int(widget: AnimatedDashboardValue, value, *, suffix="", duration=800):
    widget.animate_to(value or 0, suffix=suffix, decimals=0, duration=duration)


def animate_currency(widget: AnimatedDashboardValue, value):
    widget.animate_to(value or 0, suffix=" aUEC", decimals=0, duration=1400)


def update_scu(widget: AnimatedDashboardValue, value, *, animated=True, duration=1200):
    if animated:
        animate_scu(widget, value, duration=duration)
    else:
        widget.set_immediate(value or 0, suffix=" SCU", decimals=0)


def update_int(
    widget: AnimatedDashboardValue,
    value,
    *,
    suffix="",
    animated=True,
    duration=800,
):
    if animated:
        animate_int(widget, value, suffix=suffix, duration=duration)
    else:
        widget.set_immediate(value or 0, suffix=suffix, decimals=0)


def update_currency(widget: AnimatedDashboardValue, value, *, animated=True):
    if animated:
        animate_currency(widget, value)
    else:
        widget.set_immediate(value or 0, suffix=" aUEC", decimals=0)


class DashboardAlertBell(QToolButton):
    """Glocke — klappt die Hinweisleiste auf/zu."""

    expansion_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboardAlertBell")
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        bell_path = asset_path("assets", "images", "icons", "bell.svg")
        if bell_path.exists():
            self.setIcon(QIcon(str(bell_path)))
        self.setIconSize(QSize(22, 22))
        self.setFixedSize(36, 36)
        self.setCheckable(True)
        self.setChecked(False)
        self.clicked.connect(self._on_click)

        self._badge = QLabel("●", self)
        self._badge.setObjectName("hudMarker")
        self._badge.setFixedSize(10, 10)
        self._badge.move(24, 4)
        self._badge.hide()

        self.setEnabled(False)

    def _on_click(self):
        self.expansion_changed.emit(self.isChecked())

    def set_has_alert(self, has_alert: bool):
        self._badge.setVisible(has_alert)
        self.setEnabled(has_alert)
        if not has_alert:
            self.blockSignals(True)
            self.setChecked(False)
            self.blockSignals(False)

    def collapse(self):
        if self.isChecked():
            self.blockSignals(True)
            self.setChecked(False)
            self.blockSignals(False)
            self.expansion_changed.emit(False)


class GlobalAlertStrip(QFrame):
    """App-weiter Hinweis als horizontale Leiste."""

    clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboardAlertStrip")
        self._target = "overview"
        self._alert: dict | None = None

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

    def set_alert(self, alert: dict | None, *, expanded: bool = False):
        if not alert or not alert.get("message"):
            self._alert = None
            self.hide()
            return

        self._alert = alert
        self._target = alert.get("target_context", "overview")
        self.message_label.setText(alert["message"])
        self.action_button.setText(
            alert.get("action_label") or tr("dashboard.alert.show")
        )
        self.setVisible(expanded)

    def set_expanded(self, expanded: bool):
        if self._alert:
            self.setVisible(expanded)


class ContextHeader(QWidget):

    pin_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self.context_title = QLabel()
        self.context_title.setObjectName("dashboardContextTitle")
        self.context_subtitle = QLabel()
        self.context_subtitle.setObjectName("sectionAccent")
        text_col.addWidget(self.context_title)
        text_col.addWidget(self.context_subtitle)
        row.addLayout(text_col, 1)

        self.alert_bell = DashboardAlertBell()
        row.addWidget(self.alert_bell)

        self.mode_label = QLabel()
        self.mode_label.setObjectName("mutedLabel")
        row.addWidget(self.mode_label)

        self.pin_button = QPushButton(tr("dashboard.context.pin"))
        self.pin_button.setObjectName("secondaryAction")
        self.pin_button.setCheckable(True)
        self.pin_button.toggled.connect(self._on_pin)
        row.addWidget(self.pin_button)

    def _on_pin(self, pinned: bool):
        self._refresh_mode_label(pinned)
        self.pin_toggled.emit(pinned)

    def _refresh_mode_label(self, pinned: bool):
        if pinned:
            self.mode_label.setText(tr("dashboard.context.mode_pinned"))
            self.pin_button.setText(tr("dashboard.context.unpin"))
        else:
            self.mode_label.setText(tr("dashboard.context.mode_follow"))
            self.pin_button.setText(tr("dashboard.context.pin"))

    def set_context(
        self,
        title: str,
        subtitle: str,
        *,
        pinned: bool,
        nav_hint: str = "",
    ):
        self.context_title.setText(title)
        self.context_subtitle.setText(subtitle)
        if nav_hint:
            self.context_subtitle.setText(
                f"{subtitle}  ·  {nav_hint}"
            )
        self.pin_button.blockSignals(True)
        self.pin_button.setChecked(pinned)
        self.pin_button.blockSignals(False)
        self._refresh_mode_label(pinned)
