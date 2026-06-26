from PySide6.QtCore import Qt
from PySide6.QtWidgets import (

    QWidget,

    QLabel,

    QVBoxLayout,

    QHBoxLayout,

    QFrame,

    QTableWidget,

    QTableWidgetItem,

    QComboBox,

    QLineEdit,

    QMessageBox,

    QPushButton,

)



from database.access import get_database
from database.payout_repository import (
    UNASSIGNED_COST_PAYERS,
)
from config.dates import format_date
from config.i18n import tr, format_number
from config.strings_de import parse_number_de

from config.permissions import apply_widget_permissions

from ui.table_utils import (
    configure_mobiglas_table,
    configure_editable_table,
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

    page_panel,

    primary_button,

    empty_info_panel,

    hud_divider,

)



def _secondary_button(text):

    button = QPushButton(text)

    button.setObjectName("secondaryAction")

    return button



def _calc_placeholder():
    return tr("payout.calc.placeholder")


class StatisticsPage(QWidget):



    def __init__(self):

        super().__init__()



        self.db = get_database()

        self.current_proposal = None
        self._pending_unassigned_payers = []



        content, layout = page_content_widget()



        layout.addWidget(page_title(tr("payout.title")))

        layout.addWidget(
            section_accent(tr("payout.section.main"))
        )

        layout.addLayout(hud_divider())



        summary_panel = QFrame()

        summary_panel.setObjectName("financeSummaryPanel")

        summary_layout = QVBoxLayout(summary_panel)

        summary_layout.setSpacing(8)



        summary_layout.addWidget(

            subsection_title(tr("payout.section.summary"))

        )

        summary_layout.addLayout(hud_divider())



        self.summary_label = QLabel(

            tr(
                "payout.summary",
                count=0,
                total=format_number(0),
            )

        )

        self.summary_label.setObjectName("statValue")

        summary_layout.addWidget(self.summary_label)

        layout.addWidget(summary_panel)



        layout.addWidget(

            section_accent(tr("payout.section.unpaid"))

        )

        layout.addLayout(hud_divider())



        unpaid_panel, unpaid_layout = page_panel()

        unpaid_layout.setContentsMargins(12, 12, 12, 12)



        self.unpaid_table = QTableWidget()

        self.unpaid_table.setColumnCount(5)

        self.unpaid_table.setHorizontalHeaderLabels([

            tr("payout.table.no"),

            tr("payout.table.date"),

            tr("payout.table.location"),

            tr("payout.table.revenue"),

            tr("payout.table.seller"),

        ])

        configure_mobiglas_table(

            self.unpaid_table,

            "dataTable",

        )

        self.unpaid_table.setMinimumHeight(140)

        self.unpaid_table.itemSelectionChanged.connect(

            self.on_sale_selected

        )

        self.unpaid_empty_panel = empty_info_panel(
            tr("payout.unpaid.empty"),
            "assets/images/icons/info.svg",
        )

        unpaid_layout.addWidget(self.unpaid_table)
        unpaid_layout.addWidget(self.unpaid_empty_panel)
        self.unpaid_empty_panel.hide()
        layout.addWidget(unpaid_panel)

        payout_panel, payout_layout = info_panel()
        payout_layout.addWidget(
            subsection_title(tr("payout.section.calculate"))
        )
        payout_layout.addLayout(hud_divider())



        self.sale_combo = QComboBox()



        self.calc_info_label = QLabel(

            _calc_placeholder()

        )

        self.calc_info_label.setObjectName(

            "payoutStatusPanel"

        )

        self.calc_info_label.setWordWrap(True)



        self.cost_payer_panel = QWidget()

        cost_payer_row = QHBoxLayout(self.cost_payer_panel)

        cost_payer_row.setContentsMargins(0, 0, 0, 0)

        cost_payer_row.setSpacing(12)



        cost_payer_label = QLabel(

            tr("payout.label.cost_payer")

        )

        cost_payer_label.setObjectName("formLabel")

        self.cost_payer_combo = QComboBox()

        self.cost_payer_combo.currentIndexChanged.connect(

            self._on_cost_payer_changed

        )

        cost_payer_row.addWidget(cost_payer_label)

        cost_payer_row.addWidget(

            self.cost_payer_combo,

            1,

        )

        self.cost_payer_panel.hide()



        self.payout_table = QTableWidget()

        self.payout_table.setColumnCount(2)

        self.payout_table.setHorizontalHeaderLabels([

            tr("payout.table.crew_member"),

            tr("payout.table.amount"),

        ])

        configure_editable_table(

            self.payout_table,

            "editableTable",

        )

        self.payout_table.setMinimumHeight(120)

        finalize_table_columns(

            self.payout_table,

            stretch_column=1,

        )



        self.notes_input = QLineEdit()

        self.notes_input.setPlaceholderText(

            tr("payout.placeholder.notes")

        )



        self.save_button = primary_button(
            tr("payout.button.save")
        )



        add_form_field(

            payout_layout,

            tr("payout.label.sale"),

            self.sale_combo,

        )

        add_form_field(

            payout_layout,

            tr("payout.label.notes"),

            self.notes_input,

        )



        payout_layout.addWidget(self.calc_info_label)

        payout_layout.addWidget(self.cost_payer_panel)

        payout_layout.addWidget(self.payout_table)



        button_row = QHBoxLayout()

        button_row.setSpacing(12)

        button_row.addWidget(self.save_button)

        button_row.addStretch()

        payout_layout.addLayout(button_row)



        layout.addWidget(payout_panel)



        layout.addWidget(

            section_accent(tr("payout.section.crew_totals"))

        )

        layout.addLayout(hud_divider())



        crew_panel, crew_layout = page_panel()

        crew_layout.setContentsMargins(12, 12, 12, 12)



        self.crew_totals_table = QTableWidget()

        self.crew_totals_table.setColumnCount(2)

        self.crew_totals_table.setHorizontalHeaderLabels([

            tr("payout.table.crew_member"),

            tr("payout.table.total_received"),

        ])

        configure_mobiglas_table(

            self.crew_totals_table,

            "dataTable",

            selectable=False,

        )

        self.crew_totals_table.setMinimumHeight(120)



        self.crew_empty_panel = empty_info_panel(

            tr("payout.crew.empty"),

            "assets/images/icons/info.svg",

        )



        crew_layout.addWidget(self.crew_totals_table)

        crew_layout.addWidget(self.crew_empty_panel)

        self.crew_empty_panel.hide()

        layout.addWidget(crew_panel)



        layout.addWidget(

            section_accent(tr("payout.section.history"))

        )

        layout.addLayout(hud_divider())



        history_panel, history_layout = page_panel()

        history_layout.setContentsMargins(12, 12, 12, 12)



        self.history_table = QTableWidget()

        self.history_table.setColumnCount(6)

        self.history_table.setHorizontalHeaderLabels([

            tr("payout.table.no"),

            tr("payout.table.sale"),

            tr("payout.table.date"),

            tr("payout.table.location"),

            tr("payout.table.paid_out"),

            tr("payout.table.created_by"),

        ])

        configure_mobiglas_table(

            self.history_table,

            "historyTable",

        )

        self.history_table.setMinimumHeight(180)



        self.payout_history_empty_panel = empty_info_panel(

            tr("payout.history.empty"),

            "assets/images/icons/info.svg",

        )



        self.void_payout_button = _secondary_button(

            tr("payout.button.void")

        )

        self.void_payout_button.clicked.connect(

            self.void_selected_payout

        )



        history_actions = QHBoxLayout()

        history_actions.setSpacing(12)

        history_actions.addWidget(self.void_payout_button)

        history_actions.addStretch()



        history_layout.addWidget(self.history_table)

        history_layout.addLayout(history_actions)

        history_layout.addWidget(self.payout_history_empty_panel)

        self.payout_history_empty_panel.hide()

        layout.addWidget(history_panel)



        layout.addStretch()



        outer = QVBoxLayout(self)

        outer.setContentsMargins(0, 0, 0, 0)

        outer.addWidget(build_page_scroll(content))



        self.save_button.clicked.connect(

            self.save_payout

        )

        self.sale_combo.currentIndexChanged.connect(

            self.on_combo_changed

        )



        self.load_data()



    def apply_permissions(
        self,
        user,
        page_name="statistics",
    ):
        apply_widget_permissions(
            self,
            user,
            page_name,
        )



    def load_data(self):

        self.load_unpaid_sales()

        self.load_crew_totals()

        self.load_history()

        self.update_summary()



    def update_summary(self):

        unpaid = self.db.get_unpaid_sales()

        paid_total = self.db.get_total_payouts_value()



        self.summary_label.setText(

            tr(
                "payout.summary",
                count=len(unpaid),
                total=format_number(paid_total),
            )

        )



    def load_unpaid_sales(self):

        sales = self.db.get_unpaid_sales()
        has_sales = len(sales) > 0

        self.unpaid_table.setVisible(has_sales)
        self.unpaid_empty_panel.setVisible(not has_sales)
        self.unpaid_table.setRowCount(len(sales))



        self.sale_combo.blockSignals(True)

        self.sale_combo.clear()

        self.sale_combo.addItem(

            tr("payout.sale.placeholder"),

            None,

        )



        for row, sale in enumerate(sales):

            self.unpaid_table.setItem(

                row,

                0,

                QTableWidgetItem(f"#{sale['id']}"),

            )

            self.unpaid_table.setItem(

                row,

                1,

                QTableWidgetItem(
                    format_date(sale["sale_date"])
                ),

            )

            self.unpaid_table.setItem(

                row,

                2,

                QTableWidgetItem(sale["location"]),

            )

            self.unpaid_table.setItem(

                row,

                3,

                QTableWidgetItem(

                    f"{format_number(sale['total_amount'])} aUEC"

                ),

            )

            self.unpaid_table.setItem(

                row,

                4,

                QTableWidgetItem(sale["created_by"]),

            )



            combo_text = tr(

                "payout.sale.combo",

                sale_id=sale["id"],

                location=sale["location"],

                amount=format_number(sale["total_amount"]),

            )

            self.sale_combo.addItem(

                combo_text,

                sale["id"],

            )



        self.sale_combo.blockSignals(False)



        finalize_table_columns(
            self.unpaid_table,
            stretch_column=2,
        )



    def load_crew_totals(self):

        totals = self.db.get_crew_payout_totals()
        has_totals = len(totals) > 0

        self.crew_totals_table.setVisible(has_totals)
        self.crew_empty_panel.setVisible(not has_totals)
        self.crew_totals_table.setRowCount(len(totals))



        for row, entry in enumerate(totals):

            self.crew_totals_table.setItem(

                row,

                0,

                QTableWidgetItem(

                    entry["crew_member"]

                ),

            )

            self.crew_totals_table.setItem(

                row,

                1,

                QTableWidgetItem(

                    f"{format_number(entry['total'])} aUEC"

                ),

            )

        finalize_table_columns(
            self.crew_totals_table,
            stretch_column=0,
        )



    def load_history(self):

        history = self.db.get_payout_history()
        has_history = len(history) > 0

        self.history_table.setVisible(has_history)
        self.payout_history_empty_panel.setVisible(
            not has_history
        )
        self.history_table.setRowCount(len(history))



        for row, payout in enumerate(history):

            self.history_table.setItem(

                row,

                0,

                QTableWidgetItem(f"#{payout['id']}"),

            )

            self.history_table.setItem(

                row,

                1,

                QTableWidgetItem(

                    f"#{payout['sale_id']}"

                ),

            )

            self.history_table.setItem(

                row,

                2,

                QTableWidgetItem(
                    format_date(payout["sale_date"])
                ),

            )

            self.history_table.setItem(

                row,

                3,

                QTableWidgetItem(

                    payout["location"]

                ),

            )

            self.history_table.setItem(

                row,

                4,

                QTableWidgetItem(

                    f"{format_number(payout['payout_total'])} aUEC"

                ),

            )

            self.history_table.setItem(

                row,

                5,

                QTableWidgetItem(

                    payout["created_by"]

                ),

            )



        finalize_table_columns(
            self.history_table,
            stretch_column=3,
        )



    def on_sale_selected(self):

        row = self.unpaid_table.currentRow()



        if row < 0:

            return



        item = self.unpaid_table.item(row, 0)



        if not item:

            return



        sale_id = int(

            item.text().lstrip("#")

        )



        index = self.sale_combo.findData(sale_id)



        if index >= 0:

            self.sale_combo.setCurrentIndex(index)



    def on_combo_changed(self):

        sale_id = self.sale_combo.currentData()



        if sale_id is None:

            self.current_proposal = None

            self.payout_table.setRowCount(0)

            self.cost_payer_panel.hide()

            self._pending_unassigned_payers = []

            self.calc_info_label.setText(

                _calc_placeholder()

            )

            return



        self.calculate_proposal()



    def _selected_sale_id(self):

        return self.sale_combo.currentData()



    def _cost_payer_overrides(self):

        if not self._pending_unassigned_payers:

            return None

        if self.cost_payer_combo.currentIndex() <= 0:

            return None

        selected = self.cost_payer_combo.currentText()

        return {

            payer: selected

            for payer in self._pending_unassigned_payers

        }



    def _update_cost_payer_panel(self, proposal):

        raw_refunds = proposal.get("raw_refunds", {})

        if not proposal.get("unassigned_cost_payers"):

            self._pending_unassigned_payers = []

            self.cost_payer_panel.hide()

            return

        self._pending_unassigned_payers = sorted(

            payer

            for payer, amount in raw_refunds.items()

            if payer in UNASSIGNED_COST_PAYERS

            and amount > 0

        )

        self.cost_payer_panel.show()

        current = self.cost_payer_combo.currentText()

        self.cost_payer_combo.blockSignals(True)

        self.cost_payer_combo.clear()

        self.cost_payer_combo.addItem(
            tr("session.mission.paid_by.placeholder")
        )

        for member in proposal.get("crew", []):

            self.cost_payer_combo.addItem(member)

        index = self.cost_payer_combo.findText(current)

        if index >= 0:

            self.cost_payer_combo.setCurrentIndex(index)

        self.cost_payer_combo.blockSignals(False)



    def _on_cost_payer_changed(self):

        if self.cost_payer_combo.currentIndex() <= 0:

            return

        if self._selected_sale_id() is None:

            return

        overrides = self._cost_payer_overrides()

        if (

            overrides

            and self.current_proposal

        ):

            try:

                for old_payer, new_payer in (

                    overrides.items()

                ):

                    self.db.reassign_cost_payer(

                        self.current_proposal[

                            "cost_session_ids"

                        ],

                        old_payer,

                        new_payer,

                    )

                    refinery_jobs = self.current_proposal.get(

                        "cost_refinery_job_ids",

                        [],

                    )

                    if refinery_jobs:

                        self.db.reassign_refinery_cost_payer(

                            refinery_jobs,

                            old_payer,

                            new_payer,

                        )

            except ValueError as error:

                QMessageBox.warning(

                    self,

                    tr("common.error"),

                    str(error),

                )

                return

        self.calculate_proposal()



    def calculate_proposal(self):

        sale_id = self._selected_sale_id()



        if sale_id is None:

            QMessageBox.warning(

                self,

                tr("common.hint"),

                tr("payout.msg.select_sale"),

            )

            return



        try:

            proposal = (

                self.db.calculate_payout_proposal(

                    sale_id,

                    cost_payer_overrides=(

                        self._cost_payer_overrides()

                    ),

                )

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

                tr("payout.msg.calc_failed", error=error),

            )

            return



        self.current_proposal = proposal

        self._show_proposal(proposal)



    def _show_proposal(self, proposal):

        self._update_cost_payer_panel(proposal)

        sessions = ", ".join(

            f"#{sid}"

            for sid in proposal["session_ids"]

        ) or "—"



        cost_sessions = proposal.get(

            "cost_session_ids",

            proposal["session_ids"],

        )

        cost_note = ""

        if set(cost_sessions) != set(
            proposal["session_ids"]
        ):
            settled = ", ".join(
                f"#{sid}"
                for sid in proposal["session_ids"]
                if sid not in cost_sessions
            )
            cost_note = tr(
                "payout.proposal.cost_settled",
                sessions=settled,
            )

        refinery_job_ids = proposal.get("refinery_job_ids", [])
        cost_refinery_job_ids = proposal.get(
            "cost_refinery_job_ids",
            refinery_job_ids,
        )
        refinery_note = ""

        if (
            refinery_job_ids
            and set(cost_refinery_job_ids)
            != set(refinery_job_ids)
        ):
            settled_jobs = ", ".join(
                f"#{job_id}"
                for job_id in refinery_job_ids
                if job_id not in cost_refinery_job_ids
            )
            refinery_note = tr(
                "payout.proposal.refinery_settled",
                jobs=settled_jobs,
            )

        session_costs = proposal.get(
            "session_costs",
            proposal["total_costs"],
        )
        refinery_costs = proposal.get("refinery_costs", 0)



        refunds_text = ", ".join(

            tr(
                "payout.proposal.refund_line",
                name=name,
                amount=format_number(amount),
            )

            for name, amount in sorted(

                proposal["refunds"].items()

            )

        ) or tr("payout.proposal.refunds_none")



        warning = ""



        if proposal.get("warning"):

            warning = (

                f"\n\n⚠ {proposal['warning']}"

            )



        self.calc_info_label.setText(

            tr(
                "payout.proposal.detail",
                sale_id=proposal["sale_id"],
                revenue=format_number(proposal["revenue"]),
                sessions=sessions,
                session_costs=format_number(session_costs),
                refinery_costs=format_number(refinery_costs),
                total_costs=format_number(proposal["total_costs"]),
                refunds=refunds_text,
                equal_share=format_number(proposal["equal_share"]),
                distributed_total=format_number(
                    proposal["distributed_total"]
                ),
            )
            + cost_note
            + refinery_note
            + warning

        )



        items = proposal["items"]

        self.payout_table.setRowCount(len(items))



        for row, item in enumerate(items):

            member_item = QTableWidgetItem(

                item["crew_member"]

            )

            member_item.setFlags(

                member_item.flags()

                & ~Qt.ItemIsEditable

            )



            amount_item = QTableWidgetItem(

                format_number(item['amount'])

            )



            self.payout_table.setItem(

                row,

                0,

                member_item,

            )

            self.payout_table.setItem(

                row,

                1,

                amount_item,

            )

        finalize_table_columns(
            self.payout_table,
            stretch_column=1,
        )



    def save_payout(self):

        sale_id = self._selected_sale_id()



        if sale_id is None:

            QMessageBox.warning(

                self,

                tr("common.hint"),

                tr("payout.msg.select_sale"),

            )

            return



        if self._pending_unassigned_payers:

            overrides = self._cost_payer_overrides()

            if not overrides:

                QMessageBox.warning(

                    self,

                    tr("payout.msg.cost_payer.title"),

                    tr("payout.msg.cost_payer_required"),

                )

                return



        items = []



        for row in range(

            self.payout_table.rowCount()

        ):

            member_item = self.payout_table.item(

                row,

                0,

            )

            amount_item = self.payout_table.item(

                row,

                1,

            )



            if not member_item or not amount_item:

                continue



            member = member_item.text().strip()

            amount = parse_number_de(amount_item.text())
            if amount is None:
                QMessageBox.warning(
                    self,
                    tr("common.error"),
                    tr(
                        "payout.msg.invalid_amount",
                        member=member,
                    ),
                )
                return

            items.append({

                "crew_member": member,

                "amount": amount,

            })



        for item in items:

            if item["crew_member"] in UNASSIGNED_COST_PAYERS:

                QMessageBox.warning(

                    self,

                    tr("payout.msg.cost_payer.title"),

                    tr("payout.msg.system_costs"),

                )

                return



        if not items:

            QMessageBox.warning(

                self,

                tr("common.error"),

                tr("payout.msg.no_items"),

            )

            return



        notes = self.notes_input.text().strip() or None



        try:

            payout_id = self.db.create_payout(

                sale_id,

                items,

                notes=notes,

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

                tr("payout.msg.save_failed", error=error),

            )

            return



        QMessageBox.information(

            self,

            tr("payout.msg.saved.title"),

            tr(
                "payout.msg.saved.message",
                payout_id=payout_id,
            ),

        )



        self.current_proposal = None

        self.notes_input.clear()

        self.payout_table.setRowCount(0)

        self.calc_info_label.setText(

            _calc_placeholder()

        )



        self.load_data()



        main_window = self.window()



        if hasattr(
            main_window,
            "dashboard_page"
        ):
            main_window.dashboard_page.on_payout_saved()



    def _selected_payout_id(self):

        row = self.history_table.currentRow()

        if row < 0:

            return None

        item = self.history_table.item(row, 0)

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

        try:

            self.db.void_payout(payout_id)

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

        self.load_data()

        main_window = self.window()

        if hasattr(main_window, "refresh_all"):

            main_window.refresh_all()

        elif hasattr(main_window, "dashboard_page"):

            main_window.dashboard_page.refresh_dashboard()

        QMessageBox.information(

            self,

            tr("payout.msg.voided.title"),

            tr(
                "payout.msg.voided.message",
                payout_id=payout_id,
            ),

        )



    def refresh_data(self):

        self.load_data()


