# SC Salvage Tracker 0.14.3 Alpha — Design Control

**Build 2026.07** · Codename: **Design Control**

## Highlights

### Design-Einstellungen (Phase 1)
- Design-Tab mit Unter-Reitern: **Erscheinungsbild**, **Dichte**, **Farben**, **Dashboard**, **Organisation**
- **10 Schriftarten** (Oxanium, Exo 2, Audiowide, Michroma, Teko, Jura, …) — **Oxanium** als Standard nach frischer Installation
- **Dichte:** Tabellen kompakt / normal / geräumig
- **Transparenz:** Fenster (0–100 %) und Panel (5-%-Schritte)
- **Navigationsbreite:** schmal / normal / breit
- **Farben:** Akzent, Label, Primär- und Sekundär-Button (optional)

### UI & Polish
- Moderner Farbwähler (Launcher-Stil)
- Navigation: größere, fette Menü-Labels
- Orange Überschriften app-weit vergrößert
- Filigraner Alien-Trenner über der Versionsangabe in der Navigation
- Fensterposition und -größe werden beim Beenden gespeichert (auch Monitor 2)

### Datenbank
- Schema **026:** `font_family`-Standard (Oxanium)
- Schema **027:** `table_density`, `panel_transparency`

## Installation

1. `SC_Salvage_Tracker_Setup_0.14.3.exe` ausführen
2. Bestehende Installation wird aktualisiert (In-App-Update ab 0.14.2 möglich)

## Build (Entwickler)

```powershell
cd "X:\Projektordner\SC_Salvage_Tracker\Source\SC_Salvage_Tracker"
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1
python installer\generate_update_manifest.py --installer "..\..\..\Release\installer\SC_Salvage_Tracker_Setup_0.14.3.exe"
```

`update-manifest.json` als Release-Asset auf GitHub hochladen (zusammen mit der Setup-EXE).

## Vollständige Patchnotes

Siehe [Changelogs/PATCHNOTES.txt](../Changelogs/PATCHNOTES.txt)
