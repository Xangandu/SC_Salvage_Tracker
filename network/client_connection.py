"""Client-Verbindung zum Host-Server."""

import uuid

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtNetwork import QSslConfiguration, QSslSocket, QTcpSocket

from network.constants import (
    EVENT_DATA_CHANGED,
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
    RPC_TIMEOUT_MS,
)
from network.network_state import get_network_state
from network.protocol import ProtocolError, decode_messages, encode_message
from network.relay_constants import RELAY_ERROR, RELAY_JOIN, RELAY_OK


class ClientConnection(QObject):

    connected = Signal()
    disconnected = Signal()
    authenticated = Signal(dict)
    auth_failed = Signal(str)
    data_changed = Signal()
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._socket = None
        self._buffer = bytearray()
        self._user = None
        self._authenticated = False
        self._pending_rpc: dict[str, dict] = {}
        self._ping_timer = QTimer(self)
        self._ping_timer.setInterval(30_000)
        self._ping_timer.timeout.connect(self._send_ping)

    def _ensure_socket(self, use_tls: bool):
        if self._socket is not None:
            return
        self._socket = QSslSocket(self) if use_tls else QTcpSocket(self)
        self._socket.connected.connect(self._on_connected)
        self._socket.disconnected.connect(self._on_disconnected)
        self._socket.readyRead.connect(self._on_ready_read)
        self._socket.errorOccurred.connect(self._on_socket_error)
        if use_tls and hasattr(self._socket, "encrypted"):
            self._socket.encrypted.connect(self._send_hello)
            self._socket.sslErrors.connect(self._ignore_ssl_errors)

    def _ignore_ssl_errors(self, _errors) -> None:
        if self._socket is not None:
            self._socket.ignoreSslErrors()

    @property
    def user(self) -> dict | None:
        return self._user

    @property
    def is_connected(self) -> bool:
        if self._socket is None:
            return False
        return (
            self._socket.state() in (
                QTcpSocket.SocketState.ConnectedState,
                QSslSocket.SocketState.ConnectedState,
            )
            and self._authenticated
        )

    def connect_to_host(
        self,
        host: str,
        port: int,
        *,
        join_code: str = "",
        username: str = "",
        password: str = "",
        client_name: str = "",
        use_tls: bool = True,
        tls_fingerprint: str = "",
    ) -> None:
        self._join_code = (join_code or "").strip().upper()
        self._username = (username or "").strip()
        self._password = password or ""
        self._client_name = client_name or ""
        self._use_tls = use_tls
        self._relay_mode = False

        self._ensure_socket(use_tls)

        state = get_network_state()
        state.mode = "client"
        state.host_address = host
        state.host_port = port
        state.use_tls = use_tls
        state.client_name = self._client_name
        state.join_code = self._join_code

        if use_tls:
            config = QSslConfiguration.defaultConfiguration()
            config.setPeerVerifyMode(QSslSocket.PeerVerifyMode.VerifyNone)
            self._socket.setSslConfiguration(config)
            self._socket.connectToHostEncrypted(host, port)
        else:
            self._socket.connectToHost(host, port)

    def connect_via_relay(
        self,
        relay_host: str,
        relay_port: int,
        *,
        join_code: str = "",
        username: str = "",
        password: str = "",
        client_name: str = "",
    ) -> None:
        """Internet über Salvage-Relay — nur Relay-Adresse + Beitrittscode."""
        self._join_code = (join_code or "").strip().upper()
        self._username = (username or "").strip()
        self._password = password or ""
        self._client_name = client_name or ""
        self._use_tls = False
        self._relay_mode = True
        self._relay_handshake_done = False

        self._ensure_socket(False)

        state = get_network_state()
        state.mode = "client"
        state.host_address = relay_host
        state.host_port = relay_port
        state.use_tls = False
        state.client_name = self._client_name
        state.join_code = self._join_code

        self._socket.connectToHost(relay_host.strip(), relay_port)

    def disconnect_from_host(self) -> None:
        self._ping_timer.stop()
        self._authenticated = False
        if self._socket is None:
            return
        self._user = None
        if self._socket.state() != QTcpSocket.SocketState.UnconnectedState:
            self._socket.disconnectFromHost()

    def rpc(self, path: str, args=None, kwargs=None, timeout_ms=RPC_TIMEOUT_MS):
        if not self._authenticated:
            raise RuntimeError("Nicht mit Host verbunden")

        request_id = str(uuid.uuid4())
        payload = {
            "type": MSG_RPC,
            "id": request_id,
            "path": path,
            "args": args or [],
            "kwargs": kwargs or {},
        }

        from PySide6.QtCore import QEventLoop

        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        timer.start(timeout_ms)

        result_holder = {"done": False, "result": None, "error": None}

        def on_result(response):
            if response.get("id") != request_id:
                return
            result_holder["done"] = True
            if response.get("ok"):
                result_holder["result"] = response.get("result")
            else:
                result_holder["error"] = response.get("error", "RPC fehlgeschlagen")
            loop.quit()

        self._pending_rpc[request_id] = on_result
        self._socket.write(encode_message(payload))
        self._socket.flush()
        loop.exec()
        timer.stop()
        self._pending_rpc.pop(request_id, None)

        if not result_holder["done"]:
            raise TimeoutError(f"RPC-Timeout: {path}")
        if result_holder["error"]:
            raise RuntimeError(result_holder["error"])
        return result_holder["result"]

    def _send_hello(self) -> None:
        self._send({
            "type": MSG_HELLO,
            "protocol_version": PROTOCOL_VERSION,
            "client_name": self._client_name,
        })

    def _send_auth(self) -> None:
        payload = {
            "type": MSG_AUTH,
            "join_code": self._join_code,
        }
        if self._username:
            payload["username"] = self._username
            payload["password"] = self._password
        self._send(payload)

    def _send_ping(self) -> None:
        if self._authenticated:
            self._send({"type": MSG_PING})

    def _send(self, payload: dict) -> None:
        if self._socket is None:
            return
        self._socket.write(encode_message(payload))
        self._socket.flush()

    def _on_connected(self) -> None:
        if getattr(self, "_relay_mode", False):
            self._send({
                "type": RELAY_JOIN,
                "join_code": self._join_code,
            })
            return
        if not getattr(self, "_use_tls", True):
            self._send_hello()

    def _on_disconnected(self) -> None:
        self._ping_timer.stop()
        self._authenticated = False
        state = get_network_state()
        state.connected = False
        self.disconnected.emit()

    def _on_socket_error(self, _error) -> None:
        self.error.emit(self._socket.errorString())

    def _on_ready_read(self) -> None:
        if self._socket is None:
            return
        self._buffer.extend(self._socket.readAll().data())
        try:
            messages, self._buffer = decode_messages(self._buffer)
        except ProtocolError as error:
            self.error.emit(str(error))
            self.disconnect_from_host()
            return

        for message in messages:
            self._handle_message(message)

    def _handle_message(self, message: dict) -> None:
        msg_type = message.get("type")

        if getattr(self, "_relay_mode", False) and not getattr(
            self, "_relay_handshake_done", False
        ):
            if msg_type == RELAY_ERROR:
                self.auth_failed.emit(
                    message.get("error", "Relay-Verbindung fehlgeschlagen")
                )
                self.disconnect_from_host()
                return
            if msg_type == RELAY_OK:
                self._relay_handshake_done = True
                self._send_hello()
                return
            self.auth_failed.emit("Ungültige Relay-Antwort")
            self.disconnect_from_host()
            return

        msg_type = message.get("type")

        if msg_type == MSG_CHALLENGE:
            if message.get("protocol_version") != PROTOCOL_VERSION:
                self.auth_failed.emit("Protokollversion inkompatibel")
                self.disconnect_from_host()
                return
            self._send_auth()
            return

        if msg_type == MSG_AUTH_OK:
            self._user = message.get("user")
            self._authenticated = True
            state = get_network_state()
            state.connected = True
            self._ping_timer.start()
            self.authenticated.emit(self._user)
            self.connected.emit()
            return

        if msg_type == MSG_AUTH_FAIL:
            self.auth_failed.emit(message.get("error", "Authentifizierung fehlgeschlagen"))
            self.disconnect_from_host()
            return

        if msg_type == MSG_RPC_RESULT:
            request_id = message.get("id")
            handler = self._pending_rpc.get(request_id)
            if handler:
                handler(message)
            return

        if msg_type == MSG_EVENT:
            if message.get("name") == EVENT_DATA_CHANGED:
                self.data_changed.emit()
            return

        if msg_type == MSG_PONG:
            return
