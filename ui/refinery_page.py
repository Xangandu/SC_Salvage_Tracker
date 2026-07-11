from datetime import datetime, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QComboBox,
    QLineEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QSplitter,
)

from database.access import get_database
from config.debug import debug_log
from config.dates import (
    DB_DATETIME_FMT,
    format_datetime,
    parse_datetime,
)
from config.materials import (
    REFINERY_OUTPUT_CODE,
    material_label,
)
from config.refinery_methods import (
    REFINERY_METHODS,
)
from config.locations.cscu import cscu_to_scu
from config.i18n import tr, format_number
from config.strings_de import parse_int_de, parse_number_de
from config.permissions import apply_widget_permissions
from ui.system_location_picker import SystemLocationPicker
from ui.table_utils import (
    configure_mobiglas_table,
    finalize_table_columns,
)
from ui.page_split_persistence import (
    SETTING_REFINERY_PAGE_SPLIT,
    bind_page_split_persistence,
)
from ui.page_layout import (
    build_page_scroll,
    page_content_widget,
    page_title,
    section_accent,
    subsection_title,
    add_form_field,
    info_panel,
    page_panel,
    primary_button,
    empty_info_panel,
    hud_divider,
)
from ui.mobiglas_input_dialog import MobiglasDoubleInputDialog
from ui.refinery_job_card import RefineryJobCard


def _parse_db_datetime(value):
    if not value:
        return datetime.now()

    try:
        return parse_datetime(value)
    except ValueError:
        return datetime.now()


def _detail_label(text):
    label = QLabel(text)
    label.setObjectName("cardDetailLabel")
    return label


def _secondary_button(text):
    button = QPushButton(text)
    button.setObjectName("secondaryAction")
    return button


def _status_panel(*, ready_at="-", remaining="-", status=None):
    if status is None:
        status = tr("refinery.status.waiting_input")
    return tr(
        "refinery.status.panel",
        ready_at=ready_at,
        remaining=remaining,
        status=status,
    )


