"""
Update-Manifest — Konfiguration und Parsing für In-App-Updates.

Manifest-URL (GitHub Release Asset):
  https://github.com/Xangandu/SC_Salvage_Tracker/releases/latest/download/update-manifest.json

Nach jedem Build erzeugt installer/generate_update_manifest.py die Datei
neben der Setup-EXE. Beim GitHub-Release beide Assets hochladen:
  - SC_Salvage_Tracker_Setup_<version>.exe
  - update-manifest.json
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from config.version import APP_BUILD, APP_VERSION

GITHUB_OWNER = "Xangandu"
GITHUB_REPO = "SC_Salvage_Tracker"

UPDATE_MANIFEST_FILENAME = "update-manifest.json"
UPDATE_MANIFEST_URL = (
    f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}"
    f"/releases/latest/download/{UPDATE_MANIFEST_FILENAME}"
)

MANIFEST_FETCH_TIMEOUT_SEC = 15


@dataclass(frozen=True)
class UpdateDownload:
    filename: str
    url: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class LocalizedReleaseNotes:
    title: str
    summary: str
    highlights: tuple[str, ...]


@dataclass(frozen=True)
class UpdateManifest:
    schema_version: int
    app: str
    version: str
    version_display: str
    build: str
    codename: str
    tag: str
    published_at: str
    mandatory: bool
    min_version: str
    channel: str
    download: UpdateDownload
    release_notes: dict[str, LocalizedReleaseNotes]
    release_notes_url: str

    def notes(self, language: str = "de") -> LocalizedReleaseNotes | None:
        lang = language.lower()[:2]
        if lang in self.release_notes:
            return self.release_notes[lang]
        return self.release_notes.get("en")


def _parse_version_tuple(value: str) -> tuple[int, ...]:
    numbers = [int(part) for part in re.findall(r"\d+", value)]
    if not numbers:
        return (0,)
    return tuple(numbers)


def local_release_version() -> str:
    """Semver für Vergleich (ohne Alpha/Beta-Suffix)."""
    return re.sub(
        r"\s+(Alpha|Beta).*$",
        "",
        APP_VERSION,
        flags=re.IGNORECASE,
    ).strip()


def is_newer_version(
    remote_version: str,
    local_version: str | None = None,
) -> bool:
    if local_version is None:
        local_version = local_release_version()
    """True wenn remote_version neuer als local_version (Semver-Vergleich)."""
    return _parse_version_tuple(remote_version) > _parse_version_tuple(
        local_version
    )


def is_newer_build(
    remote_build: str,
    local_build: str = APP_BUILD,
) -> bool:
    """Build-Vergleich als Fallback bei gleicher Versionsnummer."""
    return _parse_version_tuple(remote_build) > _parse_version_tuple(
        local_build
    )


def is_update_available(
    manifest: UpdateManifest,
    local_version: str | None = None,
    local_build: str = APP_BUILD,
) -> bool:
    if local_version is None:
        local_version = local_release_version()
    if is_newer_version(manifest.version, local_version):
        return True
    if _parse_version_tuple(manifest.version) == _parse_version_tuple(
        local_version
    ):
        return is_newer_build(manifest.build, local_build)
    return False


def _parse_release_notes(raw: dict[str, Any]) -> dict[str, LocalizedReleaseNotes]:
    parsed: dict[str, LocalizedReleaseNotes] = {}
    for lang, block in raw.items():
        if not isinstance(block, dict):
            continue
        highlights = block.get("highlights") or []
        parsed[lang] = LocalizedReleaseNotes(
            title=str(block.get("title", "")),
            summary=str(block.get("summary", "")),
            highlights=tuple(str(item) for item in highlights),
        )
    return parsed


def parse_update_manifest(data: dict[str, Any]) -> UpdateManifest:
    download = data.get("download") or {}
    return UpdateManifest(
        schema_version=int(data.get("schema_version", 1)),
        app=str(data.get("app", "")),
        version=str(data.get("version", "")),
        version_display=str(data.get("version_display", "")),
        build=str(data.get("build", "")),
        codename=str(data.get("codename", "")),
        tag=str(data.get("tag", "")),
        published_at=str(data.get("published_at", "")),
        mandatory=bool(data.get("mandatory", False)),
        min_version=str(data.get("min_version", "0.0.0")),
        channel=str(data.get("channel", "stable")),
        download=UpdateDownload(
            filename=str(download.get("filename", "")),
            url=str(download.get("url", "")),
            size_bytes=int(download.get("size_bytes", 0)),
            sha256=str(download.get("sha256", "")).lower(),
        ),
        release_notes=_parse_release_notes(data.get("release_notes") or {}),
        release_notes_url=str(data.get("release_notes_url", "")),
    )


def fetch_update_manifest(
    url: str = UPDATE_MANIFEST_URL,
    timeout_sec: int = MANIFEST_FETCH_TIMEOUT_SEC,
) -> UpdateManifest:
    try:
        with urlopen(url, timeout=timeout_sec) as response:
            payload = response.read().decode("utf-8")
    except URLError as error:
        raise RuntimeError(
            f"Update-Manifest konnte nicht geladen werden: {error}"
        ) from error

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "Update-Manifest ist kein gültiges JSON."
        ) from error

    if not isinstance(data, dict):
        raise RuntimeError("Update-Manifest hat ungültiges Format.")

    return parse_update_manifest(data)
