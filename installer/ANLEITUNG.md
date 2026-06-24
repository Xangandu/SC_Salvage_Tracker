# SC Salvage Tracker — Custom Setup (Edition Foundation · 0.15.0 Beta)
#
# Standard-Build: SC Salvage Tracker - SOLO Version
#
# Ergebnis (SOLO):
#   Release\app\SC_Salvage_Tracker_SOLO\
#   Release\installer\SC_Salvage_Tracker_Setup_SOLO_0.15.0.exe
#   Release\installer\update-manifest.json
#
# Voraussetzung: Inno Setup 6.7+ (https://jrsoftware.org/isinfo.php)

## Setup bauen

**Nur SOLO (Standard-Download):**
```powershell
cd "X:\Projektordner\SC_Salvage_Tracker\Source\SC_Salvage_Tracker"
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1
```

**CREW oder ORGA:**
```powershell
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1 -Edition crew
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1 -Edition orga
```

**Alle drei Editionen nacheinander:**
```powershell
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1 -Edition all
```

Ergebnis in `Release\installer\`:
| Datei | Edition |
|-------|---------|
| `SC_Salvage_Tracker_Setup_SOLO_0.15.0.exe` | SOLO (kostenlos) |
| `SC_Salvage_Tracker_Setup_CREW_0.15.0.exe` | CREW (Vernetzung) |
| `SC_Salvage_Tracker_Setup_ORGA_0.15.0.exe` | ORGA (Roadmap) |
| `update-manifest.json` | In-App-Updates (SOLO) |
| `update-manifest-crew.json` / `-orga.json` | optional pro Edition |

Die Build-Edition wird in `config/build_edition.txt` gesetzt und von PyInstaller
mit eingepackt — jede .exe kennt ihre Edition ohne Supporter-Key.

---

## Nur Installer (App bereits gebaut)

```powershell
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1 -SkipPyInstaller
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1 -Edition crew -SkipPyInstaller
```

---

## Nur Grafiken neu erzeugen

```powershell
powershell -ExecutionPolicy Bypass -File installer\prepare_installer_assets.ps1
```

---

## Dateien

| Datei | Beschreibung |
|-------|--------------|
| `sc_salvage_tracker.iss` | Inno-Setup (Edition per `/DMyAppName=…`) |
| `build_installer.ps1` | PyInstaller + Inno, Parameter `-Edition` |
| `config/build_edition.txt` | Marker für frozen APP_EDITION |
| `salvage_tracker.spec` | PyInstaller-Spezifikation |

---

## Hinweise

- Jede Edition hat **eigene AppId** → parallele Installation möglich
- Datenbank bleibt unter `%LOCALAPPDATA%\SC Salvage Tracker\data` (gemeinsam)
- **miniupnpc / UPnP:** optional (`requirements-optional.txt`)
- Nach dem Build wird `build_edition.txt` wieder auf `solo` zurückgesetzt (Dev)
