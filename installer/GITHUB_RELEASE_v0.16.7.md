# SC Salvage Tracker 0.16.7 Beta — Polish and Performance

**Edition (Standard-Build):** SC Salvage Tracker - SOLO Version  
**Codename:** POLISH AND PERFORMANCE

## Highlights

- **UEX-Preise beim Verkauf:** Automatischer Abruf nach Standortwahl (RMC/CM); asynchron, Preis weiter editierbar
- **Tabellen-Performance:** Login-Historie und Backups passen Höhe an Zeilenanzahl an; internes Scrollen statt Leerfläche
- **Admin-Polish:** System-Tab mit HUD-Trennern, einheitlichen Abständen und Label-Stilen
- **Standort-Picker:** Signal bei Ortswechsel; erster Ort automatisch vorausgewählt

## Installation

1. **SOLO:** `SC_Salvage_Tracker_Setup_SOLO_0.16.7.exe`
2. **CREW:** `SC_Salvage_Tracker_Setup_CREW_0.16.7.exe` (oder SOLO + Supporter-Key)
3. Updates: **Einstellungen → System → Nach Updates suchen** (ab 0.16.3 empfohlen)

## Installer bauen

```powershell
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1 -Edition all
```

## GitHub Release — Assets hochladen

1. Tag: `v0.16.7`
2. Dateien (mindestens SOLO):
   - `SC_Salvage_Tracker_Setup_SOLO_0.16.7.exe`
   - `update-manifest.json`
3. Optional: CREW/ORGA-Setups + `update-manifest-crew.json`
4. Release **veröffentlichen** (nicht Draft)

## Manifest erzeugen

```powershell
python installer\generate_update_manifest.py --setup "..\..\..\Release\installer\SC_Salvage_Tracker_Setup_SOLO_0.16.7.exe" --edition solo
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
