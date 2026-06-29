"""Hybrid-Dashboard: KPIs, Aktionen, Session, Raffinerie, Summen."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.i18n import tr, format_number, status_label
from config.materials import material_label
from database.dashboard_operations_repository import (
    DashboardOperationsRepository,
)
from ui.dashboard_fit_label import DashboardFitLabel
from ui.dashboard_number_animation import AnimatedDashboardValue
from ui.dashboard_status_animation import DashboardStatusAnimator
from ui.dashboard_widget_registry import widget_definitions
from ui.page_layout import (
    empty_info_panel,
    form_label,
    hud_divider,
    section_accent,
    subsection_title,
)


def _session_field_column(label_text: str, value_widget: QWidget) -> QWidget:
    host = QWidget()
    host.setAutoFillBackground(False)
    column = QVBoxLayout(host)
    column.setContentsMargins(0, 0, 0, 0)
    column.setSpacing(2)
    column.addWidget(form_label(label_text))
    column.addWidget(value_widget)
    return host


def _create_kpi_card(title: str, value: QWidget, *, accent=False) -> QFrame:
    card = QFrame()
    card.setMinimumSize(0, 0)
    card.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Minimum,
    )
    card.setObjectName("dashboardKpiCard")

    layout = QVBoxLayout(card)
    layout.setContentsMargins(12, 10, 12, 10)
    layout.setSpacing(8)

    title_label = subsection_title(title.upper())
    divider_host = QWidget()
    divider_host.setAutoFillBackground(False)
    divider_host.setLayout(hud_divider())

    if accent:
        value.setObjectName("profitLabel")
    else:
        value.setObjectName("cardValue")

    if hasattr(value, "setAlignment"):
        value.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
    if hasattr(value, "setWordWrap"):
        value.setWordWrap(True)
    value.setSizePolicy(
        QSizePolicy.Policy.Preferred,
        QSizePolicy.Policy.Minimum,
    )

    layout.addWidget(title_label)
    layout.addWidget(divider_host)
    layout.addWidget(value, 0, Qt.AlignmentFlag.AlignTop)
    return card


def _summary_column(label_text: str, widget: QWidget) -> QVBoxLayout:
    column = QVBoxLayout()
    column.setSpacing(2)
    if widget.objectName() != "profitLabel":
        widget.setObjectName("cardValue")
    column.addWidget(form_label(label_text))
    column.addWidget(widget)
    return column


class DashboardOperationsPanel(QWidget):

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboardOperationsPanel")
        self.setAutoFillBackground(False)

        self.db = db
        self._repo = DashboardOperationsRepository(db)
        self._row_cache: list[dict] = []
        self._last_session_status = None

        defs = widget_definitions()
        idle_text = status_label("IDLE")

        self.status_kpi_value = DashboardFitLabel(idle_text, max_lines=2)
        self.crew_kpi_value = AnimatedDashboardValue("0")
        self.rmc_value = AnimatedDashboardValue("0 SCU")
        self.cm_value = AnimatedDashboardValue("0 SCU")
        self.rubble_value = AnimatedDashboardValue("0 SCU")
        self.scraps_value = AnimatedDashboardValue("0 SCU")
        self.salvage_value = AnimatedDashboardValue("0 SCU")

        self.summary_revenue = AnimatedDashboardValue("0 aUEC")
        self.summary_profit = AnimatedDashboardValue("0 aUEC")
        self.summary_profit.setObjectName("profitLabel")
        self.summary_refinery = AnimatedDashboardValue("0")
        self.summary_active = AnimatedDashboardValue("0")
        self.summary_total_sessions = AnimatedDashboardValue("0")
        self.summary_sold = AnimatedDashboardValue("0")
        self.summary_storage = AnimatedDashboardValue("0 SCU")
        self.summary_idle = AnimatedDashboardValue("0")

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 24)
        root.setSpacing(16)

        kpi_grid = QGridLayout()
        kpi_grid.setContentsMargins(0, 0, 0, 0)
        kpi_grid.setHorizontalSpacing(10)
        kpi_grid.setVerticalSpacing(10)

        kpi_specs = [
            ("status", defs["status"]["title"], self.status_kpi_value),
            ("crew", defs["crew"]["title"], self.crew_kpi_value),
            ("rmc", defs["rmc"]["title"], self.rmc_value),
            ("cm", defs["cm"]["title"], self.cm_value),
            ("rubble", defs["rubble"]["title"], self.rubble_value),
            ("scraps", defs["scraps"]["title"], self.scraps_value),
            ("salvage", defs["salvage"]["title"], self.salvage_value),
        ]

        self.status_card = None
        for index, (card_id, title, value) in enumerate(kpi_specs):
            card = _create_kpi_card(title, value)
            if card_id == "status":
                self.status_card = card
            kpi_grid.addWidget(card, index // 4, index % 4)

        for col in range(4):
            kpi_grid.setColumnStretch(col, 1)

        root.addLayout(kpi_grid)

        root.addWidget(section_accent(tr("dashboard.operations.title")))

        operations_card = QFrame()
        operations_card.setObjectName("dashboardCard")
        operations_layout = QVBoxLayout(operations_card)
        operations_layout.setContentsMargins(16, 14, 16, 14)
        operations_layout.setSpacing(12)

        self.next_action_host = QFrame()
        self.next_action_host.setObjectName("infoPanel")
        next_layout = QVBoxLayout(self.next_action_host)
        next_layout.setContentsMargins(12, 12, 12, 12)
        next_layout.setSpacing(6)

        self.next_action_title = QLabel()
        self.next_action_title.setObjectName("warningBannerTitle")
        self.next_action_title.setWordWrap(True)
        next_layout.addWidget(self.next_action_title)

        self.next_action_hint = QLabel(tr("dashboard.operations.hint"))
        self.next_action_hint.setObjectName("mutedLabel")
        self.next_action_hint.setWordWrap(True)
        next_layout.addWidget(self.next_action_hint)
        operations_layout.addWidget(self.next_action_host)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            tr("dashboard.operations.col.status"),
            tr("dashboard.operations.col.material"),
            tr("dashboard.operations.col.quantity"),
            tr("dashboard.operations.col.context"),
            tr("dashboard.operations.col.detail"),
        ])
        from ui.table_utils import configure_mobiglas_table

        configure_mobiglas_table(
            self.table,
            "dataTable",
            selectable=False,
        )
        self.table.setMinimumHeight(220)
        operations_layout.addWidget(self.table)

        self.empty_panel = empty_info_panel(
            tr("dashboard.operations.empty"),
            "assets/images/icons/info.svg",
        )
        operations_layout.addWidget(self.empty_panel)
        root.addWidget(operations_card)

        details_row = QHBoxLayout()
        details_row.setSpacing(12)

        self.session_panel = QFrame()
        self.session_panel.setObjectName("dashboardSessionPanel")
        session_layout = QVBoxLayout(self.session_panel)
        session_layout.setContentsMargins(16, 14, 16, 14)
        session_layout.setSpacing(10)

        session_layout.addWidget(
            subsection_title(tr("dashboard.session.active"))
        )
        session_layout.addLayout(hud_divider())

        self.session_label = QLabel(tr("dashboard.session.none"))
        self.session_label.setObjectName("displayValue")
        self.session_label.setWordWrap(True)
        session_layout.addWidget(
            _session_field_column(
                tr("dashboard.label.ship"),
                self.session_label,
            )
        )

        self.session_status_label = DashboardFitLabel(
            idle_text,
            max_lines=2,
        )
        self.session_status_label.setObjectName("displayValue")
        session_layout.addWidget(
            _session_field_column(
                tr("dashboard.label.status"),
                self.session_status_label,
            )
        )

        meta_row = QHBoxLayout()
        meta_row.setSpacing(16)

        self.crew_info_label = AnimatedDashboardValue("0")
        self.crew_info_label.setObjectName("displayValue")
        self.refinery_info_label = AnimatedDashboardValue("0")
        self.refinery_info_label.setObjectName("displayValue")

        meta_row.addWidget(
            _session_field_column(
                tr("dashboard.label.crew"),
                self.crew_info_label,
            ),
            1,
        )
        meta_row.addWidget(
            _session_field_column(
                tr("dashboard.label.refinery"),
                self.refinery_info_label,
            ),
            1,
        )
        session_layout.addLayout(meta_row)

        materials_title = QLabel(tr("dashboard.session.materials"))
        materials_title.setObjectName("cardTitle")
        session_layout.addWidget(materials_title)

        materials_grid_host = QWidget()
        materials_grid_host.setAutoFillBackground(False)
        materials_grid = QGridLayout(materials_grid_host)
        materials_grid.setContentsMargins(0, 0, 0, 0)
        materials_grid.setHorizontalSpacing(16)
        materials_grid.setVerticalSpacing(8)

        self.rmc_info_label = AnimatedDashboardValue("0 SCU")
        self.rmc_info_label.setObjectName("displayValue")
        self.cm_info_label = AnimatedDashboardValue("0 SCU")
        self.cm_info_label.setObjectName("displayValue")
        self.session_rubble_info_label = AnimatedDashboardValue("0 SCU")
        self.session_rubble_info_label.setObjectName("displayValue")
        self.session_scraps_info_label = AnimatedDashboardValue("0 SCU")
        self.session_scraps_info_label.setObjectName("displayValue")
        self.session_salvage_info_label = AnimatedDashboardValue("0 SCU")
        self.session_salvage_info_label.setObjectName("displayValue")

        material_fields = [
            (material_label("RMC"), self.rmc_info_label),
            (material_label("CM"), self.cm_info_label),
            (material_label("CM_RUBBLE"), self.session_rubble_info_label),
            (material_label("CM_SCRAPS"), self.session_scraps_info_label),
            (material_label("CM_SALVAGE"), self.session_salvage_info_label),
        ]
        for index, (title, value) in enumerate(material_fields):
            row = index // 2
            col = index % 2
            materials_grid.addWidget(
                _session_field_column(title, value),
                row,
                col,
            )
        materials_grid.setColumnStretch(0, 1)
        materials_grid.setColumnStretch(1, 1)
        session_layout.addWidget(materials_grid_host)

        self.refinery_stats_panel = QFrame()
        self.refinery_stats_panel.setObjectName("dashboardSessionPanel")
        refinery_stats_layout = QVBoxLayout(self.refinery_stats_panel)
        refinery_stats_layout.setContentsMargins(16, 14, 16, 14)
        refinery_stats_layout.setSpacing(8)
        refinery_stats_layout.addWidget(
            subsection_title(tr("dashboard.refinery_stats.title"))
        )
        refinery_stats_layout.addLayout(hud_divider())
        self.refinery_stats_label = QLabel(
            tr("dashboard.refinery_stats.empty_short")
        )
        self.refinery_stats_label.setObjectName("statValue")
        self.refinery_stats_label.setWordWrap(True)
        refinery_stats_layout.addWidget(self.refinery_stats_label)

        details_row.addWidget(self.session_panel, 1)
        details_row.addWidget(self.refinery_stats_panel, 1)
        root.addLayout(details_row)

        summary_card = QFrame()
        summary_card.setObjectName("dashboardCard")
        summary_layout = QHBoxLayout(summary_card)
        summary_layout.setContentsMargins(16, 14, 16, 14)
        summary_layout.setSpacing(20)

        for column in (
            _summary_column(
                tr("dashboard.widget.total_sales"),
                self.summary_revenue,
            ),
            _summary_column(
                tr("dashboard.widget.total_profit"),
                self.summary_profit,
            ),
            _summary_column(
                tr("dashboard.widget.refinery_jobs"),
                self.summary_refinery,
            ),
            _summary_column(
                tr("dashboard.widget.active_sessions"),
                self.summary_active,
            ),
            _summary_column(
                tr("dashboard.widget.total_sessions"),
                self.summary_total_sessions,
            ),
            _summary_column(
                tr("dashboard.widget.sold_sessions"),
                self.summary_sold,
            ),
            _summary_column(
                tr("dashboard.widget.ready_sessions"),
                self.summary_storage,
            ),
            _summary_column(
                tr("dashboard.operations.summary.idle"),
                self.summary_idle,
            ),
        ):
            summary_layout.addLayout(column)

        summary_layout.addStretch()
        root.addWidget(summary_card)

    def refresh(self):
        snapshot = self._repo.build_snapshot()
        self._row_cache = snapshot.get("rows") or []

        next_action = snapshot.get("next_action") or {}
        message = next_action.get("message") or tr(
            "dashboard.next_action.all_clear"
        )
        self.next_action_title.setText(message)
        self.next_action_host.setVisible(True)

        has_rows = len(self._row_cache) > 0
        self.table.setVisible(has_rows)
        self.empty_panel.setVisible(not has_rows)
        self.table.setRowCount(len(self._row_cache))

        for row_index, row in enumerate(self._row_cache):
            self.table.setItem(
                row_index,
                0,
                QTableWidgetItem(row.get("status_label") or "—"),
            )
            self.table.setItem(
                row_index,
                1,
                QTableWidgetItem(row.get("material_label") or "—"),
            )

            if row.get("quantity_display"):
                quantity_text = row["quantity_display"]
            else:
                quantity_text = (
                    format_number(row.get("quantity_scu") or 0, 0)
                    + " SCU"
                )

            qty_item = QTableWidgetItem(quantity_text)
            qty_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row_index, 2, qty_item)

            self.table.setItem(
                row_index,
                3,
                QTableWidgetItem(row.get("context_label") or "—"),
            )
            self.table.setItem(
                row_index,
                4,
                QTableWidgetItem(row.get("detail_label") or "—"),
            )

        if has_rows:
            from ui.table_utils import finalize_table_columns

            finalize_table_columns(
                self.table,
                stretch_column=3,
            )

        materials = snapshot.get("materials") or {}
        self._animate_scu(self.rmc_value, materials.get("RMC"))
        self._animate_scu(self.cm_value, materials.get("CM"))
        self._animate_scu(self.rubble_value, materials.get("CM_RUBBLE"))
        self._animate_scu(self.scraps_value, materials.get("CM_SCRAPS"))
        self._animate_scu(self.salvage_value, materials.get("CM_SALVAGE"))

        session = snapshot.get("session") or {}
        self._refresh_session_panel(session)
        self._refresh_refinery_stats(snapshot.get("refinery_stats") or {})

        summary = snapshot.get("summary") or {}
        self.summary_revenue.animate_to(
            summary.get("total_sales") or 0,
            suffix=" aUEC",
            decimals=0,
            duration=1200,
        )
        self.summary_profit.animate_to(
            summary.get("total_profit") or 0,
            suffix=" aUEC",
            decimals=0,
            duration=1200,
        )
        self.summary_refinery.animate_to(
            summary.get("open_refinery_jobs") or 0,
            duration=800,
        )
        self.summary_active.animate_to(
            summary.get("active_sessions") or 0,
            duration=800,
        )
        self.summary_total_sessions.animate_to(
            summary.get("total_sessions") or 0,
            duration=800,
        )
        self.summary_sold.animate_to(
            summary.get("sold_sessions") or 0,
            duration=800,
        )
        self.summary_storage.animate_to(
            summary.get("sellable_scu") or 0,
            suffix=" SCU",
            decimals=0,
            duration=1200,
        )
        self.summary_idle.animate_to(
            summary.get("idle_warnings") or 0,
            duration=800,
        )

    def _animate_scu(self, widget: AnimatedDashboardValue, value):
        widget.animate_to(
            value or 0,
            suffix=" SCU",
            decimals=0,
            duration=1200,
        )

    def _refresh_session_panel(self, session: dict):
        active = bool(session.get("active"))
        name = session.get("name") or tr("dashboard.session.none")
        self.session_label.setText(name)
        self.session_label.setObjectName(
            "displayValue" if active else "mutedLabel"
        )
        self.session_label.style().unpolish(self.session_label)
        self.session_label.style().polish(self.session_label)

        status_code = session.get("status") or "IDLE"
        status_text = session.get("status_label") or status_label(
            status_code
        )
        self._update_status_display(status_code, status_text)

        crew_count = session.get("crew_count") or 0
        self.crew_kpi_value.animate_to(crew_count, duration=800)
        self.crew_info_label.animate_to(crew_count, duration=800)

        refinery_count = session.get("refinery_jobs") or 0
        self.refinery_info_label.animate_to(refinery_count, duration=800)

        session_materials = session.get("materials") or {}
        self._animate_scu(
            self.rmc_info_label,
            session_materials.get("RMC"),
        )
        self._animate_scu(
            self.cm_info_label,
            session_materials.get("CM"),
        )
        self._animate_scu(
            self.session_rubble_info_label,
            session_materials.get("CM_RUBBLE"),
        )
        self._animate_scu(
            self.session_scraps_info_label,
            session_materials.get("CM_SCRAPS"),
        )
        self._animate_scu(
            self.session_salvage_info_label,
            session_materials.get("CM_SALVAGE"),
        )

    def _update_status_display(self, status_code: str, status_text: str):
        previous = self._last_session_status

        self.status_kpi_value.setText(status_text)
        self.session_status_label.setText(status_text)

        if (
            previous is not None
            and previous != status_code
            and self.status_card is not None
        ):
            DashboardStatusAnimator.pulse(
                self.status_card,
                self.status_kpi_value,
                status_code,
                status_text,
            )

        self._last_session_status = status_code

    def _refresh_refinery_stats(self, stats: dict):
        if not stats.get("job_count"):
            self.refinery_stats_label.setText(
                tr("dashboard.refinery_stats.empty")
            )
            return

        avg = stats.get("avg_efficiency_percent")
        avg_text = (
            f"{format_number(avg, 1)} %"
            if avg is not None
            else "—"
        )

        lines = [
            tr(
                "dashboard.refinery_stats.jobs",
                count=stats["job_count"],
            ),
            tr(
                "dashboard.refinery_stats.io",
                input_scu=format_number(stats["total_input"]),
                output_scu=format_number(stats["total_output"]),
            ),
            tr(
                "dashboard.refinery_stats.efficiency",
                value=avg_text,
            ),
        ]

        if stats.get("by_material"):
            lines.append("")
            lines.append(tr("dashboard.refinery_stats.by_material"))
            for row in stats["by_material"]:
                eff = row.get("efficiency_percent")
                eff_label = (
                    f"{format_number(eff, 1)} %"
                    if eff is not None
                    else "—"
                )
                lines.append(
                    tr(
                        "dashboard.refinery_stats.detail_line",
                        label=material_label(row["material_code"]),
                        efficiency=eff_label,
                        count=row["job_count"],
                    )
                )

        if stats.get("by_method"):
            lines.append("")
            lines.append(tr("dashboard.refinery_stats.by_method"))
            for row in stats["by_method"]:
                eff = row.get("efficiency_percent")
                eff_label = (
                    f"{format_number(eff, 1)} %"
                    if eff is not None
                    else "—"
                )
                lines.append(
                    tr(
                        "dashboard.refinery_stats.detail_line",
                        label=row["refinery_method"],
                        efficiency=eff_label,
                        count=row["job_count"],
                    )
                )

        self.refinery_stats_label.setText("\n".join(lines))
