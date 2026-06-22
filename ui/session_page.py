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
from config.strings_de import status_label
from config.materials import material_label, material_codes_for_ship
from config.permissions import apply_widget_permissions
import auth.session as user_session
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
        self.crew_input.setPlaceholderText(
            "Ein Name pro Zeile\n\n"
            "Beispiel:\n"
            "Xangandu\n"
            "Pilot2\n"
            "Pilot3"
        )
        self.crew_input.setMinimumHeight(100)

        self.mission_cost_input = QLineEdit()
        self.mission_cost_input.setPlaceholderText(
            "z.B. 10000"
        )

        self.mission_cost_paid_by = QComboBox()
        self.crew_input.textChanged.connect(
            self._update_mission_cost_payers
        )
        self._update_mission_cost_payers()

        self.start_button = primary_button("Sitzung starten")
        self.start_button.clicked.connect(self.start_session)

        self.client_session_combo = QComboBox()
        self.client_session_combo.currentIndexChanged.connect(
            self._on_client_session_changed
        )

        self.client_session_empty = empty_info_panel(
            "Keine aktive Sitzung auf dem Host.\n"
            "Der Host muss zuerst eine Sitzung starten.",
            "assets/images/icons/info.svg",
        )

        self.active_ship_label = _display_value_label()
        self.active_status_label = _display_value_label()

        self.rmc_input = QLineEdit()
        self.rmc_input.setPlaceholderText("RMC SCU")

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

        self.finish_button = primary_button("Einsatz speichern")
        self.finish_button.clicked.connect(self.complete_run)
        self.finish_button.setEnabled(False)

        self.end_session_button = _secondary_button(
            "Sitzung beenden"
        )
        self.end_session_button.clicked.connect(
            self.end_session
        )
        self.end_session_button.setEnabled(False)

        self.delete_session_combo = QComboBox()
        self.delete_session_button = _secondary_button(
            "Sitzung löschen"
        )
        self.delete_session_button.clicked.connect(
            self.delete_selected_session
        )

        self.delete_session_panel = QWidget()
        delete_row = QHBoxLayout(self.delete_session_panel)
        delete_row.setContentsMargins(0, 0, 0, 0)
        delete_row.setSpacing(12)
        delete_row.addWidget(
            QLabel("Fehlerhafte Sitzung:")
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
        layout.addWidget(page_title("SITZUNG"))
        layout.addWidget(
            section_accent("◆ SALVAGE-EINSATZ VERWALTEN")
        )
        layout.addLayout(hud_divider())

        self.start_panel, start_layout = info_panel()
        start_layout.addWidget(
            subsection_title("◆ NEUE SITZUNG")
        )
        start_layout.addLayout(hud_divider())

        for label_text, widget in [
            ("Schiff", self.ship_combo),
            ("Crew (ein Name pro Zeile)", self.crew_input),
            ("Missionskosten (aUEC)", self.mission_cost_input),
            (
                "Missionskosten bezahlt von",
                self.mission_cost_paid_by,
            ),
        ]:
            add_form_field(start_layout, label_text, widget)

        start_layout.addWidget(self.start_button)
        layout.addWidget(self.start_panel)

        self.client_session_panel, client_layout = info_panel()
        client_layout.addWidget(
            subsection_title("◆ NETZWERK-SITZUNG")
        )
        client_layout.addLayout(hud_divider())
        client_hint = QLabel(
            "Wähle die laufende Sitzung des Hosts. "
            "Die Materialfelder richten sich automatisch "
            "nach dem Schiff dieser Sitzung."
        )
        client_hint.setWordWrap(True)
        client_hint.setObjectName("mutedLabel")
        client_layout.addWidget(client_hint)
        add_form_field(
            client_layout,
            "Aktive Sitzung",
            self.client_session_combo,
        )
        client_layout.addWidget(self.client_session_empty)
        layout.addWidget(self.client_session_panel)
        self.client_session_panel.hide()

        active_panel, active_layout = page_panel()
        active_layout.setContentsMargins(16, 16, 16, 16)
        active_layout.addWidget(
            subsection_title("◆ AKTIVE SITZUNG")
        )
        active_layout.addLayout(hud_divider())

        for label_text, widget in [
            ("Schiff", self.active_ship_label),
            ("Status", self.active_status_label),
        ]:
            add_form_field(active_layout, label_text, widget)

        layout.addWidget(active_panel)

        material_panel, material_layout = info_panel()
        material_layout.addWidget(
            subsection_title("◆ MATERIALIEN ERFASSEN")
        )
        material_layout.addLayout(hud_divider())

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
        enabled = set(material_codes_for_ship(self._material_ship_name))

        field_map = {
            "RMC": self.rmc_input,
            "CM_RUBBLE": self.cm_rubble_input,
            "CM_SCRAPS": self.cm_scraps_input,
            "CM_SALVAGE": self.cm_salvage_input,
        }

        for code, field in field_map.items():
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
                    f"{session['total_scu']:g} SCU"
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

    def _update_mission_cost_payers(self):
        current = self.mission_cost_paid_by.currentText()
        crew_members = [
            member.strip()
            for member in self.crew_input.toPlainText().splitlines()
            if member.strip()
        ]

        self.mission_cost_paid_by.blockSignals(True)
        self.mission_cost_paid_by.clear()
        self.mission_cost_paid_by.addItem(
            "— Bitte wählen —"
        )

        for member in crew_members:
            self.mission_cost_paid_by.addItem(member)

        index = self.mission_cost_paid_by.findText(
            current
        )
        if index >= 0:
            self.mission_cost_paid_by.setCurrentIndex(
                index
            )

        self.mission_cost_paid_by.blockSignals(False)

    def refresh_session(self):
        if self.is_network_client:
            self._refresh_client_sessions()
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
                "Hinweis",
                "Keine löschbare Sitzung ausgewählt.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Sitzung löschen",
            f"Sitzung #{session_id} wirklich löschen?\n\n"
            "Material, Kosten und Crew-Einträge "
            "dieser Sitzung werden entfernt. "
            "Nur möglich ohne Raffinerie und Verkauf.",
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

        self.refresh_session()
        self._refresh_delete_sessions()

        main_window = self.window()
        if hasattr(main_window, "refresh_all"):
            main_window.refresh_all()
        elif hasattr(main_window, "dashboard_page"):
            main_window.dashboard_page.refresh_dashboard()

        QMessageBox.information(
            self,
            "Gelöscht",
            f"Sitzung #{session_id} wurde gelöscht.",
        )

    def start_session(self):
        ship = self.ship_combo.currentText()

        try:
            mission_cost = int(
                self.mission_cost_input.text() or 0
            )
        except ValueError:
            QMessageBox.warning(
                self,
                "Fehler",
                "Bitte gültige Missionskosten eingeben",
            )
            return

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
                    "Fehler",
                    "Bitte mindestens ein Crew-Mitglied "
                    "angeben.",
                )
                return

            if mission_cost > 0:
                if self.mission_cost_paid_by.currentIndex() <= 0:
                    QMessageBox.warning(
                        self,
                        "Fehler",
                        "Bitte angeben, wer die "
                        "Missionskosten bezahlt hat.",
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

            if mission_cost > 0:
                self.db.add_cost(
                    session_id,
                    "Mission",
                    mission_cost,
                    self.mission_cost_paid_by.currentText(),
                )

            self.active_ship_label.setText(ship)
            self.active_status_label.setText("AKTIV")
            self.finish_button.setEnabled(True)
            self.end_session_button.setEnabled(True)
            self._refresh_delete_sessions()
            self.mission_cost_input.clear()
            self.mission_cost_paid_by.setCurrentIndex(0)
            self._apply_material_fields_for_ship(ship)

            main_window = self.window()
            if hasattr(main_window, "dashboard_page"):
                main_window.dashboard_page.refresh_dashboard()

            QMessageBox.information(
                self,
                "Sitzung gestartet",
                "Die Salvage-Sitzung wurde gestartet.",
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Sitzung konnte nicht gestartet werden:\n\n{error}",
            )

    def complete_run(self):
        session_id = self._selected_session_id()

        if not session_id:
            QMessageBox.warning(
                self,
                "Fehler",
                "Keine aktive Sitzung ausgewählt",
            )
            return

        try:
            rmc = float(self.rmc_input.text() or 0)
            cm_rubble = float(
                self.cm_rubble_input.text() or 0
            )
            cm_scraps = float(
                self.cm_scraps_input.text() or 0
            )
            cm_salvage = float(
                self.cm_salvage_input.text() or 0
            )
        except ValueError:
            QMessageBox.warning(
                self,
                "Fehler",
                "Bitte gültige Zahlen eingeben",
            )
            return

        if not any((rmc, cm_rubble, cm_scraps, cm_salvage)):
            QMessageBox.warning(
                self,
                "Fehler",
                "Bitte mindestens ein Material mit Menge > 0 "
                "eingeben.",
            )
            return

        self.db.add_material(session_id, "RMC", rmc)
        self.db.add_material(
            session_id, "CM_RUBBLE", cm_rubble
        )
        self.db.add_material(
            session_id, "CM_SCRAPS", cm_scraps
        )
        self.db.add_material(
            session_id, "CM_SALVAGE", cm_salvage
        )

        self.rmc_input.clear()
        self.cm_rubble_input.clear()
        self.cm_scraps_input.clear()
        self.cm_salvage_input.clear()

        self.refresh_session()

        main_window = self.window()
        if hasattr(main_window, "dashboard_page"):
            main_window.dashboard_page.refresh_dashboard()

        QMessageBox.information(
            self,
            "Erfolg",
            "Materialien gespeichert",
        )

    def end_session(self):
        session = self.db.get_active_session()

        if not session:
            QMessageBox.warning(
                self,
                "Fehler",
                "Keine aktive Sitzung gefunden",
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
            "Sitzung beendet",
            "Die Sitzung wartet nun auf die Raffinerie.",
        )
