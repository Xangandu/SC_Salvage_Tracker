# Release 0.16.0 Beta — Location Flow

**Build:** 2026.11  
**Datum:** Juni 2026  
**Codename:** LOCATION FLOW

---

## Überblick

Version 0.16.0 ist das größte Feature-Release seit den Editionen (0.15.0) und der
Internationalisierung (0.15.2). Der Tracker beantwortet jetzt die zentrale Spielerfrage:

**Wo liegt wie viel von welchem Material — und seit wann?**

Das globale Lager ohne Ort wird schrittweise durch ortsbezogene Stockpiles ersetzt.

---

## Neue Funktionen

### 1. Seite „Lager / Standorte“

| Funktion | Beschreibung |
|----------|--------------|
| Bestandsliste | Nach Standort, Material oder Alter sortierbar |
| Orte | Station, Stadt, Schiff (Dropdown aus Katalog) |
| Historie | Ein- und Auslagerungen, löschbar durch Spieler |
| Summen | Sichtbare Material-Chips (CM, RMC, …) mit SCU-Mengen |
| Idle-Banner | Warnung bei >10 Tagen ohne Bewegung |
| Reserve | Tag setzen → keine Idle-Warnung |
| Aktionen | Erinnert, Reserve setzen, Verschoben/entnommen, Löschen |

**Dateien:** `ui/storage_page.py`, `database/stockpile_repository.py`,  
`database/schema/028_material_stockpiles.sql`

### 2. Standort-Katalog

- `config/locations/stations.json` — Weltraum-Stationen (Stanton, Pyro, Nyx)
- `config/locations/landing_zones.json` — Städte / Landeplätze
- `config/locations/catalog.py` — Gruppierte Dropdowns (mit/ohne Raffinerie)
- `config/locations/cscu.py` — 100 cSCU = 1 SCU
- `ui/system_location_picker.py`, `ui/location_combo.py`

### 3. Materialfluss Session → Schiff → Station

```
Salvage erfassen (Session)
    → Batch + storage_item + Stockpile IN_SHIP (Schiff der Session)
Station: Material einlagern
    → Abzug vom Schiff-Stockpile, neuer STORED-Stockpile an Station
Raffinerie starten
    → Rohmaterial vom Schiff abziehen (reserve_ship_stockpile_for_refinery)
Raffinerie abholen
    → CM als Stockpile an Station (kein doppelter globaler Eintrag)
Verkauf
    → FIFO aus storage_items (wie bisher), Dashboard ohne Doppelzählung
```

**Schlüssel-APIs:**

- `deposit_session_capture()` — Material auf Schiff
- `get_session_ship()` — Schiff aus Sitzungsname
- `_transfer_from_ship_stockpiles()` — Schiff → Station
- `get_dashboard_storage_inventory()` — gefiltertes Lager für Dashboard/Verkauf

### 4. Kontext-Dashboard & Hinweisleiste

Separates Dashboard-Fenster (`ui/context_dashboard/`):

| Kontext | Inhalt |
|---------|--------|
| Übersicht | KPIs, nächste Aktion |
| Session | Aktive Sitzung, Materialien |
| Raffinerie | Offene/fertige Jobs |
| Lager | Bestand nach Ort, Events |
| Verkauf | Verkaufsbereites Material |
| Auszahlung | Offene Payouts |
| Historie | Letzte Aktivitäten |

**Hinweisleiste (`GlobalAlertStrip`):**

- Volle Breite unter dem Header
- Ein-/Ausklappen über Glocken-Icon
- Zeigt z. B.: `Verkaufsbereit — CM · HUR-L2 Faithful Dream Station · Heute`
- Kein irreführendes „Globales Lager“ bei stockpile-geführtem Bestand

**Dateien:** `ui/context_dashboard/`, `database/dashboard_operations_repository.py`

### 5. Raffinerie-Ergänzungen

- Live cSCU → SCU im Abschluss-Dialog (`MobiglasDoubleInputDialog`, `live_scu_from_cscu`)
- Standort-Dropdown statt Freitext wo möglich
- Abbruch stellt Rohmaterial auf Schiff zurück

### 6. Session-Dashboard UX

- SITZUNGEN-Lifetime-Zähler aus Session-Ansicht entfernt (bleibt in Historie)
- Label **CREW (Sitzung)** statt CREW

---

## Datenbank

### Neue Tabellen (Schema 028)

- `material_stockpiles` — ortsbezogener Bestand
- `material_stockpile_events` — Bewegungshistorie

### Status-Werte (Stockpile)

| Status | Bedeutung |
|--------|-----------|
| `IN_SHIP` | Material noch im Schiff |
| `STORED` | An Station/Stadt eingelagert |
| `IN_REFINERY` | Im Raffinerie-Job |
| `READY_PICKUP` | Abholbereit |
| `RESERVED` | Reserve-Tag gesetzt |

---

## Migration & Upgrade

1. App starten → Schema 028 wird automatisch angewendet
2. Bestehende `storage_items` bleiben für Verkauf/FIFO erhalten
3. Neuer Workflow: ab sofort über Lager / Standorte führen
4. Alte globale Einträge können parallel existieren — ggf. manuell bereinigen

---

## Tests

```powershell
.venv\Scripts\python.exe scripts\integration_test_flow.py
```

Prüft: Session → Raffinerie → Verkauf → Gewinn (angepasst an Stockpile-Modell)

---

## Bekannt offen (0.16.x)

| Punkt | Status |
|-------|--------|
| Solo-Auto-Auszahlung nach Verkauf | Geplant |
| CREW Multi-Session + geteilte Standorte | Geplant |
| Basenbau / Heim-Lager | Zukunft |
| Mining-Rohstoffe im Standort-Workflow | Zukunft |

---

## Referenzen

- [Session-Notizen Workflows](SESSION_NOTES_2026-06-28_WORKFLOWS_UND_STANDORTE.md)
- [Spezifikation Standorte](SPEC_STANDORTE_UND_LAGER.md)
- [Patchnotes](../Changelogs/PATCHNOTES.txt)
- [Roadmap](../Changelogs/ROADMAP.txt)
