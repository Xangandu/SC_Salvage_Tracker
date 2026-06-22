"""Datenbank-Proxy für Clients — leitet Aufrufe per RPC an den Host weiter."""

from network.client_connection import ClientConnection


class _RemoteRepositoryProxy:

    def __init__(self, connection: ClientConnection, prefix: str):
        self._connection = connection
        self._prefix = prefix

    def __getattr__(self, name: str):
        path = f"{self._prefix}.{name}"

        def caller(*args, **kwargs):
            return self._connection.rpc(path, list(args), kwargs)

        return caller


class RemoteDatabase:
    """Ersetzt Database() auf Client-Seite — gleiche Aufruf-Schnittstelle per RPC."""

    def __init__(self, connection: ClientConnection):
        self._connection = connection
        self.settings = _RemoteRepositoryProxy(connection, "settings")
        self.permissions = _RemoteRepositoryProxy(connection, "permissions")
        self.dashboard_layouts = _RemoteRepositoryProxy(
            connection, "dashboard_layouts"
        )
        self.materials = _RemoteRepositoryProxy(connection, "materials")
        self.refinery = _RemoteRepositoryProxy(connection, "refinery")
        self.payouts = _RemoteRepositoryProxy(connection, "payouts")

    @staticmethod
    def database_path():
        return None

    @staticmethod
    def remember_me_path():
        return None

    @classmethod
    def delete_database_files(cls, **kwargs):
        raise RuntimeError("Nur auf dem Host verfügbar")

    @classmethod
    def close_all_connections(cls):
        pass

    def close_connection(self):
        pass

    def __getattr__(self, name: str):
        def caller(*args, **kwargs):
            return self._connection.rpc(name, list(args), kwargs)

        return caller

    def authenticate(self, username, password):
        raise RuntimeError("Authentifizierung erfolgt über die Host-Verbindung")

    def authenticate_remember_token(self, username, token):
        return None

    def record_login(self, user_id):
        return 0

    def record_logout(self, login_id):
        pass

    def revoke_remember_tokens(self, user_id):
        pass
