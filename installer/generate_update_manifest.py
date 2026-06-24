"""Erzeugt update-manifest.json für GitHub Releases und In-App-Updates."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.update import GITHUB_OWNER, GITHUB_REPO  # noqa: E402

RELEASE_NOTES_FILE = Path(__file__).resolve().parent / "update_release_notes.json"
VERSION_FILE = ROOT / "config" / "version.py"


def read_version_meta() -> dict[str, str]:
    content = VERSION_FILE.read_text(encoding="utf-8")
    meta = {
        "app_name": "SC Salvage Tracker",
        "edition": "solo",
        "version_display": "0.14.2 Alpha",
        "version_file": "0.14.2",
        "build": "2026.06",
        "codename": "Live Update",
    }
    patterns = (
        ("app_name", r'APP_NAME\s*=\s*"([^"]+)"'),
        ("version_display", r'APP_VERSION\s*=\s*"([^"]+)"'),
        ("build", r'APP_BUILD\s*=\s*"([^"]+)"'),
        ("codename", r'APP_CODENAME\s*=\s*"([^"]+)"'),
    )
    for key, pattern in patterns:
        match = re.search(pattern, content)
        if match:
            meta[key] = match.group(1).strip()

    meta["version_file"] = re.sub(
        r"\s+(Alpha|Beta|RC\d*)\s*$",
        "",
        meta["version_display"],
        flags=re.IGNORECASE,
    ).strip()
    return meta


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_release_notes(version_file: str) -> dict:
    if not RELEASE_NOTES_FILE.exists():
        return {}

    data = json.loads(RELEASE_NOTES_FILE.read_text(encoding="utf-8"))
    block = data.get(version_file)
    if block:
        return block

    return {
        "de": {
            "title": f"SC Salvage Tracker {version_file}",
            "summary": "Neue Version verfügbar.",
            "highlights": [],
        },
        "en": {
            "title": f"SC Salvage Tracker {version_file}",
            "summary": "A new version is available.",
            "highlights": [],
        },
    }


def build_manifest(
    setup_exe: Path,
    *,
    tag: str | None = None,
    channel: str = "stable",
    min_version: str = "0.8.0",
    mandatory: bool = False,
    edition: str = "solo",
    app_name: str | None = None,
) -> dict:
    meta = read_version_meta()
    version_file = meta["version_file"]
    tag = tag or f"v{version_file}"
    setup_name = setup_exe.name
    size_bytes = setup_exe.stat().st_size
    file_hash = sha256_file(setup_exe)

    resolved_app_name = app_name or meta["app_name"]
    if app_name is None and edition != "solo":
        titles = {
            "solo": "SC Salvage Tracker - SOLO Version",
            "crew": "SC Salvage Tracker - CREW Version",
            "orga": "SC Salvage Tracker - ORGA Version",
        }
        resolved_app_name = titles.get(edition, resolved_app_name)

    download_url = (
        f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}"
        f"/releases/download/{tag}/{setup_name}"
    )
    release_notes_url = (
        f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}"
        f"/releases/tag/{tag}"
    )

    return {
        "schema_version": 1,
        "app": resolved_app_name,
        "edition": edition,
        "version": version_file,
        "version_display": meta["version_display"],
        "build": meta["build"],
        "codename": meta["codename"],
        "tag": tag,
        "published_at": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "mandatory": mandatory,
        "min_version": min_version,
        "channel": channel,
        "download": {
            "filename": setup_name,
            "url": download_url,
            "size_bytes": size_bytes,
            "sha256": file_hash,
        },
        "release_notes": load_release_notes(version_file),
        "release_notes_url": release_notes_url,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate update-manifest.json for GitHub Releases.",
    )
    parser.add_argument(
        "--setup",
        required=True,
        type=Path,
        help="Path to SC_Salvage_Tracker_Setup_<version>.exe",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path (default: next to setup exe)",
    )
    parser.add_argument(
        "--tag",
        help="Git tag for download URL (default: v<version>)",
    )
    parser.add_argument(
        "--channel",
        default="stable",
        help="Release channel (stable, beta)",
    )
    parser.add_argument(
        "--min-version",
        default="0.8.0",
        help="Minimum app version allowed to update",
    )
    parser.add_argument(
        "--mandatory",
        action="store_true",
        help="Mark update as mandatory",
    )
    parser.add_argument(
        "--edition",
        default="solo",
        choices=("solo", "crew", "orga"),
        help="Product edition for this setup package",
    )
    parser.add_argument(
        "--app-name",
        help="Override app display name in manifest",
    )
    args = parser.parse_args()

    setup_exe = args.setup.resolve()
    if not setup_exe.is_file():
        print(f"Setup-EXE nicht gefunden: {setup_exe}", file=sys.stderr)
        return 1

    manifest = build_manifest(
        setup_exe,
        tag=args.tag,
        channel=args.channel,
        min_version=args.min_version,
        mandatory=args.mandatory,
        edition=args.edition,
        app_name=args.app_name,
    )

    output = args.output or setup_exe.with_name("update-manifest.json")
    output.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Update-Manifest: {output}")
    print(f"  Version:  {manifest['version_display']}")
    print(f"  SHA256:   {manifest['download']['sha256']}")
    print(f"  Size:     {manifest['download']['size_bytes']:,} bytes")
    print(f"  URL:      {manifest['download']['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
