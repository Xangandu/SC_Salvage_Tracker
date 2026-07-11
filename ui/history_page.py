from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QMessageBox,
)

from database.access import get_database
from config.dates import format_date
from config.materials import (
    REFINERY_OUTPUT_CODE,
    material_label,
)
from config.refinery_methods import display_refinery_method
from config.i18n import tr, format_number, status_label
from config.permissions import (
    apply_widget_permissions,
    has_permission,
    PERM_PAYOUTS_MANAGE,
    PERM_REFINERY_MANAGE,
)
from ui.table_utils import (
    configure_mobiglas_table,
    finalize_table_columns,
)
from ui.page_layout import (
    build_page_scroll,
    page_content_widget,
    page_title,
    section_accent,
    page_panel,
    empty_info_panel,
    hud_divider,
)


def _secondary_button(text):
    button = QPushButton(text)
    button.setObjectName("secondaryAction")
    return button


def _refinery_job_status(status: str) -> str:
    return tr(f"refinery.job_status.{status}", default=status)


class HistoryPage(QWidget):

    def __init__(self):
        super().__init__()

        content, layout = page_content_widget()
        layout.addWidget(page_title(tr("history.title")))

        layout.addWidget(
            section_accent(tr("history.section.sessions"))
        )
        layout.addLayout(hud_divider())

        sessions_panel, sessions_layout = page_panel()
        sessions_layout.setContentsMargins(12, 12, 12, 12)

        self.sessions_table = QTableWidget()
        self.sessions_table.setColumnCount(6)
        self.sessions_table.setHorizontalHeaderLabels([
            tr("history.session.no"),
            tr("history.session.ship"),
            tr("history.session.status"),
            tr("history.session.ended"),
            tr("history.session.mission_costs"),
            tr("history.session.total_costs"),
        ])
        configure_mobiglas_table(
            self.sessions_table,
            "dataTable",
        )
        self.sessions_table.setMinimumHeight(220)

        self.sessions_empty_panel = empty_info_panel(
            tr("history.sessions.empty"),
            "assets/images/icons/info.svg",
        )

        sessions_layout.addWidget(self.sessions_table)
        sessions_layout.addWidget(self.sessions_empty_panel)
        self.sessions_empty_panel.hide()
        layout.addWidget(sessions_panel)

        layout.addWidget(
            section_accent(tr("history.section.refinery"))
        )
        layout.addLayout(hud_divider())

        refinery_panel, refinery_layout = page_panel()
        refinery_layout.setContentsMargins(12, 12, 12, 12)

        self.refinery_history_table = QTableWidget()
        self.refinery_history_table.setColumnCount(9)
        self.refinery_history_table.setHorizontalHeaderLabels([
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
            self.refinery_history_table,
            "historyTable",
        )
        self.refinery_history_table.setMinimumHeight(180)

        self.refinery_history_empty_panel = empty_info_panel(
            tr("history.refinery.empty"),
            "assets/images/icons/info.svg",
        )

        self.delete_refinery_job_button = _secondary_button(
            tr("refinery.button.delete")
        )
        self.delete_refinery_job_button.clicked.connect(
            self.delete_selected_refinery_job
        )

        refinery_actions = QHBoxLayout()
        refinery_actions.setSpacing(12)
        refinery_actions.addWidget(self.delete_refinery_job_button)
        refinery_actions.addStretch()

        refinery_layout.addWidget(self.refinery_history_table)
        refinery_layout.addLayout(refinery_actions)
        refinery_layout.addWidget(self.refinery_history_empty_panel)
        self.refinery_history_empty_panel.hide()
        layout.addWidget(refinery_panel)

        layout.addWidget(
            section_accent(tr("history.section.sales"))
        )
        layout.addLayout(hud_divider())

        table_panel, table_layout = page_panel()
        table_layout.setContentsMargins(12, 12, 12, 12)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            tr("sales.history.no"),
            tr("sales.history.date"),
            tr("sales.history.location"),
            tr("sales.history.materials"),
            tr("sales.history.revenue"),
            tr("sales.history.seller"),
        ])
        configure_mobiglas_table(
            self.history_table,
            "dataTable",
        )
        self.history_table.setMinimumHeight(280)

        self.history_empty_panel = empty_info_panel(
            tr("history.empty"),
            "assets/images/icons/info.svg",
        )

        table_layout.addWidget(self.history_table)
        table_layout.addWidget(self.history_empty_panel)
        self.history_empty_panel.hide()
        layout.addWidget(table_panel)

        layout.addWidget(
            section_accent(tr("history.section.all_payouts"))
        )
        layout.addLayout(hud_divider())

        payouts_panel, payouts_layout = page_panel()
        payouts_layout.setContentsMargins(12, 12, 12, 12)

        self.payouts_table = QTableWidget()
        self.payouts_table.setColumnCount(6)
        self.payouts_table.setHorizontalHeaderLabels([
            tr("payout.table.no"),
            tr("payout.table.sale"),
            tr("payout.table.date"),
            tr("payout.table.location"),
            tr("payout.table.paid_out"),
            tr("payout.table.created_by"),
        ])
        configure_mobiglas_table(
            self.payouts_table,
            "historyTable",
        )
        self.payouts_table.setMinimumHeight(180)

        self.payouts_empty_panel = empty_info_panel(
            tr("payout.history.empty"),
            "assets/images/icons/info.svg",
        )

        self.void_payout_button = _secondary_button(
            tr("payout.button.void")
        )
        self.void_payout_button.clicked.connect(
            self.void_selected_payout
        )

        payouts_actions = QHBoxLayout()
        payouts_actions.setSpacing(12)
        payouts_actions.addWidget(self.void_payout_button)
        payouts_actions.addStretch()

        payouts_layout.addWidget(self.payouts_table)
        payouts_layout.addLayout(payouts_actions)
        payouts_layout.addWidget(self.payouts_empty_panel)
        self.payouts_empty_panel.hide()
        layout.addWidget(payouts_panel)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(build_page_scroll(content))

        self.load_history()

    def apply_permissions(self, user, page_name="history"):
        apply_widget_permissions(self, user, page_name)
        self.void_payout_button.setEnabled(
            has_permission(PERM_PAYOUTS_MANAGE, user)
        )
        self.delete_refinery_job_button.setEnabled(
            has_permission(PERM_REFINERY_MANAGE, user)
        )

    def refresh_history(self):
        self.load_history()

    def _load_sessions_history(self, db):
        sessions = db.get_archived_sessions()
        has_sessions = len(sessions) > 0

        self.sessions_table.setVisible(has_sessions)
        self.sessions_empty_panel.setVisible(not has_sessions)
        self.sessions_table.setRowCount(len(sessions))

        for row, session in enumerate(sessions):
            mission_text = (
                "\n".join(session["mission_lines"])
                if session["mission_lines"]
                else tr("history.session.no_missions")
            )
            ended = session.get("end_time") or session.get(
                "start_time"
            )

            self.sessions_table.setItem(
                row,
                0,
                QTableWidgetItem(f"#{session['id']}"),
            )
            self.sessions_table.setItem(
                row,
                1,
                QTableWidgetItem(session.get("name") or "—"),
            )
            self.sessions_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    status_label(session.get("status") or "")
                ),
            )
            self.sessions_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    format_date(ended) if ended else "—"
                ),
            )
            self.sessions_table.setItem(
                row,
                4,
                QTableWidgetItem(mission_text),
            )
            self.sessions_table.setItem(
                row,
                5,
                QTableWidgetItem(
                    tr(
                        "history.session.costs_total",
                        mission_total=format_number(
                            session.get("mission_total") or 0
                        ),
                        session_total=format_number(
                            session.get("session_total") or 0
                        ),
                    )
                ),
            )

        finalize_table_columns(
            self.sessions_table,
            stretch_column=4,
        )

    def _load_sales_history(self, db):
        sales = db.get_sales_history()
        has_sales = len(sales) > 0

        self.history_table.setVisible(has_sales)
        self.history_empty_panel.setVisible(not has_sales)
        self.history_table.setRowCount(len(sales))

        for row, sale in enumerate(sales):
            items_text = ", ".join(
                tr(
                    "sales.history.item_line",
                    quantity=format_number(item["quantity"], 0),
                    material=material_label(item["material_code"]),
                )
                for item in sale["items"]
            )

            self.history_table.setItem(
                row,
                0,
                QTableWidgetItem(f"#{sale['id']}"),
            )
            self.history_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    format_date(sale["sale_date"])
                ),
            )
            self.history_table.setItem(
                row,
                2,
                QTableWidgetItem(sale["location"]),
            )
            self.history_table.setItem(
                row,
                3,
                QTableWidgetItem(items_text or "—"),
            )
            self.history_table.setItem(
                row,
                4,
                QTableWidgetItem(
                    f"{format_number(sale['total_amount'])} aUEC"
                ),
            )
            self.history_table.setItem(
                row,
                5,
                QTableWidgetItem(sale["created_by"]),
            )

        finalize_table_columns(
            self.history_table,
            stretch_column=3,
        )

    def _load_payouts_history(self, db):
        payouts = db.get_payout_history()
        has_payouts = len(payouts) > 0

        self.payouts_table.setVisible(has_payouts)
        self.payouts_empty_panel.setVisible(not has_payouts)
        self.payouts_table.setRowCount(len(payouts))

        for row, payout in enumerate(payouts):
            self.payouts_table.setItem(
                row,
                0,
                QTableWidgetItem(f"#{payout['id']}"),
            )
            self.payouts_table.setItem(
                row,
                1,
                QTableWidgetItem(f"#{payout['sale_id']}"),
            )
            self.payouts_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    format_date(payout["sale_date"])
                ),
            )
            self.payouts_table.setItem(
                row,
                3,
                QTableWidgetItem(payout["location"]),
            )
            self.payouts_table.setItem(
                row,
                4,
                QTableWidgetItem(
                    f"{format_number(payout['payout_total'])} aUEC"
                ),
            )
            self.payouts_table.setItem(
                row,
                5,
                QTableWidgetItem(payout["created_by"]),
            )

        finalize_table_columns(
            self.payouts_table,
            stretch_column=3,
        )

    def _load_refinery_history(self, db):
        history = db.get_refinery_history()
        has_history = len(history) > 0

        self.refinery_history_table.setVisible(has_history)
        self.refinery_history_empty_panel.setVisible(not has_history)
        self.refinery_history_table.setRowCount(len(history))

        for row, job in enumerate(history):
            input_text = ", ".join(
                tr(
                    "refinery.history.input_line",
                    quantity=format_number(item["input_quantity"], 0),
                    material=material_label(item["input_material"]),
                    batch_id=item["batch_id"],
                )
                for item in job["items"]
            )
            output_scu = job.get("cm_raf_output") or job["total_output"]
            output_text = (
                tr(
                    "refinery.history.output_line",
                    quantity=format_number(output_scu, 0),
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

            self.refinery_history_table.setItem(
                row,
                0,
                QTableWidgetItem(f"#{job['id']}"),
            )
            self.refinery_history_table.setItem(
                row,
                1,
                QTableWidgetItem(job["refinery_name"]),
            )
            self.refinery_history_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    display_refinery_method(
                        job.get("refinery_method") or ""
                    ) or "—"
                ),
            )
            self.refinery_history_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    _refinery_job_status(job["status"])
                ),
            )
            self.refinery_history_table.setItem(
                row,
                4,
                QTableWidgetItem(input_text),
            )
            self.refinery_history_table.setItem(
                row,
                5,
                QTableWidgetItem(output_text),
            )
            self.refinery_history_table.setItem(
                row,
                6,
                QTableWidgetItem(yield_text),
            )
            cost = job.get("cost", 0) or 0
            payer = (job.get("cost_paid_by") or "").strip()
            cost_text = f"{format_number(cost)} aUEC"

            if cost > 0 and payer:
                cost_text = f"{cost_text} ({payer})"

            self.refinery_history_table.setItem(
                row,
                7,
                QTableWidgetItem(cost_text),
            )
            self.refinery_history_table.setItem(
                row,
                8,
                QTableWidgetItem(job["created_by"]),
            )

        finalize_table_columns(
            self.refinery_history_table,
            stretch_column=4,
        )

    def load_history(self):
        db = get_database()
        self._load_sessions_history(db)
        self._load_refinery_history(db)
        self._load_sales_history(db)
        self._load_payouts_history(db)

    def _selected_payout_id(self):
        row = self.payouts_table.currentRow()
        if row < 0:
            return None
        item = self.payouts_table.item(row, 0)
        if not item:
            return None
        return int(item.text().lstrip("#"))

    def void_selected_payout(self):
        payout_id = self._selected_payout_id()
        if payout_id is None:
            QMessageBox.warning(
                self,
                tr("common.hint"),
                tr("payout.msg.no_selection"),
            )
            return

        answer = QMessageBox.question(
            self,
            tr("payout.msg.void_confirm.title"),
            tr(
                "payout.msg.void_confirm.message",
                payout_id=payout_id,
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        db = get_database()
        try:
            db.void_payout(payout_id)
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
                tr("payout.msg.void_failed", error=error),
            )
            return

        self.load_history()

        main_window = self.window()
        if hasattr(main_window, "statistics_page"):
            main_window.statistics_page.refresh_data()
        if hasattr(main_window, "refresh_all"):
            main_window.refresh_all()
        elif hasattr(main_window, "dashboard_page"):
            main_window.dashboard_page.refresh_dashboard()
        if hasattr(main_window, "session_page"):
            main_window.session_page.refresh_session()

        QMessageBox.information(
            self,
            tr("payout.msg.voided.title"),
            tr(
                "payout.msg.voided.message",
                payout_id=payout_id,
            ),
        )

    def _selected_refinery_job_id(self):
        row = self.refinery_history_table.currentRow()
        if row < 0:
            return None
        item = self.refinery_history_table.item(row, 0)
        if not item:
            return None
        return int(item.text().lstrip("#"))

    def delete_selected_refinery_job(self):
        job_id = self._selected_refinery_job_id()
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

        db = get_database()
        try:
            db.delete_refinery_job(job_id)
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

        self.load_history()

        main_window = self.window()
        if hasattr(main_window, "refinery_page"):
            main_window.refinery_page.load_data()
        if hasattr(main_window, "refresh_all"):
            main_window.refresh_all()
        elif hasattr(main_window, "dashboard_page"):
            main_window.dashboard_page.refresh_dashboard()

        QMessageBox.information(
            self,
            tr("refinery.msg.deleted.title"),
            tr(
                "refinery.msg.deleted.message",
                job_id=job_id,
            ),
        )
