# Edition-Upgrade per Supporter-Key — Plan & Roadmap

Stand: Juni 2026 · Version 0.15.x · Codename GLOBAL INTERFACE

> **Zweck:** Dieses Dokument hält Strategie, Nutzer-Flows und UX-Backlog fest,
> damit das Key-Upgrade-Modell (SOLO → CREW ohne Neuinstallation) später
> gezielt umgesetzt werden kann.
>
> **Status:** Geplant — Kern-Technik existiert bereits im Code (siehe unten).

---

## Kurzfassung

- **Ja, das geht** — SOLO installieren, CREW-Key eingeben, Badge wechselt, Netzwerk
  frei, **ohne Neuinstallation**.
- **Technik ist größtenteils fertig** — fehlt vor allem bessere UX und klare
  Release-Strategie (Universal-EXE).
- **Kein echter Kopierschutz** — Keys sind offline prüfbar und theoretisch
  weitergebbar (bewusst so designed).

---

## Empfohlene Strategie: Eine Universal-EXE (SOLO) + Key-Upgrade

**Primärer Download:** nur `SC Salvage Tracker - SOLO Version`  
**Upgrade:** CREW/ORGA per Supporter-Key in der App — ohne Neuinstallation  

**Optional parallel:** CREW-Installer für Käufer, die keinen Key eingeben wollen
(Edition ist im Build schon `crew`; Key entfällt).

| Kanal | Zielgruppe | Technik |
|-------|------------|---------|
| SOLO-Installer (Standard) | Alle, kostenlos | `build_edition = solo`, Upgrade per Key |
| CREW-Installer (Premium) | Direktkäufer | `build_edition = crew`, sofort frei |
| Supporter-Key | SOLO → CREW Upgrade | `edition_unlock` in DB |

Beide Wege führen zur **gleichen App** — nur der Einstieg unterscheidet sich.

---

## Was im Code bereits existiert

| Baustein | Datei / Ort |
|----------|-------------|
| Key-Prüfung (CREW/ORGA, HMAC) | `config/edition_keys.py` |
| Key speichern in der DB | `app_settings.edition_unlock` |
| Effektive Edition | `config/editions.py` → `effective_edition()` = `max(build, unlock)` |
| Feature-Gates (Netzwerk) | `has_feature("network.*")` |
| Key-Eingabe UI | Admin → Support-Tab (`ui/admin_page.py`) |
| Badge + Fenstertitel nach Unlock | `ui/main_window.py` → `refresh_edition_state()` |
| Vernetzungs-Tab entsperren | `ui/edition_feature_panel.py` |
| Key generieren | `scripts/generate_supporter_keys.py` |
| Tests | `scripts/test_edition_keys.py` |

**Nach Key-Eingabe (bereits implementiert):**

- Badge oben links: SOLO → CREW (inkl. Editions-Farbe / Glow)
- Fenstertitel: „SC Salvage Tracker - CREW Version“
- Vernetzungs-Bereich: Teaser verschwindet, Host/Client-UI erscheint
- **Kein Neustart nötig** — Signal `edition_unlock_changed` aktualisiert live

---

## Nutzer-Flows

### Flow 1: SOLO-Nutzer kauft CREW (Hauptfall)

```
SOLO installieren & starten
    → Normal spielen
    → CREW-Vernetzung entdecken (Admin → Vernetzung oder Support-Tab)
    → Teaser / Key-Hinweis
    → Key kaufen / erhalten
    → Admin → Support → Key eingeben → Freischalten
    → Key gültig?
        Nein → Fehlermeldung
        Ja  → Badge SOLO → CREW, Netzwerk frei
    → Optional: Verbindungs-Assistent (Host oder Client)
```

**Schritte für den Nutzer (Zieltext):**

1. **Installation** — SOLO-Setup von Website/GitHub
2. **Erststart** — Login, Badge zeigt **SOLO** (cyan)
3. **Entdeckung** — Vernetzungs-Tab zeigt Teaser + „Mehr erfahren“
4. **Kauf** — Key per Spende/Shop/E-Mail (Vertriebskanal festlegen)
5. **Einlösung** — `Administration → Support → Supporter-Key → Freischalten`
6. **Sofort sichtbar** — Badge **CREW** (grün), Vernetzung nutzbar
7. **Optional** — Verbindungs-Assistent: Host starten oder per Code beitreten

**Persistenz:** Key liegt in `app_settings.edition_unlock` — überlebt Neustart und Updates.

---

### Flow 2: Direktkäufer (CREW-Installer)

```
CREW-Setup laden → Installieren → Start: Badge CREW → Vernetzung sofort aktiv → Kein Key nötig
```

Für Supporter, die eine „fertige CREW-Version“ wollen — technisch identisch, nur ohne Key-Schritt.

---

### Flow 3: Admin vs. normaler Nutzer (Ist-Zustand)

| Rolle | Kann Key einlösen? | Heute |
|-------|-------------------|--------|
| Administrator | Ja | ✅ |
| Operator / andere | Nein | ⚠️ Meldung „Nur Administratoren…“ |

**Empfehlung:** Key-Einlösung für **jeden angemeldeten Nutzer** erlauben
(Installation ist meist Single-User). Admin-Recht nur für „Freischaltung entfernen“.

---

## Universal-EXE: Release-Prozess

**Öffentlich:**

- Ein Installer: `SC_Salvage_Tracker_Setup_SOLO_x.y.z.exe`
- GitHub Release: SOLO als Haupt-Asset

