"""Lädt eingebettete Google Fonts (OFL) in assets/fonts herunter."""

from __future__ import annotations

import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DOWNLOADS = {
    "assets/fonts/Orbitron-Bold.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/orbitron/static/Orbitron-Bold.ttf"
    ),
    "assets/fonts/Rajdhani-Regular.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/rajdhani/Rajdhani-Regular.ttf"
    ),
    "assets/fonts/Rajdhani-Bold.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/rajdhani/Rajdhani-Bold.ttf"
    ),
    "assets/fonts/scifi/Exo2-Variable.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/exo2/Exo2%5Bwght%5D.ttf"
    ),
    "assets/fonts/scifi/Audiowide-Regular.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/audiowide/Audiowide-Regular.ttf"
    ),
    "assets/fonts/scifi/Michroma-Regular.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/michroma/Michroma-Regular.ttf"
    ),
    "assets/fonts/scifi/Oxanium-Variable.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/oxanium/Oxanium%5Bwght%5D.ttf"
    ),
    "assets/fonts/scifi/Teko-Variable.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/teko/Teko%5Bwght%5D.ttf"
    ),
    "assets/fonts/scifi/Jura-Variable.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/jura/Jura%5Bwght%5D.ttf"
    ),
    "assets/fonts/scifi/Electrolize-Regular.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/electrolize/Electrolize-Regular.ttf"
    ),
    "assets/fonts/scifi/ShareTechMono-Regular.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/sharetechmono/ShareTechMono-Regular.ttf"
    ),
}


def main():
    for rel_path, url in DOWNLOADS.items():
        target = ROOT / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.stat().st_size > 0:
            print(f"skip {rel_path}")
            continue
        print(f"fetch {rel_path}")
        urllib.request.urlretrieve(url, target)
        print(f"  -> {target.stat().st_size} bytes")


if __name__ == "__main__":
    main()
