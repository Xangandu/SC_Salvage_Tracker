"""Verbindungsassistent — einfach: Allein, Host (Code teilen), Client (Code eingeben)."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from network.client_connect import read_client_settings
from network.constants import (
    NETWORK_MODE_CLIENT,
    NETWORK_MODE_HOST,
    NETWORK_MODE_STANDALONE,
)
from network.network_state import get_network_state
from network.simple_connect import (
    apply_host_simple_defaults,
    connect_client_simple,
    format_simple_invite,
    generate_join_code,
)
from ui.clipboard_utils import copy_to_clipboard
from ui.mobiglas_window_frame import (
    MobiglasFramelessMixin,
    apply_mobiglas_window_frame,
)
from ui.page_layout import (
    hud_divider,
    page_title,
    primary_button,
    subsection_title,
)


class ConnectionAssistantDialog(MobiglasFramelessMixin, QDialog):

    MODE_STANDALONE = NETWORK_MODE_STANDALONE
    MODE_HOST = NETWORK_MODE_HOST
    MODE_CLIENT = NETWORK_MODE_CLIENT

    def __init__(self, db, parent=None, *, initial_mode: str | None = None):
        super().__init__(parent)
        self.db = db
        self.selected_mode = self.MODE_STANDALONE
        self.client_user = None
        self._client_connection = None

        self.setObjectName("mobiglasDialog")
        self.setWindowTitle("Vernetzung")
        self.setModal(True)
        self.resize(520, 420)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        subtitle = QLabel(
            "Allein spielen, als Host eine Crew einladen, "
            "oder mit einem Code beitreten."
        )
        subtitle.setWordWrap(True)
        subtitle.setObjectName("mutedLabel")

        self.mode_group = QButtonGroup(self)
        mode_row = QHBoxLayout()

        self.standalone_radio = QRadioButton("Allein spielen")
        self.host_radio = QRadioButton("Crew hosten")
        self.client_radio = QRadioButton("Crew beitreten")

        for radio in (
            self.standalone_radio,
            self.host_radio,
            self.client_radio,
        ):
            self.mode_group.addButton(radio)
            mode_row.addWidget(radio)

        self.standalone_radio.toggled.connect(self._on_mode_changed)
        self.host_radio.toggled.connect(self._on_mode_changed)
        self.client_radio.toggled.connect(self._on_mode_changed)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_standalone_page())
        self.stack.addWidget(self._build_host_page())
        self.stack.addWidget(self._build_client_page())

        self.continue_button = primary_button("Weiter")
        self.continue_button.clicked.connect(self._on_continue)

        cancel_button = QPushButton("Abbrechen")
        cancel_button.setObjectName("secondaryAction")
        cancel_button.clicked.connect(self.reject)

        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(cancel_button)
        button_row.addWidget(self.continue_button)

        layout.addWidget(page_title("VERNETZUNG"))
        layout.addWidget(subtitle)
        layout.addLayout(hud_divider())
        layout.addLayout(mode_row)
        layout.addWidget(self.stack)
        layout.addLayout(button_row)
        self.setLayout(layout)

        settings = self.db.settings.get_app_settings()
        saved_mode = initial_mode or settings.get(
            "network_mode",
            self.MODE_STANDALONE,
        )
        self._select_mode(saved_mode)
        apply_mobiglas_window_frame(self)

    def _build_standalone_page(self) -> QWidget:
        page = QWidget()
        panel = QFrame()
        panel.setObjectName("pagePanel")
        panel_layout = QVBoxLayout()
        panel_layout.addWidget(subsection_title("◆ LOKAL"))
        info = QLabel(
            "Alle Daten bleiben auf diesem Rechner. "
            "Keine Crew-Verbindung nötig."
        )
        info.setWordWrap(True)
        info.setObjectName("mutedLabel")
        panel_layout.addWidget(info)
        panel.setLayout(panel_layout)
        outer = QVBoxLayout(page)
        outer.addWidget(panel)
        return page

    def _build_host_page(self) -> QWidget:
        page = QWidget()
        panel = QFrame()
        panel.setObjectName("pagePanel")
        panel_layout = QVBoxLayout()
        panel_layout.addWidget(subsection_title("◆ CREW EINLADEN"))

        info = QLabel(
            "Teile diesen Code mit deiner Crew. "
            "Sie brauchen nur den Salvage Tracker und den Code — "
            "keine IP, kein Router, keine Extra-Software."
        )
        info.setWordWrap(True)
        info.setObjectName("mutedLabel")
        panel_layout.addWidget(info)

        self.host_code_input = QLineEdit()
        self.host_code_input.setReadOnly(True)
        self.host_code_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.host_code_input.setStyleSheet(
            "font-size: 28px; letter-spacing: 6px; padding: 12px;"
        )

        saved_code = self.db.settings.get_app_setting(
            "network_join_code",
            "",
        )
        if saved_code:
            self.host_code_input.setText(saved_code.upper())
        else:
            self.host_code_input.setText(generate_join_code())

        copy_button = QPushButton("Code kopieren")
        copy_button.setObjectName("secondaryAction")
        copy_button.clicked.connect(self._copy_host_code)

        panel_layout.addWidget(self.host_code_input)
        panel_layout.addWidget(copy_button)
        panel.setLayout(panel_layout)
        outer = QVBoxLayout(page)
        outer.addWidget(panel)
        return page

    def _build_client_page(self) -> QWidget:
        page = QWidget()
        panel = QFrame()
        panel.setObjectName("pagePanel")
        panel_layout = QVBoxLayout()
        panel_layout.addWidget(subsection_title("◆ CREW BEITRETEN"))

        info = QLabel(
            "Code vom Host eingeben — oder die Einladung einfügen."
        )
        info.setWordWrap(True)
        info.setObjectName("mutedLabel")
        panel_layout.addWidget(info)

        self.client_code_input = QLineEdit()
        self.client_code_input.setPlaceholderText("6-stelliger Code")
        self.client_name_input = QLineEdit()
        self.client_name_input.setPlaceholderText(
            "Dein Name (optional)"
        )

        panel_layout.addWidget(QLabel("Beitrittscode"))
        panel_layout.addWidget(self.client_code_input)
        panel_layout.addWidget(QLabel("Anzeigename"))
        panel_layout.addWidget(self.client_name_input)

        client_settings = read_client_settings(self.db)
        if client_settings["join_code"]:
            self.client_code_input.setText(
                client_settings["join_code"]
            )
        if client_settings["client_name"]:
            self.client_name_input.setText(
                client_settings["client_name"]
            )

        panel.setLayout(panel_layout)
        outer = QVBoxLayout(page)
        outer.addWidget(panel)
        return page

    def _copy_host_code(self) -> None:
        code = self.host_code_input.text().strip().upper()
        if not code:
            return
        copy_to_clipboard(
            format_simple_invite(code),
            self,
            message="Code kopiert — z. B. in Discord schicken.",
        )

    def _select_mode(self, mode: str) -> None:
        radios = {
            self.MODE_STANDALONE: self.standalone_radio,
            self.MODE_HOST: self.host_radio,
            self.MODE_CLIENT: self.client_radio,
        }
        radio = radios.get(mode, self.standalone_radio)
        radio.setChecked(True)

    def _on_mode_changed(self) -> None:
        if self.standalone_radio.isChecked():
            self.stack.setCurrentIndex(0)
            self.continue_button.setText("Weiter")
        elif self.host_radio.isChecked():
            self.stack.setCurrentIndex(1)
            self.continue_button.setText("Weiter")
        elif self.client_radio.isChecked():
            self.stack.setCurrentIndex(2)
            self.continue_button.setText("Beitreten")

    def _on_continue(self) -> None:
        state = get_network_state()

        if self.standalone_radio.isChecked():
            state.mode = self.MODE_STANDALONE
            self.db.settings.set_app_setting(
                "network_mode",
                self.MODE_STANDALONE,
            )
            self.selected_mode = self.MODE_STANDALONE
            self.accept()
            return

        if self.host_radio.isChecked():
            code = self.host_code_input.text().strip().upper()
            if not code:
                code = generate_join_code()
                self.host_code_input.setText(code)

            apply_host_simple_defaults(self.db, code)
            state.mode = self.MODE_HOST
            state.join_code = code
            self.selected_mode = self.MODE_HOST
            self.accept()
            return

        if self.client_radio.isChecked():
            self._connect_as_client()

    def _connect_as_client(self) -> None:
        text = self.client_code_input.text().strip()
        if not text:
            QMessageBox.warning(
                self,
                "Beitritt",
                "Bitte Beitrittscode eingeben.",
            )
            return

        self.continue_button.setEnabled(False)
        self.continue_button.setText("Verbinde…")

        result = connect_client_simple(
            self.db,
            self,
            text,
            client_name=self.client_name_input.text().strip(),
        )

        self.continue_button.setEnabled(True)
        self.continue_button.setText("Beitreten")

        if not result:
            return

        connection, user = result
        self.client_user = user
        self._client_connection = connection
        self.selected_mode = self.MODE_CLIENT
        get_network_state().mode = self.MODE_CLIENT
        self.db.settings.set_app_setting(
            "network_mode",
            self.MODE_CLIENT,
        )
        self.accept()

    @property
    def client_connection(self):
        return self._client_connection
