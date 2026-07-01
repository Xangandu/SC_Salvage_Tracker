"""Kontext-Ansichten mit echten Tracker-Daten."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.dates import format_month_year
from config.i18n import tr, format_number, format_scu, status_label
from config.materials import (
    RAW_CM_MATERIAL_CODES,
    REFINED_SELLABLE_CODES,
    material_label,
)
from ui.context_dashboard.components import (
    ProgressBarRow,
    SessionRefineryProcessRow,
    TimelineRow,
    _hud_divider_widget,
    animate_currency,
    animate_int,
    animate_scu,
    animated_scu,
    dashboard_card,
    field_column,
    kpi_card,
    build_session_materials_grid,
)
from ui.dashboard_fit_label import DashboardFitLabel
from ui.dashboard_number_animation import AnimatedDashboardValue
from ui.page_layout import empty_info_panel, subsection_title
from ui.table_utils import configure_mobiglas_table, finalize_table_columns


class _BaseContextView(QScrollArea):

    context_key = "overview"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboardScroll")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.viewport().setAutoFillBackground(False)

        host = QWidget()
        host.setObjectName("dashboardOperationsPanel")
        host.setAutoFillBackground(False)
        self._layout = QVBoxLayout(host)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(14)
        self.setWidget(host)

    def apply_data(self, data: dict):
        raise NotImplementedError


class OverviewView(_BaseContextView):
    context_key = "overview"

    def __init__(self, parent=None):
        super().__init__(parent)

        self.readiness_status = DashboardFitLabel("—", max_lines=4)
        self.readiness_status.setObjectName("cardValue")
        self._layout.addWidget(
            kpi_card(
                tr("dashboard.widget.status"),
                self.readiness_status,
            )
        )

        card, card_layout = dashboard_card()
        card_layout.addWidget(subsection_title(tr("dashboard.operations.title")))

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            tr("dashboard.operations.col.status"),
            tr("dashboard.operations.col.material"),
            tr("dashboard.operations.col.quantity"),
            tr("dashboard.operations.col.context"),
        ])
        configure_mobiglas_table(self.table, "dataTable", selectable=False)
        self.table.setMinimumHeight(180)
        card_layout.addWidget(self.table)

        self.empty_panel = empty_info_panel(
            tr("dashboard.operations.empty"),
            "assets/images/icons/info.svg",
        )
        card_layout.addWidget(self.empty_panel)
        self._layout.addWidget(card)

        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(10)
        self.kpi_revenue = AnimatedDashboardValue("0 aUEC")
        self.kpi_profit = AnimatedDashboardValue("0 aUEC")
        self.kpi_profit.setObjectName("profitLabel")
        self.kpi_jobs = AnimatedDashboardValue("0")
        self.kpi_storage = animated_scu()
        for title, widget in (
            (tr("dashboard.widget.total_sales"), self.kpi_revenue),
            (tr("dashboard.widget.total_profit"), self.kpi_profit),
            (tr("dashboard.widget.refinery_jobs"), self.kpi_jobs),
            (tr("dashboard.widget.ready_sessions"), self.kpi_storage),
        ):
            kpi_row.addWidget(kpi_card(title, widget))
        self._layout.addLayout(kpi_row)
        self._layout.addStretch()

    def apply_data(self, data: dict):
        self.readiness_status.setText(
            data.get("readiness_summary")
            or tr("dashboard.readiness.none")
        )

        rows = data.get("actions") or []
        has_rows = len(rows) > 0
        self.table.setVisible(has_rows)
        self.empty_panel.setVisible(not has_rows)
        self.table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            for col, text in enumerate(row):
                item = QTableWidgetItem(str(text))
                if col == 2:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight
                        | Qt.AlignmentFlag.AlignVCenter
                    )
                self.table.setItem(index, col, item)
        if has_rows:
            finalize_table_columns(self.table, stretch_column=3)

        summary = data.get("summary") or {}
        animate_currency(self.kpi_revenue, summary.get("total_sales"))
        animate_currency(self.kpi_profit, summary.get("total_profit"))
        animate_int(self.kpi_jobs, summary.get("open_refinery_jobs"))
        animate_scu(self.kpi_storage, summary.get("sellable_scu"))


class SessionView(_BaseContextView):
    context_key = "session"

    def __init__(self, parent=None):
        super().__init__(parent)
        top = QHBoxLayout()
        top.setSpacing(10)

        self.status_kpi_value = DashboardFitLabel(status_label("IDLE"), max_lines=4)
        self.status_kpi_value.setObjectName("cardValue")
        self.crew_value = AnimatedDashboardValue("0")
        self.session_scu = animated_scu()

        self.status_card = kpi_card(
            tr("dashboard.widget.status"),
            self.status_kpi_value,
        )
        top.addWidget(self.status_card)
        top.addWidget(
            kpi_card(tr("dashboard.widget.session_crew"), self.crew_value)
        )
        top.addWidget(kpi_card(tr("dashboard.context.session_scu"), self.session_scu))
        self._layout.addLayout(top)

        mat_card, mat_layout = dashboard_card()
        mat_layout.addWidget(subsection_title(tr("dashboard.session.materials")))
        divider_host = _hud_divider_widget()
        mat_layout.addWidget(divider_host)

        self.mat_widgets = {}
        raw_codes = [
            code for code in RAW_CM_MATERIAL_CODES if code != "CM"
        ]
        mat_layout.addLayout(
            build_session_materials_grid(
                REFINED_SELLABLE_CODES,
                raw_codes,
                self.mat_widgets,
                sellable_heading=tr("dashboard.context.materials_sellable"),
                raw_heading=tr("dashboard.context.materials_raw"),
            )
        )
        self._layout.addWidget(mat_card)

        mission_card, mission_layout = dashboard_card()
        mission_layout.addWidget(
            subsection_title(tr("session.section.missions"))
        )
        self.mission_costs_total_label = QLabel(
            tr(
                "dashboard.context.mission_costs_subtotal",
                mission_total=format_number(0),
            )
        )
        self.mission_costs_total_label.setObjectName("displayValue")
        self.mission_costs_total_label.setWordWrap(True)
        mission_layout.addWidget(self.mission_costs_total_label)
        self.mission_costs_host = QWidget()
        self.mission_costs_layout = QVBoxLayout(self.mission_costs_host)
        self.mission_costs_layout.setContentsMargins(0, 0, 0, 0)
        self.mission_costs_layout.setSpacing(4)
        mission_layout.addWidget(self.mission_costs_host)
        self._layout.addWidget(mission_card)

        refinery_card, refinery_layout = dashboard_card()
        refinery_layout.addWidget(
            subsection_title(tr("session.section.refinery_costs"))
        )
        self.refinery_costs_total_label = QLabel(
            tr(
                "dashboard.context.refinery_costs_subtotal",
                refinery_total=format_number(0),
            )
        )
        self.refinery_costs_total_label.setObjectName("displayValue")
        self.refinery_costs_total_label.setWordWrap(True)
        refinery_layout.addWidget(self.refinery_costs_total_label)
        self.refinery_costs_host = QWidget()
        self.refinery_costs_layout = QVBoxLayout(self.refinery_costs_host)
        self.refinery_costs_layout.setContentsMargins(0, 0, 0, 0)
        self.refinery_costs_layout.setSpacing(4)
        refinery_layout.addWidget(self.refinery_costs_host)
        self._layout.addWidget(refinery_card)

        costs_total_card, costs_total_layout = dashboard_card()
        self.session_costs_total_label = QLabel(
            tr(
                "dashboard.context.session_costs_total",
                session_total=format_number(0),
            )
        )
        self.session_costs_total_label.setObjectName("displayValue")
        self.session_costs_total_label.setWordWrap(True)
        costs_total_layout.addWidget(self.session_costs_total_label)
        self._layout.addWidget(costs_total_card)

        loc_card, loc_layout = dashboard_card()
        loc_layout.addWidget(subsection_title(tr("dashboard.context.locations")))
        self.locations_host = QWidget()
        self.locations_layout = QVBoxLayout(self.locations_host)
        self.locations_layout.setContentsMargins(0, 0, 0, 0)
        self.locations_layout.setSpacing(10)
        loc_layout.addWidget(self.locations_host)
        self._layout.addWidget(loc_card)

        proc_card, proc_layout = dashboard_card()
        proc_layout.addWidget(subsection_title(tr("dashboard.context.processes")))
        self.process_host = QWidget()
        self.process_layout = QVBoxLayout(self.process_host)
        self.process_layout.setContentsMargins(0, 0, 0, 0)
        self.process_layout.setSpacing(8)
        proc_layout.addWidget(self.process_host)
        self._layout.addWidget(proc_card)

        detail_card, detail_layout = dashboard_card()
        detail_layout.addWidget(subsection_title(tr("dashboard.session.active")))
        self.session_label = QLabel(tr("dashboard.session.none"))
        self.session_label.setObjectName("displayValue")
        self.session_label.setWordWrap(True)
        detail_layout.addWidget(
            field_column(tr("dashboard.label.ship"), self.session_label)
        )
        self.session_status_label = QLabel(status_label("IDLE"))
        self.session_status_label.setObjectName("dashboardFieldValue")
        self.session_status_label.setWordWrap(True)
        self.session_status_label.setMinimumHeight(36)
        detail_layout.addWidget(
            field_column(tr("dashboard.label.status"), self.session_status_label)
        )
        self._layout.addWidget(detail_card)
        self._layout.addStretch()

    def apply_data(self, data: dict):
        active = bool(data.get("active"))
        name = (
            (data.get("name") or tr("dashboard.session.none"))
            if active
            else tr("dashboard.session.none")
        )
        self.session_label.setText(name)
        self.session_label.setObjectName(
            "displayValue" if active else "mutedLabel"
        )
        self.session_label.style().unpolish(self.session_label)
        self.session_label.style().polish(self.session_label)

        readiness_text = (
            data.get("readiness_summary")
            or tr("dashboard.readiness.none")
        )
        self.status_kpi_value.setText(readiness_text)

        workflow_status = (
            data.get("status_label") or status_label("IDLE")
            if active
            else status_label("IDLE")
        )
        self.session_status_label.setText(workflow_status)

        animate_int(self.crew_value, data.get("crew_count"))
        animate_scu(self.session_scu, data.get("session_scu_total"))

        materials = data.get("materials") or {}
        for code, widget in self.mat_widgets.items():
            animate_scu(widget, materials.get(code))

        mission_total = data.get("mission_costs_total") or 0
        session_total = data.get("session_costs_total") or 0
        self.mission_costs_total_label.setText(
            tr(
                "dashboard.context.mission_costs_subtotal",
                mission_total=format_number(mission_total),
            )
        )
        self.session_costs_total_label.setText(
            tr(
                "dashboard.context.session_costs_total",
                session_total=format_number(session_total),
            )
        )

        while self.mission_costs_layout.count():
            item = self.mission_costs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        mission_costs = data.get("mission_costs") or []
        for title, detail in mission_costs:
            self.mission_costs_layout.addWidget(
                TimelineRow("◆", title, detail, compact=True)
            )
        if not mission_costs:
            empty = QLabel(tr("session.mission.none"))
            empty.setObjectName("mutedLabel")
            empty.setWordWrap(True)
            self.mission_costs_layout.addWidget(empty)

        refinery_total = data.get("refinery_costs_total") or 0
        self.refinery_costs_total_label.setText(
            tr(
                "dashboard.context.refinery_costs_subtotal",
                refinery_total=format_number(refinery_total),
            )
        )

        while self.refinery_costs_layout.count():
            item = self.refinery_costs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        refinery_costs = data.get("refinery_costs") or []
        for title, detail in refinery_costs:
            self.refinery_costs_layout.addWidget(
                TimelineRow("◆", title, detail, compact=True)
            )
        if not refinery_costs:
            empty = QLabel(tr("session.refinery.none"))
            empty.setObjectName("mutedLabel")
            empty.setWordWrap(True)
            self.refinery_costs_layout.addWidget(empty)

        while self.locations_layout.count():
            item = self.locations_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for label, detail, pct in data.get("locations") or []:
            self.locations_layout.addWidget(
                ProgressBarRow(label, detail, pct)
            )
        if not data.get("locations"):
            empty = QLabel(tr("dashboard.context.no_locations"))
            empty.setObjectName("mutedLabel")
            empty.setWordWrap(True)
            self.locations_layout.addWidget(empty)

        while self.process_layout.count():
            item = self.process_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        processes = data.get("processes") or []
        for proc in processes:
            self.process_layout.addWidget(
                TimelineRow(
                    "◆",
                    proc.get("title") or "—",
                    proc.get("detail") or "",
                    compact=True,
                )
            )
        if not processes:
            empty = QLabel(tr("dashboard.context.no_processes"))
            empty.setObjectName("mutedLabel")
            empty.setWordWrap(True)
            self.process_layout.addWidget(empty)


class RefineryView(_BaseContextView):
    context_key = "refinery"

    def __init__(self, parent=None):
        super().__init__(parent)
        top = QHBoxLayout()
        top.setSpacing(10)
        self.jobs_open = AnimatedDashboardValue("0")
        self.jobs_ready = AnimatedDashboardValue("0")
        self.efficiency = AnimatedDashboardValue("0 %")
        self.io_in = animated_scu()
        self.io_out = animated_scu()
        for title, widget in (
            (tr("dashboard.context.open"), self.jobs_open),
            (tr("dashboard.action.refinery_ready"), self.jobs_ready),
            (tr("dashboard.context.avg_efficiency"), self.efficiency),
            ("Input", self.io_in),
            ("Output", self.io_out),
        ):
            top.addWidget(kpi_card(title, widget))
        self._layout.addLayout(top)

        input_card, input_layout = dashboard_card()
        input_layout.addWidget(
            subsection_title(tr("refinery.section.batches"))
        )
        self.input_table = QTableWidget()
        self.input_table.setColumnCount(3)
        self.input_table.setHorizontalHeaderLabels([
            tr("dashboard.operations.col.material"),
            tr("dashboard.operations.col.context"),
            tr("dashboard.operations.col.quantity"),
        ])
        configure_mobiglas_table(
            self.input_table,
            "dataTable",
            selectable=False,
        )
        self.input_table.setMinimumHeight(120)
        input_layout.addWidget(self.input_table)
        self._layout.addWidget(input_card)

        jobs_card, jobs_layout = dashboard_card()
        jobs_layout.addWidget(subsection_title(tr("dashboard.context.active_jobs")))
        self.jobs_host = QWidget()
        self.jobs_layout = QVBoxLayout(self.jobs_host)
        self.jobs_layout.setContentsMargins(0, 0, 0, 0)
        jobs_layout.addWidget(self.jobs_host)
        self._layout.addWidget(jobs_card)

        self._job_rows: dict[int, SessionRefineryProcessRow] = {}
        self._jobs_timer = QTimer(self)
        self._jobs_timer.setInterval(1000)
        self._jobs_timer.timeout.connect(self._tick_job_rows)
        self._jobs_timer.start()

        mat_card, mat_layout = dashboard_card()
        mat_layout.addWidget(subsection_title(tr("dashboard.refinery_stats.by_material")))
        self.mat_host = QWidget()
        self.mat_layout = QVBoxLayout(self.mat_host)
        self.mat_layout.setContentsMargins(0, 0, 0, 0)
        mat_layout.addWidget(self.mat_host)
        self._layout.addWidget(mat_card)
        self._layout.addStretch()

    def apply_data(self, data: dict):
        animate_int(self.jobs_open, data.get("open_jobs"))
        animate_int(self.jobs_ready, data.get("ready_jobs"))
        avg = data.get("avg_efficiency") or 0
        self.efficiency.animate_to(avg, suffix=" %", decimals=1, duration=1000)
        animate_scu(self.io_in, data.get("total_input"))
        animate_scu(self.io_out, data.get("total_output"))

        input_rows = data.get("input_items") or []
        self.input_table.setRowCount(len(input_rows))
        for row_index, (material, location, qty) in enumerate(input_rows):
            self.input_table.setItem(
                row_index,
                0,
                QTableWidgetItem(material),
            )
            self.input_table.setItem(
                row_index,
                1,
                QTableWidgetItem(location),
            )
            qty_item = QTableWidgetItem(format_scu(qty))
            qty_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
            )
            self.input_table.setItem(row_index, 2, qty_item)
        if input_rows:
            finalize_table_columns(
                self.input_table,
                stretch_column=1,
            )

        while self.jobs_layout.count():
            item = self.jobs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._job_rows.clear()

        for job in data.get("jobs") or []:
            title = (
                f"#{job.get('id')} · {job.get('status_label')} · "
                f"{job.get('station')}"
            )
            detail = (
                f"{job.get('material')} · "
                f"{format_scu(job.get('input_scu', 0))}"
            )
            full_job = job.get("job") or job
            if full_job.get("start_time") and full_job.get("end_time"):
                row = SessionRefineryProcessRow(
                    full_job,
                    title,
                    detail,
                )
                job_id = full_job.get("id")
                if job_id is not None:
                    self._job_rows[job_id] = row
                self.jobs_layout.addWidget(row)
            else:
                self.jobs_layout.addWidget(
                    TimelineRow("◆", title, detail, compact=True)
                )
        if self._job_rows:
            self._tick_job_rows()

        while self.mat_layout.count():
            item = self.mat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for code, eff, count in data.get("by_material") or []:
            self.mat_layout.addWidget(
                ProgressBarRow(
                    material_label(code),
                    tr("dashboard.refinery_stats.jobs", count=count),
                    int(eff),
                )
            )


    def _tick_job_rows(self) -> None:
        for row in self._job_rows.values():
            row.tick()


class StorageView(_BaseContextView):
    context_key = "storage"

    def __init__(self, parent=None):
        super().__init__(parent)
        top = QHBoxLayout()
        top.setSpacing(10)
        self.total_scu = animated_scu()
        self.idle_warn = AnimatedDashboardValue("0")
        self.item_count = AnimatedDashboardValue("0")
        top.addWidget(kpi_card(tr("dashboard.context.total"), self.total_scu))
        top.addWidget(kpi_card(tr("dashboard.operations.summary.idle"), self.idle_warn))
        top.addWidget(kpi_card(tr("dashboard.context.inventory"), self.item_count))
        self._layout.addLayout(top)

        self.readiness_status = DashboardFitLabel("—", max_lines=4)
        self.readiness_status.setObjectName("cardValue")
        self._layout.addWidget(
            kpi_card(
                tr("dashboard.widget.status"),
                self.readiness_status,
            )
        )

        inv_card, inv_layout = dashboard_card()
        inv_layout.addWidget(subsection_title(tr("dashboard.context.inventory")))
        self.inv_host = QWidget()
        self.inv_layout = QVBoxLayout(self.inv_host)
        self.inv_layout.setContentsMargins(0, 0, 0, 0)
        self.inv_layout.setSpacing(4)
        inv_layout.addWidget(self.inv_host)
        self._layout.addWidget(inv_card)

        evt_card, evt_layout = dashboard_card()
        evt_layout.addWidget(subsection_title(tr("dashboard.context.recent_moves")))
        self.evt_host = QWidget()
        self.evt_layout = QVBoxLayout(self.evt_host)
        self.evt_layout.setContentsMargins(0, 0, 0, 0)
        self.evt_layout.setSpacing(4)
        evt_layout.addWidget(self.evt_host)
        self._layout.addWidget(evt_card)
        self._layout.addStretch()

    def apply_data(self, data: dict):
        animate_scu(self.total_scu, data.get("total_scu"))
        animate_int(self.idle_warn, data.get("idle_warnings"))
        inventory = data.get("inventory") or []
        animate_int(self.item_count, len(inventory))
        self.readiness_status.setText(
            data.get("readiness_summary")
            or tr("dashboard.readiness.none")
        )

        while self.inv_layout.count():
            item = self.inv_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for when, title, detail in inventory:
            self.inv_layout.addWidget(TimelineRow(when, title, detail))
        if not inventory:
            empty = QLabel(tr("dashboard.context.no_inventory"))
            empty.setObjectName("mutedLabel")
            empty.setWordWrap(True)
            self.inv_layout.addWidget(empty)

        while self.evt_layout.count():
            item = self.evt_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for when, title, detail in data.get("recent_events") or []:
            self.evt_layout.addWidget(TimelineRow(when, title, detail))


class SalesView(_BaseContextView):
    context_key = "sales"

    def __init__(self, parent=None):
        super().__init__(parent)
        top = QHBoxLayout()
        top.setSpacing(10)
        self.ready_scu = animated_scu()
        self.pending = AnimatedDashboardValue("0")
        self.pending_amount = AnimatedDashboardValue("0 aUEC")
        top.addWidget(kpi_card(tr("dashboard.action.sale_ready"), self.ready_scu))
        top.addWidget(kpi_card(tr("dashboard.context.pending"), self.pending))
        top.addWidget(kpi_card(tr("dashboard.context.pending_amount"), self.pending_amount))
        self._layout.addLayout(top)

        self.readiness_status = DashboardFitLabel("—", max_lines=4)
        self.readiness_status.setObjectName("cardValue")
        self._layout.addWidget(
            kpi_card(
                tr("dashboard.widget.status"),
                self.readiness_status,
            )
        )

        card, card_layout = dashboard_card()
        card_layout.addWidget(subsection_title(tr("dashboard.context.sale_items")))
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            tr("dashboard.operations.col.material"),
            tr("dashboard.operations.col.context"),
            tr("dashboard.operations.col.quantity"),
        ])
        configure_mobiglas_table(self.table, "dataTable", selectable=False)
        self.table.setMinimumHeight(220)
        card_layout.addWidget(self.table)
        self._layout.addWidget(card)
        self._layout.addStretch()

    def apply_data(self, data: dict):
        animate_scu(self.ready_scu, data.get("ready_total_scu"))
        animate_int(self.pending, data.get("pending_sales"))
        animate_currency(self.pending_amount, data.get("pending_amount"))
        self.readiness_status.setText(
            data.get("readiness_summary")
            or tr("dashboard.readiness.none")
        )

        rows = data.get("items") or []
        self.table.setRowCount(len(rows))
        for r, (mat, loc, qty, _val) in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(mat))
            self.table.setItem(r, 1, QTableWidgetItem(loc))
            qty_item = QTableWidgetItem(format_scu(qty))
            qty_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(r, 2, qty_item)
        finalize_table_columns(self.table, stretch_column=1)


class PayoutView(_BaseContextView):
    context_key = "payout"

    def __init__(self, parent=None):
        super().__init__(parent)
        top = QHBoxLayout()
        top.setSpacing(10)
        self.open_count = AnimatedDashboardValue("0")
        self.open_total = AnimatedDashboardValue("0 aUEC")
        top.addWidget(kpi_card(tr("dashboard.context.open_payouts"), self.open_count))
        top.addWidget(kpi_card(tr("dashboard.context.open_total"), self.open_total))
        self._layout.addLayout(top)

        card, card_layout = dashboard_card()
        card_layout.addWidget(subsection_title(tr("dashboard.action.payout_pending")))
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Session",
            tr("dashboard.operations.col.material"),
            tr("dashboard.operations.col.quantity"),
            tr("dashboard.widget.total_sales"),
            tr("sales.history.location"),
        ])
        configure_mobiglas_table(self.table, "dataTable", selectable=False)
        self.table.setMinimumHeight(220)
        card_layout.addWidget(self.table)
        self._layout.addWidget(card)
        self._layout.addStretch()

    def apply_data(self, data: dict):
        animate_int(self.open_count, data.get("open_count"))
        animate_currency(self.open_total, data.get("open_total"))

        rows = data.get("items") or []
        self.table.setRowCount(len(rows))
        for r, (session, mat, qty, amount, loc) in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(session))
            self.table.setItem(r, 1, QTableWidgetItem(mat))
            qty_item = QTableWidgetItem(format_scu(qty))
            qty_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(r, 2, qty_item)
            amt_item = QTableWidgetItem(
                f"{format_number(amount, 0)} aUEC"
            )
            amt_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(r, 3, amt_item)
            self.table.setItem(r, 4, QTableWidgetItem(loc))
        finalize_table_columns(self.table, stretch_column=0)


class HistoryView(_BaseContextView):
    context_key = "history"

    def __init__(self, parent=None):
        super().__init__(parent)
        top = QHBoxLayout()
        top.setSpacing(10)
        self.sold = AnimatedDashboardValue("0")
        self.total = AnimatedDashboardValue("0")
        self.revenue = AnimatedDashboardValue("0 aUEC")
        top.addWidget(kpi_card(tr("dashboard.widget.sold_sessions"), self.sold))
        top.addWidget(kpi_card(tr("dashboard.widget.total_sessions"), self.total))
        top.addWidget(kpi_card(tr("dashboard.widget.total_sales"), self.revenue))
        self._layout.addLayout(top)

        rev_card, rev_layout = dashboard_card()
        rev_layout.addWidget(subsection_title(tr("dashboard.context.revenue_trend")))
        self.revenue_trend_hint = QLabel(tr("dashboard.context.revenue_trend_hint"))
        self.revenue_trend_hint.setObjectName("mutedLabel")
        self.revenue_trend_hint.setWordWrap(True)
        rev_layout.addWidget(self.revenue_trend_hint)
        self.rev_host = QWidget()
        self.rev_layout = QVBoxLayout(self.rev_host)
        self.rev_layout.setContentsMargins(0, 0, 0, 0)
        rev_layout.addWidget(self.rev_host)
        self._layout.addWidget(rev_card)

        evt_card, evt_layout = dashboard_card()
        evt_layout.addWidget(subsection_title(tr("dashboard.context.recent_events")))
        self.evt_host = QWidget()
        self.evt_layout = QVBoxLayout(self.evt_host)
        self.evt_layout.setContentsMargins(0, 0, 0, 0)
        self.evt_layout.setSpacing(4)
        evt_layout.addWidget(self.evt_host)
        self._layout.addWidget(evt_card)
        self._layout.addStretch()

    def apply_data(self, data: dict):
        animate_int(self.sold, data.get("sold_sessions"))
        animate_int(self.total, data.get("total_sessions"))
        animate_currency(self.revenue, data.get("total_revenue"))

        while self.rev_layout.count():
            item = self.rev_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        monthly = data.get("monthly_revenue") or []
        if not monthly:
            empty = QLabel(tr("dashboard.context.revenue_trend_empty"))
            empty.setObjectName("mutedLabel")
            empty.setWordWrap(True)
            self.rev_layout.addWidget(empty)
        else:
            max_val = max((v for _, v in monthly), default=0)
            multi_month = len(monthly) > 1
            for month_key, value in monthly:
                month_label = format_month_year(month_key)
                amount_text = f"{format_number(value, 0)} aUEC"
                if multi_month and max_val:
                    pct = int(round(100 * value / max_val))
                    badge = (
                        tr("dashboard.context.revenue_peak_month")
                        if pct >= 100
                        else tr(
                            "dashboard.context.revenue_vs_peak",
                            pct=pct,
                        )
                    )
                else:
                    pct = 100 if value else 0
                    badge = None
                self.rev_layout.addWidget(
                    ProgressBarRow(
                        month_label,
                        amount_text,
                        pct,
                        badge_text=badge,
                    )
                )

        while self.evt_layout.count():
            item = self.evt_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for when, title, detail in data.get("recent") or []:
            self.evt_layout.addWidget(TimelineRow(when, title, detail))


CONTEXT_VIEWS = {
    "overview": OverviewView,
    "session": SessionView,
    "refinery": RefineryView,
    "storage": StorageView,
    "sales": SalesView,
    "payout": PayoutView,
    "history": HistoryView,
}
