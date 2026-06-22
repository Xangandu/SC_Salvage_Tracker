"""Führt RPC-Aufrufe auf dem Host gegen die lokale Database aus."""

import auth.session as user_session
from network.rpc_registry import check_rpc_permission


WRITE_METHOD_PREFIXES = (
    "create_",
    "add_",
    "update_",
    "delete_",
    "save_",
    "set_",
    "end_",
    "complete_",
    "cancel_",
    "approve_",
    "reset_",
    "reassign_",
    "change_",
    "revoke_",
    "record_",
    "migrate_",
    "run_",
)


def _is_write_method(method_name: str) -> bool:
    if method_name.startswith("get_") or method_name.startswith("list_"):
        return False
    if method_name.startswith(("calculate_", "fetch_", "resolve_", "attach_")):
        return False
    return any(method_name.startswith(p) for p in WRITE_METHOD_PREFIXES)


def _resolve_callable(db, path: str):
    parts = path.split(".")
    target = db
    for part in parts[:-1]:
        target = getattr(target, part)
    method = getattr(target, parts[-1])
    return method


def execute_rpc(db, user: dict, path: str, args: list, kwargs: dict):
    check_rpc_permission(
        user,
        path,
        _is_write_method(path.split(".")[-1]),
        args=args,
        kwargs=kwargs,
    )

    previous_user = user_session.get_user()
    login_id = user_session.get_login_id()
    user_session.set_session(user, login_id or 0)

    try:
        method = _resolve_callable(db, path)
        return method(*(args or []), **(kwargs or {}))
    finally:
        if previous_user:
            user_session.set_session(previous_user, login_id)
        else:
            user_session.clear_session()


def serialize_result(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [serialize_result(item) for item in value]
    if isinstance(value, dict):
        return {k: serialize_result(v) for k, v in value.items()}
    try:
        import sqlite3

        if isinstance(value, sqlite3.Row):
            return dict(value)
    except ImportError:
        pass
    return value
