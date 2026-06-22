"""UPnP — automatische Portweiterleitung am Router."""

from __future__ import annotations

import socket


def try_forward_port(
    port: int,
    *,
    description: str = "SC Salvage Tracker",
    internal_host: str | None = None,
) -> tuple[bool, str]:
    """Versucht TCP-Port per UPnP IGD zu öffnen. Gibt (Erfolg, Meldung) zurück."""
    try:
        import miniupnpc
    except ImportError:
        import sys

        version = f"{sys.version_info.major}.{sys.version_info.minor}"
        hint = (
            "UPnP-Bibliothek nicht installiert.\n\n"
            f"Aktuelle Python-Version: {version}\n"
        )
        if sys.version_info >= (3, 14):
            hint += (
                "Unter Python 3.14 gibt es noch kein fertiges "
                "miniupnpc-Wheel.\n"
                "Optional: Python 3.12/3.13 installieren und dort "
                "'pip install miniupnpc' ausführen,\n"
                "oder UPnP manuell am Router einrichten."
            )
        else:
            hint += "Installation: pip install miniupnpc"
        return False, hint

    if internal_host is None:
        internal_host = _guess_lan_ip()

    upnp = miniupnpc.UPnP()
    upnp.discoverdelay = 200
    try:
        devices = upnp.discover()
        if not devices:
            return False, "Kein UPnP-Router im Netzwerk gefunden."
        upnp.selectigd()
        upnp.addportmapping(
            port,
            "TCP",
            internal_host,
            port,
            description,
            "",
        )
        return True, (
            f"Port {port} wurde per UPnP auf {internal_host} weitergeleitet."
        )
    except Exception as error:
        return False, f"UPnP fehlgeschlagen: {error}"


def try_remove_port_forward(port: int) -> None:
    try:
        import miniupnpc
    except ImportError:
        return

    upnp = miniupnpc.UPnP()
    upnp.discoverdelay = 200
    try:
        if upnp.discover():
            upnp.selectigd()
            upnp.deleteportmapping(port, "TCP")
    except Exception:
        pass


def _guess_lan_ip() -> str:
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        return probe.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        probe.close()
