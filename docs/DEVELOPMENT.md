# Entwicklung — SC Salvage Tracker

Interne Doku für Entwickler und Maintainer. **Nicht** in README.md duplizieren.

---

## Voraussetzungen

- Windows 10/11, Python 3.11+ (empfohlen: projekt `.venv`)
- Git, optional Inno Setup 6.7+ (Installer)
- Optional: GitHub CLI (`gh`) für Releases

---

## Projekt starten

Im Repository-Root (`Source/SC_Salvage_Tracker`):

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

**Hinweis PowerShell:** Falls `Activate.ps1` blockiert ist → Python direkt über `.venv\Scripts\python.exe` nutzen, oder:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

## Editionen testen (nur Entwicklung, nicht frozen)

```powershell
$env:SST_EDITION="crew"   # oder orga
.\.venv\Scripts\python.exe main.py
```

Gilt nur wenn **nicht** als `.exe` gebaut (`is_frozen()` = false).

Build-Edition für Installer: `config/build_edition.txt` + `installer/build_installer.ps1 -Edition`.

---

## Installer & Release

| Thema | Datei |
|-------|--------|
| Installer bauen | [`installer/ANLEITUNG.md`](../installer/ANLEITUNG.md) |
| GitHub Release | [`installer/GITHUB_RELEASE_v0.15.0.md`](../installer/GITHUB_RELEASE_v0.15.0.md) |
| Editionen | [`Changelogs/EDITIONS.txt`](../Changelogs/EDITIONS.txt) |
| Supporter-Keys erzeugen | `python scripts/generate_supporter_keys.py crew` (Keys **nicht** committen) |

---

## Tests

```powershell
.\.venv\Scripts\python.exe scripts\test_edition_keys.py
.\.venv\Scripts\python.exe scripts\integration_test_flow.py
```

---

## Datenpfade (Dev)

| Inhalt | Pfad |
|--------|------|
| SQLite (Dev) | `data/salvage_tracker.db` |
| Installiert | `%LOCALAPPDATA%\SC Salvage Tracker\data` |

Diese Pfade **nicht** in öffentliche README schreiben, wenn sie interne Projektstruktur verraten.
