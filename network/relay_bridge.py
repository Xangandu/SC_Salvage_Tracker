"""Host-Registrierung am Salvage-Relay (Internet ohne Portweiterleitung)."""

from __future__ import annotations

import json
import logging
import socket
import struct
import threading

from PySide6.QtCore import QObject, Signal

from network.protocol import decode_messages, encode_message
from network.relay_constants import (
    RELAY_HOST_LINK,
    RELAY_INCOMING,
    RELAY_OK,
    RELAY_PROTOCOL_VERSION,
    RELAY_REGISTER,
)

logger = logging.getLogger(__name__)


def _recv_loop(sock: socket.socket, callback) -> None:
    buffer = bytearray()
    while True:
        try:
            chunk = sock.recv(65536)
            if not chunk:
                break
            buffer.extend(chunk)
            messages, buffer = decode_messages(buffer)
            for message in messages:
                callback(message)
        except OSError:
            break


class HostRelayBridge(QObject):
    """Registriert den Host am Relay und leitet eingehende Clients lokal weiter."""

    registered = Signal()
    stopped = Signal()
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._control_sock: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._join_code = ""
        self._relay_host = ""
        self._relay_port = 0
        self._local_port = 47890

    @property
    def is_active(self) -> bool:
        return self._running and self._control_sock is not None

    def start(
        self,
        *,
        relay_host: str,
        relay_port: int,
        join_code: str,
        local_port: int,
    ) -> bool:
        self.stop()
        self._join_code = join_code.strip().upper()
        self._relay_host = relay_host.strip()
        self._relay_port = relay_port
        self._local_port = local_port

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            sock.connect((self._relay_host, self._relay_port))
            sock.sendall(encode_message({
                "type": RELAY_REGISTER,
                "protocol_version": RELAY_PROTOCOL_VERSION,
                "join_code": self._join_code,
            }))
            response = self._read_message(sock)
            if response.get("type") != RELAY_OK:
                raise OSError(
                    response.get("error", "Relay-Registrierung fehlgeschlagen")
                )

            sock.settimeout(None)
            self._control_sock = sock
            self._running = True
            self._thread = threading.Thread(
                target=_recv_loop,
                args=(sock, self._on_control_message),
                daemon=True,
            )
            self._thread.start()
            self.registered.emit()
            logger.info(
                "Host am Relay registriert: %s:%s Code %s",
                self._relay_host,
                self._relay_port,
                self._join_code,
            )
            return True
        except OSError as error:
            self.error.emit(str(error))
            self.stop()
            return False

    def stop(self) -> None:
        was_running = self._running
        self._running = False
        if self._control_sock:
            try:
                self._control_sock.close()
            except OSError:
                pass
            self._control_sock = None
        if was_running:
            self.stopped.emit()

    def _on_control_message(self, message: dict) -> None:
        if message.get("type") != RELAY_INCOMING:
            return
        client_id = message.get("client_id", "")
        if not client_id:
            return
        threading.Thread(
            target=self._open_host_link,
            args=(client_id,),
            daemon=True,
        ).start()

    def _open_host_link(self, client_id: str) -> None:
        relay_data = None
        local = None
        try:
            relay_data = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            relay_data.settimeout(15.0)
            relay_data.connect((self._relay_host, self._relay_port))
            relay_data.sendall(encode_message({
                "type": RELAY_HOST_LINK,
                "join_code": self._join_code,
                "client_id": client_id,
            }))
            local = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            local.connect(("127.0.0.1", self._local_port))
            relay_data.settimeout(None)
            self._bridge(relay_data, local)
        except OSError as error:
            logger.warning("Relay-Host-Link fehlgeschlagen: %s", error)
        finally:
            for sock in (relay_data, local):
                if sock:
                    try:
                        sock.close()
                    except OSError:
                        pass

    @staticmethod
    def _bridge(left: socket.socket, right: socket.socket) -> None:
        def copy(source: socket.socket, target: socket.socket) -> None:
            try:
                while True:
                    data = source.recv(65536)
                    if not data:
                        break
                    target.sendall(data)
            except OSError:
                pass

        t1 = threading.Thread(target=copy, args=(left, right), daemon=True)
        t2 = threading.Thread(target=copy, args=(right, left), daemon=True)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

    @staticmethod
    def _read_message(sock: socket.socket) -> dict:
        header = HostRelayBridge._recv_exact(sock, 4)
        if not header:
            raise OSError("Keine Relay-Antwort")
        (length,) = struct.unpack(">I", header)
        body = HostRelayBridge._recv_exact(sock, length)
        if not body:
            raise OSError("Unvollständige Relay-Antwort")
        return json.loads(body.decode("utf-8"))

    @staticmethod
    def _recv_exact(sock: socket.socket, size: int) -> bytes | None:
        chunks = []
        remaining = size
        while remaining > 0:
            chunk = sock.recv(remaining)
            if not chunk:
                return None
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)
