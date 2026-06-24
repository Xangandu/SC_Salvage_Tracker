"""PATCHNOTES per OpenAI/ChatGPT aus Git-Änderungen erzeugen.

Konfiguration (eine Option reicht):
  1. Umgebungsvariable OPENAI_API_KEY
  2. config/patchnotes_ai.local.json (von patchnotes_ai.example.json kopieren)

Aufruf:
  python scripts/generate_patchnotes_ai.py
  python scripts/generate_patchnotes_ai.py --force
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCHNOTES_PATH = ROOT / "Changelogs" / "PATCHNOTES.txt"
VERSION_PATH = ROOT / "config" / "version.py"
CONFIG_PATH = ROOT / "config" / "patchnotes_ai.local.json"
EXAMPLE_CONFIG_PATH = ROOT / "config" / "patchnotes_ai.example.json"

PLACEHOLDER_MARKERS = (
    "Details bitte bei Bedarf ergänzen",
    "Siehe Git-Commit-Historie für technische Änderungen",
)

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


def _run_git(*args: str, cwd: Path = ROOT) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def read_version_meta() -> dict[str, str]:
    content = VERSION_PATH.read_text(encoding="utf-8")
    meta = {
        "display_version": "",
        "file_version": "",
        "build": "",
        "codename": "",
    }
    if match := re.search(r'APP_VERSION\s*=\s*"([^"]+)"', content):
        meta["display_version"] = match.group(1).strip()
        meta["file_version"] = re.sub(
            r"\s+(Alpha|Beta|RC\d*)\s*$",
            "",
            meta["display_version"],
        ).strip()
    if match := re.search(r'APP_BUILD\s*=\s*"([^"]+)"', content):
        meta["build"] = match.group(1).strip()
    if match := re.search(r'APP_CODENAME\s*=\s*"([^"]+)"', content):
        meta["codename"] = match.group(1).strip()
    if not meta["file_version"]:
        raise RuntimeError("APP_VERSION in config/version.py fehlt oder ist ungültig.")
    return meta


def load_ai_config() -> dict:
    config: dict = {"enabled": True, "model": "gpt-4o-mini", "api_key": ""}
    if EXAMPLE_CONFIG_PATH.exists():
        with EXAMPLE_CONFIG_PATH.open(encoding="utf-8") as handle:
            config.update(json.load(handle))
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open(encoding="utf-8") as handle:
            config.update(json.load(handle))
    env_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if env_key:
        config["api_key"] = env_key
    return config


def extract_version_block(content: str, display_version: str) -> str | None:
    pattern = (
        rf"(?ms)^(VERSION {re.escape(display_version)}.*?)"
        rf"(?=^VERSION \d|\Z)"
    )
    match = re.search(pattern, content)
    if not match:
        return None
    return match.group(1).strip()


def is_placeholder_block(block: str | None) -> bool:
    if not block:
        return True
    if any(marker in block for marker in PLACEHOLDER_MARKERS):
        return True
    bullets = [line for line in block.splitlines() if line.strip().startswith("•")]
    return len(bullets) <= 2


def sample_style_reference(content: str) -> str:
    match = re.search(r"(?ms)^VERSION \d.+?(?=^VERSION \d|\Z)", content)
    if not match:
        return ""
    sample = match.group(0).strip()
    lines = sample.splitlines()
    return "\n".join(lines[:35])


def collect_git_context(file_version: str) -> str:
    parts: list[str] = []

    tags = _run_git("tag", "--list", "v*.*.*", "--sort=-v:refname")
    previous_tag = ""
    if tags:
        for tag in tags.splitlines():
            tag_version = tag.lstrip("v")
            if tag_version != file_version:
                previous_tag = tag
                break

    if previous_tag:
        parts.append(f"Referenz seit Tag: {previous_tag}")
        log = _run_git(
            "log",
            f"{previous_tag}..HEAD",
            "--pretty=format:%h %s (%an, %ar)",
            "--no-merges",
        )
        stat = _run_git("diff", f"{previous_tag}..HEAD", "--stat")
    else:
        parts.append("Referenz: letzte 40 Commits (kein älterer Tag gefunden)")
        log = _run_git(
            "log",
            "-40",
            "--pretty=format:%h %s (%an, %ar)",
            "--no-merges",
        )
        stat = _run_git("diff", "HEAD~40..HEAD", "--stat")

    if log:
        parts.append("\nCommit-Liste:\n" + log)
    if stat:
        parts.append("\nGeänderte Dateien:\n" + stat)

    status = _run_git("status", "--short")
    if status:
        parts.append("\nNoch nicht committete Änderungen:\n" + status)

    return "\n".join(parts).strip() or "Keine Git-Informationen verfügbar."


def build_prompt(meta: dict[str, str], style_sample: str, git_context: str) -> list[dict]:
    system = (
        "Du schreibst deutsche Patchnotes für SC Salvage Tracker "
        "(Star Citizen Salvage Tracker, Windows Desktop App, PySide6). "
        "Antworte nur mit dem Patchnotes-Block — ohne Markdown-Codeblöcke, "
        "ohne Einleitung. Stil: sachlich, für Endnutzer verständlich, "
        "technische Dateinamen nur wenn hilfreich. "
        "Nutze Abschnittsüberschriften wie NEU — …, UI, FIXES, HINWEIS "
        "und Bulletpoints mit •."
    )
    user = f"""
