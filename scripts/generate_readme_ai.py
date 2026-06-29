"""README-Highlights per OpenAI aus PATCHNOTES / Git aktualisieren.

Nutzt dieselbe Konfiguration wie generate_patchnotes_ai.py.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"

sys.path.insert(0, str(ROOT / "scripts"))

from generate_patchnotes_ai import (  # noqa: E402
    call_openai,
    collect_git_context,
    extract_version_block,
    load_ai_config,
    read_version_meta,
)

PATCHNOTES_PATH = ROOT / "Changelogs" / "PATCHNOTES.txt"
HIGHLIGHTS_HEADER = "## Highlights (Beta)"


def build_readme_prompt(
    meta: dict[str, str],
    patchnotes_block: str,
    git_context: str,
) -> list[dict]:
    system = (
        "Du schreibst kurze README-Highlights für SC Salvage Tracker "
        "(Star Citizen Salvage Desktop App, GitHub README, deutsch). "
        "Antworte nur mit 4–6 Bulletpoints im Markdown-Format "
        "(jede Zeile beginnt mit '- **Titel** — Kurztext'). "
        "Keine Überschrift, keine Codeblöcke, keine Versionsnummern in Dateinamen."
    )
    user = f"""
Version: {meta["display_version"]} | Codename: {meta["codename"]}

PATCHNOTES-Auszug:
{patchnotes_block[:3500]}

Git-Kontext:
{git_context[:2500]}

Regeln:
- Nur Inhalte aus PATCHNOTES/Git — nichts erfinden
- Endnutzer-sprache, sachlich, deutsch
- Keine Secrets, keine internen Pfade, kein Dev-Bypass
- Themen: Lager/Standorte, Materialfluss, Dashboard, Themes, Sprache — wenn relevant
""".strip()
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def replace_highlights_section(readme: str, bullets: str) -> str:
    bullets = bullets.strip()
    if not bullets.startswith("-"):
        bullets = "\n".join(
            f"- {line.lstrip('- ').strip()}"
            for line in bullets.splitlines()
            if line.strip()
        )

    section = f"{HIGHLIGHTS_HEADER}\n\n{bullets}\n"
    pattern = rf"(?ms)^{re.escape(HIGHLIGHTS_HEADER)}.*?(?=^!\[|^> \*\*Download|^## )"
    if re.search(pattern, readme):
        return re.sub(pattern, section + "\n", readme, count=1)

    marker = "Crew-Auszahlungen.\n"
    if marker in readme:
        return readme.replace(
            marker,
            marker + "\n" + section + "\n",
            1,
        )

    return section + "\n" + readme


def main() -> int:
    parser = argparse.ArgumentParser(
        description="README-Highlights per ChatGPT aktualisieren.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Highlights auch bei vorhandenem Abschnitt neu generieren",
    )
    args = parser.parse_args()

    config = load_ai_config()
    if not config.get("enabled", True):
        print("README-AI deaktiviert.")
        return 2

    api_key = str(config.get("api_key", "")).strip()
    if not api_key:
        print("Kein OPENAI_API_KEY — README unverändert.")
        return 2

    meta = read_version_meta()
    patchnotes = ""
    if PATCHNOTES_PATH.exists():
        content = PATCHNOTES_PATH.read_text(encoding="utf-8")
        block = extract_version_block(content, meta["display_version"])
        if block:
            patchnotes = block

    if not patchnotes:
        print("Kein PATCHNOTES-Block für aktuelle Version — README übersprungen.")
        return 2

    readme = README_PATH.read_text(encoding="utf-8")
    if HIGHLIGHTS_HEADER in readme and not args.force:
        print("README-Highlights vorhanden — übersprungen (--force zum Neu-Generieren).")
        return 0

    git_context = collect_git_context(meta["file_version"])
    model = str(config.get("model", "gpt-4o-mini"))
    messages = build_readme_prompt(meta, patchnotes, git_context)

    print(f"ChatGPT ({model}) schreibt README-Highlights...")
    bullets = call_openai(api_key, model, messages)
    updated = replace_highlights_section(readme, bullets)
    README_PATH.write_text(updated, encoding="utf-8")
    print(f"README aktualisiert: {README_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
