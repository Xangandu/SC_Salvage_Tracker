"""UPnP — automatische Portweiterleitung am Router."""

from __future__ import annotations

import socket

from config.i18n import tr


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
        hint = tr("admin.network.upnp.msg.lib_missing", version=version)
        if sys.version_info >= (3, 14):
            hint += tr("admin.network.upnp.msg.lib_missing_py314")
        else:
            hint += tr("admin.network.upnp.msg.install_pip")
        return False, hint

    if internal_host is None:
        internal_host = _guess_lan_ip()

    upnp = miniupnpc.UPnP()
    upnp.discoverdelay = 200
    try:
        devices = upnp.discover()
        if not devices:
            return False, tr("admin.network.upnp.msg.no_router")
        upnp.selectigd()
        upnp.addportmapping(
            port,
            "TCP",
            internal_host,
            port,
            description,
            "",
        )
        return True, tr(
            "admin.network.upnp.msg.success",
            port=port,
            host=internal_host,
        )
    except Exception as error:
        return False, tr(
            "admin.network.upnp.msg.failed",
            error=error,
        )


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
