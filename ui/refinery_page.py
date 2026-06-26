from datetime import datetime, timedelta

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
from config.refinery_methods import REFINERY_METHODS
from config.i18n import tr, format_number
from config.strings_de import parse_int_de, parse_number_de
from config.permissions import apply_widget_permissions
from ui.table_utils import (
    configure_mobiglas_table,
    finalize_table_columns,
)
from ui.page_layout import (
    build_page_scroll,
    page_content_widget,
    page_title,
    section_accent,
    subsection_title,
    add_form_field,
    info_panel,
    primary_button,
    empty_info_panel,
    svg_icon_widget,
)
from ui.mobiglas_input_dialog import MobiglasDoubleInputDialog


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


def _refinery_job_status(status):
    return tr(f"refinery.job_status.{status}", default=status)


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
            section_accent(tr("refinery.section.batches"))
        )

        self.batches_table = QTableWidget()
        self.batches_table.setColumnCount(5)
        self.batches_table.setHorizontalHeaderLabels([
            tr("refinery.table.batch"),
            tr("refinery.table.material"),
            tr("refinery.table.available_scu"),
            tr("refinery.table.original_scu"),
            tr("refinery.table.session"),
        ])
        configure_mobiglas_table(
            self.batches_table,
            "dataTable",
        )
        self.batches_table.setMinimumHeight(140)
        layout.addWidget(self.batches_table)

        form_panel, form_layout = info_panel()
        form_layout.addWidget(
            subsection_title(tr("refinery.section.create"))
        )

        self.refinery_name_input = QLineEdit()
        self.refinery_name_input.setPlaceholderText(
            tr("refinery.placeholder.station")
        )
        self.refinery_name_input.setText("Orison")

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

        self.batch_combo = QComboBox()

        self.input_scu = QLineEdit()
        self.input_scu.setPlaceholderText(
            tr("refinery.placeholder.input_scu")
        )

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

        add_form_field(
            form_layout,
            tr("refinery.label.station"),
            self.refinery_name_input,
        )
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
            tr("refinery.label.batch"),
            self.batch_combo,
        )
        add_form_field(
            form_layout,
            tr("refinery.label.input_scu"),
            self.input_scu,
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
        layout.addWidget(form_panel)

        layout.addWidget(
            section_accent(tr("refinery.section.active"))
        )

        self.jobs_container = QVBoxLayout()
        self.jobs_container.setSpacing(10)
        jobs_widget = QWidget()
        jobs_widget.setLayout(self.jobs_container)
        layout.addWidget(jobs_widget)

        layout.addWidget(
            section_accent(tr("refinery.section.history"))
        )

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(9)
        self.history_table.setHorizontalHeaderLabels([
            tr("refinery.history.no"),
            tr("refinery.history.station"),
            tr("refinery.history.method"),
            tr("refinery.history.status"),
            tr("refinery.history.input"),
            tr("refinery.history.cm_output"),
            tr("refinery.history.yield"),
            tr("refinery.history.cost"),
            tr("refinery.history.created_by"),
        ])
        configure_mobiglas_table(
            self.history_table,
            "historyTable",
        )
        self.history_table.setMinimumHeight(180)

        history_actions = QHBoxLayout()
        history_actions.setSpacing(12)
        self.delete_job_button = _secondary_button(
            tr("refinery.button.delete")
        )
        self.delete_job_button.clicked.connect(
            self.delete_selected_job
        )
        history_actions.addWidget(self.delete_job_button)
        history_actions.addStretch()
        layout.addWidget(self.history_table)
        layout.addLayout(history_actions)

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
        self.batch_combo.currentIndexChanged.connect(
            self._update_refinery_cost_payers
        )
        self.create_button.clicked.connect(
            self.create_job
        )

        self.load_data()

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
        self.load_history()

    def load_batches(self):
        batches = self.db.get_available_refinery_batches()

        self.batch_combo.blockSignals(True)
        self.batch_combo.clear()

        self.batches_table.setRowCount(len(batches))

        for row, batch in enumerate(batches):
            label = material_label(
                batch["material_code"]
            )
            batch_id = batch["batch_id"]
            remaining = batch["remaining_quantity"]
            original = batch["original_quantity"]
            session_name = batch["session_name"]

            self.batches_table.setItem(
                row,
                0,
                QTableWidgetItem(f"#{batch_id}"),
            )
            self.batches_table.setItem(
                row,
                1,
                QTableWidgetItem(label),
            )
            self.batches_table.setItem(
                row,
                2,
                QTableWidgetItem(format_number(remaining, 1)),
            )
            self.batches_table.setItem(
                row,
                3,
                QTableWidgetItem(format_number(original, 1)),
            )
            self.batches_table.setItem(
                row,
                4,
                QTableWidgetItem(session_name),
            )

            combo_text = tr(
                "refinery.batch.combo",
                batch_id=batch_id,
                material=label,
                remaining=format_number(remaining, 1),
            )
            self.batch_combo.addItem(
                combo_text,
                {
                    "batch_id": batch_id,
                    "session_id": batch["session_id"],
                },
            )

        self.batch_combo.blockSignals(False)
        self._update_refinery_cost_payers()

        finalize_table_columns(
            self.batches_table,
            stretch_column=4,
        )

    def _update_refinery_cost_payers(self):
        current = self.refinery_cost_paid_by.currentText()
        batch_data = self.batch_combo.currentData()
        session_id = None

        if isinstance(batch_data, dict):
            session_id = batch_data.get("session_id")

        self.refinery_cost_paid_by.blockSignals(True)
        self.refinery_cost_paid_by.clear()
        self.refinery_cost_paid_by.addItem(
            tr("session.mission.paid_by.placeholder")
        )

        if session_id is not None:
            for row in self.db.get_crew_members(session_id):
                member = row[0].strip()

                if member:
                    self.refinery_cost_paid_by.addItem(member)

        index = self.refinery_cost_paid_by.findText(current)

        if index >= 0:
            self.refinery_cost_paid_by.setCurrentIndex(index)

        self.refinery_cost_paid_by.blockSignals(False)

    def load_history(self):
        history = self.db.get_refinery_history()

        self.history_table.setRowCount(len(history))

        for row, job in enumerate(history):
            input_text = ", ".join(
                tr(
                    "refinery.history.input_line",
                    quantity=f"{item['input_quantity']:g}",
                    material=material_label(item["input_material"]),
                    batch_id=item["batch_id"],
                )
                for item in job["items"]
            )
            output_scu = job.get("cm_raf_output") or job["total_output"]
            output_text = (
                tr(
                    "refinery.history.output_line",
                    quantity=f"{output_scu:g}",
                    material=material_label(REFINERY_OUTPUT_CODE),
                )
                if output_scu > 0
                else "—"
            )
            yield_text = "—"

            if job["total_input"] > 0 and output_scu > 0:
                yield_pct = (
                    output_scu
                    / job["total_input"]
                    * 100
                )
                yield_text = tr(
                    "refinery.history.yield_pct",
                    yield_pct=format_number(yield_pct, 1),
                )

            self.history_table.setItem(
                row,
                0,
                QTableWidgetItem(f"#{job['id']}"),
            )
            self.history_table.setItem(
                row,
                1,
                QTableWidgetItem(job["refinery_name"]),
            )
            self.history_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    job.get("refinery_method") or "—"
                ),
            )
            self.history_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    _refinery_job_status(job["status"])
                ),
            )
            self.history_table.setItem(
                row,
                4,
                QTableWidgetItem(input_text),
            )
            self.history_table.setItem(
                row,
                5,
                QTableWidgetItem(output_text),
            )
            self.history_table.setItem(
                row,
                6,
                QTableWidgetItem(yield_text),
            )
            cost = job.get("cost", 0) or 0
            payer = (job.get("cost_paid_by") or "").strip()
            cost_text = f"{format_number(cost)} aUEC"

            if cost > 0 and payer:
                cost_text = f"{cost_text} ({payer})"

            self.history_table.setItem(
                row,
                7,
                QTableWidgetItem(cost_text),
            )
            self.history_table.setItem(
                row,
                8,
                QTableWidgetItem(job["created_by"]),
            )

        finalize_table_columns(
            self.history_table,
            stretch_column=4,
        )

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

    def load_active_jobs(self):
        while self.jobs_container.count():
            item = self.jobs_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        jobs = self.db.get_active_refinery_jobs()

        if not jobs:
            self.jobs_container.addWidget(
                empty_info_panel(
                    tr("refinery.active.empty"),
                    "assets/images/icons/info.svg",
                )
            )
            return

        for job in jobs:
            try:
                self._add_job_card(job)
            except Exception as error:
                debug_log(
                    "JOB CARD FEHLER:",
                    error,
                )

    def _add_job_card(self, job):
        job_id = job["id"]
        ready_time = _parse_db_datetime(
            job["end_time"]
        )
        remaining = ready_time - datetime.now()
        remaining_minutes = int(
            remaining.total_seconds() / 60
        )

        job_status = job.get("status", "RUNNING")

        if job_status == "READY" or remaining_minutes <= 0:
            is_ready = True
            status_text = tr("refinery.status.ready_for_pickup")
            status_icon = (
                "assets/images/icons/ready.svg"
            )
            remaining_text = tr("refinery.status.finished")
        elif remaining_minutes <= 60:
            is_ready = False
            status_text = tr("refinery.status.final_phase")
            status_icon = (
                "assets/images/icons/processing.svg"
            )
            remaining_text = tr(
                "refinery.status.remaining_min",
                minutes=remaining_minutes,
            )
        else:
            is_ready = False
            hours = remaining_minutes // 60
            minutes = remaining_minutes % 60
            status_text = tr("refinery.status.in_progress")
            status_icon = (
                "assets/images/icons/processing.svg"
            )
            remaining_text = tr(
                "refinery.status.remaining_hm",
                hours=hours,
                minutes=minutes,
            )

        card = QFrame()
        card.setObjectName(
            "jobCardReady" if is_ready else "jobCard"
        )
        card_layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        icon_widget = svg_icon_widget(
            status_icon,
            size=36,
            object_name="jobStatusIcon",
        )
        status_label = QLabel(status_text)
        status_label.setObjectName(
            "jobStatusLabelReady"
            if is_ready
            else "jobStatusLabel"
        )
        header_layout.addWidget(icon_widget)
        header_layout.addWidget(status_label)
        header_layout.addStretch()
        card_layout.addLayout(header_layout)

        card_layout.addWidget(_detail_label(
            tr(
                "refinery.job.detail",
                job_id=job_id,
                name=job["refinery_name"],
            )
        ))
        method = (job.get("refinery_method") or "").strip()
        if method:
            card_layout.addWidget(_detail_label(
                tr("refinery.job.method", method=method)
            ))
        cost = job.get("cost", 0) or 0
        payer = (job.get("cost_paid_by") or "").strip()

        if cost > 0 and payer:
            cost_line = tr(
                "refinery.job.cost_paid",
                cost=format_number(cost),
                payer=payer,
            )
        else:
            cost_line = tr(
                "refinery.job.cost",
                cost=format_number(cost),
            )

        card_layout.addWidget(_detail_label(cost_line))
        card_layout.addWidget(_detail_label(
            tr("refinery.job.created_by", name=job["created_by"])
        ))

        for item in job["items"]:
            card_layout.addWidget(_detail_label(
                tr(
                    "refinery.job.batch_line",
                    batch_id=item["batch_id"],
                    material=material_label(item["input_material"]),
                    quantity=format_number(item["input_quantity"]),
                )
            ))

        card_layout.addWidget(_detail_label(
            tr(
                "refinery.job.ready_at",
                time=format_datetime(ready_time),
            )
        ))
        card_layout.addWidget(_detail_label(
            tr(
                "refinery.job.remaining",
                remaining=remaining_text,
            )
        ))

        cancel_button = _secondary_button(tr("refinery.button.cancel"))
        cancel_button.clicked.connect(
            lambda checked=False, jid=job_id:
            self.cancel_job(jid)
        )
        card_layout.addWidget(cancel_button)

        if is_ready:
            collect_button = primary_button(tr("refinery.button.complete"))
            collect_button.clicked.connect(
                lambda checked=False, jid=job_id:
                self.complete_job(jid)
            )
            card_layout.addWidget(collect_button)

        card.setLayout(card_layout)
        self.jobs_container.addWidget(card)

    def create_job(self):
        batch_data = self.batch_combo.currentData()
        batch_id = None

        if isinstance(batch_data, dict):
            batch_id = batch_data.get("batch_id")
        else:
            batch_id = batch_data

        if batch_id is None:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("refinery.msg.no_batch"),
            )
            return

        refinery_name = (
            self.refinery_name_input.text().strip()
        )

        if not refinery_name:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("refinery.msg.no_station"),
            )
            return

        input_scu = parse_number_de(self.input_scu.text())
        hours = parse_int_de(self.hours_input.text(), default=0)
        minutes = parse_int_de(self.minutes_input.text(), default=0)
        cost = parse_number_de(
            self.refinery_cost_input.text(),
            default=0,
        )
        if input_scu is None or hours is None or minutes is None or cost is None:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("refinery.msg.invalid_values"),
            )
            return

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
            self.db.create_refinery_job_from_batches(
                refinery_name,
                ready_time.strftime(DB_DATETIME_FMT),
                [{
                    "batch_id": batch_id,
                    "input_quantity": input_scu,
                }],
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

        self.input_scu.clear()
        self.hours_input.clear()
        self.minutes_input.clear()
        self.notes_input.clear()
        self.refinery_cost_input.clear()
        self.refinery_cost_paid_by.setCurrentIndex(0)
        self.ready_info_label.setText(_status_panel())

        self.load_data()
        self._refresh_dashboard()

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

        output_cm, ok = MobiglasDoubleInputDialog.get_double(
            self,
            tr("refinery.complete.dialog.title"),
            tr("refinery.complete.dialog.field"),
            0,
            0,
            100000,
            1,
            hint_text=hint_text,
            field_tooltip=tr("refinery.complete.dialog.tooltip"),
        )

        if not ok:
            return

        try:
            result = self.db.complete_refinery_job(
                job_id,
                output_cm,
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
                quantity=format_number(result["output_quantity"], 1),
                material=material_label(REFINERY_OUTPUT_CODE),
                yield_pct=format_number(result["yield_percent"], 1),
            ),
        )

        self.load_data()
        self._refresh_dashboard()

    def _selected_history_job_id(self):
        row = self.history_table.currentRow()

        if row < 0:
            return None

        item = self.history_table.item(row, 0)

        if not item:
            return None

        return int(item.text().lstrip("#"))

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

        QMessageBox.information(
            self,
            tr("refinery.msg.cancelled.title"),
            tr(
                "refinery.msg.cancelled.message",
                job_id=job_id,
            ),
        )

    def delete_selected_job(self):
        job_id = self._selected_history_job_id()

        if job_id is None:
            QMessageBox.warning(
                self,
                tr("common.hint"),
                tr("refinery.msg.no_selection"),
            )
            return

        answer = QMessageBox.question(
            self,
            tr("refinery.msg.delete_confirm.title"),
            tr(
                "refinery.msg.delete_confirm.message",
                job_id=job_id,
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        try:
            self.db.delete_refinery_job(job_id)
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
                tr("refinery.msg.delete_failed", error=error),
            )
            return

        self.load_data()
        self._refresh_dashboard()

        QMessageBox.information(
            self,
            tr("refinery.msg.deleted.title"),
            tr(
                "refinery.msg.deleted.message",
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
