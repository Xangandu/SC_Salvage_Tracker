# Session-Notizen — Workflows & Standort-Feature

Stand: **v0.16.0 Beta (Location Flow)** — Kernfunktionen umgesetzt.

Referenz Stationen: [Star Citizen Wiki — Space stations](https://starcitizen.tools/Category:Space_stations)

---

## Bereits umgesetzt (technisch)

- Installer, Splash, Raffinerie-Live-Sync, GitHub v0.15.2
- **v0.16.0:** Lager / Standorte, Materialfluss Schiff→Station, Kontext-Dashboard,
  Hinweisleiste, Idle-Warnungen, Reserve-Tags — siehe `docs/RELEASE_0.16.0_LOCATION_FLOW.md`

---

## Nutzer-Antworten (vollständig)

### Phase 0 — Hangar

| # | Antwort |
|---|---------|
| 1 | Beides möglich: leeres Schiff **oder** Reste im Laderaum |
| 2 | **Ja**, vor Start immer prüfen, was los ist |
| 3 | **Beides** soll möglich sein: Session beim Spawn **oder** erst beim Abflug |

### Phase 1 — Session (SOLO-Fokus, CREW/ORGA später anders)

| # | Antwort |
|---|---------|
| 4 | SOLO: immer der Benutzer |
| 5 | Missionskosten **am Anfang** |
| 6 | Mehrere aktive Sessions: **nein** in SOLO, **ja** in CREW und ORGA |

### Phase 2 — Salvage

| # | Antwort |
|---|---------|
| 7 | Material **abhängig vom Schiff** |
| 8 | Mengen **erst an der Station nach dem Einlagern** erfassen |
| 9 | Material **immer getrennt** buchen |

### Phase 3 — Station

| # | Antwort |
|---|---------|
| 10 | **Dropdown** aller Weltraum-Stationen, sortiert nach System: **Stanton, Pyro, Nyx**. Quelle: [Space stations](https://starcitizen.tools/Category:Space_stations). **Trennung: mit Raffinerie / ohne Raffinerie** |
| 11 | Heute: Material **überall** möglich (Station, großes Schiff). **Zukunft:** Basenbau → eigenes Lager in Base |
| 12 | **Spontan/situativ:** oft RMC mit aus Station, wenn noch weiter gespielt wird; sonst ausloggen |

### Phase 4 — Tracker-Erfassung

| # | Antwort |
|---|---------|
| 13 | RMC an Station **heute nicht erfasst** — nur Notiz möglich → **Kernlücke** |
| 14 | Ort **nicht Pflicht**, aber **optional eintragbar** |
| 15 | Material im Schiff = **noch nicht gelagert/verkauft** |

### Phase 5 — Raffinerie

| # | Antwort |
|---|---------|
| 16 | Meist Rubble, manchmal **CM_SCRAPS / CM_SALVAGE**. **Zukunft:** Mining → viele Rohstoffe |
| 17 | Job **sofort** eintragen (wenn ingame gestartet — dann kennt man Input/Output) |
| 17b | **cSCU-Umrechnung nötig:** Terminal = cSCU, Tracker = SCU. **1000 cSCU = 10 SCU** (Faktor 100). Beispiel: 20 SCU Station → 2000 cSCU rein → 600 cSCU raus = 6 SCU |
| 18 | Während Job: woanders farmen, RMC aus Platzmangel auf Station. Tracker zeigt **Job**, aber **kein RMC-Lager** |
| 19 | CM-Abholung kann **Tage** dauern |

### Phase 6 — „Wo liegt was?“

| # | Antwort |
|---|---------|
| 20 | **Beides:** Liste nach Ort **und** nach Material, **sortierbar** |
| 21 | Hinweis nach **10 Tagen**, **alle 10 Tage wiederholen**, **nicht störend** |
| 22 | Granularität: **Station oder Stadt** reicht |
| 23 | **Historie behalten**; Spieler darf Einträge **selbst löschen** |

### Phase 7 — Verkauf

| # | Antwort |
|---|---------|
| 24 | **Oft getrennt** (viele Stationen kaufen kein RMC; Städte schon: Orison, Area18, NB, Lorville; Pyro/Nyx z. B. Checkmate, Levski) |
| 25 | **Verkaufsort wichtig** (unterschiedliche Ankaufspreise) |
| 26 | **Getrennte Verkäufe sinnvoll** (Material im Schiff an verschiedenen Orten verkauft) |

### Phase 8 — Auszahlung

| # | Antwort |
|---|---------|
| 27 | SOLO: **Gewinn nach Kosten** reicht |
| 28 | CREW: Auszahlung durch **wer tatsächlich verkauft hat** |
| 29 | Raffinerie-Kosten „bezahlt von“: **wechselnd** je nach Tag |

### Phase 9 — Vergessenes

| # | Antwort |
|---|---------|
| 30 | **Große Menge** RMC auf unbekannten Stationen — genaue Häufigkeit unbekannt, Problem **real und akut** |
| 31 | **Eigene Seite „Lager / Standorte“** mit WO welche Ware liegt |
| 32 | **Tag/Flag** für bewusst gelagerte Reserve → **keine Warnung** |

---

## Abgeleitete Produkt-Entscheidungen

| Thema | Entscheidung |
|-------|----------------|
| Ort Pflicht | **Nein** — optional |
| Ort-Granularität | Station/Stadt (+ System: Stanton/Pyro/Nyx) |
| Schiff vs. Station | Schiff = Status „noch nicht abgegeben“ |
| UI Hauptfeature | **Eigene Seite** „Lager / Standorte“ |
| Sortierung | Nach Ort **und** Material |
| Erinnerung | 10 Tage idle → Hinweis, alle 10 Tage, dezent |
| Reserve | User-Tag „keine Warnung“ |
| Historie | Vollständig + **manuell löschbar** durch Spieler |
| Verkauf | Ort pro Verkauf (**Schema `sales.location` existiert bereits**) |
| Raffinerie Terminal | **cSCU ↔ SCU** Hilfe/Umrechnung (×100) |
| Stationen UI | Dropdown aus kuratierter Liste, gruppiert System + Raffinerie ja/nein |

---

## Referenz-Workflows (SOLO)

### Workflow A — Standard-Station mit Raffinerie

1. Hangar → Tracker prüfen (offene Standorte, laufende Jobs)
2. Session starten (flexibel) + **Kosten am Anfang**
3. Salvage (material je nach Schiff) — **noch nichts buchen**
4. Landung Station → Material **getrennt** eintragen (Mengen nach Einlagern)
5. Rubble → Raffinerie-Job (**sofort**, cSCU am Terminal → SCU im Tracker)
6. RMC optional: im Schiff behalten **oder** an Station → **Standort erfassen**
7. Weiterfliegen / ausloggen
8. Job läuft (Tracker Live) — CM später abholen
9. Verkauf **getrennt** an passender Stadt/Station + **Verkaufsort**
10. SOLO: Gewinn nach Kosten — fertig

### Workflow B — RMC vergessen (Ist-Problem)

1. Schritte 1–6 wie oben, RMC an Station gelassen
2. **Nicht** im Tracker erfasst (nur Notiz oder gar nichts)
3. Wochen später: Tracker zeigt globales RMC evtl. nicht — ingame liegt es noch irgendwo
4. **Ziel:** Standort-Seite + optionaler 10-Tage-Hinweis verhindert das

### Workflow C — Verkauf an zwei Orten

1. CM in Orison verkauft, RMC später in Area18 vom Schiff
2. **Zwei Verkaufsbuchungen** mit unterschiedlichem Ort
3. Gewinn/Statistik pro Ort nachvollziehbar

---

## Technische Anknüpfung (bestehend)

- `refinery_jobs.station` — Freitext heute („Orison“), soll Dropdown werden
- `sales.location` — bereits vorhanden, nutzen/ausbauen
- `storage_items` — global, **ohne Ort** → Erweiterung nötig für Standort-Feature
- Materialtypen in Seed bereits Mining-Vorbereitung (Quantanium, Gold, …)

---

## Zukunft (explizit nicht jetzt)

- **Basenbau:** Heim-Lager in eigener Base
- **Mining-Tracking:** viele Rohstoffe
- **CREW/ORGA:** Multi-Session, geteilte Standort-Übersicht

---

## Nächste Planungsschritte

Erledigt (2026-06-28):

1. **Spezifikation:** [`SPEC_STANDORTE_UND_LAGER.md`](SPEC_STANDORTE_UND_LAGER.md) — Datenmodell, UI-Wireframe, Phasen A–E
2. **Stationen-Katalog:** `config/locations/stations.json` (Stanton/Pyro/Nyx, mit/ohne Raffinerie)
3. **Landeplätze:** `config/locations/landing_zones.json` (Orison, Area18, …)
4. **Loader:** `config/locations/catalog.py` — Dropdown-Gruppen
5. **cSCU-Hilfe:** `config/locations/cscu.py` — 100 cSCU = 1 SCU

Erledigt Phase B (2026-06-28):

- DB-Tabellen `material_stockpiles` + `material_stockpile_events`
- Repository + neue Seite **Lager** in der Navigation
- Manuell: Material an Station/Stadt oder **pro Schiff** erfassen
- Historie mit löschbaren Einträgen
- Raffinerie-Methoden auf ingame-Reihenfolge aktualisiert

Erledigt Phase C (2026-06-28 / Release 0.16.0):

- 10-Tage-Hinweis, Reserve-Tags in Warnlogik
- Summen-Panel auf Lager-Seite (sichtbare Chips)
- Hinweisleiste im Kontext-Dashboard mit Ort + Zeit

Offen:

- **Solo-Auto-Auszahlung** nach Verkauf
- CREW-Unterschiede separat (Multi-Session, geteilte Standort-Übersicht)
