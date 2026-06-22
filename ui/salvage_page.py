from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QComboBox,
    QLabel,
)

from database.access import get_database
from config.permissions import apply_widget_permissions
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


class SalvagePage(QWidget):

    def __init__(self):
        super().__init__()

        self.db = get_database()

        content, layout = page_content_widget()
        layout.addWidget(page_title("KOSTEN & CREW"))
        layout.addWidget(
            section_accent("◆ SITZUNGS-KOSTEN VERWALTEN")
        )
        layout.addLayout(hud_divider())

        status_panel, status_layout = page_panel()
        status_layout.setContentsMargins(16, 16, 16, 16)
        status_layout.addWidget(
            subsection_title("◆ AKTUELLE SITZUNG")
        )
        status_layout.addLayout(hud_divider())

        self.session_label = QLabel(
            "Aktive Sitzung: Bitte Sitzung starten"
        )
        self.session_label.setObjectName("infoValue")
        self.session_label.setWordWrap(True)

        self.crew_label = QLabel(
            "Crew: Bitte Crew anlegen"
        )
        self.crew_label.setObjectName("mutedLabel")
        self.crew_label.setWordWrap(True)

        self.costs_label = QLabel(
            "Gesamtkosten: 0 aUEC"
        )
        self.costs_label.setObjectName("statValue")

        status_layout.addWidget(self.session_label)
        status_layout.addWidget(self.crew_label)
        status_layout.addWidget(self.costs_label)
        layout.addWidget(status_panel)

        form_panel, form_layout = info_panel()
        form_layout.addWidget(
            subsection_title("◆ KOSTEN HINZUFÜGEN")
        )
        form_layout.addLayout(hud_divider())

        self.cost_type = QComboBox()
        self.cost_type.addItems([
            "Mission",
            "Raffinerie",
        ])

        self.cost_amount = QLineEdit()
        self.cost_amount.setPlaceholderText(
            "Kostenbetrag in aUEC"
        )

        self.paid_by = QComboBox()

        for label_text, widget in [
            ("Kostenart", self.cost_type),
            ("Betrag (aUEC)", self.cost_amount),
            ("Bezahlt von", self.paid_by),
        ]:
            add_form_field(form_layout, label_text, widget)

        self.cost_button = primary_button(
            "Kosten hinzufügen"
        )
        self.cost_button.clicked.connect(self.add_cost)
        form_layout.addWidget(self.cost_button)
        layout.addWidget(form_panel)

        layout.addWidget(
            subsection_title("◆ ERFASSTE KOSTEN")
        )

        costs_panel, costs_layout = page_panel()
        costs_layout.setContentsMargins(12, 12, 12, 12)

        self.cost_list_label = QLabel(
            "Keine Kosten erfasst"
        )
        self.cost_list_label.setObjectName("mutedLabel")
        self.cost_list_label.setWordWrap(True)

        self.costs_empty_panel = empty_info_panel(
            "Noch keine Kosten für diese Sitzung erfasst.",
            "assets/images/icons/info.svg",
        )

        costs_layout.addWidget(self.cost_list_label)
        costs_layout.addWidget(self.costs_empty_panel)
        self.costs_empty_panel.hide()
        layout.addWidget(costs_panel)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(build_page_scroll(content))

        self.load_session()

    def apply_permissions(self, user, page_name="salvage"):
        apply_widget_permissions(self, user, page_name)

    def load_session(self):
        session = self.db.get_active_session()

        if not session:
            self.session_label.setText(
                "Aktive Sitzung: Bitte Sitzung starten"
            )
            self.crew_label.setText(
                "Crew: Bitte Crew anlegen"
            )
            self.paid_by.clear()
            self.refresh_costs()
            self.refresh_cost_list()
            return

        session_id = session[0]
        ship_name = session[1]
        crew = self.db.get_crew_members(session_id)

        self.paid_by.clear()
        self.paid_by.addItem("— Bitte wählen —")

        for member in crew:
            self.paid_by.addItem(member[0])

        self.session_label.setText(
            f"Aktive Sitzung: {ship_name}"
        )

        crew_names = "\n".join(
            member[0] for member in crew
        )
        self.crew_label.setText(
            f"Crew:\n{crew_names or '—'}"
        )

        self.refresh_costs()
        self.refresh_cost_list()

    def refresh_costs(self):
        session = self.db.get_active_session()

        if not session:
            self.costs_label.setText(
                "Gesamtkosten: 0 aUEC"
            )
            return

        total_costs = self.db.get_total_costs(session[0])
        self.costs_label.setText(
            f"Gesamtkosten (Sitzung): "
            f"{total_costs:,.0f} aUEC"
        )

    def refresh_cost_list(self):
        session = self.db.get_active_session()

        if not session:
            self.cost_list_label.setText(
                "Keine Kosten erfasst"
            )
            self.cost_list_label.hide()
            self.costs_empty_panel.show()
            return

        costs = self.db.get_session_costs(session[0])

        if not costs:
            self.cost_list_label.hide()
            self.costs_empty_panel.show()
            return

        self.cost_list_label.show()
        self.costs_empty_panel.hide()

        lines = []
        for cost in costs:
            cost_type, amount, paid_by = cost
            lines.append(
                f"{cost_type}: {amount:,.0f} aUEC ({paid_by})"
            )

        self.cost_list_label.setText(
            "\n".join(lines)
        )

    def add_cost(self):
        session = self.db.get_active_session()

        if not session:
            return

        if self.paid_by.currentIndex() == 0:
            return

        try:
            amount = int(self.cost_amount.text())
        except ValueError:
            return

        self.db.add_cost(
            session[0],
            self.cost_type.currentText(),
            amount,
            self.paid_by.currentText(),
        )

        self.cost_amount.clear()
        self.refresh_costs()
        self.refresh_cost_list()

        main_window = self.window()
        if hasattr(main_window, "dashboard_page"):
            main_window.dashboard_page.refresh_dashboard()
