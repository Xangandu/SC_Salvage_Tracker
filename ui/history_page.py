from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
)

from database.access import get_database
from config.dates import format_date
from config.materials import material_label
from config.i18n import tr, format_number, status_label
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
    page_panel,
    empty_info_panel,
    hud_divider,
)


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

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(build_page_scroll(content))

        self.load_history()

    def apply_permissions(self, user, page_name="history"):
        apply_widget_permissions(self, user, page_name)

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

    def load_history(self):
        db = get_database()
        self._load_sessions_history(db)

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
