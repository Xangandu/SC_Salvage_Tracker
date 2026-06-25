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

## GitHub Release (Build + Upload automatisch)

Ein Befehl baut den Installer, erzeugt das Update-Manifest und lädt alles als
GitHub Release hoch (Voraussetzung: `gh auth login`).

**Vollautomatisch (empfohlen):**

Doppelklick auf **`Release_veroeffentlichen.bat`** im Projektroot — oeffnet ein **blaues PowerShell-Fenster** (kein schwarzes CMD).
Alternativ direkt: **`Release_veroeffentlichen.ps1`**

Das Skript erledigt automatisch:
1. Version aus `config/version.py` lesen  
2. `Changelogs/PATCHNOTES.txt` prüfen (fehlenden Eintrag ergänzen)  
3. Git commit + push (`Release 0.x.x Beta`)  
4. Installer bauen + Update-Manifest  
5. GitHub Release veröffentlichen  

**In Cursor:** `Strg+Shift+P` → **Tasks: Run Task** → **Release veröffentlichen (vollautomatisch)**

**Einmalig vorher:** `gh auth login`  
**Optional — PATCHNOTES per ChatGPT:** siehe Abschnitt *ChatGPT für PATCHNOTES* unten.  
**Vor jedem neuen Release:** nur `APP_VERSION` / Build / Codename in `config/version.py` anheben.

Manuell in PowerShell (optional):

```powershell
cd "X:\Projektordner\SC_Salvage_Tracker\Source\SC_Salvage_Tracker"
powershell -ExecutionPolicy Bypass -File installer\publish_release.ps1
```

**Mit Commit + Push des Codes vor dem Release:**

```powershell
powershell -ExecutionPolicy Bypass -File installer\publish_release.ps1 `
  -CommitMessage "Release 0.16.0 Beta"
```

**Nur hochladen** (Setup/Manifest liegen schon in `Release\installer`):

```powershell
powershell -ExecutionPolicy Bypass -File installer\publish_release.ps1 -SkipBuild
```

**Alle Editionen** (SOLO + CREW + ORGA):

```powershell
powershell -ExecutionPolicy Bypass -File installer\publish_release.ps1 -Edition all
```

| Parameter | Bedeutung |
|-----------|-----------|
| `-Edition solo\|crew\|orga\|all` | Was gebaut/hochgeladen wird: Standard `solo` |
| `-SkipBuild` | Kein Neubau, nur GitHub-Upload |
| `-CommitMessage "…"` | `git add`, commit, push vor dem Release |
| `-Draft` | Release als Entwurf (noch nicht öffentlich) |
| `-ReplaceRelease` | Bestehenden Tag/Release ersetzen (nur bei gleicher Version) |

**Vor dem ersten Aufruf:** `config/version.py` und `Changelogs/PATCHNOTES.txt`
anpassen.

Skript: `installer/publish_release.ps1`

---

## ChatGPT für PATCHNOTES (optional)

Beim Release kann ChatGPT automatisch den Patchnotes-Text aus deinen Git-Commits
schreiben. Ohne API-Key wird wie bisher ein kurzer Platzhalter ergänzt.

**Einrichtung (einmalig):**

1. API-Key auf https://platform.openai.com/api-keys erstellen  
2. Datei kopieren:

```powershell
copy config\patchnotes_ai.example.json config\patchnotes_ai.local.json
```

3. In `config\patchnotes_ai.local.json` den Key eintragen:

```json
{
  "enabled": true,
  "model": "gpt-4o-mini",
  "api_key": "sk-..."
}
```

**Alternativ** (ohne Datei): Umgebungsvariable setzen:

```powershell
setx OPENAI_API_KEY "sk-dein-key-hier"
```

(Danach neues Terminal / Cursor neu starten.)

**Manuell testen:**

```powershell
.\.venv\Scripts\python.exe scripts\generate_patchnotes_ai.py
```

`config/patchnotes_ai.local.json` ist in `.gitignore` — Key nie committen.

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
