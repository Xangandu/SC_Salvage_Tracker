"""Schnell beitreten — nur Beitrittscode."""

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from network.simple_connect import connect_client_simple
from ui.mobiglas_window_frame import (
    MobiglasFramelessMixin,
    apply_mobiglas_window_frame,
)
from ui.page_layout import hud_divider, page_title, primary_button, form_label


class QuickJoinDialog(MobiglasFramelessMixin, QDialog):

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.client_user = None
        self._client_connection = None

        self.setObjectName("mobiglasDialog")
        self.setWindowTitle("Crew beitreten")
        self.setModal(True)
        self.resize(480, 280)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        hint = QLabel(
            "Gib den 6-stelligen Code vom Host ein — "
            "oder füge die Einladung ein."
        )
        hint.setWordWrap(True)
        hint.setObjectName("mutedLabel")

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("z. B. K7M2XP")
        self.code_input.setMaxLength(512)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(
            "Dein Name in der Crew (optional)"
        )
        saved_name = db.settings.get_app_setting(
            "network_client_name",
            "",
        )
        if saved_name:
            self.name_input.setText(saved_name)

        self.join_button = primary_button("Beitreten")
        self.join_button.clicked.connect(self._on_join)

        cancel = QPushButton("Abbrechen")
        cancel.setObjectName("secondaryAction")
        cancel.clicked.connect(self.reject)

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(cancel)
        row.addWidget(self.join_button)

        layout.addWidget(page_title("CREW BEITRETEN"))
        layout.addWidget(hint)
        layout.addLayout(hud_divider())
        layout.addWidget(form_label("Beitrittscode"))
        layout.addWidget(self.code_input)
        layout.addWidget(form_label("Anzeigename"))
        layout.addWidget(self.name_input)
        layout.addLayout(row)
        self.setLayout(layout)

        apply_mobiglas_window_frame(
            self,
            title="Crew beitreten",
            dialog=True,
        )
        self.code_input.setFocus()

    def _on_join(self) -> None:
        text = self.code_input.text().strip()
        if not text:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self,
                "Beitritt",
                "Bitte Beitrittscode eingeben.",
            )
            return

        self.join_button.setEnabled(False)
        self.join_button.setText("Verbinde…")

        result = connect_client_simple(
            self.db,
            self,
            text,
            client_name=self.name_input.text().strip(),
        )

        self.join_button.setEnabled(True)
        self.join_button.setText("Beitreten")

        if not result:
            return

        connection, user = result
        self._client_connection = connection
        self.client_user = user
        self.accept()

    @property
    def client_connection(self):
        return self._client_connection
