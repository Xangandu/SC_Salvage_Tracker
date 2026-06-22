"""Zentraler Datenbankzugriff — lokal oder Remote je nach Netzwerkmodus."""

from database.database import Database

_app_database = None
_local_database = None
_client_connection = None
_host_server = None
_host_relay_bridge = None


def get_database():
    global _app_database
    if _app_database is None:
        _app_database = Database()
    return _app_database


def get_local_database():
    """Lokale SQLite — UI-Einstellungen auf dem Client (unabhängig vom Host-RPC)."""
    global _local_database
    if _local_database is None:
        _local_database = Database()
    return _local_database


def get_dashboard_layout_repository(db=None):
    """Dashboard-Layouts immer lokal auf dem Client speichern."""
    if get_client_connection() is not None:
        return get_local_database().dashboard_layouts
    target = db if db is not None else get_database()
    return target.dashboard_layouts


def set_database(db) -> None:
    global _app_database
    _app_database = db


def get_client_connection():
    return _client_connection


def set_client_connection(connection) -> None:
    global _client_connection
    _client_connection = connection


def get_host_server():
    return _host_server


def set_host_server(server) -> None:
    global _host_server
    _host_server = server


def get_host_relay_bridge():
    return _host_relay_bridge


def set_host_relay_bridge(bridge) -> None:
    global _host_relay_bridge
    _host_relay_bridge = bridge


def reset_database_access() -> None:
    global _app_database, _local_database, _client_connection, _host_server
    global _host_relay_bridge
    _app_database = None
    _local_database = None
    _client_connection = None
    _host_server = None
    _host_relay_bridge = None


def reconnect_database():
    """Alle DB-Verbindungen schließen und neu aufbauen (nach Restore)."""
    Database.close_all_connections()
    reset_database_access()
    return get_database()
