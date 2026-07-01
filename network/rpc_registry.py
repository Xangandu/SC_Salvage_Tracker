"""RPC-Pfad-Regeln und Berechtigungsprüfung auf dem Host."""

from config.i18n import tr
from config.permissions import (
    PERM_CREW_MANAGE,
    PERM_DASHBOARD_VIEW,
    PERM_DATABASE_RESET,
    PERM_HISTORY_VIEW,
    PERM_PAYOUTS_APPROVE,
    PERM_PAYOUTS_MANAGE,
    PERM_PAYOUTS_VIEW_OWN,
    PERM_REFINERY_MANAGE,
    PERM_ROLES_MANAGE,
    PERM_SALES_MANAGE,
    PERM_STORAGE_MANAGE,
    PERM_SESSIONS_MANAGE,
    PERM_SESSIONS_MANAGE_OWN,
    PERM_SETTINGS_MANAGE,
    PERM_STATISTICS_VIEW,
    PERM_USERS_MANAGE,
    has_permission,
)

# Pfade ohne explizite Regel: Lesen erlaubt für authentifizierte Verbindung.
# Schreibende Methoden müssen gelistet sein.

WRITE_RPC_RULES = {
    "create_session": (PERM_SESSIONS_MANAGE, PERM_SESSIONS_MANAGE_OWN),
    "end_session": (PERM_SESSIONS_MANAGE, PERM_SESSIONS_MANAGE_OWN),
    "add_material": (PERM_SESSIONS_MANAGE, PERM_SESSIONS_MANAGE_OWN),
    "add_crew_member": (PERM_CREW_MANAGE, PERM_SESSIONS_MANAGE_OWN),
    "add_cost": (PERM_CREW_MANAGE, PERM_SESSIONS_MANAGE_OWN),
    "create_refinery_job_from_batches": (PERM_REFINERY_MANAGE,),
    "create_refinery_job_from_pool": (PERM_REFINERY_MANAGE,),
    "sync_expired_refinery_jobs": (PERM_REFINERY_MANAGE,),
    "complete_refinery_job": (PERM_REFINERY_MANAGE,),
    "record_storage_sale": (PERM_SALES_MANAGE,),
    "create_payout": (PERM_PAYOUTS_MANAGE,),
    "approve_payout": (PERM_PAYOUTS_APPROVE,),
    "reassign_cost_payer": (PERM_PAYOUTS_MANAGE,),
    "reassign_refinery_cost_payer": (PERM_PAYOUTS_MANAGE,),
    "delete_session": (PERM_SESSIONS_MANAGE, PERM_SESSIONS_MANAGE_OWN),
    "cancel_refinery_job": (PERM_REFINERY_MANAGE,),
    "delete_refinery_job": (PERM_REFINERY_MANAGE,),
    "create_material_stockpile": (PERM_STORAGE_MANAGE,),
    "transfer_material_stockpile": (PERM_STORAGE_MANAGE,),
    "transfer_from_material_pool": (PERM_STORAGE_MANAGE,),
    "withdraw_from_material_pool": (PERM_STORAGE_MANAGE,),
    "update_material_stockpile": (PERM_STORAGE_MANAGE,),
    "delete_material_stockpile": (PERM_STORAGE_MANAGE,),
    "delete_stockpile_event": (PERM_STORAGE_MANAGE,),
    "acknowledge_stockpile_idle": (PERM_STORAGE_MANAGE,),
    "set_stockpile_reserve": (PERM_STORAGE_MANAGE,),
    "clear_stockpile_reserve": (PERM_STORAGE_MANAGE,),
    "mark_stockpile_moved": (PERM_STORAGE_MANAGE,),
    "void_sale": (PERM_SALES_MANAGE,),
    "void_payout": (PERM_PAYOUTS_MANAGE,),
    "change_password": None,
    "create_user": (PERM_USERS_MANAGE,),
    "update_user_display_name": (PERM_USERS_MANAGE,),
    "reset_user_password": (PERM_USERS_MANAGE,),
    "update_user_role": (PERM_USERS_MANAGE,),
    "set_user_active": (PERM_USERS_MANAGE,),
    "delete_user": (PERM_USERS_MANAGE,),
    "close_connection": None,
    "delete_database_files": (PERM_DATABASE_RESET,),
    "reset_database_with_backup": (PERM_DATABASE_RESET,),
    "reinitialize_database": (PERM_DATABASE_RESET,),
    "rerun_migrations": (PERM_DATABASE_RESET,),
    "restore_from_backup": (PERM_DATABASE_RESET,),
    "save_database_backup_settings": (PERM_DATABASE_RESET,),
    "delete_database_backup": (PERM_DATABASE_RESET,),
    "create_database_backup": (PERM_DATABASE_RESET,),
    "record_login": None,
    "record_logout": None,
    "revoke_remember_tokens": None,
    "authenticate_remember_token": None,
}

