# SC Salvage Tracker 0.16.0 Beta — Location Flow

**Edition (Standard-Build):** SC Salvage Tracker - SOLO Version  
**Codename:** LOCATION FLOW  
**Build:** 2026.11

## Highlights

- **Lager / Standorte:** Eigene Seite — wo liegt wie viel Material (Station, Stadt, Schiff)
- **Materialfluss:** Session → Schiff → Station → Raffinerie → Verkauf ohne globales „Geister-Lager“
- **Kontext-Dashboard:** Separates Fenster mit Hinweisleiste (nächste Aktion mit Ort und Zeit)
- **Idle-Warnungen:** 10-Tage-Hinweis + Reserve-Tags für bewusst gelagertes Material
- **Raffinerie:** cSCU ↔ SCU Live-Hilfe beim Abschluss; Rohmaterial vom Schiff

## Installation

1. **SOLO:** `SC_Salvage_Tracker_Setup_SOLO_0.16.0.exe`
2. **CREW:** `SC_Salvage_Tracker_Setup_CREW_0.16.0.exe` (oder SOLO + Supporter-Key)
3. Bestehende Datenbank: Migration 028 legt `material_stockpiles` an — App einmal starten

## Nach dem Update

- Alte globale `storage_items` ohne Ort können noch in der Verkaufsseite erscheinen
- Neuer Bestand sollte über **Lager / Standorte** geführt werden
- Bei Doppelzählungen: Legacy-Einträge in Admin prüfen oder manuell bereinigen

## Installer bauen

```powershell
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1 -Edition all
```

## GitHub Release — Assets hochladen

1. Tag: `v0.16.0`
2. Dateien (mindestens SOLO):
   - `SC_Salvage_Tracker_Setup_SOLO_0.16.0.exe`
   - `update-manifest.json`
3. Optional: CREW/ORGA-Setups + `update-manifest-crew.json`
4. Release **veröffentlichen** (nicht Draft)

## Manifest erzeugen

```powershell
python installer\generate_update_manifest.py --setup "..\..\..\Release\installer\SC_Salvage_Tracker_Setup_SOLO_0.16.0.exe" --edition solo
```

## Vollautomatischer Release

```powershell
powershell -ExecutionPolicy Bypass -File installer\publish_release.ps1 -CommitMessage "Release 0.16.0 Beta"
```

## Dokumentation

- [Patchnotes](../Changelogs/PATCHNOTES.txt)
- [Release-Zusammenfassung](../docs/RELEASE_0.16.0_LOCATION_FLOW.md)
- [Spezifikation Standorte](../docs/SPEC_STANDORTE_UND_LAGER.md)
- [Roadmap](../Changelogs/ROADMAP.txt)
