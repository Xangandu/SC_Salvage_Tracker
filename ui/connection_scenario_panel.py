"""UI-Panel: Verbindungsszenario LAN / Internet / Router."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from network.connection_guide import (
    CLIENT_HINTS,
    CLIENT_PLACEHOLDERS,
    HOST_HINTS,
    SCENARIO_LABELS,
    SCENARIO_LAN,
    SCENARIO_RELAY,
    SCENARIO_INTERNET,
    SCENARIO_ROUTER,
    default_relay_host,
    default_relay_port,
    fetch_public_ip,
    format_invite_text,
    is_relay_scenario,
    local_lan_addresses,
    normalize_scenario,
)
from network.constants import DEFAULT_PORT
from ui.clipboard_utils import copy_to_clipboard
from ui.page_layout import add_form_field, form_label, subsection_title


class ConnectionScenarioPanel(QWidget):

    scenario_changed = Signal(str)

    def __init__(
        self,
        parent=None,
        *,
        role: str = "host",
        show_invite: bool = True,
    ):
        super().__init__(parent)
        self._role = role
        self._show_invite = show_invite
        self._port = DEFAULT_PORT
        self._join_code = ""
        self._use_tls = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = (
            "◆ WO SPIELT IHR?"
            if role == "client"
            else "◆ WIE VERBINDEN SICH CLIENTS?"
        )
        layout.addWidget(subsection_title(title))

        self.scenario_combo = QComboBox()
        for key in (
            SCENARIO_LAN,
            SCENARIO_RELAY,
            SCENARIO_INTERNET,
            SCENARIO_ROUTER,
        ):
            self.scenario_combo.addItem(SCENARIO_LABELS[key], key)
        self.scenario_combo.currentIndexChanged.connect(
            self._on_scenario_changed
        )
        add_form_field(layout, "Verbindungsart", self.scenario_combo)

        self.hint_label = QLabel()
        self.hint_label.setWordWrap(True)
        self.hint_label.setObjectName("mutedLabel")
        layout.addWidget(self.hint_label)

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Adresse für Einladung")
        self.address_label = form_label("Adresse für Einladung")
        layout.addWidget(self.address_label)
        layout.addWidget(self.address_input)

        self.relay_port_input = QLineEdit(str(default_relay_port()))
        self.relay_port_label = form_label("Relay-Port")
        layout.addWidget(self.relay_port_label)
        layout.addWidget(self.relay_port_input)
        self.relay_port_label.hide()
        self.relay_port_input.hide()

        self.fetch_public_ip_button = QPushButton("Externe IP abrufen")
        self.fetch_public_ip_button.setObjectName("secondaryAction")
        self.fetch_public_ip_button.clicked.connect(
            self._fetch_public_ip
        )

        invite_row = QHBoxLayout()
        self.copy_invite_button = QPushButton("Einladung kopieren")
        self.copy_invite_button.setObjectName("secondaryAction")
        self.copy_invite_button.clicked.connect(self._copy_invite)
        invite_row.addWidget(self.fetch_public_ip_button)
        invite_row.addWidget(self.copy_invite_button)
        invite_row.addStretch()
        layout.addLayout(invite_row)

        if role == "client":
            self._set_address_row_visible(False)
            self.fetch_public_ip_button.hide()
            self.copy_invite_button.hide()
        elif not show_invite:
            self._set_address_row_visible(False)
            self.fetch_public_ip_button.hide()
            self.copy_invite_button.hide()

        self._populate_lan_addresses()
        self._on_scenario_changed()

    def set_scenario(self, scenario: str) -> None:
        scenario = normalize_scenario(scenario)
        for index in range(self.scenario_combo.count()):
            if self.scenario_combo.itemData(index) == scenario:
                self.scenario_combo.setCurrentIndex(index)
                return

    def get_scenario(self) -> str:
        return normalize_scenario(self.scenario_combo.currentData())

    def set_host_invite_context(
        self,
        *,
        port: int,
        join_code: str,
        use_tls: bool,
        addresses: list[str] | None = None,
    ) -> None:
        self._port = port
        self._join_code = (join_code or "").strip().upper()
        self._use_tls = use_tls

        lan_addresses = addresses or local_lan_addresses()
        if lan_addresses and not self.address_input.text().strip():
            self.address_input.setText(lan_addresses[0])

        if self._role == "host" and self.get_scenario() == SCENARIO_LAN:
            if lan_addresses:
                self.address_input.setText(lan_addresses[0])

    def invite_address(self) -> str:
        return self.address_input.text().strip()

    def relay_port(self) -> int:
        try:
            return int(
                self.relay_port_input.text().strip()
                or default_relay_port()
            )
        except ValueError:
            return default_relay_port()

    def set_relay_defaults(
        self,
        *,
        relay_host: str = "",
        relay_port: int | None = None,
    ) -> None:
        if relay_host and not self.address_input.text().strip():
            self.address_input.setText(relay_host.strip())
        if relay_port is not None:
            self.relay_port_input.setText(str(relay_port))

    def client_placeholder(self) -> str:
        return CLIENT_PLACEHOLDERS.get(
            self.get_scenario(),
            CLIENT_PLACEHOLDERS[SCENARIO_LAN],
        )

    def _set_relay_port_row_visible(self, visible: bool) -> None:
        self.relay_port_label.setVisible(visible)
        self.relay_port_input.setVisible(visible)

    def _set_address_row_visible(self, visible: bool) -> None:
        self.address_label.setVisible(visible)
        self.address_input.setVisible(visible)

    def _populate_lan_addresses(self) -> None:
        lan_addresses = local_lan_addresses()
        if lan_addresses and not self.address_input.text().strip():
            self.address_input.setText(lan_addresses[0])

    def _on_scenario_changed(self) -> None:
        scenario = self.get_scenario()
        hints = CLIENT_HINTS if self._role == "client" else HOST_HINTS
        self.hint_label.setText(hints.get(scenario, ""))

        is_relay = is_relay_scenario(scenario)

        if self._role == "client":
            self._set_address_row_visible(is_relay)
            self._set_relay_port_row_visible(is_relay)
            if is_relay:
                self.address_label.setText("Relay-Adresse")
                self.address_input.setPlaceholderText(
                    CLIENT_PLACEHOLDERS[SCENARIO_RELAY]
                )
                if not self.address_input.text().strip():
                    self.address_input.setText(default_relay_host())
            self.scenario_changed.emit(scenario)
            return

        if self._role == "host" and self._show_invite:
            is_router = scenario == SCENARIO_ROUTER
            is_internet = scenario == SCENARIO_INTERNET
            self._set_address_row_visible(True)
            self._set_relay_port_row_visible(is_relay)
            self.fetch_public_ip_button.setVisible(
                is_router or is_internet
            )
            self.copy_invite_button.setVisible(True)

            if scenario == SCENARIO_LAN:
                self.address_label.setText("Adresse für Einladung")
                self.address_input.setPlaceholderText(
                    "LAN-IP für die Crew"
                )
                lan_addresses = local_lan_addresses()
                if lan_addresses:
                    self.address_input.setText(lan_addresses[0])
            elif is_relay:
                self.address_label.setText("Relay-Adresse")
                self.address_input.setPlaceholderText(
                    "Salvage-Relay, z. B. relay.example.com"
                )
                if not self.address_input.text().strip():
                    self.address_input.setText(default_relay_host())
            elif is_internet:
                self.address_label.setText("Adresse für Einladung")
                self.address_input.setPlaceholderText(
                    "Erreichbare Adresse für die Einladung "
                    "(externe IP oder LAN-IP)"
                )
            elif is_router:
                self.address_label.setText("Adresse für Einladung")
                self.address_input.setPlaceholderText(
                    "Externe IP — „Externe IP abrufen“ oder vom Provider"
                )

        self.scenario_changed.emit(scenario)

    def _fetch_public_ip(self) -> None:
        self.fetch_public_ip_button.setEnabled(False)
        self.fetch_public_ip_button.setText("Rufe ab…")
        try:
            public_ip = fetch_public_ip()
        finally:
            self.fetch_public_ip_button.setEnabled(True)
            self.fetch_public_ip_button.setText("Externe IP abrufen")

        if public_ip:
            self.address_input.setText(public_ip)
            return

        from PySide6.QtWidgets import QMessageBox

        QMessageBox.warning(
            self,
            "Externe IP",
            "Die externe IP konnte nicht abgerufen werden.\n"
            "Prüfe die Internetverbindung oder trage die IP "
            "manuell ein (Router-Statusseite oder Anbieter).",
        )

    def _copy_invite(self) -> None:
        host = self.invite_address()
        scenario = self.get_scenario()

        if is_relay_scenario(scenario):
            if not host:
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self,
                    "Einladung",
                    "Bitte zuerst die Relay-Adresse eintragen.",
                )
                return
        elif not host:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self,
                "Einladung",
                "Bitte zuerst eine Adresse eintragen oder abrufen.",
            )
            return

        if not self._join_code:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self,
                "Einladung",
                "Beitrittscode fehlt — Host starten oder Code erzeugen.",
            )
            return

        text = format_invite_text(
            host=host,
            port=self._port,
            join_code=self._join_code,
            use_tls=self._use_tls,
            scenario=scenario,
            relay_host=host if is_relay_scenario(scenario) else "",
            relay_port=self.relay_port(),
        )
        copy_to_clipboard(
            text,
            self,
            message=(
                "Einladungstext wurde kopiert.\n"
                "Sende ihn an deine Crew (Chat, Discord, …)."
            ),
        )