WRITE_PREFIX_RULES = {
    "settings.": PERM_SETTINGS_MANAGE,
    "permissions.create_role": PERM_ROLES_MANAGE,
    "permissions.update_role": PERM_ROLES_MANAGE,
    "permissions.delete_role": PERM_ROLES_MANAGE,
    "permissions.set_role_permissions": PERM_ROLES_MANAGE,
    "dashboard_layouts.save": PERM_SETTINGS_MANAGE,
    "dashboard_layouts.delete": PERM_SETTINGS_MANAGE,
}

BLOCKED_RPC_PREFIXES = (
    "connection.",
    "cursor.",
    "run_schema",
    "migrate_",
    "seed_",
    "_",
)

GUEST_PERMISSIONS = (
    PERM_SESSIONS_MANAGE_OWN,
    PERM_DASHBOARD_VIEW,
    PERM_HISTORY_VIEW,
    PERM_STATISTICS_VIEW,
    PERM_PAYOUTS_VIEW_OWN,
    PERM_REFINERY_MANAGE,
    PERM_STORAGE_MANAGE,
    PERM_SALES_MANAGE,
    PERM_PAYOUTS_MANAGE,
)


def build_guest_user(client_name: str = "") -> dict:
    guest_label = tr("network.guest.username")
    name = (client_name or "").strip() or guest_label
    return {
        "id": 0,
        "username": name,
        "display_name": name,
        "role_name": tr("network.guest.role_name"),
        "active": 1,
        "must_change_password": 0,
        "permissions": list(GUEST_PERMISSIONS),
        "is_network_guest": True,
    }


def is_rpc_path_allowed(path: str) -> bool:
    for prefix in BLOCKED_RPC_PREFIXES:
        if path.startswith(prefix):
            return False
    return True


def guest_has_write_permission(path: str) -> bool:
    method = path.split(".")[-1]
    if method in WRITE_RPC_RULES:
        required = WRITE_RPC_RULES[method]
        if required is None:
            return False
        if isinstance(required, tuple):
            return any(perm in GUEST_PERMISSIONS for perm in required)
        return required in GUEST_PERMISSIONS
    for prefix, required in WRITE_PREFIX_RULES.items():
        if path.startswith(prefix):
            return required in GUEST_PERMISSIONS
    return False


def _user_has_any_permission(user: dict, required) -> bool:
    if isinstance(required, tuple):
        return any(
            has_permission(perm, user)
            for perm in required
        )
    return has_permission(required, user)


def _resolve_change_password_target(args, kwargs):
    if args:
        return args[0]
    return kwargs.get("user_id")


def check_rpc_permission(
    user: dict,
    path: str,
    is_write: bool,
    args=None,
    kwargs=None,
) -> None:
    if not is_rpc_path_allowed(path):
        raise PermissionError(
            tr("network.error.rpc_path_denied", path=path)
        )

    if user.get("is_network_guest"):
        if is_write and not guest_has_write_permission(path):
            raise PermissionError(tr("network.error.guest_no_permission"))
        return

    method = path.split(".")[-1]
    if not is_write:
        return

    if method == "change_password":
        target_id = _resolve_change_password_target(
            args or [],
            kwargs or {},
        )
        actor_id = user.get("id")
        if (
            target_id is not None
            and actor_id is not None
            and target_id != actor_id
            and not has_permission(PERM_USERS_MANAGE, user)
        ):
            raise PermissionError(tr("network.error.no_permission"))
        return

    required = WRITE_RPC_RULES.get(method)
    if required is None and method.startswith(("get_", "fetch_", "list_", "calculate_")):
        return
    if required is None:
        for prefix, perm in WRITE_PREFIX_RULES.items():
            if path.startswith(prefix):
                required = perm
                break

    if required is None:
        if any(
            path.startswith(p)
            for p in ("settings.", "permissions.", "dashboard_layouts.")
        ):
            raise PermissionError(tr("network.error.write_not_allowed"))
        return

    if not _user_has_any_permission(user, required):
        raise PermissionError(tr("network.error.no_permission"))
