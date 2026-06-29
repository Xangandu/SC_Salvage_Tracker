# SC Salvage Tracker 0.16.1 Beta — Location Flow (Update-Fix)

**Edition (Standard-Build):** SC Salvage Tracker - SOLO Version  
**Codename:** LOCATION FLOW  
**Build:** 2026.12

## Highlights

- **In-App-Update repariert:** Neue Version wird nach Download wieder korrekt installiert
- **Stille Installation:** Setup-Assistent versteht `/VERYSILENT`, `/SILENT`, `--quiet`
- **Verzögerter Start:** Updater wartet, bis die App beendet ist, bevor das Setup läuft
- **Installations-Log:** `%LOCALAPPDATA%\SC Salvage Tracker\data\updates\install.log`

## Installation

1. **SOLO:** `SC_Salvage_Tracker_Setup_SOLO_0.16.1.exe`
2. **CREW:** `SC_Salvage_Tracker_Setup_CREW_0.16.1.exe` (oder SOLO + Supporter-Key)
3. Wer **0.16.0** nutzt und das In-App-Update nicht funktionierte: **einmal manuell** 0.16.1 installieren — danach funktionieren Updates wieder automatisch

## Vollautomatischer Release

```powershell
powershell -ExecutionPolicy Bypass -File installer\publish_release.ps1 -CommitMessage "Release 0.16.1 Beta"
```

## Dokumentation

- [Patchnotes](../Changelogs/PATCHNOTES.txt)
- [Release 0.16.0](../docs/RELEASE_0.16.0_LOCATION_FLOW.md)
- [Roadmap](../Changelogs/ROADMAP.txt)
