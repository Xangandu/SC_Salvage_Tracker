"""UI-Hülle für editionsgesperrte Bereiche (sichtbar, aber gesperrt + Teaser)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config.editions import (
    edition_title,
    feature_teaser_text,
    has_feature,
    required_edition,
)
from ui.mobiglas_message_box import information as mobiglas_information
from ui.page_layout import info_panel, primary_button


class EditionFeaturePanel(QWidget):
    """Zeigt Inhalt gesperrt mit Teaser, wenn die Edition das Feature nicht hat."""

    def __init__(
        self,
        feature_id: str,
        db,
        parent=None,
    ):
        super().__init__(parent)
        self._feature_id = feature_id
        self._db = db

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        self._teaser_frame, teaser_layout = info_panel()
        self._teaser_frame.setObjectName("editionTeaserPanel")
        self._teaser_frame.hide()

        needed = required_edition(feature_id)
        badge = QLabel(f"◆ SC SALVAGE TRACKER - {edition_title(needed).upper()}")
        badge.setObjectName("editionTeaserBadge")
        teaser_layout.addWidget(badge)

        self._teaser_body = QLabel(feature_teaser_text(feature_id))
        self._teaser_body.setWordWrap(True)
        self._teaser_body.setObjectName("mutedLabel")
        teaser_layout.addWidget(self._teaser_body)

        self._learn_button = primary_button(
            f"Mehr zur {edition_title(needed)}"
        )
        self._learn_button.clicked.connect(self._show_edition_info)
        teaser_layout.addWidget(
            self._learn_button,
            0,
            Qt.AlignmentFlag.AlignLeft,
        )

        root.addWidget(self._teaser_frame)

        self._content_host = QFrame()
        self._content_host.setObjectName("editionFeatureContent")
        self._content_layout = QVBoxLayout(self._content_host)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(8)
        root.addWidget(self._content_host, 1)

        self.refresh()

    @property
    def content_layout(self) -> QVBoxLayout:
        return self._content_layout

    def refresh(self):
        allowed = has_feature(self._feature_id, self._db)
        self._teaser_frame.setVisible(not allowed)
        self._content_host.setEnabled(allowed)
        if not allowed:
            self._content_host.setStyleSheet(
                "QFrame#editionFeatureContent { opacity: 0.92; }"
            )
        else:
            self._content_host.setStyleSheet("")

    def _show_edition_info(self):
        needed = required_edition(self._feature_id)
        mobiglas_information(
            self.window(),
            edition_title(needed),
            feature_teaser_text(self._feature_id)
            + "\n\n"
            "Die SOLO Version bleibt für Einzelspieler kostenlos. "
            "CREW und ORGA erweitern das Programm um Mehrspieler "
            "und Organisation — ohne Solo-Features zu entfernen.\n\n"
            "Supporter-Keys kannst du unter Einstellungen → "
            "Unterstützen einlösen.",
        )
