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
from config.strings_de import format_number_de, parse_int_de, parse_number_de
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


class RefineryPage(QWidget):

    def __init__(self):
        super().__init__()

        self.db = get_database()

        content, layout = page_content_widget()

        layout.addWidget(page_title("RAFFINERIE"))
        layout.addWidget(
            section_accent("◆ VERFÜGBARE MATERIAL-BATCHES")
        )

        self.batches_table = QTableWidget()
        self.batches_table.setColumnCount(5)
        self.batches_table.setHorizontalHeaderLabels([
            "Batch",
            "Material",
            "Verfügbar (SCU)",
            "Original (SCU)",
            "Sitzung",
        ])
        configure_mobiglas_table(
            self.batches_table,
            "dataTable",
        )
        self.batches_table.setMinimumHeight(140)
        layout.addWidget(self.batches_table)

        form_panel, form_layout = info_panel()
        form_layout.addWidget(
            subsection_title("◆ RAFFINERIEAUFTRAG ANLEGEN")
        )

        self.refinery_name_input = QLineEdit()
        self.refinery_name_input.setPlaceholderText(
            "z.B. Orison"
        )
        self.refinery_name_input.setText("Orison")

        self.refinery_method_combo = QComboBox()
        self.refinery_method_combo.addItem("— Methode wählen —", "")
        for method in REFINERY_METHODS:
            self.refinery_method_combo.addItem(method, method)

        self.refinery_cost_input = QLineEdit()
        self.refinery_cost_input.setPlaceholderText(
            "Kosten in aUEC (beim Anlegen)"
        )

        self.refinery_cost_paid_by = QComboBox()
        self.refinery_cost_paid_by.addItem(
            "— Bitte wählen —"
        )

        self.batch_combo = QComboBox()

        self.input_scu = QLineEdit()
        self.input_scu.setPlaceholderText(
            "Eingabemenge in SCU"
        )

        self.hours_input = QLineEdit()
        self.hours_input.setPlaceholderText("Stunden")

        self.minutes_input = QLineEdit()
        self.minutes_input.setPlaceholderText("Minuten")

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText(
            "Notiz (optional)"
        )

        self.ready_info_label = QLabel(
            "● RAFFINERIE STATUS\n\n"
            "Fertig am:\n-\n\n"
            "Verbleibend:\n-\n\n"
            "Status:\nWARTET AUF EINGABE"
        )
        self.ready_info_label.setObjectName(
            "refineryStatusPanel"
        )

        self.create_button = primary_button(
            "Auftrag erstellen"
        )

        add_form_field(
            form_layout,
            "Raffinerie / Station",
            self.refinery_name_input,
        )
        add_form_field(
            form_layout,
            "Raffinerie-Methode",
            self.refinery_method_combo,
        )
        add_form_field(
            form_layout,
            "Kosten (aUEC)",
            self.refinery_cost_input,
        )
        add_form_field(
            form_layout,
            "Bezahlt von",
            self.refinery_cost_paid_by,
        )
        add_form_field(
            form_layout,
            "Material-Batch",
            self.batch_combo,
        )
        add_form_field(
            form_layout,
            "Eingabe (SCU)",
            self.input_scu,
        )

        time_row = QHBoxLayout()
        time_row.setSpacing(12)

        hours_col = QVBoxLayout()
        hours_label = QLabel("Stunden")
        hours_label.setObjectName("formLabel")
        hours_col.addWidget(hours_label)
        hours_col.addWidget(self.hours_input)

        minutes_col = QVBoxLayout()
        minutes_label = QLabel("Minuten")
        minutes_label.setObjectName("formLabel")
        minutes_col.addWidget(minutes_label)
        minutes_col.addWidget(self.minutes_input)

        time_row.addLayout(hours_col, 1)
        time_row.addLayout(minutes_col, 1)
        form_layout.addLayout(time_row)

        add_form_field(
            form_layout,
            "Notiz",
            self.notes_input,
        )

        form_layout.addWidget(self.ready_info_label)
        form_layout.addWidget(self.create_button)
        layout.addWidget(form_panel)

        layout.addWidget(
            section_accent("◆ AKTIVE AUFTRÄGE")
        )

        self.jobs_container = QVBoxLayout()
        self.jobs_container.setSpacing(10)
        jobs_widget = QWidget()
        jobs_widget.setLayout(self.jobs_container)
        layout.addWidget(jobs_widget)

        layout.addWidget(
            section_accent("◆ RAFFINERIE-HISTORIE")
        )

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(9)
        self.history_table.setHorizontalHeaderLabels([
            "Nr.",
            "Station",
            "Methode",
            "Status",
            "Input",
            "CM Raf Output",
            "Ausbeute",
            "Kosten",
            "Erstellt von",
        ])
        configure_mobiglas_table(
            self.history_table,
            "historyTable",
        )
        self.history_table.setMinimumHeight(180)

        history_actions = QHBoxLayout()
        history_actions.setSpacing(12)
        self.delete_job_button = _secondary_button(
            "Auftrag löschen"
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
                QTableWidgetItem(format_number_de(remaining, 1)),
            )
            self.batches_table.setItem(
                row,
                3,
                QTableWidgetItem(format_number_de(original, 1)),
            )
            self.batches_table.setItem(
                row,
                4,
                QTableWidgetItem(session_name),
            )

            combo_text = (
                f"#{batch_id} | {label} | "
                f"{format_number_de(remaining, 1)} SCU"
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
            "— Bitte wählen —"
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
                f"{item['input_quantity']:g} SCU "
                f"{material_label(item['input_material'])} "
                f"(Batch #{item['batch_id']})"
                for item in job["items"]
            )
            output_scu = job.get("cm_raf_output") or job["total_output"]
            output_text = (
                f"{output_scu:g} SCU "
                f"{material_label(REFINERY_OUTPUT_CODE)}"
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
                yield_text = f"{format_number_de(yield_pct, 1)} %"

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
                QTableWidgetItem(job["status"]),
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
            cost_text = f"{format_number_de(cost)} aUEC"

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
            self.ready_info_label.setText(
                "● RAFFINERIE STATUS\n\n"
                "Fertig am:\n-\n\n"
                "Verbleibend:\n-\n\n"
                "Status:\nWARTET AUF EINGABE"
            )
            return

        ready_time = (
            datetime.now()
            + timedelta(hours=hours, minutes=minutes)
        )

        self.ready_info_label.setText(
            f"● RAFFINERIE STATUS\n\n"
            f"Fertig am:\n"
            f"{format_datetime(ready_time)}\n\n"
            f"Verbleibend:\n"
            f"{hours}h {minutes}m\n\n"
            f"Status:\nIN BEARBEITUNG"
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
                    "Keine aktiven Raffinerieaufträge.",
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
            status_text = "ABHOLBEREIT"
            status_icon = (
                "assets/images/icons/ready.svg"
            )
            remaining_text = "Fertig"
        elif remaining_minutes <= 60:
            is_ready = False
            status_text = "ENDPHASE"
            status_icon = (
                "assets/images/icons/processing.svg"
            )
            remaining_text = f"{remaining_minutes} Min"
        else:
            is_ready = False
            hours = remaining_minutes // 60
            minutes = remaining_minutes % 60
            status_text = "IN BEARBEITUNG"
            status_icon = (
                "assets/images/icons/processing.svg"
            )
            remaining_text = f"{hours}h {minutes}m"

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
            f"Auftrag #{job_id} | {job['refinery_name']}"
        ))
        method = (job.get("refinery_method") or "").strip()
        if method:
            card_layout.addWidget(_detail_label(
                f"Methode: {method}"
            ))
        cost = job.get("cost", 0) or 0
        payer = (job.get("cost_paid_by") or "").strip()
        cost_line = f"Kosten: {format_number_de(cost)} aUEC"

        if cost > 0 and payer:
            cost_line = f"{cost_line} · bezahlt von {payer}"

        card_layout.addWidget(_detail_label(cost_line))
        card_layout.addWidget(_detail_label(
            f"Erstellt von: {job['created_by']}"
        ))

        for item in job["items"]:
            card_layout.addWidget(_detail_label(
                f"Batch #{item['batch_id']} | "
                f"{material_label(item['input_material'])} | "
                f"Input: {format_number_de(item['input_quantity'])} SCU"
            ))

        card_layout.addWidget(_detail_label(
            f"Fertig: {format_datetime(ready_time)}"
        ))
        card_layout.addWidget(_detail_label(
            f"Verbleibend: {remaining_text}"
        ))

        cancel_button = _secondary_button("Stornieren")
        cancel_button.clicked.connect(
            lambda checked=False, jid=job_id:
            self.cancel_job(jid)
        )
        card_layout.addWidget(cancel_button)

        if is_ready:
            collect_button = primary_button("ABSCHLIESSEN")
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
                "Fehler",
                "Kein Material-Batch verfügbar.",
            )
            return

        refinery_name = (
            self.refinery_name_input.text().strip()
        )

        if not refinery_name:
            QMessageBox.warning(
                self,
                "Fehler",
                "Bitte Raffinerie/Station angeben.",
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
                "Fehler",
                "Bitte gültige Werte eingeben.",
            )
            return

        if cost < 0:
            QMessageBox.warning(
                self,
                "Fehler",
                "Kosten dürfen nicht negativ sein.",
            )
            return

        if cost > 0:
            if self.refinery_cost_paid_by.currentIndex() <= 0:
                QMessageBox.warning(
                    self,
                    "Fehler",
                    "Bitte angeben, wer die "
                    "Raffinerie-Kosten bezahlt hat.",
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
                "Fehler",
                str(error),
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Auftrag konnte nicht erstellt werden:\n\n{error}",
            )
            return

        self.input_scu.clear()
        self.hours_input.clear()
        self.minutes_input.clear()
        self.notes_input.clear()
        self.refinery_cost_input.clear()
        self.refinery_cost_paid_by.setCurrentIndex(0)
        self.ready_info_label.setText(
            "● RAFFINERIE STATUS\n\n"
            "Fertig am:\n-\n\n"
            "Verbleibend:\n-\n\n"
            "Status:\nWARTET AUF EINGABE"
        )

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
                hint_text = (
                    f"Dein bisheriger Durchschnitt für "
                    f"{material_label(material_code)}: "
                    f"{format_number_de(stats['efficiency_percent'], 1)} % "
                    f"({stats['job_count']} Aufträge)"
                )

        output_cm, ok = MobiglasDoubleInputDialog.get_double(
            self,
            "Raffinerie abschließen",
            "CM Raf Output (SCU)",
            0,
            0,
            100000,
            1,
            hint_text=hint_text,
            field_tooltip=(
                "Tatsächliche Menge an raffiniertem Construction "
                "Material nach Abschluss des Raffinerieauftrags."
            ),
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
                "Fehler",
                str(error),
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Abschluss fehlgeschlagen:\n\n{error}",
            )
            return

        QMessageBox.information(
            self,
            "Abgeschlossen",
            f"{format_number_de(result['output_quantity'], 1)} SCU "
            f"{material_label(REFINERY_OUTPUT_CODE)} ins Lager "
            f"gebucht (Ausbeute: {format_number_de(result['yield_percent'], 1)} %).",
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
            "Auftrag stornieren",
            f"Raffinerieauftrag #{job_id} stornieren?\n\n"
            "Reserviertes Material wird wieder "
            "dem Batch gutgeschrieben.",
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
                "Nicht möglich",
                str(error),
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Stornierung fehlgeschlagen:\n\n{error}",
            )
            return

        self.load_data()
        self._refresh_dashboard()

        QMessageBox.information(
            self,
            "Storniert",
            f"Auftrag #{job_id} wurde storniert.",
        )

    def delete_selected_job(self):
        job_id = self._selected_history_job_id()

        if job_id is None:
            QMessageBox.warning(
                self,
                "Hinweis",
                "Bitte zuerst einen Auftrag in der "
                "Historie auswählen.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Auftrag löschen",
            f"Abgeschlossenen Auftrag #{job_id} löschen?\n\n"
            "CM wird aus dem Lager entfernt und "
            "Rohmaterial den Batches zurückgebucht. "
            "Nur möglich, wenn das CM nicht verkauft wurde.",
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
                "Nicht möglich",
                str(error),
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Löschen fehlgeschlagen:\n\n{error}",
            )
            return

        self.load_data()
        self._refresh_dashboard()

        QMessageBox.information(
            self,
            "Gelöscht",
            f"Auftrag #{job_id} wurde gelöscht.",
        )

    def _refresh_dashboard(self):
        main_window = self.window()

        if hasattr(
            main_window,
            "dashboard_page"
        ):
            main_window.dashboard_page.refresh_dashboard()
