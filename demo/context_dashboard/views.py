"""Kontext-spezifische Dashboard-Ansichten (Demo)."""

from PySide6.QtCore import Qt
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

from config.materials import material_label
from demo.context_dashboard import mock_data as data
from demo.context_dashboard.components import (
    ProgressBarRow,
    TimelineRow,
    animate_currency,
    animate_int,
    animate_scu,
    animated_scu,
    dashboard_card,
    kpi_card,
)
from ui.dashboard_number_animation import AnimatedDashboardValue
from ui.page_layout import section_accent, subsection_title
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

    def refresh(self):
        raise NotImplementedError


class OverviewView(_BaseContextView):
    context_key = "overview"

    def __init__(self, parent=None):
        super().__init__(parent)

        card, card_layout = dashboard_card()
        card_layout.addWidget(section_accent("Nächste Aktionen"))

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Status",
            "Material",
            "Menge",
            "Kontext",
        ])
        configure_mobiglas_table(self.table, "dataTable", selectable=False)
        self.table.setMinimumHeight(180)
        card_layout.addWidget(self.table)
        self._layout.addWidget(card)

        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(10)
        self.kpi_revenue = AnimatedDashboardValue("0 aUEC")
        self.kpi_profit = AnimatedDashboardValue("0 aUEC")
        self.kpi_profit.setObjectName("profitLabel")
        self.kpi_jobs = AnimatedDashboardValue("0")
        self.kpi_storage = animated_scu()
        for title, widget in (
            ("Umsatz", self.kpi_revenue),
            ("Gewinn", self.kpi_profit),
            ("Raffinerie", self.kpi_jobs),
            ("Verkaufbar", self.kpi_storage),
        ):
            kpi_row.addWidget(kpi_card(title, widget))
        self._layout.addLayout(kpi_row)
        self._layout.addStretch()

    def refresh(self):
        rows = data.OVERVIEW["actions"]
        self.table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            for col, text in enumerate(row):
                item = QTableWidgetItem(text)
                if col == 2:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight
                        | Qt.AlignmentFlag.AlignVCenter
                    )
                self.table.setItem(index, col, item)
        finalize_table_columns(self.table, stretch_column=3)

        kpis = data.OVERVIEW["kpis"]
        animate_currency(self.kpi_revenue, kpis["revenue"])
        animate_currency(self.kpi_profit, kpis["profit"])
        animate_int(self.kpi_jobs, kpis["open_jobs"])
        animate_scu(self.kpi_storage, kpis["sellable_scu"])


