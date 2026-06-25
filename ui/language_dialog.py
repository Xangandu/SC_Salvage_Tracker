"""Sprachauswahl beim ersten Start (Standard: Englisch)."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from config.i18n import (
    DEFAULT_LANGUAGE,
    is_language_confirmed,
    normalize_language,
    set_language,
    tr,
)
from database.access import get_database
from ui.mobiglas_window_frame import (
    MobiglasFramelessMixin,
    apply_mobiglas_window_frame,
)
from ui.page_layout import hud_divider, page_title, primary_button


class LanguageDialog(MobiglasFramelessMixin, QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected = DEFAULT_LANGUAGE
        self.db = get_database()

        saved = DEFAULT_LANGUAGE
        if is_language_confirmed(self.db):
            saved = normalize_language(
                self.db.settings.get_app_setting("language", DEFAULT_LANGUAGE)
            )
        self._selected = saved
        set_language(self._selected)

        self.setObjectName("mobiglasDialog")
        self.setModal(True)
        self.resize(520, 420)
        self.setWindowTitle("SC Salvage Tracker")

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(440)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 24)
        card_layout.setSpacing(12)

        logo = QLabel("MOBIGLAS")
        logo.setObjectName("loginLogo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(logo)
        card_layout.addWidget(
            page_title(tr("language.dialog.title").upper())
        )
        card_layout.addLayout(hud_divider())

        subtitle = QLabel(tr("language.dialog.subtitle"))
        subtitle.setObjectName("mutedLabel")
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(subtitle)
        self.subtitle_label = subtitle

        self._group = QButtonGroup(self)

        self.radio_en = QRadioButton(tr("language.name.en"))
        self.radio_de = QRadioButton(tr("language.name.de"))
        self.radio_en.setObjectName("languageOption")
        self.radio_de.setObjectName("languageOption")

        self._group.addButton(self.radio_en, 0)
        self._group.addButton(self.radio_de, 1)

        if self._selected == "de":
            self.radio_de.setChecked(True)
        else:
            self.radio_en.setChecked(True)

        self.radio_en.toggled.connect(self._on_language_toggled)
        self.radio_de.toggled.connect(self._on_language_toggled)

        card_layout.addWidget(self.radio_en)
        card_layout.addWidget(self.radio_de)

        hint = QLabel(tr("language.dialog.hint"))
        hint.setObjectName("mutedLabel")
        hint.setWordWrap(True)
        card_layout.addWidget(hint)
        self.hint_label = hint

        self.continue_button = primary_button(
            tr("language.dialog.continue").upper()
        )
        self.continue_button.clicked.connect(self.accept)
        card_layout.addWidget(self.continue_button)

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(card)
        row.addStretch()
        layout.addStretch(1)
        layout.addLayout(row)
        layout.addStretch(1)
        self.setLayout(layout)

        apply_mobiglas_window_frame(
            self,
            title=tr("language.dialog.title"),
            dialog=True,
            show_close=False,
        )

    def _on_language_toggled(self):
        if self.radio_de.isChecked():
            self._selected = "de"
        else:
            self._selected = "en"
        set_language(self._selected)
        self._refresh_texts()

    def _refresh_texts(self):
        self.setWindowTitle("SC Salvage Tracker")
        self.subtitle_label.setText(tr("language.dialog.subtitle"))
        self.hint_label.setText(tr("language.dialog.hint"))
        self.radio_en.setText(tr("language.name.en"))
        self.radio_de.setText(tr("language.name.de"))
        self.continue_button.setText(
            tr("language.dialog.continue").upper()
        )
        if hasattr(self, "_mobiglas_title_bar"):
            self._mobiglas_title_bar.set_title(
                tr("language.dialog.title")
            )

    @property
    def selected_language(self) -> str:
        return self._selected