Erstelle den Patchnotes-Abschnitt für diese Version:

VERSION {meta["display_version"]} | Build {meta["build"]} | Codename: {meta["codename"]}
{"-" * 68}

Beginne exakt mit der VERSION-Zeile oben (mit Build und Codename).
Dann die Trennlinie aus 68 Bindestrichen.
Dann 3–8 thematische Abschnitte mit Bulletpoints (•).

Stil-Referenz aus einer früheren Version:
{style_sample or "(keine Referenz)"}

Git-Änderungen seit letztem Release:
{git_context}

Regeln:
- Nur Features/Fixes aus den Git-Daten — nichts erfinden
- Deutsch, Du-Ansprache vermeiden (neutral: „Neue …“, „Behoben …“)
- Keine Supporter-Keys, keine Secrets, keine internen Pfade
- Maximal ca. 35 Zeilen
""".strip()
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def call_openai(api_key: str, model: str, messages: list[dict]) -> str:
    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": 0.35,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        OPENAI_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read()
        try:
            detail = json.loads(body.decode("utf-8", errors="replace"))
            message = detail.get("error", {}).get("message", str(error))
        except json.JSONDecodeError:
            message = str(error)
        raise RuntimeError(f"OpenAI API Fehler: {message}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"OpenAI Verbindung fehlgeschlagen: {error}") from error

    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError("Unerwartete OpenAI-Antwort.") from error


def normalize_block(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:markdown|text)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip() + "\n"


def insert_or_replace_block(content: str, block: str, display_version: str) -> str:
    block = normalize_block(block)
    existing = extract_version_block(content, display_version)

    if existing:
        return content.replace(existing, block.rstrip(), 1)

    if re.search(r"(?ms)^VERSION \d", content):
        match = re.search(r"(?ms)^VERSION \d", content)
        assert match is not None
        index = match.start()
        return content[:index] + block + "\n\n" + content[index:]

    if "====" in content:
        return re.sub(r"(={3,}\r?\n)", rf"\1\n{block}\n", content, count=1)

    header = "SC SALVAGE TRACKER – PATCHNOTES\n================================\n\n"
    return header + block + "\n\n" + content.lstrip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PATCHNOTES per ChatGPT/OpenAI aus Git erzeugen.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bestehenden Eintrag für diese Version neu generieren",
    )
    args = parser.parse_args()

    config = load_ai_config()
    if not config.get("enabled", True):
        print("PATCHNOTES-AI deaktiviert (enabled=false).")
        return 2

    api_key = str(config.get("api_key", "")).strip()
    if not api_key:
        print("Kein OPENAI_API_KEY — Fallback auf Platzhalter-Text.")
        return 2

    meta = read_version_meta()
    display_version = meta["display_version"]

    if not PATCHNOTES_PATH.exists():
        PATCHNOTES_PATH.parent.mkdir(parents=True, exist_ok=True)
        PATCHNOTES_PATH.write_text(
            "SC SALVAGE TRACKER – PATCHNOTES\n================================\n\n",
            encoding="utf-8",
        )

    content = PATCHNOTES_PATH.read_text(encoding="utf-8")
    existing = extract_version_block(content, display_version)

    if existing and not is_placeholder_block(existing) and not args.force:
        print(f"PATCHNOTES für {display_version} bereits vorhanden — übersprungen.")
        return 0

    style_sample = sample_style_reference(content)
    git_context = collect_git_context(meta["file_version"])
    messages = build_prompt(meta, style_sample, git_context)
    model = str(config.get("model", "gpt-4o-mini"))

    print(f"ChatGPT ({model}) schreibt PATCHNOTES für {display_version}...")
    block = call_openai(api_key, model, messages)

    if display_version not in block:
        header = (
            f"VERSION {display_version} | Build {meta['build']} | "
            f"Codename: {meta['codename']}\n"
            f"{'-' * 68}\n\n"
        )
        block = header + block.lstrip()

    updated = insert_or_replace_block(content, block, display_version)
    PATCHNOTES_PATH.write_text(updated.rstrip() + "\n", encoding="utf-8")
    print(f"PATCHNOTES aktualisiert: {PATCHNOTES_PATH}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"FEHLER: {error}", file=sys.stderr)
        raise SystemExit(1) from error