class SessionView(_BaseContextView):
    context_key = "session"

    def __init__(self, parent=None):
        super().__init__(parent)

        top = QHBoxLayout()
        top.setSpacing(10)

        self.status_value = AnimatedDashboardValue("—")
        self.crew_value = AnimatedDashboardValue("0")
        self.session_scu = animated_scu()

        top.addWidget(kpi_card("Status", self.status_value))
        top.addWidget(kpi_card("Crew (Session)", self.crew_value))
        top.addWidget(kpi_card("Session SCU", self.session_scu))
        self._layout.addLayout(top)

        mat_card, mat_layout = dashboard_card()
        mat_layout.addWidget(subsection_title("Material gesammelt"))
        mat_grid = QGridLayout()
        mat_grid.setHorizontalSpacing(10)
        mat_grid.setVerticalSpacing(8)
        self.mat_widgets = {}
        specs = [
            ("RMC", "RMC"),
            ("CM", "CM"),
            ("CM_RUBBLE", "CM_RUBBLE"),
            ("CM_SCRAPS", "CM_SCRAPS"),
            ("CM_SALVAGE", "CM_SALVAGE"),
        ]
        for index, (code, key) in enumerate(specs):
            widget = animated_scu()
            self.mat_widgets[key] = widget
            mat_grid.addWidget(
                kpi_card(material_label(code), widget),
                index // 3,
                index % 3,
            )
        mat_layout.addLayout(mat_grid)
        self._layout.addWidget(mat_card)

        loc_card, loc_layout = dashboard_card()
        loc_layout.addWidget(subsection_title("Wo sind die Materialien?"))
        self.locations_host = QWidget()
        self.locations_host.setAutoFillBackground(False)
        self.locations_layout = QVBoxLayout(self.locations_host)
        self.locations_layout.setContentsMargins(0, 0, 0, 0)
        self.locations_layout.setSpacing(10)
        loc_layout.addWidget(self.locations_host)
        self._layout.addWidget(loc_card)

        proc_card, proc_layout = dashboard_card()
        proc_layout.addWidget(subsection_title("Was passiert gerade?"))
        self.process_host = QWidget()
        self.process_host.setAutoFillBackground(False)
        self.process_layout = QVBoxLayout(self.process_host)
        self.process_layout.setContentsMargins(0, 0, 0, 0)
        self.process_layout.setSpacing(8)
        proc_layout.addWidget(self.process_host)
        self._layout.addWidget(proc_card)
        self._layout.addStretch()

    def refresh(self):
        session = data.SESSION
        self.status_value.setText(session["status_label"])
        animate_int(self.crew_value, session["crew"])
        animate_scu(self.session_scu, session["session_scu_total"])

        for key, widget in self.mat_widgets.items():
            animate_scu(widget, session["materials"].get(key, 0))

        while self.locations_layout.count():
            item = self.locations_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for label, detail, pct in session["locations"]:
            self.locations_layout.addWidget(
                ProgressBarRow(label, detail, pct)
            )

        while self.process_layout.count():
            item = self.process_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for title, detail in session["processes"]:
            self.process_layout.addWidget(
                TimelineRow("◆", title, detail)
            )


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
            ("Offen", self.jobs_open),
            ("Abholbereit", self.jobs_ready),
            ("Ø Effizienz", self.efficiency),
            ("Input", self.io_in),
            ("Output", self.io_out),
        ):
            top.addWidget(kpi_card(title, widget))
        self._layout.addLayout(top)

        jobs_card, jobs_layout = dashboard_card()
        jobs_layout.addWidget(subsection_title("Aktive Jobs"))
        self.jobs_host = QWidget()
        self.jobs_host.setAutoFillBackground(False)
        self.jobs_layout = QVBoxLayout(self.jobs_host)
        self.jobs_layout.setContentsMargins(0, 0, 0, 0)
        self.jobs_layout.setSpacing(8)
        jobs_layout.addWidget(self.jobs_host)
        self._layout.addWidget(jobs_card)

        mat_card, mat_layout = dashboard_card()
        mat_layout.addWidget(subsection_title("Effizienz nach Material"))
        self.mat_host = QWidget()
        self.mat_host.setAutoFillBackground(False)
        self.mat_layout = QVBoxLayout(self.mat_host)
        self.mat_layout.setContentsMargins(0, 0, 0, 0)
        mat_layout.addWidget(self.mat_host)
        self._layout.addWidget(mat_card)
        self._layout.addStretch()

    def refresh(self):
        ref = data.REFINERY
        animate_int(self.jobs_open, ref["open_jobs"])
        animate_int(self.jobs_ready, ref["ready_jobs"])
        self.efficiency.animate_to(
            ref["avg_efficiency"],
            suffix=" %",
            decimals=1,
            duration=1000,
        )
        animate_scu(self.io_in, ref["total_input"])
        animate_scu(self.io_out, ref["total_output"])

        while self.jobs_layout.count():
            item = self.jobs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for job in ref["jobs"]:
            if job["status"] == "READY":
                detail = (
                    f"{material_label(job['material'])} · "
                    f"{job['output_scu']:.1f} SCU Output · {job['station']}"
                )
                title = f"Job #{job['id']} · {job['status_label']}"
            else:
                detail = (
                    f"{material_label(job['material'])} · "
                    f"{job['input_scu']:.1f} SCU · ETA ~{job['eta_minutes']} min"
                )
                title = f"Job #{job['id']} · {job['status_label']} · {job['station']}"
            self.jobs_layout.addWidget(TimelineRow("◆", title, detail))

        while self.mat_layout.count():
            item = self.mat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for code, eff, count in ref["by_material"]:
            self.mat_layout.addWidget(
                ProgressBarRow(
                    material_label(code),
                    f"{count} Jobs abgeschlossen",
                    int(eff),
                )
            )


