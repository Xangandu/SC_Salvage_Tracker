"""Farbwahl-Dialog im Tracker-Design (Ersatz für QColorDialog.getColor)."""

from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QColorDialog,
    QSizePolicy,
    QScrollArea,
)

from config.i18n import tr
from ui.page_layout import primary_button, page_panel
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
            initial = QColor("#E07A2A")

        self._initial = QColor(initial)
        self._selected = QColor(initial)

        self.setObjectName("mobiglasDialog")
        self.setWindowTitle(title)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(12)

        panel, panel_layout = page_panel()
        panel.setObjectName("colorPickerPanel")
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(0)

        self._picker = QColorDialog(self._initial, panel)
        self._picker.setObjectName("colorPicker")
        self._picker.setOptions(
            QColorDialog.ColorDialogOption.DontUseNativeDialog
            | QColorDialog.ColorDialogOption.NoButtons
        )
        self._picker.setWindowFlags(
            Qt.WindowType.Widget
        )
        self._picker.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )

        self._scroll = QScrollArea(panel)
        self._scroll.setObjectName("colorPickerScroll")
        self._scroll.setWidgetResizable(False)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self._scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._scroll.setWidget(self._picker)

        panel_layout.addWidget(self._scroll)
        layout.addWidget(panel, 1)

        buttons = QHBoxLayout()
        buttons.setSpacing(12)
        buttons.addStretch()

        cancel_button = _secondary_button(tr("common.cancel"))
        cancel_button.clicked.connect(self.reject)

        confirm_button = primary_button(tr("common.ok"))
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

        self._apply_picker_geometry()

    def _apply_picker_geometry(self):
        self._picker.adjustSize()
        hint = self._picker.sizeHint()
        picker_w = hint.width()
        picker_h = hint.height()

        self._picker.setFixedSize(picker_w, picker_h)
        self._scroll.setMinimumHeight(picker_h)

        dialog_w = picker_w + 88
        dialog_h = picker_h + 40 + 52 + 72
        self.setMinimumSize(
            max(660, dialog_w),
            max(560, dialog_h),
        )
        self.resize(
            max(720, dialog_w),
            max(600, dialog_h),
        )

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_picker_geometry()

        parent = self.parentWidget()
        if parent is not None:
            center = parent.frameGeometry().center()
        else:
            screen = QApplication.primaryScreen()
            if screen is None:
                return
            center = screen.availableGeometry().center()

        frame = self.frameGeometry()
        frame.moveCenter(center)
        self.move(frame.topLeft())

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
