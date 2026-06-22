"""JSON-Nachrichten mit Längenpräfix (4 Byte, big-endian)."""

import json
import struct

from network.constants import MAX_MESSAGE_BYTES


class ProtocolError(Exception):
    pass


def encode_message(payload: dict) -> bytes:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    if len(body) > MAX_MESSAGE_BYTES:
        raise ProtocolError("Nachricht zu groß")
    return struct.pack(">I", len(body)) + body


def decode_messages(buffer: bytearray) -> tuple[list[dict], bytearray]:
    """Extrahiert vollständige Nachrichten aus dem Puffer."""
    messages = []
    offset = 0
    total = len(buffer)

    while total - offset >= 4:
        (length,) = struct.unpack(">I", buffer[offset:offset + 4])
        if length <= 0 or length > MAX_MESSAGE_BYTES:
            raise ProtocolError("Ungültige Nachrichtenlänge")
        if total - offset < 4 + length:
            break
        body = bytes(buffer[offset + 4:offset + 4 + length])
        offset += 4 + length
        messages.append(json.loads(body.decode("utf-8")))

    return messages, buffer[offset:]
