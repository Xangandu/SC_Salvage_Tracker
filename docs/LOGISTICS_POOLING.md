# Logistik-Pooling (Material-Pools)

## Überblick

Salvage-Runs werden weiterhin **einzeln in der Sitzung** erfasst. Im Hintergrund fasst der Tracker gleichartiges Material zu **Pools** zusammen, damit Raffinerie und Lager mit **Gesamtmengen** arbeiten — nicht Batch für Batch oder Zeile für Zeile.

**Pool = Standort + Materialtyp**, z. B.:

- Reclaimer · CM Rubble · 1.245 SCU (alle Runs derselben Sitzung auf dem Schiff)
- Orison · RMC · 800 SCU (alle Einlagerungen am selben Standort)

Materialtypen bleiben getrennt (RMC, CM Rubble, …).

---

## Spieler-Workflow

### Sitzung: Beute eintragen

1. Mehrere Salvage-Runs in derselben Sitzung erfassen (z. B. 3× Reclaimer).
2. Gleiches Material wird **automatisch zusammengeführt**:
   - **Batch-Ebene:** eine Batch-Zeile pro Sitzung + Material (`create_batch_from_session`).
   - **Schiff-Lager:** eine Stockpile-Zeile pro Schiff + Material.

### Raffinerie: Auftrag aus Pool

1. Seite **Raffinerie** → Tabelle **Verfügbares Material** zeigt Pools (Standort, Material, SCU).
2. **Material-Quelle** wählen (Schiff oder Lager-Standort).
3. **Eingabemenge** frei wählen (z. B. 800 SCU von 1.245 SCU am Schiff).
4. Auftrag `Auftrag anlegen` — der Tracker:
   - reserviert die Menge **FIFO** aus dem Lager/Schiff-Pool,
   - bucht die Raffinerie **FIFO über offene Batches** (Nachverfolgung pro Sitzung).

### Lager: Verschieben

1. **Material verschieben** → Quellen sind **zusammengefasst** (Standort · Material · Gesamtmenge).
2. Menge eingeben (Standard: volle Pool-Summe).
3. Ziel wählen (Station/Stadt oder anderes Schiff).
4. Entnahme erfolgt **FIFO** über die zugrundeliegenden Stockpile-Zeilen.

### Lager: Als bewegt markieren (Entnahme)

1. Zeile in der Bestandsliste wählen.
2. **Als bewegt markieren** → die Menge der gewählten Zeile wird aus dem **Pool** entnommen (FIFO), Material verlässt den Tracker.

---

## Technisches Modell

### Pool-Schlüssel

| Pool-Typ | Schlüssel |
|----------|-----------|
| Schiff | `(SHIP, ship_id, material_code)` |
| Lager | `(STORED, location_kind, location_key, material_code)` |

### Wichtige API-Methoden

| Methode | Repository | Zweck |
|---------|------------|-------|
| `list_material_pools()` | `stockpile_repository` | Aggregierte Pools für UI |
| `allocate_batches_fifo()` | `material_repository` | Raffinerie-Buchführung über Batches |
| `create_job_from_pool()` | `refinery_repository` | Raffinerie-Auftrag aus Pool |
| `transfer_from_material_pool()` | `stockpile_repository` | Verschieben zwischen Standorten |
| `withdraw_from_material_pool()` | `stockpile_repository` | Entnahme / „Als bewegt markieren“ |
| `reserve_ship_stockpile_for_refinery()` | `stockpile_repository` | Schiff-Pool → Raffinerie |
| `reserve_stored_stockpile_for_refinery()` | `stockpile_repository` | Lager-Pool → Raffinerie |

### FIFO

Bei Entnahme, Verschiebung und Raffinerie-Reservierung werden die **ältesten** Stockpile-Zeilen zuerst reduziert (`ORDER BY last_activity_at ASC`).

Raffinerie-Jobs verteilen die Eingabemenge zusätzlich **FIFO über `material_batches`** (älteste Batch-ID zuerst), optional gefiltert nach Schiff der Sitzung.

### Batch-Merge bei Session-Erfassung

`create_batch_from_session` sucht einen offenen Batch mit gleicher `session_id` + `material_type_id` und erhöht dessen Menge, statt jedes Mal einen neuen Batch anzulegen.

### UI-Hilfsmodule

- `ui/storage_pool_utils.py` — Zeilen → Pools für Lager-Dialog und Entnahme
- `ui/storage_transfer_dialog.py` — Pool-basierter Verschiebe-Dialog
- `ui/refinery_page.py` — Pool-Tabelle + `create_refinery_job_from_pool`

### Netzwerk (RPC)

Pool-Operationen sind über RPC verfügbar (Pool als `dict` serialisierbar):

- `create_refinery_job_from_pool`
- `transfer_from_material_pool`
- `withdraw_from_material_pool`

---

## Fehlermeldungen (Auszug)

| Key | Bedeutung |
|-----|-----------|
| `error.storage.insufficient_pool` | Nicht genug Material am gewählten Standort |
| `error.storage.insufficient_ship_pool` | Nicht genug Material am Schiff |
| `error.refinery.insufficient_pool` | Raffinerie: Pool-Menge zu gering |
| `error.material.insufficient_batches` | Batch-Buchführung kann Menge nicht zuordnen |

---

## Siehe auch

- [SPEC_STANDORTE_UND_LAGER.md](SPEC_STANDORTE_UND_LAGER.md) — Standort- und Lagerkonzept
- [RELEASE_0.16.0_LOCATION_FLOW.md](RELEASE_0.16.0_LOCATION_FLOW.md) — Materialfluss Session → Schiff → Station
