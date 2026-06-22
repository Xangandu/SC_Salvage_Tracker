"""MobiGlas-Farbwahl-Dialog (Ersatz für QColorDialog.getColor)."""

from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QColorDialog,
)

from ui.page_layout import (
    page_title,
    hud_divider,
    primary_button,
)
from ui.mobiglas_window_frame import (
    MobiglasFramelessMixin,
    apply_mobiglas_window_frame,
)


def _secondary_button(text):
    button = QPushButton(text)
    button.setObjectName("secondaryAction")
    return button


class MobiglasColorDialog(MobiglasFramelessMixin, QDialog):

    def __init__(
        self,
        parent,
        title,
        initial=None,
    ):
        super().__init__(parent)

        if initial is None or not initial.isValid():
            initial = QColor("#00D9FF")

        self._initial = QColor(initial)
        self._selected = QColor(initial)

        self.setObjectName("mobiglasDialog")
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(580, 460)
        self.setMinimumSize(520, 420)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(page_title(title.upper()))
        layout.addLayout(hud_divider())

        self._picker = QColorDialog(self._initial, self)
        self._picker.setObjectName("mobiglasColorPicker")
        self._picker.setOptions(
            QColorDialog.ColorDialogOption.DontUseNativeDialog
            | QColorDialog.ColorDialogOption.NoButtons
        )
        self._picker.setWindowFlags(
            Qt.WindowType.Widget
        )
        layout.addWidget(self._picker, 1)

        buttons = QHBoxLayout()
        buttons.setSpacing(12)
        buttons.addStretch()

        cancel_button = _secondary_button("Abbrechen")
        cancel_button.clicked.connect(self.reject)

        confirm_button = primary_button("OK")
        confirm_button.clicked.connect(self._accept_color)
        confirm_button.setDefault(True)

        buttons.addWidget(cancel_button)
        buttons.addWidget(confirm_button)
        layout.addLayout(buttons)

        self.setLayout(layout)

        apply_mobiglas_window_frame(
            self,
            title=title,
            dialog=True,
        )

    def selected_color(self) -> QColor:
        return QColor(self._selected)

    def _accept_color(self):
        color = self._picker.currentColor()
        if not color.isValid():
            color = self._picker.selectedColor()
        if color.isValid():
            self._selected = color
            self.accept()

    @classmethod
    def get_color(
        cls,
        parent,
        title,
        initial=None,
    ):
        dialog = cls(parent, title, initial=initial)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.selected_color(), True

        return QColor(), False