**Intern / Premium (optional):**

- CREW-Build nur auf Anfrage oder im Supporter-Bereich
- Keys: `py scripts/generate_supporter_keys.py crew -n 10` (nicht ins Repo committen)

**Build-Befehle:**

```powershell
# Standard-Release (Universal)
installer\build_installer.ps1 -Edition solo

# Optional: CREW-Direktversion
installer\build_installer.ps1 -Edition crew
```

**Updates:** Ein Update-Kanal für SOLO reicht — CREW-Unlock bleibt in der DB erhalten.

---

## UX-Backlog (priorisiert)

### Phase 1 — Geringer Aufwand, großer Effekt

| # | Was | Warum |
|---|-----|--------|
| 1 | **Key-Dialog erreichbarer machen** | Nicht nur Admin → Support; z.B. Klick auf SOLO-Badge oder Teaser-Button „CREW freischalten“ |
| 2 | **Teaser-Texte anpassen** | Statt „CREW Version kaufen“ → „Supporter-Key einlösen — keine Neuinstallation“ |
| 3 | **Erfolgs-Dialog erweitern** | Nach Unlock: „Vernetzung ist frei — jetzt einrichten?“ → Assistent oder Vernetzungs-Tab |
| 4 | **Key für alle Rollen** | Nicht nur `PERM_SETTINGS_MANAGE` |

### Phase 2 — Polishing

| # | Was |
|---|-----|
| 5 | Eigener Dialog „Edition freischalten“ (Key-Feld + Statuszeilen) |
| 6 | Support-Tab: drei Zeilen vereinfachen (Installation / Freischaltung / **Aktiv: CREW**) |
| 7 | Nach Entfernen des Keys: kurzer Hinweis, dass Netzwerk wieder gesperrt ist |

### Phase 3 — Optional / später

| # | Was |
|---|-----|
| 8 | Spenden-Link + automatischer Key-Versand (Shop/Webhook) |
| 9 | ORGA-Teaser + Keys wenn Modul kommt |
| 10 | Lizenzserver (nur bei echtem Kopierschutz-Bedarf) |

---

## Key-Vertrieb (Prozess, kein Code)

```
Nutzer → Shop/Spende → Benachrichtigung an Entwickler
    → generate_supporter_key crew
    → Key per E-Mail an Nutzer
    → Nutzer löst in App ein → CREW aktiv
```

**Praxis-Tipps:**

- Keys **pro Kauf** generieren, in sicherer Liste führen (wer, wann, Key-Hash)
- Format: `CREW-ABCD-EFGH-XXXXXXXX` (Bindestriche optional)
- Bei Missbrauch: aktuell **kein Remote-Widerruf** — bewusst offline-fähig

---

## Ziel-Texte für die UI (Entwurf)

**SOLO-Badge / Teaser:**

> Mit einem Supporter-Key schaltest du CREW frei — Host & Client, gemeinsame
> Datenbank. Keine Neuinstallation.

**Nach erfolgreichem Key:**

> CREW freigeschaltet. Badge und Vernetzung wurden aktualisiert.

**Support-Tab:**

- **Installation:** bleibt SOLO (Build) — welche EXE installiert wurde
- **Aktiv:** zeigt CREW — das zählt für Features

---

## Offene Entscheidungen

| Frage | Empfehlung |
|-------|------------|
| Nur noch SOLO-Installer öffentlich? | **Ja** — einfacher |
| CREW-Installer behalten? | **Optional** für Direktkäufer |
| Key nur Admin oder alle? | **Alle** angemeldeten Nutzer |
| Nach Unlock Assistent anbieten? | **Ja** — ein Klick |

---

## Technische Nuance: Build vs. Key

`effective_edition()` rechnet: **`max(Build-Edition, Unlock)`**.

- SOLO-Build + CREW-Key → **CREW aktiv** ✅
- Key wird in der **lokalen DB** gespeichert — überlebt App-Neustart

In `Changelogs/EDITIONS.txt` steht teils „begrenzt durch Build“ — im Code ist es
**Upgrade per Key möglich**. Falls eine SOLO-EXE **niemals** per Key hochgestuft
werden soll, müsste die Logik auf `min` statt `max` geändert werden. Aktuell:
**Upgrade erlaubt**.

---

## Aufwandsschätzung Umsetzung

| Phase | Inhalt | Aufwand |
|-------|--------|---------|
| **Phase 1** | Teaser-Texte, Badge-Klick → Key, Erfolgsdialog, Rechte lockern | ~0,5–1 Tag |
| **Phase 2** | Eigener Unlock-Dialog, Support-Tab vereinfachen | ~1 Tag |
| **Phase 3** | Shop-Integration | projektabhängig |

Die **Technik steht** — Phase 1 ist vor allem UX und Texte.

---

## Verwandte Dateien

- `Changelogs/EDITIONS.txt` — Feature-Matrix & Technik-Übersicht
- `config/editions.py` — Edition-Logik
- `config/edition_keys.py` — Key-Format & Validierung
- `ui/admin_page.py` — Support-Tab & Key-Einlösung
- `ui/main_window.py` — `refresh_edition_state()`
- `installer/build_installer.ps1` — SOLO/CREW/ORGA Builds

---

## Nächster Schritt (wenn angegangen)

**Phase 1 umsetzen:** Badge-Klick, Teaser-Texte, Key für alle Nutzer,
Assistent nach Unlock.
