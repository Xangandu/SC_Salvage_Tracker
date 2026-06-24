# SC Salvage Tracker

**Version 0.15.0 Beta** · Build 2026.08 · Codename *Edition Foundation*

Desktop-Programm (Python / PySide6 / SQLite) zur Verwaltung von **Star Citizen Salvage**-Operationen: Sitzungen, Materialfluss, Raffinerie, Verkäufe, Kosten und Crew-Auszahlungen — im MobiGlas-inspirierten Design.

> **Standard-Download:** [SC Salvage Tracker - SOLO Version](https://github.com/Xangandu/SC_Salvage_Tracker/releases/latest) (kostenlos)

---

## Produkt-Editionen

| Edition | Beschreibung |
|---------|--------------|
| **SOLO** | Kostenlos. Voller Solo-Workflow. Vernetzung sichtbar, aber gesperrt (Teaser). |
| **CREW** | Host/Client-Vernetzung für gemeinsame Sessions (separater Build oder Supporter-Key). |
| **ORGA** | Organisations-Features (Roadmap). |

Details: [`Changelogs/EDITIONS.txt`](Changelogs/EDITIONS.txt)

---

## Installation

1. Release öffnen: [GitHub Releases](https://github.com/Xangandu/SC_Salvage_Tracker/releases)
2. **`SC_Salvage_Tracker_Setup_SOLO_0.15.0.exe`** herunterladen und ausführen
3. Erstinstallation: Setup-Wizard → Anmeldung anlegen

**System:** Windows 10/11 (64-bit)

Updates: In der App unter **Einstellungen → System → Nach Updates suchen** (GitHub Releases).

---

## Entwicklung (lokal)

```powershell
cd Source\SC_Salvage_Tracker
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Installer bauen: [`installer/ANLEITUNG.md`](installer/ANLEITUNG.md)

CREW lokal testen (nur Entwicklung):

```powershell
$env:SST_EDITION="crew"
.\.venv\Scripts\python.exe main.py
```

---

## Datenschutz

- **Alle Spieldaten** (Datenbank, Backups, Einstellungen) bleiben **lokal** auf deinem PC.
- Standardpfad: `%LOCALAPPDATA%\SC Salvage Tracker\data`
- Es werden **keine** Nutzerdaten an den Entwickler oder Dritte übertragen.
- Update-Check lädt nur die öffentliche **`update-manifest.json`** von GitHub Releases (Versionsnummer, Download-URL, Prüfsumme).

---

## Haftungsausschluss (Software)

Diese Software wird **„wie besehen“ (as is)** bereitgestellt.

- Keine Garantie für Fehlerfreiheit, Verfügbarkeit oder Eignung für einen bestimmten Zweck.
- Der Entwickler haftet nicht für Datenverlust, entgangenen Profit oder Schäden durch Nutzung der Software.
- **Backup:** Vor Updates und DB-Wartung empfiehlt sich ein Backup (in der App: Einstellungen → System → Datensicherung).

Die Software befindet sich in der **öffentlichen Beta**. Funktionen können sich ändern.

---

## Star Citizen / Cloud Imperium Games

**English (official community-tool wording):**

This project is a **fan-made, unofficial** tool and is **not affiliated with, endorsed by, or sponsored by** Cloud Imperium Games® or Roberts Space Industries®.

**Star Citizen®**, **Roberts Space Industries®**, **Cloud Imperium Games®**, and related names, logos, and assets are trademarks or registered trademarks of Cloud Imperium Rights LLC / Cloud Imperium Games.

This software does not contain official game assets unless explicitly noted. Game data entered by users is their own responsibility.

**Deutsch:**

Dieses Projekt ist ein **inoffizielles Fan-Tool** und steht in **keiner Verbindung** zu Cloud Imperium Games (CIG) oder Roberts Space Industries (RSI). Es handelt sich **nicht** um ein offizielles Star-Citizen-Produkt.

Markennamen und Logos von Star Citizen gehören Cloud Imperium Games bzw. Cloud Imperium Rights LLC.

---

## Lizenz & Nutzung

Copyright © 2024–2026 Christian (Xan-Gan-Du). Alle Rechte vorbehalten.

Siehe [`LICENSE`](LICENSE). Kurzfassung:

- **SOLO Version:** Kostenlose Nutzung für private/persönliche Zwecke.
- **Quellcode:** Einsehbar auf GitHub; Weiterverbreitung, Verkauf oder Entfernen von Hinweisen ohne Zustimmung ist nicht gestattet.
- **CREW / ORGA:** Erweiterte Editionen nur gemäß Supporter-Key oder separatem Build des Autors.

---

## Support & Feedback

- **Issues:** [GitHub Issues](https://github.com/Xangandu/SC_Salvage_Tracker/issues)
- **Patchnotes:** [`Changelogs/PATCHNOTES.txt`](Changelogs/PATCHNOTES.txt)
- **Roadmap:** [`Changelogs/ROADMAP.txt`](Changelogs/ROADMAP.txt)

---

## Autor

**Christian** · **Xan-Gan-Du**

Entwickelt als Solo-Projekt neben dem normalen Alltag.
