"""
Feingranulare Berechtigungen und Seitenzugriff.

Nur die Rolle „Administrator“ ist systemseitig vordefiniert.
Weitere Rollen legt der Admin selbst an und weist Rechte zu.

Bestehende Legacy-Rollen (Manager, Operator, Viewer) behalten
ihren Namen; fehlende Rechte werden einmalig per Backfill gesetzt,
bis der Admin sie manuell anpasst.
"""

import auth.session as user_session

from config.setup import ROLE_SUPER_ADMIN

ROLE_ADMIN = "Administrator"

# Legacy-Rollennamen (bestehende Installationen, Option 2: nicht umbenennen)
ROLE_LEGACY_OFFICER = "Manager"
ROLE_LEGACY_MEMBER = "Operator"
ROLE_LEGACY_GUEST = "Viewer"

PERM_USERS_MANAGE = "users.manage"
PERM_ROLES_MANAGE = "roles.manage"
PERM_SETTINGS_MANAGE = "settings.manage"
PERM_DATABASE_RESET = "database.reset"
PERM_SESSIONS_MANAGE = "sessions.manage"
PERM_SESSIONS_MANAGE_OWN = "sessions.manage_own"
PERM_CREW_MANAGE = "crew.manage"
PERM_REFINERY_MANAGE = "refinery.manage"
PERM_SALES_MANAGE = "sales.manage"
PERM_PAYOUTS_MANAGE = "payouts.manage"
PERM_PAYOUTS_APPROVE = "payouts.approve"
PERM_PAYOUTS_VIEW_OWN = "payouts.view_own"
PERM_HISTORY_VIEW = "history.view"
PERM_STATISTICS_VIEW = "statistics.view"
PERM_DASHBOARD_VIEW = "dashboard.view"

PERMISSION_LABELS = {
    PERM_USERS_MANAGE: "Benutzer verwalten",
    PERM_ROLES_MANAGE: "Rollen verwalten",
    PERM_SETTINGS_MANAGE: "Systemeinstellungen ändern",
    PERM_DATABASE_RESET: "Datenbank zurücksetzen",
    PERM_SESSIONS_MANAGE: "Alle Sitzungen verwalten",
    PERM_SESSIONS_MANAGE_OWN: "Eigene Sitzungen verwalten",
    PERM_CREW_MANAGE: "Crew verwalten",
    PERM_REFINERY_MANAGE: "Raffinerie verwalten",
    PERM_SALES_MANAGE: "Verkäufe durchführen",
    PERM_PAYOUTS_MANAGE: "Auszahlungen erstellen",
    PERM_PAYOUTS_APPROVE: "Auszahlungen freigeben",
    PERM_PAYOUTS_VIEW_OWN: "Eigene Auszahlungen ansehen",
    PERM_HISTORY_VIEW: "Historie ansehen",
    PERM_STATISTICS_VIEW: "Statistiken / Auszahlung ansehen",
    PERM_DASHBOARD_VIEW: "Dashboard nutzen",
}

PERMISSION_GROUPS = (
    ("users_system", (
        PERM_USERS_MANAGE,
        PERM_ROLES_MANAGE,
        PERM_SETTINGS_MANAGE,
        PERM_DATABASE_RESET,
    )),
    ("sessions_crew", (
        PERM_SESSIONS_MANAGE,
        PERM_SESSIONS_MANAGE_OWN,
        PERM_CREW_MANAGE,
    )),
    ("operations", (
        PERM_REFINERY_MANAGE,
        PERM_SALES_MANAGE,
    )),
    ("payouts", (
        PERM_PAYOUTS_MANAGE,
        PERM_PAYOUTS_APPROVE,
        PERM_PAYOUTS_VIEW_OWN,
    )),
    ("views", (
        PERM_DASHBOARD_VIEW,
        PERM_STATISTICS_VIEW,
        PERM_HISTORY_VIEW,
    )),
)

