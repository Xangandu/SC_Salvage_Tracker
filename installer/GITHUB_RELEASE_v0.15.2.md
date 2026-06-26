# SC Salvage Tracker 0.15.2 Beta — Global Interface

**Edition (Standard-Build):** SC Salvage Tracker - SOLO Version  
**Codename:** GLOBAL INTERFACE

## Highlights

- **Vollständige Internationalisierung (i18n):** Englisch (Standard) und Deutsch
- Sprachauswahl beim ersten Start; Umschaltung unter **Einstellungen → Design → Erscheinungsbild**
- Übersetzt: Hauptseiten, Dialoge, Admin, Fehlermeldungen, Netzwerk-Texte, Updates
- **Hinweis:** Nach Sprachwechsel die App **neu starten**, damit alle UI-Elemente aktualisiert werden

## Installation

1. **SOLO:** `SC_Salvage_Tracker_Setup_SOLO_0.15.2.exe`
2. **CREW:** `SC_Salvage_Tracker_Setup_CREW_0.15.2.exe` (oder SOLO + Supporter-Key)
3. Beim ersten Start: Sprache wählen (English / Deutsch), danach Setup-Wizard bzw. Anmeldung

## Installer bauen

```powershell
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1 -Edition all
```

## GitHub Release — Assets hochladen

1. Tag: `v0.15.2`
2. Dateien (mindestens SOLO):
   - `SC_Salvage_Tracker_Setup_SOLO_0.15.2.exe`
   - `update-manifest.json`
3. Optional: CREW/ORGA-Setups + `update-manifest-crew.json`
4. Release **veröffentlichen** (nicht Draft) — Repo muss **öffentlich** sein

## Manifest erzeugen

```powershell
python installer\generate_update_manifest.py --setup "..\..\..\Release\installer\SC_Salvage_Tracker_Setup_SOLO_0.15.2.exe" --edition solo
```

Manifest neben die Setup-EXE legen und zusammen hochladen.

## Vollautomatischer Release (optional)

Voraussetzungen: `gh auth login`, Python, Inno Setup

```powershell
powershell -ExecutionPolicy Bypass -File installer\release_auto.ps1
```

Optional PATCHNOTES per ChatGPT: `OPENAI_API_KEY` setzen oder `config/patchnotes_ai.local.json` anlegen.

## Entwickler

- CREW lokal testen: `$env:SST_EDITION="crew"; python main.py`
- Sprache testen: `$env:SST_LANGUAGE="de"; python main.py` (Dev-Override, falls vorhanden)

## Links

- [Patchnotes](../Changelogs/PATCHNOTES.txt)
- [Editionen](../Changelogs/EDITIONS.txt)
- [Roadmap](../Changelogs/ROADMAP.txt)
