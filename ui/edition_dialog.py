"""Hinweis, wenn eine Funktion in der aktuellen Edition gesperrt ist."""

from config.editions import (
    edition_title,
    feature_teaser_text,
    required_edition,
)
from config.i18n import tr
from ui.mobiglas_message_box import information as mobiglas_information


def show_edition_locked(parent, feature_id: str) -> None:
    needed = required_edition(feature_id)
    mobiglas_information(
        parent,
        tr("edition.locked.title", edition=edition_title(needed)),
        feature_teaser_text(feature_id),
    )