class RefineryPage(QWidget):

    def __init__(self):
        super().__init__()

        self.db = get_database()

        content, layout = page_content_widget()

        layout.addWidget(page_title(tr("refinery.title")))
        layout.addWidget(
            section_accent(tr("refinery.section.main"))
        )
        layout.addLayout(hud_divider())

        kpi_row = QWidget()
        kpi_layout = QHBoxLayout(kpi_row)
        kpi_layout.setContentsMargins(0, 0, 0, 0)
        kpi_layout.setSpacing(12)

        available_panel = QFrame()
        available_panel.setObjectName("financeSummaryPanel")
        available_layout = QVBoxLayout(available_panel)
        available_layout.setContentsMargins(14, 10, 14, 10)
        available_layout.setSpacing(4)
        available_layout.addWidget(
            QLabel(tr("refinery.kpi.available_scu"))
        )
        self.available_scu_label = QLabel(
            f"{format_number(0)} SCU"
        )
        self.available_scu_label.setObjectName("statValue")
        available_layout.addWidget(self.available_scu_label)

        active_panel = QFrame()
        active_panel.setObjectName("financeSummaryPanel")
        active_kpi_layout = QVBoxLayout(active_panel)
        active_kpi_layout.setContentsMargins(14, 10, 14, 10)
        active_kpi_layout.setSpacing(4)
        active_kpi_layout.addWidget(
            QLabel(tr("refinery.kpi.active_jobs"))
        )
        self.active_jobs_label = QLabel("0")
        self.active_jobs_label.setObjectName("statValue")
        active_kpi_layout.addWidget(self.active_jobs_label)

        ready_panel = QFrame()
        ready_panel.setObjectName("financeSummaryPanel")
        ready_kpi_layout = QVBoxLayout(ready_panel)
        ready_kpi_layout.setContentsMargins(14, 10, 14, 10)
        ready_kpi_layout.setSpacing(4)
        ready_kpi_layout.addWidget(
            QLabel(tr("refinery.kpi.ready_jobs"))
        )
        self.ready_jobs_label = QLabel("0")
        self.ready_jobs_label.setObjectName("statValue")
        ready_kpi_layout.addWidget(self.ready_jobs_label)

        kpi_layout.addWidget(available_panel, 1)
        kpi_layout.addWidget(active_panel, 1)
        kpi_layout.addWidget(ready_panel, 1)
        layout.addWidget(kpi_row)

        self._ready_banner = QFrame()
        self._ready_banner.setObjectName("refineryReadyBanner")
        self._ready_banner.hide()
        banner_layout = QHBoxLayout(self._ready_banner)
        banner_layout.setContentsMargins(12, 10, 12, 10)
        self._ready_banner_label = QLabel()
        self._ready_banner_label.setObjectName("refineryReadyBannerText")
        self._ready_banner_label.setWordWrap(True)
        banner_layout.addWidget(self._ready_banner_label, 1)
        layout.addWidget(self._ready_banner)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("pageSplit")
        splitter.setHandleWidth(14)
        splitter.setChildrenCollapsible(False)

        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 16, 0)
        left_layout.setSpacing(12)

        batches_panel, batches_layout = page_panel()
        batches_layout.setContentsMargins(12, 12, 12, 12)
        batches_layout.setSpacing(8)
        batches_layout.addWidget(
            subsection_title(tr("refinery.section.batches"))
        )
        batches_layout.addLayout(hud_divider())

        self.batches_table = QTableWidget()
        self.batches_table.setColumnCount(3)
        self.batches_table.setHorizontalHeaderLabels([
            tr("refinery.table.location"),
            tr("refinery.table.material"),
            tr("refinery.table.available_scu"),
        ])
        configure_mobiglas_table(
            self.batches_table,
            "dataTable",
        )
        self.batches_empty = empty_info_panel(
            tr("refinery.msg.no_pool"),
            "assets/images/icons/info.svg",
        )
        batches_layout.addWidget(self.batches_table)
        batches_layout.addWidget(self.batches_empty)
        self.batches_empty.hide()
        left_layout.addWidget(batches_panel)

        form_panel, form_layout = info_panel()
        form_layout.addWidget(
            subsection_title(tr("refinery.section.create"))
        )
        form_layout.addLayout(hud_divider())

        self.refinery_location_picker = SystemLocationPicker(
            refinery_stations_only=True,
        )

        self.refinery_method_combo = QComboBox()
        self.refinery_method_combo.addItem(
            tr("refinery.method.placeholder"),
            "",
        )
        for method in REFINERY_METHODS:
            self.refinery_method_combo.addItem(method, method)

        self.refinery_cost_input = QLineEdit()
        self.refinery_cost_input.setPlaceholderText(
            tr("refinery.placeholder.cost")
        )

        self.refinery_cost_paid_by = QComboBox()
        self.refinery_cost_paid_by.addItem(
            tr("session.mission.paid_by.placeholder")
        )

        self.pool_combo = QComboBox()

        self.input_cscu = QLineEdit()
        self.input_cscu.setPlaceholderText(
            tr("refinery.placeholder.input_cscu")
        )

        self.input_cscu_formula = QLabel(
            tr("refinery.hint.cscu_formula")
        )
        self.input_cscu_formula.setObjectName("refineryCscuFormula")

        self.input_scu_hint = QLabel()
        self.input_scu_hint.setObjectName("refineryScuConversion")
        self.input_scu_hint.hide()

        input_cscu_col = QWidget()
        input_cscu_layout = QVBoxLayout(input_cscu_col)
        input_cscu_layout.setContentsMargins(0, 0, 0, 0)
        input_cscu_layout.setSpacing(6)
        input_cscu_layout.addWidget(self.input_cscu)
        input_cscu_layout.addWidget(self.input_cscu_formula)
        input_cscu_layout.addWidget(self.input_scu_hint)

        self.hours_input = QLineEdit()
        self.hours_input.setPlaceholderText(
            tr("refinery.placeholder.hours")
        )

        self.minutes_input = QLineEdit()
        self.minutes_input.setPlaceholderText(
            tr("refinery.placeholder.minutes")
        )

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText(
            tr("refinery.placeholder.notes")
        )

        self.ready_info_label = QLabel(_status_panel())
        self.ready_info_label.setObjectName(
            "refineryStatusPanel"
        )

        self.create_button = primary_button(
            tr("refinery.button.create")
        )

        form_layout.addWidget(self.refinery_location_picker)
        add_form_field(
            form_layout,
            tr("refinery.label.method"),
            self.refinery_method_combo,
        )
        add_form_field(
            form_layout,
            tr("refinery.label.cost"),
            self.refinery_cost_input,
        )
        add_form_field(
            form_layout,
            tr("refinery.label.paid_by"),
            self.refinery_cost_paid_by,
        )
        add_form_field(
            form_layout,
            tr("refinery.label.material_source"),
            self.pool_combo,
        )
        add_form_field(
            form_layout,
            tr("refinery.label.input_cscu"),
            input_cscu_col,
        )

        time_row = QHBoxLayout()
        time_row.setSpacing(12)

        hours_col = QVBoxLayout()
        hours_label = QLabel(tr("refinery.label.hours"))
        hours_label.setObjectName("formLabel")
        hours_col.addWidget(hours_label)
        hours_col.addWidget(self.hours_input)

        minutes_col = QVBoxLayout()
        minutes_label = QLabel(tr("refinery.label.minutes"))
        minutes_label.setObjectName("formLabel")
        minutes_col.addWidget(minutes_label)
        minutes_col.addWidget(self.minutes_input)

        time_row.addLayout(hours_col, 1)
        time_row.addLayout(minutes_col, 1)
        form_layout.addLayout(time_row)

        add_form_field(
            form_layout,
            tr("refinery.label.notes"),
            self.notes_input,
        )

        form_layout.addWidget(self.ready_info_label)
        form_layout.addWidget(self.create_button)
        left_layout.addWidget(form_panel)
        left_layout.addStretch()

        self._job_cards: dict[int, RefineryJobCard] = {}
        self._live_sync = None

        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(16, 0, 0, 0)
        right_layout.setSpacing(12)

        active_outer, active_outer_layout = page_panel()
        active_outer_layout.setContentsMargins(12, 12, 12, 12)
        active_outer_layout.setSpacing(8)
        active_outer_layout.addWidget(
            subsection_title(tr("refinery.section.active"))
        )
        active_outer_layout.addLayout(hud_divider())

        self.jobs_container = QVBoxLayout()
        self.jobs_container.setSpacing(10)
        self._jobs_host = QWidget()
        self._jobs_host.setLayout(self.jobs_container)
        active_outer_layout.addWidget(self._jobs_host)
        right_layout.addWidget(active_outer, 1)

        splitter.addWidget(left_column)
        splitter.addWidget(right_column)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([620, 420])
        layout.addWidget(splitter, 1)

        bind_page_split_persistence(
            splitter,
            self.db,
            SETTING_REFINERY_PAGE_SPLIT,
            default_sizes=[620, 420],
        )

        layout.addStretch()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(build_page_scroll(content))

        self.hours_input.textChanged.connect(
            self.update_ready_time
        )
        self.minutes_input.textChanged.connect(
            self.update_ready_time
        )
        self.pool_combo.currentIndexChanged.connect(
            self._update_refinery_cost_payers
        )
        self.input_cscu.textChanged.connect(
            self._update_input_scu_hint
        )
        self.create_button.clicked.connect(
            self.create_job
        )

        self.load_data()

    def attach_live_sync(self, live_sync) -> None:
        if self._live_sync is live_sync:
            return

        if self._live_sync is not None:
            try:
                self._live_sync.jobs_updated.disconnect(
                    self._on_jobs_updated
                )
                self._live_sync.jobs_became_ready.disconnect(
                    self._on_jobs_became_ready
                )
            except RuntimeError:
                pass

        self._live_sync = live_sync
        live_sync.jobs_updated.connect(self._on_jobs_updated)
        live_sync.jobs_became_ready.connect(
            self._on_jobs_became_ready
        )

    def showEvent(self, event):
        super().showEvent(event)
        if self._live_sync is not None:
            self._on_jobs_updated()

    def _on_jobs_updated(self) -> None:
        if not self.isVisible():
            return

        jobs = self.db.get_active_refinery_jobs()
        self._sync_job_cards(jobs)
        for card in self._job_cards.values():
            card.tick()
        self._update_ready_banner(jobs)
        self._update_kpis()

    def _on_jobs_became_ready(self, job_ids: list) -> None:
        jobs = self.db.get_active_refinery_jobs()
        ready_jobs = [
            job for job in jobs if job["id"] in job_ids
        ]
        if len(ready_jobs) == 1:
            job = ready_jobs[0]
            text = tr(
                "refinery.banner.ready_one",
                job_id=job["id"],
                station=job["refinery_name"],
            )
        else:
            text = tr(
                "refinery.banner.ready_many",
                count=len(job_ids),
            )
        self._ready_banner_label.setText(text)
        self._ready_banner.show()
        self._on_jobs_updated()

    def _update_ready_banner(self, jobs=None) -> None:
        if jobs is None:
            jobs = self.db.get_active_refinery_jobs()

        ready_jobs = [
            job
            for job in jobs
            if job.get("status") == "READY"
        ]
        if not ready_jobs:
            self._ready_banner.hide()
            return

        if not self._ready_banner.isVisible():
            if len(ready_jobs) == 1:
                job = ready_jobs[0]
                text = tr(
                    "refinery.banner.ready_one",
                    job_id=job["id"],
                    station=job["refinery_name"],
                )
            else:
                text = tr(
                    "refinery.banner.ready_many",
                    count=len(ready_jobs),
                )
            self._ready_banner_label.setText(text)
            self._ready_banner.show()

    def _clear_job_cards(self) -> None:
        for card in self._job_cards.values():
            self.jobs_container.removeWidget(card)
            card.deleteLater()
        self._job_cards.clear()

    def _sync_job_cards(self, jobs) -> None:
        job_ids = {job["id"] for job in jobs}

        for job_id in list(self._job_cards):
            if job_id not in job_ids:
                card = self._job_cards.pop(job_id)
                self.jobs_container.removeWidget(card)
                card.deleteLater()
                if self._live_sync is not None:
                    self._live_sync.clear_notified(job_id)

        if not jobs:
            if self.jobs_container.count() == 0:
                self.jobs_container.addWidget(
                    empty_info_panel(
                        tr("refinery.active.empty"),
                        "assets/images/icons/info.svg",
                    )
                )
            return

        while self.jobs_container.count():
            item = self.jobs_container.takeAt(0)
            widget = item.widget()
            if widget and not isinstance(widget, RefineryJobCard):
                widget.deleteLater()

        for job in jobs:
            job_id = job["id"]
            if job_id in self._job_cards:
                self._job_cards[job_id].set_job(job)
                self.jobs_container.addWidget(
                    self._job_cards[job_id]
                )
                continue

            card = RefineryJobCard(job, self._jobs_host)
            card.complete_requested.connect(self.complete_job)
            card.cancel_requested.connect(self.cancel_job)
            self._job_cards[job_id] = card
            self.jobs_container.addWidget(card)

    def apply_permissions(
        self,
        user,
        page_name="refinery",
    ):
        apply_widget_permissions(
            self,
            user,
            page_name,
        )

    def load_data(self):
        self.load_batches()
        self.load_active_jobs()

    def _refresh_history_page(self) -> None:
        main_window = self.window()
        if hasattr(main_window, "history_page"):
            main_window.history_page.refresh_history()

    def _update_kpis(self) -> None:
        pools = self.db.get_refinery_material_pools()
        total_scu = sum(
            float(pool.get("quantity_scu") or 0)
            for pool in pools
        )
        self.available_scu_label.setText(
            f"{format_number(total_scu, 0)} SCU"
        )

        jobs = self.db.get_active_refinery_jobs()
        ready_count = sum(
            1 for job in jobs if job.get("status") == "READY"
        )
        self.active_jobs_label.setText(
            format_number(len(jobs), 0)
        )
        self.ready_jobs_label.setText(
            format_number(ready_count, 0)
        )
        self.ready_jobs_label.setObjectName(
            "warningBannerTitle" if ready_count > 0 else "statValue"
        )
        style = self.ready_jobs_label.style()
        if style is not None:
            style.unpolish(self.ready_jobs_label)
            style.polish(self.ready_jobs_label)

    def load_batches(self):
        pools = self.db.get_refinery_material_pools()

        has_pools = len(pools) > 0
        self.batches_table.setVisible(has_pools)
        self.batches_empty.setVisible(not has_pools)

        self.pool_combo.blockSignals(True)
        self.pool_combo.clear()

        self.batches_table.setRowCount(len(pools))

        for row, pool in enumerate(pools):
            label = material_label(pool["material_code"])
            if pool.get("pool_kind") == "SHIP":
                location = tr(
                    "storage.location.ship",
                    ship=pool.get("ship_name") or "—",
                )
            else:
                location = pool.get("location_label") or "—"
            quantity = pool.get("quantity_scu") or 0

            self.batches_table.setItem(
                row,
                0,
                QTableWidgetItem(location),
            )
            self.batches_table.setItem(
                row,
                1,
                QTableWidgetItem(label),
            )
            self.batches_table.setItem(
                row,
                2,
                QTableWidgetItem(format_number(quantity, 0)),
            )

            combo_text = tr(
                "refinery.pool.combo",
                location=location,
                material=label,
                quantity=format_number(quantity, 0),
            )
            self.pool_combo.addItem(combo_text, pool)

        self.pool_combo.blockSignals(False)
        self._update_refinery_cost_payers()

        finalize_table_columns(
            self.batches_table,
            stretch_column=0,
        )
        self._update_kpis()

    def _update_refinery_cost_payers(self):
        current = self.refinery_cost_paid_by.currentText()
        pool = self.pool_combo.currentData()

        self.refinery_cost_paid_by.blockSignals(True)
        self.refinery_cost_paid_by.clear()
        self.refinery_cost_paid_by.addItem(
            tr("session.mission.paid_by.placeholder")
        )

        if isinstance(pool, dict):
            for member in self.db.get_crew_for_material_pool(pool):
                self.refinery_cost_paid_by.addItem(member)

        index = self.refinery_cost_paid_by.findText(current)

        if index >= 0:
            self.refinery_cost_paid_by.setCurrentIndex(index)

        self.refinery_cost_paid_by.blockSignals(False)

    def update_ready_time(self):
        try:
            hours = int(
                self.hours_input.text() or 0
            )
            minutes = int(
                self.minutes_input.text() or 0
            )
        except ValueError:
            self.ready_info_label.setText(_status_panel())
            return

        ready_time = (
            datetime.now()
            + timedelta(hours=hours, minutes=minutes)
        )

        self.ready_info_label.setText(
            _status_panel(
                ready_at=format_datetime(ready_time),
                remaining=tr(
                    "refinery.status.remaining_hm",
                    hours=hours,
                    minutes=minutes,
                ),
                status=tr("refinery.status.in_progress"),
            )
        )

    def _update_input_scu_hint(self):
        cscu = parse_number_de(self.input_cscu.text())
        if cscu is None or cscu <= 0:
            self.input_scu_hint.hide()
            return

        scu = cscu_to_scu(cscu)
        self.input_scu_hint.setText(
            tr(
                "refinery.hint.scu_from_cscu",
                scu=format_number(scu, 0),
                cscu=format_number(cscu),
            )
        )
        self.input_scu_hint.show()

    def load_active_jobs(self):
        jobs = self.db.get_active_refinery_jobs()
        self._sync_job_cards(jobs)
        for card in self._job_cards.values():
            card.tick()
        self._update_ready_banner(jobs)
        self._update_kpis()
        if not jobs:
            self.refinery_location_picker.clear_selection()

    def create_job(self):
        pool = self.pool_combo.currentData()

        if not isinstance(pool, dict):
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("refinery.msg.no_pool"),
            )
            return

        refinery_name = self.refinery_location_picker.location_label()

        if not self.refinery_location_picker.is_selected():
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("refinery.msg.no_station"),
            )
            return

        input_cscu = parse_number_de(self.input_cscu.text())
        hours = parse_int_de(self.hours_input.text(), default=0)
        minutes = parse_int_de(self.minutes_input.text(), default=0)
        cost = parse_number_de(
            self.refinery_cost_input.text(),
            default=0,
        )
        if input_cscu is None or hours is None or minutes is None or cost is None:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("refinery.msg.invalid_values"),
            )
            return

        if input_cscu <= 0:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("refinery.msg.invalid_values"),
            )
            return

        input_scu = cscu_to_scu(input_cscu)

        if cost < 0:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("refinery.msg.negative_cost"),
            )
            return

        if cost > 0:
            if self.refinery_cost_paid_by.currentIndex() <= 0:
                QMessageBox.warning(
                    self,
                    tr("common.error"),
                    tr("refinery.msg.paid_by_required"),
                )
                return

        ready_time = (
            datetime.now()
            + timedelta(hours=hours, minutes=minutes)
        )

        notes = self.notes_input.text().strip() or None
        cost_paid_by = ""

        if cost > 0:
            cost_paid_by = (
                self.refinery_cost_paid_by.currentText()
            )

        try:
            self.db.create_refinery_job_from_pool(
                refinery_name,
                ready_time.strftime(DB_DATETIME_FMT),
                pool=pool,
                input_quantity=input_scu,
                notes=notes,
                refinery_method=self.refinery_method_combo.currentData()
                or "",
                cost=cost,
                cost_paid_by=cost_paid_by,
            )
        except ValueError as error:
            QMessageBox.warning(
                self,
                tr("common.error"),
                str(error),
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                tr("common.error"),
                tr("refinery.msg.create_failed", error=error),
            )
            return

        self.input_cscu.clear()
        self.hours_input.clear()
        self.minutes_input.clear()
        self.notes_input.clear()
        self.refinery_cost_input.clear()
        self.refinery_cost_paid_by.setCurrentIndex(0)
        self.refinery_location_picker.clear_selection()
        self.ready_info_label.setText(_status_panel())

        self.load_data()
        self._refresh_dashboard()
        self._refresh_history_page()

    def complete_job(self, job_id):
        hint_text = ""
        material_code = ""
        jobs = self.db.get_active_refinery_jobs()
        for job in jobs:
            if job["id"] == job_id and job.get("items"):
                material_code = job["items"][0].get(
                    "input_material",
                    "",
                )
                break

        if material_code:
            stats = self.db.get_refinery_efficiency_hint(
                material_code
            )
            if stats:
                hint_text = tr(
                    "refinery.complete.hint",
                    material=material_label(material_code),
                    efficiency=format_number(
                        stats["efficiency_percent"],
                        1,
                    ),
                    job_count=stats["job_count"],
                )

        dialog_hints = [tr("refinery.hint.cscu_formula")]
        if hint_text:
            dialog_hints.insert(0, hint_text)

        output_cscu, ok = MobiglasDoubleInputDialog.get_double(
            self,
            tr("refinery.complete.dialog.title"),
            tr("refinery.complete.dialog.field"),
            0,
            0,
            10000000,
            0,
            hint_text="\n\n".join(dialog_hints),
            field_tooltip=tr("refinery.complete.dialog.tooltip"),
            live_scu_from_cscu=True,
        )

        if not ok:
            return

        if output_cscu <= 0:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("refinery.msg.invalid_values"),
            )
            return

        output_scu = cscu_to_scu(output_cscu)

        try:
            result = self.db.complete_refinery_job(
                job_id,
                output_scu,
            )
        except ValueError as error:
            QMessageBox.warning(
                self,
                tr("common.error"),
                str(error),
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                tr("common.error"),
                tr("refinery.msg.complete_failed", error=error),
            )
            return

        QMessageBox.information(
            self,
            tr("refinery.msg.completed.title"),
            tr(
                "refinery.msg.completed.message",
                quantity=format_number(result["output_quantity"], 0),
                material=material_label(REFINERY_OUTPUT_CODE),
                yield_pct=format_number(result["yield_percent"], 1),
            ),
        )

        self.load_data()
        self._refresh_dashboard()
        self._refresh_history_page()

        if self._live_sync is not None:
            self._live_sync.clear_notified(job_id)

    def cancel_job(self, job_id):
        answer = QMessageBox.question(
            self,
            tr("refinery.msg.cancel_confirm.title"),
            tr(
                "refinery.msg.cancel_confirm.message",
                job_id=job_id,
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        try:
            self.db.cancel_refinery_job(job_id)
        except ValueError as error:
            QMessageBox.warning(
                self,
                tr("common.not_possible"),
                str(error),
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                tr("common.error"),
                tr("refinery.msg.cancel_failed", error=error),
            )
            return

        self.load_data()
        self._refresh_dashboard()
        self._refresh_history_page()

        if self._live_sync is not None:
            self._live_sync.clear_notified(job_id)

        QMessageBox.information(
            self,
            tr("refinery.msg.cancelled.title"),
            tr(
                "refinery.msg.cancelled.message",
                job_id=job_id,
            ),
        )

    def _refresh_dashboard(self):
        main_window = self.window()

        if hasattr(
            main_window,
            "dashboard_page"
        ):
            main_window.dashboard_page.refresh_dashboard()
