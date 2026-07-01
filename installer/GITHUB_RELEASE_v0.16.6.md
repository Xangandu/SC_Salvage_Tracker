# SC Salvage Tracker 0.16.6 Beta — Operations HUD

**Edition (Standard-Build):** SC Salvage Tracker - SOLO Version  
**Codename:** OPERATIONS HUD

## Highlights

- **Dashboard SESSION:** Nach Sitzungsende keine falsche „Aktive Sitzung“ mehr; STATUS zeigt Material-Bereitschaft (RMC + CM Salvage)
- **Auszahlungen & Historie:** Aufklappbare Crew-Auszahlungen; „Alle Auszahlungen“ unter Historie
- **Fenster:** Titelleiste zum Verschieben; Skalieren an Ecken/Rändern; Min/Max/Restore; zentrierte Symbole
- **Fixes:** Lager-Transfer, Verkaufs-Zähler, Sitzungs-Idle, Fenster-Geometrie beim Start

## Installation

1. **SOLO:** `SC_Salvage_Tracker_Setup_SOLO_0.16.6.exe`
2. **CREW:** `SC_Salvage_Tracker_Setup_CREW_0.16.6.exe` (oder SOLO + Supporter-Key)
3. Updates: **Einstellungen → System → Nach Updates suchen** (ab 0.16.3 empfohlen)

## Installer bauen

```powershell
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1 -Edition all
```

## GitHub Release — Assets hochladen

1. Tag: `v0.16.6`
2. Dateien (mindestens SOLO):
   - `SC_Salvage_Tracker_Setup_SOLO_0.16.6.exe`
   - `update-manifest.json`
3. Optional: CREW/ORGA-Setups + `update-manifest-crew.json`
4. Release **veröffentlichen** (nicht Draft)

## Manifest erzeugen

```powershell
python installer\generate_update_manifest.py --setup "..\..\..\Release\installer\SC_Salvage_Tracker_Setup_SOLO_0.16.6.exe" --edition solo
```

## Vollautomatischer Release

```powershell
powershell -ExecutionPolicy Bypass -File Release_veroeffentlichen.ps1
```

Voraussetzungen: `gh auth login`, Python, PyInstaller-Build-Umgebung

## Links

- [Patchnotes](../Changelogs/PATCHNOTES.txt)
- [Editionen](../Changelogs/EDITIONS.txt)
- [Roadmap](../Changelogs/ROADMAP.txt)
