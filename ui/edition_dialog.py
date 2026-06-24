"""Hinweis, wenn eine Funktion in der aktuellen Edition gesperrt ist."""

from config.editions import (
    edition_title,
    feature_teaser_text,
    required_edition,
)
from ui.mobiglas_message_box import information as mobiglas_information


def show_edition_locked(parent, feature_id: str) -> None:
    needed = required_edition(feature_id)
    mobiglas_information(
        parent,
        f"{edition_title(needed)} erforderlich",
        feature_teaser_text(feature_id),
    )