ALL_PERMISSION_NAMES = (
    PERM_USERS_MANAGE,
    PERM_ROLES_MANAGE,
    PERM_SETTINGS_MANAGE,
    PERM_DATABASE_RESET,
    PERM_SESSIONS_MANAGE,
    PERM_SESSIONS_MANAGE_OWN,
    PERM_CREW_MANAGE,
    PERM_REFINERY_MANAGE,
    PERM_SALES_MANAGE,
    PERM_PAYOUTS_MANAGE,
    PERM_PAYOUTS_APPROVE,
    PERM_PAYOUTS_VIEW_OWN,
    PERM_HISTORY_VIEW,
    PERM_STATISTICS_VIEW,
    PERM_DASHBOARD_VIEW,
)

LEGACY_ROLE_PERMISSIONS = {
    ROLE_LEGACY_OFFICER: (
        PERM_SESSIONS_MANAGE,
        PERM_CREW_MANAGE,
        PERM_REFINERY_MANAGE,
        PERM_SALES_MANAGE,
        PERM_PAYOUTS_MANAGE,
        PERM_PAYOUTS_APPROVE,
        PERM_HISTORY_VIEW,
        PERM_STATISTICS_VIEW,
        PERM_DASHBOARD_VIEW,
    ),
    ROLE_LEGACY_MEMBER: (
        PERM_SESSIONS_MANAGE_OWN,
        PERM_PAYOUTS_VIEW_OWN,
        PERM_STATISTICS_VIEW,
        PERM_DASHBOARD_VIEW,
    ),
    ROLE_LEGACY_GUEST: (
        PERM_HISTORY_VIEW,
        PERM_STATISTICS_VIEW,
        PERM_DASHBOARD_VIEW,
    ),
}

PAGE_PERMISSIONS = {
    "dashboard": {
        "read": (PERM_DASHBOARD_VIEW,),
        "write": (PERM_DASHBOARD_VIEW,),
    },
    "session": {
        "read": (
            PERM_SESSIONS_MANAGE,
            PERM_SESSIONS_MANAGE_OWN,
        ),
        "write": (
            PERM_SESSIONS_MANAGE,
            PERM_SESSIONS_MANAGE_OWN,
        ),
    },
    "salvage": {
        "read": (
            PERM_SESSIONS_MANAGE,
            PERM_SESSIONS_MANAGE_OWN,
        ),
        "write": (
            PERM_SESSIONS_MANAGE,
            PERM_SESSIONS_MANAGE_OWN,
        ),
    },
    "refinery": {
        "read": (PERM_REFINERY_MANAGE,),
        "write": (PERM_REFINERY_MANAGE,),
    },
    "sales": {
        "read": (PERM_SALES_MANAGE,),
        "write": (PERM_SALES_MANAGE,),
    },
    "statistics": {
        "read": (
            PERM_STATISTICS_VIEW,
            PERM_PAYOUTS_VIEW_OWN,
            PERM_PAYOUTS_MANAGE,
        ),
        "write": (PERM_PAYOUTS_MANAGE,),
    },
    "history": {
        "read": (PERM_HISTORY_VIEW,),
        "write": (),
    },
    "settings": {
        "read": (
            PERM_USERS_MANAGE,
            PERM_ROLES_MANAGE,
            PERM_SETTINGS_MANAGE,
            PERM_DATABASE_RESET,
        ),
        "write": (
            PERM_USERS_MANAGE,
            PERM_ROLES_MANAGE,
            PERM_SETTINGS_MANAGE,
            PERM_DATABASE_RESET,
        ),
    },
    "administration": {
        "read": (
            PERM_USERS_MANAGE,
            PERM_DATABASE_RESET,
        ),
        "write": (
            PERM_USERS_MANAGE,
            PERM_DATABASE_RESET,
        ),
    },
}


def _user_permissions(user):
    if not user:
        return set()

    perms = user.get("permissions")
    if perms is None:
        return set()

    return set(perms)


