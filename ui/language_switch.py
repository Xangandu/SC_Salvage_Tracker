"""Sprache wechseln, speichern und Anwendung neu starten."""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget

from auth.app_restart import prepare_language_restart_login
from config.i18n import (
    normalize_language,
    save_language_choice,
    set_language,
    tr,
)


def change_user_language(
    *,
    main_window,
    db,
    user: dict,
    selected_language: str,
    parent_widget: QWidget,
) -> bool:
    """Sprache speichern und Neustart anstoßen. True = Neustart geplant."""
    selected = normalize_language(selected_language)
    previous = normalize_language(
        db.settings.resolve_effective_settings(user["id"]).get(
            "language"
        )
    )
    if selected == previous:
        return False

    save_language_choice(db, selected)
    set_language(selected)
    db.settings.save_user_settings(
        user["id"],
        {"language": selected},
    )

    prepare_language_restart_login(
        db,
        user,
        is_network_client=getattr(
            main_window,
            "is_network_client",
            False,
        ),
    )

    QMessageBox.information(
        parent_widget,
        tr("nav.language.title"),
        tr("admin.language.restart_now"),
    )
    if hasattr(main_window, "request_language_restart"):
        main_window.request_language_restart()
    return True