class StorageView(_BaseContextView):
    context_key = "storage"

    def __init__(self, parent=None):
        super().__init__(parent)

        top = QHBoxLayout()
        top.setSpacing(10)
        self.total_scu = animated_scu()
        self.idle_warn = AnimatedDashboardValue("0")
        self.loc_count = AnimatedDashboardValue("0")
        top.addWidget(kpi_card("Gesamt", self.total_scu))
        top.addWidget(kpi_card("Inaktiv-Warnungen", self.idle_warn))
        top.addWidget(kpi_card("Standorte", self.loc_count))
        self._layout.addLayout(top)

        loc_card, loc_layout = dashboard_card()
        loc_layout.addWidget(subsection_title("Bestand nach Standort"))
        self.loc_host = QWidget()
        self.loc_host.setAutoFillBackground(False)
        self.loc_layout = QVBoxLayout(self.loc_host)
        self.loc_layout.setContentsMargins(0, 0, 0, 0)
        self.loc_layout.setSpacing(8)
        loc_layout.addWidget(self.loc_host)
        self._layout.addWidget(loc_card)

        evt_card, evt_layout = dashboard_card()
        evt_layout.addWidget(subsection_title("Letzte Bewegungen"))
        self.evt_host = QWidget()
        self.evt_host.setAutoFillBackground(False)
        self.evt_layout = QVBoxLayout(self.evt_host)
        self.evt_layout.setContentsMargins(0, 0, 0, 0)
        evt_layout.addWidget(self.evt_host)
        self._layout.addWidget(evt_card)
        self._layout.addStretch()

    def refresh(self):
        store = data.STORAGE
        animate_scu(self.total_scu, store["total_scu"])
        animate_int(self.idle_warn, store["idle_warnings"])
        animate_int(self.loc_count, len(store["locations"]))

        while self.loc_layout.count():
            item = self.loc_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for name, detail, idle in store["locations"]:
            row = TimelineRow(
                "⚠" if idle else "◆",
                name + (" · INAKTIV" if idle else ""),
                detail,
            )
            self.loc_layout.addWidget(row)

        while self.evt_layout.count():
            item = self.evt_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for when, title, detail in store["recent_events"]:
            self.evt_layout.addWidget(
                TimelineRow(when, title, detail)
            )


class SalesView(_BaseContextView):
    context_key = "sales"

    def __init__(self, parent=None):
        super().__init__(parent)

        top = QHBoxLayout()
        top.setSpacing(10)
        self.ready_scu = animated_scu()
        self.estimate = AnimatedDashboardValue("0 aUEC")
        self.pending = AnimatedDashboardValue("0")
        self.pending_amount = AnimatedDashboardValue("0 aUEC")
        top.addWidget(kpi_card("Verkaufsbereit", self.ready_scu))
        top.addWidget(kpi_card("Schätzwert", self.estimate))
        top.addWidget(kpi_card("Offen", self.pending))
        top.addWidget(kpi_card("Offen (aUEC)", self.pending_amount))
        self._layout.addLayout(top)

        card, card_layout = dashboard_card()
        card_layout.addWidget(subsection_title("Verkaufsbereite Posten"))
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Material",
            "Standort",
            "Menge",
            "Schätzwert",
        ])
        configure_mobiglas_table(self.table, "dataTable", selectable=False)
        self.table.setMinimumHeight(200)
        card_layout.addWidget(self.table)
        self._layout.addWidget(card)
        self._layout.addStretch()

    def refresh(self):
        sales = data.SALES
        animate_scu(self.ready_scu, sales["ready_total_scu"])
        animate_currency(self.estimate, sales["ready_value_estimate"])
        animate_int(self.pending, sales["pending_sales"])
        animate_currency(self.pending_amount, sales["pending_amount"])

        rows = sales["items"]
        self.table.setRowCount(len(rows))
        for r, (mat, loc, qty, val) in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(mat))
            self.table.setItem(r, 1, QTableWidgetItem(loc))
            qty_item = QTableWidgetItem(f"{qty:.1f} SCU")
            qty_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(r, 2, qty_item)
            val_item = QTableWidgetItem(f"{val:,.0f} aUEC".replace(",", "."))
            val_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(r, 3, val_item)
        finalize_table_columns(self.table, stretch_column=1)


