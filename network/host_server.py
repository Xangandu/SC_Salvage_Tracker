"""Host-Server: nimmt Client-Verbindungen entgegen und führt RPC aus."""

import secrets
import socket
import string

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import (
    QHostAddress,
    QSsl,
    QSslCertificate,
    QSslConfiguration,
    QSslKey,
    QSslSocket,
    QTcpServer,
    QTcpSocket,
)

from network.constants import (
    DEFAULT_HOST_BIND,
    DEFAULT_PORT,
    EVENT_CLIENTS_CHANGED,
    EVENT_DATA_CHANGED,
    JOIN_CODE_LENGTH,
    MSG_AUTH,
    MSG_AUTH_FAIL,
    MSG_AUTH_OK,
    MSG_CHALLENGE,
    MSG_EVENT,
    MSG_HELLO,
    MSG_PING,
    MSG_PONG,
    MSG_RPC,
    MSG_RPC_RESULT,
    PROTOCOL_VERSION,
)
from network.network_state import get_network_state
from network.protocol import ProtocolError, decode_messages, encode_message
from network.rpc_executor import execute_rpc, serialize_result
from network.rpc_registry import build_guest_user
from network.tls_utils import certificate_fingerprint, ensure_host_certificate


def _generate_join_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(JOIN_CODE_LENGTH))


def _local_addresses() -> list[str]:
    addresses = {"127.0.0.1"}
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            addresses.add(info[4][0])
    except OSError:
        pass
    return sorted(addresses)


class _ClientSession(QObject):

    disconnected = Signal(object)

    def __init__(self, socket, db, join_code: str, parent=None):
        super().__init__(parent)
        self.socket = socket
        self.db = db
        self.join_code = join_code
        self.user = None
        self.client_name = ""
        self._buffer = bytearray()
        self._authenticated = False

        socket.readyRead.connect(self._on_ready_read)
        socket.disconnected.connect(self._on_disconnected)
        socket.errorOccurred.connect(self._on_disconnected)

    def label(self) -> str:
        if self.user:
            return self.user.get("username", "?")
        return self.client_name or "Unbekannt"

    def send(self, payload: dict) -> None:
        state = self.socket.state()
        if state not in (
            QTcpSocket.SocketState.ConnectedState,
            QSslSocket.SocketState.ConnectedState,
        ):
            return
        self.socket.write(encode_message(payload))
        self.socket.flush()

    def close(self) -> None:
        self.socket.disconnectFromHost()

    def _on_disconnected(self, *_args) -> None:
        self.disconnected.emit(self)

    def _on_ready_read(self) -> None:
        self._buffer.extend(self.socket.readAll().data())
        try:
            messages, self._buffer = decode_messages(self._buffer)
        except ProtocolError:
            self.close()
            return

        for message in messages:
            self._handle_message(message)

    def _handle_message(self, message: dict) -> None:
        msg_type = message.get("type")

        if msg_type == MSG_HELLO:
            self.client_name = message.get("client_name", "")
            self.send({
                "type": MSG_CHALLENGE,
                "protocol_version": PROTOCOL_VERSION,
                "join_code_required": bool(self.join_code),
                "tls_fingerprint": certificate_fingerprint(),
            })
            return

        if msg_type == MSG_AUTH:
            self._handle_auth(message)
            return

        if not self._authenticated:
            self.send({"type": MSG_AUTH_FAIL, "error": "Nicht authentifiziert"})
            return

        if msg_type == MSG_PING:
            self.send({"type": MSG_PONG})
            return

        if msg_type == MSG_RPC:
            self._handle_rpc(message)

    def _handle_auth(self, message: dict) -> None:
        join_code = (message.get("join_code") or "").strip().upper()
        username = (message.get("username") or "").strip()
        password = message.get("password") or ""

        if self.join_code and join_code != self.join_code:
            self.send({
                "type": MSG_AUTH_FAIL,
                "error": "Ungültiger Beitrittscode",
            })
            return

        if username and password:
            user = self.db.authenticate_user(username, password)
            if not user:
                self.send({
                    "type": MSG_AUTH_FAIL,
                    "error": "Anmeldung fehlgeschlagen",
                })
                return
            user = self.db.permissions.attach_permissions_to_user(user)
            self.user = user
        elif self.join_code:
            guest_name = self.client_name or "Gast"
            self.user = build_guest_user(guest_name)
        else:
            self.send({
                "type": MSG_AUTH_FAIL,
                "error": "Benutzername und Passwort erforderlich",
            })
            return

        self._authenticated = True
        self.send({
            "type": MSG_AUTH_OK,
            "user": self.user,
            "protocol_version": PROTOCOL_VERSION,
        })

    def _handle_rpc(self, message: dict) -> None:
        request_id = message.get("id")
        path = message.get("path", "")
        args = message.get("args") or []
        kwargs = message.get("kwargs") or {}

        try:
            result = execute_rpc(
                self.db,
                self.user,
                path,
                args,
                kwargs,
            )
            self.send({
                "type": MSG_RPC_RESULT,
                "id": request_id,
                "ok": True,
                "result": serialize_result(result),
            })
            if path and not path.split(".")[-1].startswith("get_"):
                self._broadcast_event({"type": MSG_EVENT, "name": EVENT_DATA_CHANGED})
                server = self.parent()
                if server and hasattr(server, "data_changed"):
                    server.data_changed.emit()
        except Exception as error:
            self.send({
                "type": MSG_RPC_RESULT,
                "id": request_id,
                "ok": False,
                "error": str(error),
            })

    def _broadcast_event(self, payload: dict) -> None:
        server = self.parent()
        if server and hasattr(server, "broadcast"):
            server.broadcast(payload, exclude=self)


