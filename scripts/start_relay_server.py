"""Salvage-Relay-Server starten (für Tests oder eigener Server)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from network.relay_server import run_relay_server

if __name__ == "__main__":
    run_relay_server()
