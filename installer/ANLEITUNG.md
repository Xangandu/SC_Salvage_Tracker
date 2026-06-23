# SC Salvage Tracker — Custom Setup (Design Control · 0.14.3)
#
# Ergebnis:
#   Release\app\SC_Salvage_Tracker\
#   Release\installer\SC_Salvage_Tracker_Setup_0.14.3.exe
#
# Voraussetzung: Inno Setup 6.7+ (https://jrsoftware.org/isinfo.php)

## Setup bauen (alles in einem Schritt)

```powershell
cd "X:\Projektordner\SC_Salvage_Tracker\Source\SC_Salvage_Tracker"
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1
```

Der Assistent nutzt **denselben Launcher-Stil** wie die App:
- Dunkler Hintergrund (#0A0D12)
- Orange Primär-Aktion (#E07A2A)
- Cyan-Akzente (#42D4F5)
- Deutsche HUD-Texte (◆ SETUP, WEITER, INSTALLIEREN)
- Hintergrund-Grafik aus `config/version.py` + Splash

---

## Nur Grafiken neu erzeugen

```powershell
powershell -ExecutionPolicy Bypass -File installer\prepare_installer_assets.ps1
```

Erzeugt in `installer\assets\`:
- `install_bg.png` (920×580, Launcher-Look)
- `app_icon.ico`
- `wizard_small.png`, `wizard_sidebar.png`

---

## Nur Installer (App bereits gebaut)

```powershell
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1 -SkipPyInstaller
```

---

## Dateien

| Datei | Beschreibung |
|-------|--------------|
| `sc_salvage_tracker.iss` | Inno-Setup-Hauptskript |
| `mobiglas_wizard.inc` | Custom Wizard (Farben, Layout, deutsche Texte) |
| `generate_installer_assets.py` | Launcher-Hintergrund + Icon |
| `build_installer.ps1` | PyInstaller + Inno Setup |
| `salvage_tracker.spec` | PyInstaller-Spezifikation |

---

## Hinweise

- **Kein Standard-Windows-Look:** Classic Wizard + eigenes Pascal-Skript
- Version/Codename kommen automatisch aus `config/version.py`
- Bei gesperrter Setup-EXE: Antivirus/Explorer schließen, erneut bauen
- **miniupnpc / UPnP:** optional (`requirements-optional.txt`). Fehlender Build bricht den Installer nicht ab; UPnP-Button in den Einstellungen zeigt dann eine Hinweismeldung.