class HostServer(QObject):

    started = Signal()
    stopped = Signal()
    client_connected = Signal(str)
    client_disconnected = Signal(str)
    data_changed = Signal()
    error = Signal(str)

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._server = QTcpServer(self)
        self._clients: list[_ClientSession] = []
        self._join_code = ""
        self._port = DEFAULT_PORT
        self._use_tls = True
        self._ssl_config = None

        self._server.newConnection.connect(self._on_new_connection)

    @property
    def join_code(self) -> str:
        return self._join_code

    @property
    def port(self) -> int:
        return self._port

    @property
    def addresses(self) -> list[str]:
        return _local_addresses()

    @property
    def client_labels(self) -> list[str]:
        return [client.label() for client in self._clients]

    def is_running(self) -> bool:
        return self._server.isListening()

    def start(
        self,
        *,
        port: int = DEFAULT_PORT,
        join_code: str | None = None,
        use_tls: bool = True,
    ) -> bool:
        if self.is_running():
            return True

        self._port = port
        self._use_tls = use_tls
        self._join_code = (join_code or _generate_join_code()).upper()

        if use_tls:
            cert_path, key_path = ensure_host_certificate()
            if cert_path and key_path:
                cert_bytes = cert_path.read_bytes()
                key_bytes = key_path.read_bytes()
                cert = QSslCertificate(
                    cert_bytes,
                    QSsl.EncodingFormat.Pem,
                )
                key = QSslKey(
                    key_bytes,
                    QSsl.KeyAlgorithm.Rsa,
                    QSsl.EncodingFormat.Pem,
                    QSsl.KeyType.PrivateKey,
                )
                if not cert.isNull() and not key.isNull():
                    self._ssl_config = QSslConfiguration.defaultConfiguration()
                    self._ssl_config.setLocalCertificate(cert)
                    self._ssl_config.setPrivateKey(key)
                    self._ssl_config.setProtocol(
                        QSsl.SslProtocol.TlsV1_2OrLater
                    )
                else:
                    self._use_tls = False
                    self._ssl_config = None
            else:
                self._use_tls = False
                self._ssl_config = None

        if not self._server.listen(
            QHostAddress(DEFAULT_HOST_BIND),
            self._port,
        ):
            self.error.emit(self._server.errorString())
            return False

        state = get_network_state()
        state.mode = "host"
        state.host_running = True
        state.host_port = self._port
        state.join_code = self._join_code
        state.use_tls = self._use_tls
        state.tls_fingerprint = certificate_fingerprint()
        state.connected_clients = self.client_labels

        self.db.settings.set_app_setting("network_join_code", self._join_code)
        self.db.settings.set_app_setting("network_host_port", str(self._port))
        self.db.settings.set_app_setting("network_use_tls", "1" if self._use_tls else "0")

        self.started.emit()
        return True

    def stop(self) -> None:
        for client in list(self._clients):
            client.close()
        self._clients.clear()
        if self._server.isListening():
            self._server.close()

        state = get_network_state()
        state.host_running = False
        state.connected_clients = []
        state.mode = "standalone"
        self.stopped.emit()

    def regenerate_join_code(self) -> str:
        self._join_code = _generate_join_code()
        self.db.settings.set_app_setting("network_join_code", self._join_code)
        state = get_network_state()
        state.join_code = self._join_code
        return self._join_code

    def set_join_code(self, join_code: str) -> None:
        self._join_code = (join_code or "").strip().upper()
        self.db.settings.set_app_setting("network_join_code", self._join_code)
        state = get_network_state()
        state.join_code = self._join_code

    def broadcast(self, payload: dict, exclude=None) -> None:
        for client in self._clients:
            if client is exclude:
                continue
            if client._authenticated:
                client.send(payload)

    def _on_new_connection(self) -> None:
        pending = self._server.nextPendingConnection()
        if pending is None:
            return

        if self._use_tls and self._ssl_config:
            socket = QSslSocket(self)
            socket.setSslConfiguration(self._ssl_config)
            descriptor = pending.socketDescriptor()
            pending.close()
            pending.deleteLater()
            if not socket.setSocketDescriptor(descriptor):
                socket.deleteLater()
                return
            socket.startServerEncryption()
        else:
            socket = pending

        session = _ClientSession(
            socket,
            self.db,
            self._join_code,
            parent=self,
        )
        session.disconnected.connect(self._on_client_disconnected)
        self._clients.append(session)
        self.client_connected.emit(session.label())
        self._sync_client_state()

    def _on_client_disconnected(self, session: _ClientSession) -> None:
        if session in self._clients:
            self._clients.remove(session)
        self.client_disconnected.emit(session.label())
        session.deleteLater()
        self._sync_client_state()

    def _sync_client_state(self) -> None:
        state = get_network_state()
        state.connected_clients = self.client_labels
        self.broadcast({
            "type": MSG_EVENT,
            "name": EVENT_CLIENTS_CHANGED,
            "clients": state.connected_clients,
        })
