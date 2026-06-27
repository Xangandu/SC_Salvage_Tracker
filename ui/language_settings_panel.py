"""Spracheinstellungen — eigener Tab unter Einstellungen."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config.i18n import SUPPORTED_LANGUAGES, normalize_language, tr
from ui.language_switch import change_user_language
from ui.page_layout import primary_button


def _secondary_button(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("secondaryAction")
    return button


class LanguageSettingsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("languageSettingsPanel")

        self._db = None
        self._user = None
        self._main_window = None
        self._syncing = False
        self._saved_language = normalize_language(None)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.hint_label = QLabel(tr("admin.language.tab_hint"))
        self.hint_label.setObjectName("mutedLabel")
        self.hint_label.setWordWrap(True)

        self.language_combo = QComboBox()
        self.language_combo.setObjectName("languageSettingsCombo")
        self._populate_options()

        field_label = QLabel(tr("admin.language"))
        field_label.setObjectName("formLabel")
        field_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.cancel_button = _secondary_button(tr("common.cancel"))
        self.save_button = primary_button(tr("common.save"))
        self.cancel_button.clicked.connect(self._cancel_changes)
        self.save_button.clicked.connect(self._save_changes)
        self.language_combo.currentIndexChanged.connect(
            self._update_action_state
        )

        actions = QHBoxLayout()
        actions.setSpacing(12)
        actions.addWidget(self.cancel_button)
        actions.addWidget(self.save_button)
        actions.addStretch()

        layout.addWidget(self.hint_label)
        layout.addWidget(field_label)
        layout.addWidget(self.language_combo)
        layout.addLayout(actions)

        self._update_action_state()

    def bind(self, db, user, main_window) -> None:
        self._db = db
        self._user = user
        self._main_window = main_window
        self.refresh()

    def refresh(self) -> None:
        if not self._db or not self._user:
            return

        self.hint_label.setText(tr("admin.language.tab_hint"))
        self.cancel_button.setText(tr("common.cancel"))
        self.save_button.setText(tr("common.save"))
        self._populate_options()

        effective = self._db.settings.resolve_effective_settings(
            self._user["id"]
        )
        self._saved_language = normalize_language(
            effective.get("language")
        )
        self._syncing = True
        index = self.language_combo.findData(self._saved_language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        self._syncing = False
        self._update_action_state()

    def _populate_options(self) -> None:
        current = self.language_combo.currentData()
        self.language_combo.blockSignals(True)
        self.language_combo.clear()
        for lang_code in SUPPORTED_LANGUAGES:
            self.language_combo.addItem(
                tr(f"language.name.{lang_code}"),
                lang_code,
            )
        if current is not None:
            index = self.language_combo.findData(current)
            if index >= 0:
                self.language_combo.setCurrentIndex(index)
        self.language_combo.blockSignals(False)

    def _selected_language(self) -> str:
        return normalize_language(self.language_combo.currentData())

    def _has_pending_changes(self) -> bool:
        return self._selected_language() != self._saved_language

    def _update_action_state(self) -> None:
        changed = self._has_pending_changes()
        self.cancel_button.setEnabled(changed)
        self.save_button.setEnabled(changed)

    def _cancel_changes(self) -> None:
        if not self._has_pending_changes():
            return

        self._syncing = True
        index = self.language_combo.findData(self._saved_language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        self._syncing = False
        self._update_action_state()

    def _save_changes(self) -> None:
        if self._syncing or not self._db or not self._user:
            return

        selected = self._selected_language()
        if selected == self._saved_language:
            return

        change_user_language(
            main_window=self._main_window,
            db=self._db,
            user=self._user,
            selected_language=selected,
            parent_widget=self,
        )
