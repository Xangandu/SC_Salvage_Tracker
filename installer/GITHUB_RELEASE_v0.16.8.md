# SC Salvage Tracker 0.16.8 Beta — MobiGlas Layouts

**Edition (Standard-Build):** SC Salvage Tracker - SOLO Version  
**Codename:** MOBIGLAS LAYOUTS

## Highlights

- **SOLO-App-Icon:** Neues SCST-SOLO-Logo in EXE, Setup-Assistent und Fenster
- **Seiten-Layout Variante B:** KPI-Zeile + horizontaler Spalter auf Auszahlung, Verkäufe, Lager und Raffinerie
- **MobiGlas-Spalter:** Neues `#pageSplit`-Design in allen Themes; Spalter-Position wird gespeichert
- **Raffinerie:** Historie auf Seite Historie; Raffinerie fokussiert auf Material und aktive Aufträge
- **Übersicht-Nav:** Variante C mit 6px Akzentstreifen (grün=offen, rot=zu) + X-Schließen-Fix

## Installation

1. **SOLO:** `SC_Salvage_Tracker_Setup_SOLO_0.16.8.exe`
2. **CREW:** `SC_Salvage_Tracker_Setup_CREW_0.16.8.exe` (oder SOLO + Supporter-Key)
3. Updates: **Einstellungen → System → Nach Updates suchen** (ab 0.16.3 empfohlen)

## Installer bauen

```powershell
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1 -Edition all
```

## GitHub Release — Assets hochladen

1. Tag: `v0.16.8`
2. Dateien (mindestens SOLO):
   - `SC_Salvage_Tracker_Setup_SOLO_0.16.8.exe`
   - `update-manifest.json`
3. Optional: CREW/ORGA-Setups + `update-manifest-crew.json`
4. Release **veröffentlichen** (nicht Draft)

## Manifest erzeugen

```powershell
python installer\generate_update_manifest.py --setup "..\..\..\Release\installer\SC_Salvage_Tracker_Setup_SOLO_0.16.8.exe" --edition solo
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
