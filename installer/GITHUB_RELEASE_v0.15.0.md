# SC Salvage Tracker 0.15.0 Beta — Edition Foundation

**Phasenwechsel:** Alpha → **Beta**  
**Edition (Standard-Build):** SC Salvage Tracker - SOLO Version

## Highlights

- Produkt-Editionen: **SOLO**, **CREW**, **ORGA** (eine Codebasis)
- SOLO: alle Solo-Features kostenlos; Vernetzung sichtbar aber gesperrt (Teaser)
- CREW: Host/Client-Vernetzung (separater Build oder später Supporter-Key)
- Dokumentation: `Changelogs/EDITIONS.txt`

## Installation

1. **SOLO:** `SC_Salvage_Tracker_Setup_SOLO_0.15.0.exe`
2. **CREW:** `SC_Salvage_Tracker_Setup_CREW_0.15.0.exe` (oder SOLO + Supporter-Key)
3. Erstinstallation: Setup-Wizard, danach Anmeldung

## Installer bauen

```powershell
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1 -Edition all
```

## GitHub Release — Assets hochladen

1. Tag: `v0.15.0`
2. Dateien (mindestens SOLO):
   - `SC_Salvage_Tracker_Setup_SOLO_0.15.0.exe`
   - `update-manifest.json`
3. Optional: CREW/ORGA-Setups + `update-manifest-crew.json`
4. Release **veröffentlichen** (nicht Draft) — Repo muss **öffentlich** sein

## Manifest erzeugen

```powershell
python installer\generate_update_manifest.py --setup "..\..\..\Release\installer\SC_Salvage_Tracker_Setup_SOLO_0.15.0.exe" --edition solo
```

Manifest neben die Setup-EXE legen und zusammen hochladen.

## Entwickler

- CREW lokal testen: `$env:SST_EDITION="crew"; python main.py`
- Build-Edition: `installer\build_installer.ps1 -Edition crew`

## Links

- [Editionen-Doku](../Changelogs/EDITIONS.txt)
- [Patchnotes](../Changelogs/PATCHNOTES.txt)