class PayoutView(_BaseContextView):
    context_key = "payout"

    def __init__(self, parent=None):
        super().__init__(parent)

        top = QHBoxLayout()
        top.setSpacing(10)
        self.open_count = AnimatedDashboardValue("0")
        self.open_total = AnimatedDashboardValue("0 aUEC")
        top.addWidget(kpi_card("Offene Payouts", self.open_count))
        top.addWidget(kpi_card("Summe offen", self.open_total))
        self._layout.addLayout(top)

        card, card_layout = dashboard_card()
        card_layout.addWidget(subsection_title("Ausstehende Auszahlungen"))
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Session",
            "Material",
            "Menge",
            "Betrag",
            "Ort",
        ])
        configure_mobiglas_table(self.table, "dataTable", selectable=False)
        self.table.setMinimumHeight(220)
        card_layout.addWidget(self.table)
        self._layout.addWidget(card)
        self._layout.addStretch()

    def refresh(self):
        payout = data.PAYOUT
        animate_int(self.open_count, payout["open_count"])
        animate_currency(self.open_total, payout["open_total"])

        rows = payout["items"]
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            session, mat, qty, amount, loc = row
            self.table.setItem(r, 0, QTableWidgetItem(session))
            self.table.setItem(r, 1, QTableWidgetItem(mat))
            qty_item = QTableWidgetItem(f"{qty:.1f} SCU")
            qty_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(r, 2, qty_item)
            amt_item = QTableWidgetItem(f"{amount:,.0f} aUEC".replace(",", "."))
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
        top.addWidget(kpi_card("Verkauft", self.sold))
        top.addWidget(kpi_card("Sessions gesamt", self.total))
        top.addWidget(kpi_card("Umsatz", self.revenue))
        self._layout.addLayout(top)

        rev_card, rev_layout = dashboard_card()
        rev_layout.addWidget(subsection_title("Umsatz pro Monat"))
        self.rev_host = QWidget()
        self.rev_host.setAutoFillBackground(False)
        self.rev_layout = QVBoxLayout(self.rev_host)
        self.rev_layout.setContentsMargins(0, 0, 0, 0)
        rev_layout.addWidget(self.rev_host)
        self._layout.addWidget(rev_card)

        evt_card, evt_layout = dashboard_card()
        evt_layout.addWidget(subsection_title("Letzte Ereignisse"))
        self.evt_host = QWidget()
        self.evt_host.setAutoFillBackground(False)
        self.evt_layout = QVBoxLayout(self.evt_host)
        self.evt_layout.setContentsMargins(0, 0, 0, 0)
        evt_layout.addWidget(self.evt_host)
        self._layout.addWidget(evt_card)
        self._layout.addStretch()

    def refresh(self):
        hist = data.HISTORY
        animate_int(self.sold, hist["sold_sessions"])
        animate_int(self.total, hist["total_sessions"])
        animate_currency(self.revenue, hist["total_revenue"])

        while self.rev_layout.count():
            item = self.rev_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        max_val = max(v for _, v in hist["monthly_revenue"])
        for month, value in hist["monthly_revenue"]:
            pct = int(100 * value / max_val) if max_val else 0
            self.rev_layout.addWidget(
                ProgressBarRow(
                    month,
                    f"{value:,.0f} aUEC".replace(",", "."),
                    pct,
                )
            )

        while self.evt_layout.count():
            item = self.evt_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for when, title, detail in hist["recent"]:
            self.evt_layout.addWidget(
                TimelineRow(when, title, detail)
            )


CONTEXT_VIEWS = {
    "overview": OverviewView,
    "session": SessionView,
    "refinery": RefineryView,
    "storage": StorageView,
    "sales": SalesView,
    "payout": PayoutView,
    "history": HistoryView,
}
