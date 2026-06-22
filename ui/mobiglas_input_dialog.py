"""MobiGlas-Eingabedialoge (Ersatz für QInputDialog)."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QMessageBox,
    QLabel,
)

from ui.page_layout import (
    page_title,
    hud_divider,
    primary_button,
    page_panel,
    add_form_field,
)
from ui.mobiglas_window_frame import (
    MobiglasFramelessMixin,
    apply_mobiglas_window_frame,
)


def _secondary_button(text):
    button = QPushButton(text)
    button.setObjectName("secondaryAction")
    return button


class MobiglasDoubleInputDialog(MobiglasFramelessMixin, QDialog):

    def __init__(
        self,
        parent,
        title,
        label,
        value=0.0,
        minimum=0.0,
        maximum=100000.0,
        decimals=1,
        hint_text="",
        field_tooltip="",
    ):
        super().__init__(parent)

        self._minimum = float(minimum)
        self._maximum = float(maximum)
        self._decimals = int(decimals)
        self._value = float(value)

        self.setObjectName("mobiglasDialog")
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(480, 260)
        self.setMinimumWidth(420)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        layout.addWidget(page_title(title.upper()))
        layout.addLayout(hud_divider())

        panel, panel_layout = page_panel()
        panel_layout.setContentsMargins(16, 16, 16, 16)
        panel_layout.setSpacing(10)

        if hint_text:
            hint = QLabel(hint_text)
            hint.setWordWrap(True)
            hint.setObjectName("mutedLabel")
            panel_layout.addWidget(hint)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Menge in SCU")
        formatted = (
            f"{float(value):.{self._decimals}f}"
            .rstrip("0")
            .rstrip(".")
        )
        self.input.setText(formatted or "0")
        if field_tooltip:
            self.input.setToolTip(field_tooltip)
        add_form_field(panel_layout, label, self.input)

        button_row = QHBoxLayout()
        button_row.setSpacing(12)

        cancel_button = _secondary_button("Abbrechen")
        cancel_button.clicked.connect(self.reject)

        confirm_button = primary_button("OK")
        confirm_button.clicked.connect(self._accept_value)
        confirm_button.setDefault(True)

        button_row.addStretch()
        button_row.addWidget(cancel_button)
        button_row.addWidget(confirm_button)
        panel_layout.addLayout(button_row)

        panel.setLayout(panel_layout)
        layout.addWidget(panel)
        self.setLayout(layout)

        self.input.returnPressed.connect(self._accept_value)
        self.input.selectAll()
        self.input.setFocus()

        apply_mobiglas_window_frame(
            self,
            title=title,
            dialog=True,
        )

    def value(self):
        return self._value

    def _accept_value(self):
        text = self.input.text().strip().replace(",", ".")

        if not text:
            QMessageBox.warning(
                self,
                "Eingabe",
                "Bitte eine gültige Menge eingeben.",
            )
            return

        try:
            parsed = round(float(text), self._decimals)
        except ValueError:
            QMessageBox.warning(
                self,
                "Eingabe",
                "Bitte eine gültige Zahl eingeben.",
            )
            return

        if parsed < self._minimum or parsed > self._maximum:
            QMessageBox.warning(
                self,
                "Eingabe",
                f"Die Menge muss zwischen "
                f"{self._minimum:g} und "
                f"{self._maximum:g} SCU liegen.",
            )
            return

        self._value = parsed
        self.accept()

    @classmethod
    def get_double(
        cls,
        parent,
        title,
        label,
        value=0.0,
        minimum=0.0,
        maximum=100000.0,
        decimals=1,
        hint_text="",
        field_tooltip="",
    ):
        dialog = cls(
            parent,
            title,
            label,
            value=value,
            minimum=minimum,
            maximum=maximum,
            decimals=decimals,
            hint_text=hint_text,
            field_tooltip=field_tooltip,
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.value(), True

        return 0.0, False
