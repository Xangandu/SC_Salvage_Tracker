"""Salvage-Relay-Server — leitet Clients zum Host weiter (Beitrittscode)."""

from __future__ import annotations

import json
import logging
import socket
import struct
import threading
import uuid

from network.relay_constants import (
    DEFAULT_RELAY_PORT,
    RELAY_ERROR,
    RELAY_HOST_LINK,
    RELAY_INCOMING,
    RELAY_JOIN,
    RELAY_OK,
    RELAY_PROTOCOL_VERSION,
    RELAY_REGISTER,
)

logger = logging.getLogger(__name__)


def _encode(payload: dict) -> bytes:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return struct.pack(">I", len(body)) + body


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


def _decode_one(sock: socket.socket) -> dict | None:
    header = _recv_exact(sock, 4)
    if not header:
        return None
    (length,) = struct.unpack(">I", header)
    if length <= 0 or length > 1024 * 1024:
        raise ValueError("Ungültige Relay-Nachricht")
    body = _recv_exact(sock, length)
    if not body:
        return None
    return json.loads(body.decode("utf-8"))


def _bridge_sockets(
    left: socket.socket,
    right: socket.socket,
) -> None:
    left.settimeout(None)
    right.settimeout(None)

    def copy(source: socket.socket, target: socket.socket) -> None:
        try:
            while True:
                data = source.recv(65536)
                if not data:
                    break
                target.sendall(data)
        except OSError:
            pass
        finally:
            try:
                target.shutdown(socket.SHUT_WR)
            except OSError:
                pass

    t1 = threading.Thread(
        target=copy,
        args=(left, right),
        daemon=True,
    )
    t2 = threading.Thread(
        target=copy,
        args=(right, left),
        daemon=True,
    )
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    for sock in (left, right):
        try:
            sock.close()
        except OSError:
            pass


class _RelayRoom:
    def __init__(self) -> None:
        self.control: socket.socket | None = None
        self.pending: dict[str, socket.socket] = {}


class SalvageRelayServer:
    def __init__(self, host: str = "0.0.0.0", port: int = DEFAULT_RELAY_PORT):
        self._host = host
        self._port = port
        self._rooms: dict[str, _RelayRoom] = {}
        self._rooms_lock = threading.Lock()
        self._listener: socket.socket | None = None
        self._running = False

    def start(self) -> None:
        self._listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listener.bind((self._host, self._port))
        self._listener.listen(128)
        self._running = True
        logger.info("Salvage-Relay lauscht auf %s:%s", self._host, self._port)

        while self._running:
            try:
                client, addr = self._listener.accept()
            except OSError:
                break
            threading.Thread(
                target=self._handle_connection,
                args=(client, addr),
                daemon=True,
            ).start()

    def stop(self) -> None:
        self._running = False
        if self._listener:
            try:
                self._listener.close()
            except OSError:
                pass

    def _handle_connection(
        self,
        sock: socket.socket,
        addr,
    ) -> None:
        try:
            message = _decode_one(sock)
            if not message:
                sock.close()
                return

            msg_type = message.get("type")
            if msg_type == RELAY_REGISTER:
                self._register_host(sock, message)
            elif msg_type == RELAY_JOIN:
                self._join_client(sock, message)
            elif msg_type == RELAY_HOST_LINK:
                self._link_host(sock, message)
            else:
                sock.sendall(_encode({
                    "type": RELAY_ERROR,
                    "error": "Unbekannter Relay-Befehl",
                }))
                sock.close()
        except Exception as error:
            logger.warning("Relay-Fehler von %s: %s", addr, error)
            try:
                sock.close()
            except OSError:
                pass

    def _register_host(self, sock: socket.socket, message: dict) -> None:
        join_code = (message.get("join_code") or "").strip().upper()
        if not join_code:
            sock.sendall(_encode({
                "type": RELAY_ERROR,
                "error": "Beitrittscode fehlt",
            }))
            sock.close()
            return

        if message.get("protocol_version") != RELAY_PROTOCOL_VERSION:
            sock.sendall(_encode({
                "type": RELAY_ERROR,
                "error": "Relay-Protokoll inkompatibel",
            }))
            sock.close()
            return

        with self._rooms_lock:
            room = self._rooms.get(join_code)
            if room is None:
                room = _RelayRoom()
                self._rooms[join_code] = room
            if room.control is not None:
                try:
                    room.control.close()
                except OSError:
                    pass
            room.control = sock

        sock.sendall(_encode({"type": RELAY_OK, "join_code": join_code}))
        logger.info("Host registriert: Code %s", join_code)

    def _join_client(self, sock: socket.socket, message: dict) -> None:
        join_code = (message.get("join_code") or "").strip().upper()
        client_id = str(uuid.uuid4())

        with self._rooms_lock:
            room = self._rooms.get(join_code)
            if not room or room.control is None:
                sock.sendall(_encode({
                    "type": RELAY_ERROR,
                    "error": "Kein Host für diesen Code",
                }))
                sock.close()
                return
            room.pending[client_id] = sock
            control = room.control

        control.sendall(_encode({
            "type": RELAY_INCOMING,
            "client_id": client_id,
        }))
        logger.info("Client wartet auf Host-Link: %s", join_code)

    def _link_host(self, sock: socket.socket, message: dict) -> None:
        join_code = (message.get("join_code") or "").strip().upper()
        client_id = message.get("client_id", "")

        with self._rooms_lock:
            room = self._rooms.get(join_code)
            if not room:
                sock.close()
                return
            client_sock = room.pending.pop(client_id, None)

        if not client_sock:
            sock.close()
            return

        client_sock.sendall(_encode({"type": RELAY_OK}))
        logger.info("Relay-Tunnel aktiv: %s", join_code)
        _bridge_sockets(sock, client_sock)


def run_relay_server(
    host: str = "0.0.0.0",
    port: int = DEFAULT_RELAY_PORT,
) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    server = SalvageRelayServer(host=host, port=port)
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Relay-Server beendet")
        server.stop()


if __name__ == "__main__":
    run_relay_server()