def permissions_for_user(user=None):
    user = user or user_session.get_user()

    if not user:
        return set()

    if is_super_administrator(user):
        return set(ALL_PERMISSION_NAMES)

    if is_administrator(user):
        return set(ALL_PERMISSION_NAMES)

    return _user_permissions(user)


def filter_role_permissions_for_actor(
    actor,
    existing_permissions,
    requested_permissions,
    actor_grantable=None,
):
    """Rechte einer Rolle nur im Rahmen der eigenen Rechte ändern."""
    if is_super_administrator(actor):
        return set(requested_permissions or ())

    if is_administrator(actor):
        return set(requested_permissions or ())

    existing = set(existing_permissions or ())
    requested = set(requested_permissions or ())
    grantable = (
        set(actor_grantable)
        if actor_grantable is not None
        else permissions_for_user(actor)
    )

    locked = existing - grantable
    managed = requested & grantable

    return locked | managed


def role_permissions_exceed_actor(
    actor,
    role_permissions,
    actor_grantable=None,
):
    actor_perms = (
        set(actor_grantable)
        if actor_grantable is not None
        else permissions_for_user(actor)
    )
    role_perms = set(role_permissions or ())
    return bool(role_perms - actor_perms)


def forbidden_role_permission_changes(
    actor,
    existing_permissions,
    requested_permissions,
    actor_grantable=None,
):
    """Rechte, die der Actor nicht vergeben oder entziehen darf."""
    if is_super_administrator(actor):
        return set(requested_permissions or ())

    if is_administrator(actor):
        return set()

    existing = set(existing_permissions or ())
    requested = set(requested_permissions or ())
    allowed = filter_role_permissions_for_actor(
        actor,
        existing,
        requested,
        actor_grantable=actor_grantable,
    )

    return requested ^ allowed


def is_super_administrator(user=None):
    user = user or user_session.get_user()

    if not user:
        return False

    if user.get("is_system"):
        return True

    return user.get("role_name") == ROLE_SUPER_ADMIN


def is_administrator(user=None):
    user = user or user_session.get_user()

    return bool(
        user
        and user.get("role_name") == ROLE_ADMIN
    )


def has_permission(permission_name, user=None):
    user = user or user_session.get_user()

    if not user:
        return False

    if is_super_administrator(user):
        return True

    if is_administrator(user):
        return True

    return permission_name in _user_permissions(user)


def can_access(user, page):
    if not user:
        return False

    # Einstellungen/Design: jeder angemeldete Benutzer
    if page == "settings":
        return True

    requirements = PAGE_PERMISSIONS.get(
        page,
        {},
    ).get("read", ())

    if not requirements:
        return False

    return any(
        has_permission(perm, user)
        for perm in requirements
    )


def can_write(user, page):
    if not can_access(user, page):
        return False

    write_requirements = PAGE_PERMISSIONS.get(
        page,
        {},
    ).get("write", ())

    if not write_requirements:
        return False

    return any(
        has_permission(perm, user)
        for perm in write_requirements
    )


def sessions_restrict_to_own(user=None):
    user = user or user_session.get_user()

    return (
        has_permission(PERM_SESSIONS_MANAGE_OWN, user)
        and not has_permission(PERM_SESSIONS_MANAGE, user)
    )


def payouts_restrict_to_own(user=None):
    user = user or user_session.get_user()

    return (
        has_permission(PERM_PAYOUTS_VIEW_OWN, user)
        and not has_permission(PERM_PAYOUTS_MANAGE, user)
    )


def apply_widget_permissions(widget, user, page):
    from PySide6.QtWidgets import (
        QPushButton,
        QLineEdit,
        QComboBox,
        QTextEdit,
    )

    writable = can_write(user, page)

    for button in widget.findChildren(QPushButton):
        button.setEnabled(writable)

    for field in widget.findChildren(QLineEdit):
        field.setReadOnly(not writable)

    for field in widget.findChildren(QTextEdit):
        field.setReadOnly(not writable)

    for field in widget.findChildren(QComboBox):
        field.setEnabled(writable)
