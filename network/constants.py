"""Netzwerk-Konstanten für Host-Client-Kommunikation."""

PROTOCOL_VERSION = 1
DEFAULT_PORT = 47890
DEFAULT_HOST_BIND = "0.0.0.0"

NETWORK_MODE_STANDALONE = "standalone"
NETWORK_MODE_HOST = "host"
NETWORK_MODE_CLIENT = "client"

JOIN_CODE_LENGTH = 6
RPC_TIMEOUT_MS = 30_000
MAX_MESSAGE_BYTES = 8 * 1024 * 1024

MSG_HELLO = "hello"
MSG_CHALLENGE = "challenge"
MSG_AUTH = "auth"
MSG_AUTH_OK = "auth_ok"
MSG_AUTH_FAIL = "auth_fail"
MSG_RPC = "rpc"
MSG_RPC_RESULT = "rpc_result"
MSG_EVENT = "event"
MSG_PING = "ping"
MSG_PONG = "pong"

EVENT_DATA_CHANGED = "data_changed"
EVENT_CLIENTS_CHANGED = "clients_changed"
