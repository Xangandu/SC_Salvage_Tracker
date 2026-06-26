from config.dates import now_db_timestamp

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QMessageBox,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QLabel,
)

from database.access import get_database
from config.i18n import tr, format_number, status_label
from config.strings_de import parse_int_de, parse_number_de
from config.materials import (
    material_label,
    material_codes_for_ship,
    materials_summary_for_ship,
    ship_supports_material,
)
from config.permissions import apply_widget_permissions
import auth.session as user_session
from ui.page_layout import (
    build_page_scroll,
    page_content_widget,
    page_title,
    section_accent,
    subsection_title,
    add_form_field,
    form_label,
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


def _display_value_label(text="—"):
    label = QLabel(text)
    label.setObjectName("displayValue")
    label.setWordWrap(True)
    return label


class SessionPage(QWidget):

    def __init__(self, is_network_client=False):
        super().__init__()

        self.db = get_database()
        self.is_network_client = is_network_client
        self._material_ship_name = ""

        self.ship_combo = QComboBox()
        self.ship_combo.addItems([
            "RSI Salvation",
            "MISC Fortune",
            "Drake Vulture",
            "ARGO MOTH",
            "Aegis Reclaimer",
        ])
        self.ship_combo.currentTextChanged.connect(
            self._on_host_ship_changed
        )

        self.crew_input = QTextEdit()
        self.crew_input.setPlaceholderText(tr("session.crew.placeholder"))
        self.crew_input.setMinimumHeight(100)

        self.start_button = primary_button(tr("session.button.start"))
        self.start_button.clicked.connect(self.start_session)

        self.client_session_combo = QComboBox()
        self.client_session_combo.currentIndexChanged.connect(
            self._on_client_session_changed
        )

        self.client_session_empty = empty_info_panel(
            tr("session.client.empty"),
            "assets/images/icons/info.svg",
        )

        self.active_ship_label = _display_value_label()
        self.active_status_label = _display_value_label()

        self.mission_cost_input = QLineEdit()
        self.mission_cost_input.setPlaceholderText(
            tr("session.placeholder.mission_cost")
        )

        self.mission_cost_paid_by = QComboBox()
        self.mission_costs_total_label = QLabel(
            tr(
                "session.mission.costs_total",
                mission_total=format_number(0),
                session_total=format_number(0),
            )
        )
        self.mission_costs_total_label.setObjectName("statValue")
        self.mission_costs_list_label = QLabel("")
        self.mission_costs_list_label.setObjectName("mutedLabel")
        self.mission_costs_list_label.setWordWrap(True)

        self.add_mission_cost_button = primary_button(
            tr("session.button.add_mission")
        )
        self.add_mission_cost_button.clicked.connect(
            self.add_mission_cost
        )

        self.rmc_input = QLineEdit()
        self.rmc_input.setPlaceholderText(tr("session.placeholder.rmc"))

        self.cm_rubble_input = QLineEdit()
        self.cm_rubble_input.setPlaceholderText(
            f"{material_label('CM_RUBBLE')} SCU"
        )

        self.cm_scraps_input = QLineEdit()
        self.cm_scraps_input.setPlaceholderText(
            f"{material_label('CM_SCRAPS')} SCU"
        )

        self.cm_salvage_input = QLineEdit()
        self.cm_salvage_input.setPlaceholderText(
            f"{material_label('CM_SALVAGE')} SCU"
        )

        self.finish_button = primary_button(tr("session.button.save_run"))
        self.finish_button.clicked.connect(self.complete_run)
        self.finish_button.setEnabled(False)

        self.end_session_button = _secondary_button(
            tr("session.button.end")
        )
        self.end_session_button.clicked.connect(
            self.end_session
        )
        self.end_session_button.setEnabled(False)

        self.delete_session_combo = QComboBox()
        self.delete_session_button = _secondary_button(
            tr("session.button.delete")
        )
        self.delete_session_button.clicked.connect(
            self.delete_selected_session
        )

        self.delete_session_panel = QWidget()
        delete_row = QHBoxLayout(self.delete_session_panel)
        delete_row.setContentsMargins(0, 0, 0, 0)
        delete_row.setSpacing(12)
        delete_row.addWidget(
            form_label(tr("session.label.deletable_session"))
        )
        delete_row.addWidget(
            self.delete_session_combo,
            1,
        )
        delete_row.addWidget(
            self.delete_session_button
        )
        self.delete_session_panel.hide()

        content, layout = page_content_widget()
        layout.addWidget(page_title(tr("session.title")))
        layout.addWidget(
            section_accent(tr("session.section.manage"))
        )
        layout.addLayout(hud_divider())

        self.start_panel, start_layout = info_panel()
        start_layout.addWidget(
            subsection_title(tr("session.section.new"))
        )
        start_layout.addLayout(hud_divider())

        for label_text, widget in [
            (tr("session.label.ship"), self.ship_combo),
            (tr("session.label.crew"), self.crew_input),
        ]:
            add_form_field(start_layout, label_text, widget)

        start_hint = QLabel(tr("session.hint.start"))
        start_hint.setWordWrap(True)
        start_hint.setObjectName("mutedLabel")
        start_layout.addWidget(start_hint)

        start_layout.addWidget(self.start_button)
        layout.addWidget(self.start_panel)

        self.client_session_panel, client_layout = info_panel()
        client_layout.addWidget(
            subsection_title(tr("session.section.network"))
        )
        client_layout.addLayout(hud_divider())
        client_hint = QLabel(tr("session.hint.client"))
        client_hint.setWordWrap(True)
        client_hint.setObjectName("mutedLabel")
        client_layout.addWidget(client_hint)
        add_form_field(
            client_layout,
            tr("session.label.active_session"),
            self.client_session_combo,
        )
        client_layout.addWidget(self.client_session_empty)
        layout.addWidget(self.client_session_panel)
        self.client_session_panel.hide()

        active_panel, active_layout = page_panel()
        active_layout.setContentsMargins(16, 16, 16, 16)
        active_layout.addWidget(
            subsection_title(tr("session.section.active"))
        )
        active_layout.addLayout(hud_divider())

        for label_text, widget in [
            (tr("session.label.ship"), self.active_ship_label),
            (tr("session.label.status"), self.active_status_label),
        ]:
            add_form_field(active_layout, label_text, widget)

        layout.addWidget(active_panel)

        self.mission_costs_panel, mission_layout = info_panel()
        mission_layout.addWidget(
            subsection_title(tr("session.section.missions"))
        )
        mission_layout.addLayout(hud_divider())

        mission_hint = QLabel(tr("session.hint.mission"))
        mission_hint.setWordWrap(True)
        mission_hint.setObjectName("mutedLabel")
        mission_layout.addWidget(mission_hint)

        for label_text, widget in [
            (tr("session.label.mission_cost"), self.mission_cost_input),
            (
                tr("session.label.paid_by"),
                self.mission_cost_paid_by,
            ),
        ]:
            add_form_field(mission_layout, label_text, widget)

        mission_layout.addWidget(self.add_mission_cost_button)
        mission_layout.addWidget(self.mission_costs_total_label)
        mission_layout.addWidget(self.mission_costs_list_label)
        layout.addWidget(self.mission_costs_panel)
        self.mission_costs_panel.hide()

        material_panel, material_layout = info_panel()
        material_layout.addWidget(
            subsection_title(tr("session.section.materials"))
        )
        material_layout.addLayout(hud_divider())

        self.material_ship_hint = QLabel("")
        self.material_ship_hint.setWordWrap(True)
        self.material_ship_hint.setObjectName("mutedLabel")
        material_layout.addWidget(self.material_ship_hint)

        self._material_inputs = {
            "RMC": self.rmc_input,
            "CM_RUBBLE": self.cm_rubble_input,
            "CM_SCRAPS": self.cm_scraps_input,
            "CM_SALVAGE": self.cm_salvage_input,
        }

        for label_text, widget in [
            ("RMC", self.rmc_input),
            (material_label("CM_RUBBLE"), self.cm_rubble_input),
            (material_label("CM_SCRAPS"), self.cm_scraps_input),
            (material_label("CM_SALVAGE"), self.cm_salvage_input),
        ]:
            add_form_field(material_layout, label_text, widget)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        action_row.addWidget(self.finish_button)
        action_row.addWidget(self.end_session_button)
        action_row.addStretch()
        material_layout.addLayout(action_row)
        material_layout.addWidget(self.delete_session_panel)
        layout.addWidget(material_panel)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(build_page_scroll(content))

        self._apply_client_layout()
        self.refresh_session()

    def _apply_client_layout(self):
        if self.is_network_client:
            self.start_panel.hide()
            self.client_session_panel.show()
            self.end_session_button.hide()
        else:
            self.start_panel.show()
            self.client_session_panel.hide()
            self.end_session_button.show()
            self._refresh_delete_sessions()

    def set_network_client_mode(self, is_network_client: bool):
        """Client-Modus zur Laufzeit (z. B. nach Verbindung in Einstellungen)."""
        if self.is_network_client == is_network_client:
            self.db = get_database()
            if is_network_client:
                self.refresh_session()
            return

        self.is_network_client = is_network_client
        self.db = get_database()
        self._apply_client_layout()
        self.refresh_session()

    def apply_permissions(self, user, page_name="session"):
        apply_widget_permissions(self, user, page_name)
        self.refresh_session()

    def _on_host_ship_changed(self, ship_name):
        if not self.is_network_client:
            self._apply_material_fields_for_ship(ship_name)

    def _on_client_session_changed(self, _index=-1):
        if not self.is_network_client:
            return

        session = self._selected_client_session()
        if not session:
            self.active_ship_label.setText("—")
            self.active_status_label.setText("—")
            self.finish_button.setEnabled(False)
            self._apply_material_fields_for_ship("")
            return

        ship = session.get("name", "")
        status = session.get("status", "")
        self.active_ship_label.setText(ship)
        self.active_status_label.setText(status_label(status))
        self.finish_button.setEnabled(status == "ACTIVE")
        self._apply_material_fields_for_ship(ship)

    def _apply_material_fields_for_ship(self, ship_name):
        self._material_ship_name = ship_name or ""
        enabled = set(
            material_codes_for_ship(self._material_ship_name)
        )

        if self._material_ship_name:
            self.material_ship_hint.setText(
                tr(
                    "session.hint.material_ship",
                    ship=self._material_ship_name,
                    materials=materials_summary_for_ship(
                        self._material_ship_name
                    ),
                )
            )
        else:
            self.material_ship_hint.setText(
                tr("session.hint.material_default")
            )

        for code, field in self._material_inputs.items():
            active = code in enabled
            field.setEnabled(active)
            if not active:
                field.clear()
            field.style().unpolish(field)
            field.style().polish(field)
            field.update()

    def _selected_client_session(self):
        if self.client_session_combo.currentIndex() < 0:
            return None
        data = self.client_session_combo.currentData()
        if not data:
            return None
        return data

    def _selected_session_id(self):
        if self.is_network_client:
            session = self._selected_client_session()
            return session["id"] if session else None

        session = self.db.get_active_session()
        return session[0] if session else None

    def _refresh_client_sessions(self):
        if not self.is_network_client:
            return

        current_id = None
        selected = self._selected_client_session()
        if selected:
            current_id = selected.get("id")

        self.client_session_combo.blockSignals(True)
        self.client_session_combo.clear()

        sessions = self.db.get_sessions_by_status("ACTIVE")

        if not sessions:
            self.client_session_empty.show()
            self.client_session_combo.hide()
            self.finish_button.setEnabled(False)
        else:
            self.client_session_empty.hide()
            self.client_session_combo.show()
            for session in sessions:
                label = (
                    f"#{session['id']} · {session['name']} · "
                    f"{status_label(session['status'])} · "
                    f"{format_number(session['total_scu'])} SCU"
                )
                self.client_session_combo.addItem(
                    label,
                    session,
                )

            if current_id is not None:
                for index in range(
                    self.client_session_combo.count()
                ):
                    item = self.client_session_combo.itemData(
                        index
                    )
                    if item and item.get("id") == current_id:
                        self.client_session_combo.setCurrentIndex(
                            index
                        )
                        break
            elif self.client_session_combo.count() == 1:
                self.client_session_combo.setCurrentIndex(0)

        self.client_session_combo.blockSignals(False)
        self._on_client_session_changed()

    def update_material_inputs(self):
        if self.is_network_client:
            session = self._selected_client_session()
            ship = session.get("name", "") if session else ""
            self._apply_material_fields_for_ship(ship)
        else:
            self._apply_material_fields_for_ship(
                self.ship_combo.currentText()
            )

    def _refresh_mission_cost_payers(self, session_id):
        current = self.mission_cost_paid_by.currentText()
        crew = self.db.get_crew_members(session_id)

        self.mission_cost_paid_by.blockSignals(True)
        self.mission_cost_paid_by.clear()
        self.mission_cost_paid_by.addItem(
            tr("session.mission.paid_by.placeholder")
        )

        for member in crew:
            self.mission_cost_paid_by.addItem(member[0])

        index = self.mission_cost_paid_by.findText(current)
        if index >= 0:
            self.mission_cost_paid_by.setCurrentIndex(index)

        self.mission_cost_paid_by.blockSignals(False)

    def _refresh_mission_costs(self, session_id=None):
        if session_id is None:
            session_id = self._selected_session_id()

        if not session_id:
            self.mission_costs_panel.hide()
            self.mission_cost_input.clear()
            self.mission_cost_paid_by.clear()
            self.mission_costs_total_label.setText(
                tr(
                    "session.mission.costs_total",
                    mission_total=format_number(0),
                    session_total=format_number(0),
                )
            )
            self.mission_costs_list_label.setText("")
            return

        session = None
        if self.is_network_client:
            selected = self._selected_client_session()
            if selected and selected.get("id") == session_id:
                session = selected
        else:
            active = self.db.get_active_session()
            if active and active[0] == session_id:
                session = active

        if not session:
            self.mission_costs_panel.hide()
            return

        status = (
            session.get("status")
            if isinstance(session, dict)
            else session[2]
        )
        if status != "ACTIVE":
            self.mission_costs_panel.hide()
            return

        self.mission_costs_panel.show()
        self._refresh_mission_cost_payers(session_id)

        costs = self.db.get_session_costs(session_id)
        mission_costs = [
            row for row in costs
            if row[0] == "Mission"
        ]
        mission_total = sum(row[1] for row in mission_costs)
        session_total = self.db.get_total_costs(session_id)

        self.mission_costs_total_label.setText(
            tr(
                "session.mission.costs_total",
                mission_total=format_number(mission_total),
                session_total=format_number(session_total),
            )
        )

        if mission_costs:
            lines = [
                tr(
                    "session.mission.line",
                    index=index,
                    amount=format_number(amount),
                    paid_by=paid_by,
                )
                for index, (_, amount, paid_by) in enumerate(
                    mission_costs,
                    start=1,
                )
            ]
            self.mission_costs_list_label.setText(
                "\n".join(lines)
            )
        else:
            self.mission_costs_list_label.setText(
                tr("session.mission.none")
            )

    def add_mission_cost(self):
        session_id = self._selected_session_id()

        if not session_id:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("session.msg.no_session"),
            )
            return

        if self.mission_cost_paid_by.currentIndex() <= 0:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("session.msg.paid_by_required"),
            )
            return

        amount = parse_int_de(self.mission_cost_input.text())
        if amount is None:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("session.msg.invalid_mission_cost"),
            )
            return

        if amount <= 0:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("session.msg.amount_positive"),
            )
            return

        self.db.add_cost(
            session_id,
            "Mission",
            amount,
            self.mission_cost_paid_by.currentText(),
        )

        self.mission_cost_input.clear()
        self._refresh_mission_costs(session_id)

        main_window = self.window()
        if hasattr(main_window, "dashboard_page"):
            main_window.dashboard_page.refresh_dashboard()

        QMessageBox.information(
            self,
            tr("session.msg.mission_added.title"),
            tr(
                "session.msg.mission_added.message",
                amount=format_number(amount),
            ),
        )

    def refresh_session(self):
        if self.is_network_client:
            self._refresh_client_sessions()
            session = self._selected_client_session()
            session_id = session.get("id") if session else None
            self._refresh_mission_costs(session_id)
            return

        session = self.db.get_active_session()

        if not session:
            self.active_ship_label.setText("—")
            self.active_status_label.setText("—")
            self.finish_button.setEnabled(False)
            self.end_session_button.setEnabled(False)
            self._apply_material_fields_for_ship(
                self.ship_combo.currentText()
            )
            self._refresh_delete_sessions()
            self._refresh_mission_costs()
            return

        self.active_ship_label.setText(session[1])
        self.active_status_label.setText(
            status_label(session[2])
        )
        self.finish_button.setEnabled(
            session[2] == "ACTIVE"
        )
        self.end_session_button.setEnabled(
            session[2] == "ACTIVE"
        )
        self._apply_material_fields_for_ship(session[1])
        self._refresh_delete_sessions()
        self._refresh_mission_costs(session[0])

    def _refresh_delete_sessions(self):
        if self.is_network_client:
            self.delete_session_panel.hide()
            return

        sessions = self.db.get_correctable_sessions()

        self.delete_session_combo.blockSignals(True)
        self.delete_session_combo.clear()

        if not sessions:
            self.delete_session_panel.hide()
        else:
            self.delete_session_panel.show()

            for session in sessions:
                self.delete_session_combo.addItem(
                    f"#{session['id']} · "
                    f"{session['name']} · "
                    f"{status_label(session['status'])}",
                    session["id"],
                )

        self.delete_session_combo.blockSignals(False)

    def delete_selected_session(self):
        session_id = self.delete_session_combo.currentData()

        if session_id is None:
            QMessageBox.warning(
                self,
                tr("common.hint"),
                tr("session.msg.no_deletable"),
            )
            return

        answer = QMessageBox.question(
            self,
            tr("session.msg.delete_confirm.title"),
            tr(
                "session.msg.delete_confirm.message",
                session_id=session_id,
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        try:
            self.db.delete_session(session_id)
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
                tr("session.msg.delete_failed", error=error),
            )
            return

        self.refresh_session()
        self._refresh_delete_sessions()

        main_window = self.window()
        if hasattr(main_window, "refresh_all"):
            main_window.refresh_all()
        elif hasattr(main_window, "dashboard_page"):
            main_window.dashboard_page.refresh_dashboard()

        QMessageBox.information(
            self,
            tr("session.msg.deleted.title"),
            tr(
                "session.msg.deleted.message",
                session_id=session_id,
            ),
        )

    def start_session(self):
        ship = self.ship_combo.currentText()

        try:
            crew_text = self.crew_input.toPlainText()
            crew_members = [
                member.strip()
                for member in crew_text.splitlines()
                if member.strip()
            ]

            if not crew_members:
                QMessageBox.warning(
                    self,
                    tr("common.error"),
                    tr("session.msg.no_crew"),
                )
                return

            start_time = now_db_timestamp()

            session_id = self.db.create_session(
                None,
                ship,
                start_time,
                created_by=user_session.get_user_id(),
            )

            for member in crew_members:
                self.db.add_crew_member(
                    session_id,
                    member,
                )

            self.refresh_session()
            self._refresh_delete_sessions()
            self._refresh_mission_costs(session_id)

            main_window = self.window()
            if hasattr(main_window, "dashboard_page"):
                main_window.dashboard_page.refresh_dashboard()

            QMessageBox.information(
                self,
                tr("session.msg.started.title"),
                tr("session.msg.started.message"),
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                tr("common.error"),
                tr("session.msg.start_failed", error=error),
            )

    def _session_ship_name(self):
        if self.is_network_client:
            session = self._selected_client_session()
            return session.get("name", "") if session else ""

        session = self.db.get_active_session()
        if session:
            return session[1]
        return self.ship_combo.currentText()

    def complete_run(self):
        session_id = self._selected_session_id()

        if not session_id:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("session.msg.no_active_selected"),
            )
            return

        ship_name = self._session_ship_name()

        material_values = {}
        for code, field in self._material_inputs.items():
            if not field.isEnabled():
                material_values[code] = 0.0
                continue

            amount = parse_number_de(field.text(), default=0)
            if amount is None:
                QMessageBox.warning(
                    self,
                    tr("common.error"),
                    tr("session.msg.invalid_numbers"),
                )
                return
            material_values[code] = amount

        if not any(amount > 0 for amount in material_values.values()):
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("session.msg.material_required"),
            )
            return

        for code, amount in material_values.items():
            if amount <= 0:
                continue
            if not ship_supports_material(ship_name, code):
                QMessageBox.warning(
                    self,
                    tr("common.error"),
                    tr(
                        "session.msg.material_not_allowed",
                        material=material_label(code),
                        ship=ship_name or tr("session.ship.unnamed"),
                        allowed=materials_summary_for_ship(ship_name),
                    ),
                )
                return

        for code, amount in material_values.items():
            if amount > 0:
                self.db.add_material(session_id, code, amount)

        for field in self._material_inputs.values():
            field.clear()

        self.refresh_session()

        main_window = self.window()
        if hasattr(main_window, "dashboard_page"):
            main_window.dashboard_page.refresh_dashboard()

        QMessageBox.information(
            self,
            tr("session.msg.material_saved.title"),
            tr("session.msg.material_saved.message"),
        )

    def end_session(self):
        session = self.db.get_active_session()

        if not session:
            QMessageBox.warning(
                self,
                tr("common.error"),
                tr("session.msg.no_active_found"),
            )
            return

        self.db.end_session(session[0])
        self.refresh_session()
        self._refresh_delete_sessions()

        main_window = self.window()
        if hasattr(main_window, "dashboard_page"):
            main_window.dashboard_page.refresh_dashboard()

        QMessageBox.information(
            self,
            tr("session.msg.ended.title"),
            tr("session.msg.ended.message"),
        )
