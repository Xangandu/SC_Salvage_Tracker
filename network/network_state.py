"""Globaler Netzwerk-Modus und Verbindungszustand."""

from dataclasses import dataclass, field

from network.constants import NETWORK_MODE_STANDALONE


@dataclass
class NetworkState:
    mode: str = NETWORK_MODE_STANDALONE
    host_address: str = ""
    host_port: int = 47890
    use_tls: bool = True
    join_code: str = ""
    client_name: str = ""
    connected: bool = False
    host_running: bool = False
    connected_clients: list[str] = field(default_factory=list)
    tls_fingerprint: str = ""
    show_connection_assistant: bool = True

    def is_client(self) -> bool:
        return self.mode == "client" and self.connected

    def is_host(self) -> bool:
        return self.mode == "host" and self.host_running

    def is_standalone(self) -> bool:
        return self.mode == NETWORK_MODE_STANDALONE


_state = NetworkState()


def get_network_state() -> NetworkState:
    return _state


def reset_network_state() -> None:
    global _state
    _state = NetworkState()
