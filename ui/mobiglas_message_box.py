"""MobiGlas-Meldungsfenster mit einheitlicher Titelleiste."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
)

from config.paths import asset_path
from config.i18n import tr
from ui.mobiglas_window_frame import (
    MobiglasFramelessMixin,
    apply_mobiglas_window_frame,
)
from ui.page_layout import primary_button, svg_icon_widget

_ICON_PATHS = {
    "info": "assets/images/icons/info.svg",
    "warning": "assets/images/icons/warning.svg",
    "critical": "assets/images/icons/warning.svg",
    "question": "assets/images/icons/info.svg",
}

_BUTTON_ORDER = (
    QMessageBox.StandardButton.Yes,
    QMessageBox.StandardButton.No,
    QMessageBox.StandardButton.Ok,
    QMessageBox.StandardButton.Cancel,
    QMessageBox.StandardButton.Close,
    QMessageBox.StandardButton.Save,
    QMessageBox.StandardButton.Discard,
    QMessageBox.StandardButton.Apply,
    QMessageBox.StandardButton.Retry,
    QMessageBox.StandardButton.Ignore,
    QMessageBox.StandardButton.Abort,
)

_BUTTON_I18N = {
    QMessageBox.StandardButton.Ok: "common.ok",
    QMessageBox.StandardButton.Yes: "common.yes",
    QMessageBox.StandardButton.No: "common.no",
    QMessageBox.StandardButton.Cancel: "common.cancel",
    QMessageBox.StandardButton.Close: "common.close",
    QMessageBox.StandardButton.Save: "common.save",
    QMessageBox.StandardButton.Discard: "common.discard",
    QMessageBox.StandardButton.Apply: "common.apply",
    QMessageBox.StandardButton.Retry: "common.retry",
    QMessageBox.StandardButton.Ignore: "common.ignore",
    QMessageBox.StandardButton.Abort: "common.abort",
}


def _secondary_button(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("secondaryAction")
    return button


def _expand_buttons(buttons):
    if buttons == QMessageBox.StandardButton.NoButton:
        return [QMessageBox.StandardButton.Ok]

    flags = int(buttons)
    selected = [
        button
        for button in _BUTTON_ORDER
        if flags & int(button)
    ]
    return selected or [QMessageBox.StandardButton.Ok]


def _button_label(button: QMessageBox.StandardButton) -> str:
    key = _BUTTON_I18N.get(button)
    if key:
        return tr(key)
    return tr("common.ok")


def _create_action_button(
    button: QMessageBox.StandardButton,
    *,
    primary: bool,
) -> QPushButton:
    label = _button_label(button)
    if primary:
        return primary_button(label)
    return _secondary_button(label)


def _is_primary_button(
    button: QMessageBox.StandardButton,
    button_specs: list[QMessageBox.StandardButton],
) -> bool:
    if button == QMessageBox.StandardButton.Yes and len(button_specs) > 1:
        return True
    if button == QMessageBox.StandardButton.Save:
        return True
    return (
        len(button_specs) == 1
        and button == QMessageBox.StandardButton.Ok
    )


class MobiglasMessageBox(MobiglasFramelessMixin, QDialog):

    def __init__(
        self,
        parent,
        title: str,
        text: str,
        *,
        icon_kind: str = "info",
        buttons=QMessageBox.StandardButton.Ok,
        default_button=QMessageBox.StandardButton.NoButton,
    ):
        super().__init__(parent)

        self.setObjectName("mobiglasDialog")
        self.setWindowTitle(title)
        self.setModal(True)
        self._clicked = QMessageBox.StandardButton.NoButton

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        body = QHBoxLayout()
        body.setSpacing(16)

        icon_path = asset_path(
            _ICON_PATHS.get(icon_kind, _ICON_PATHS["info"])
        )
        body.addWidget(
            svg_icon_widget(str(icon_path), size=40),
            0,
            Qt.AlignmentFlag.AlignTop,
        )

        message = QLabel(text)
        message.setWordWrap(True)
        message.setObjectName("infoValue")
        message.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        body.addWidget(message, 1)
        layout.addLayout(body)

        button_row = QHBoxLayout()
        button_row.addStretch()

        button_specs = _expand_buttons(buttons)
        if default_button == QMessageBox.StandardButton.NoButton:
            if QMessageBox.StandardButton.Ok in button_specs:
                default_button = QMessageBox.StandardButton.Ok
            elif QMessageBox.StandardButton.Yes in button_specs:
                default_button = QMessageBox.StandardButton.Yes
            else:
                default_button = button_specs[-1]

        for button in button_specs:
            widget = _create_action_button(
                button,
                primary=_is_primary_button(button, button_specs),
            )
            if button == default_button:
                widget.setDefault(True)
                widget.setFocus()

            widget.clicked.connect(
                lambda checked=False, value=button: self._on_button(value)
            )
            button_row.addWidget(widget)

        layout.addLayout(button_row)

        apply_mobiglas_window_frame(
            self,
            title=title,
            dialog=True,
        )

        self.setMinimumWidth(420)
        self.adjustSize()

    def _on_button(self, button: QMessageBox.StandardButton):
        self._clicked = button
        self.accept()

    def exec_with_result(self) -> QMessageBox.StandardButton:
        self.exec()
        return self._clicked


def _show_message(
    parent,
    title: str,
    text: str,
    *,
    icon_kind: str,
    buttons=QMessageBox.StandardButton.Ok,
    default_button=QMessageBox.StandardButton.NoButton,
) -> QMessageBox.StandardButton:
    dialog = MobiglasMessageBox(
        parent,
        title,
        text,
        icon_kind=icon_kind,
        buttons=buttons,
        default_button=default_button,
    )
    return dialog.exec_with_result()


def information(
    parent,
    title: str,
    text: str,
    buttons=QMessageBox.StandardButton.Ok,
    default_button=QMessageBox.StandardButton.NoButton,
):
    return _show_message(
        parent,
        title,
        text,
        icon_kind="info",
        buttons=buttons,
        default_button=default_button,
    )


def warning(
    parent,
    title: str,
    text: str,
    buttons=QMessageBox.StandardButton.Ok,
    default_button=QMessageBox.StandardButton.NoButton,
):
    return _show_message(
        parent,
        title,
        text,
        icon_kind="warning",
        buttons=buttons,
        default_button=default_button,
    )


def critical(
    parent,
    title: str,
    text: str,
    buttons=QMessageBox.StandardButton.Ok,
    default_button=QMessageBox.StandardButton.NoButton,
):
    return _show_message(
        parent,
        title,
        text,
        icon_kind="critical",
        buttons=buttons,
        default_button=default_button,
    )


def question(
    parent,
    title: str,
    text: str,
    buttons=(
        QMessageBox.StandardButton.Yes
        | QMessageBox.StandardButton.No
    ),
    default_button=QMessageBox.StandardButton.NoButton,
):
    return _show_message(
        parent,
        title,
        text,
        icon_kind="question",
        buttons=buttons,
        default_button=default_button,
    )


def install_mobiglas_message_boxes():
    """Ersetzt QMessageBox-Standarddialoge durch MobiGlas-Fenster."""
    QMessageBox.information = information
    QMessageBox.warning = warning
    QMessageBox.critical = critical
    QMessageBox.question = question
