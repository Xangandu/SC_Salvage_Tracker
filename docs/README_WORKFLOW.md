# Workflow — README & GitHub-Öffentlichkeit

Checkliste für jede Version und vor jedem Push, der `README.md` betrifft.

---

## 1. Zwei Zielgruppen, zwei Dateien

| Datei | Zielgruppe | Inhalt |
|-------|------------|--------|
| **`README.md`** | Endnutzer, GitHub-Besucher | Download, Editionen, Disclaimer, Datenschutz, Lizenz-Verweis |
| **`docs/DEVELOPMENT.md`** | Entwickler | venv, Build, `SST_EDITION`, Tests, interne Pfade |
| **`LICENSE`** | Rechtliches (vollständig) | Haftung, Marken, Nutzungsbedingungen |

**Regel:** README kurz halten. Details → verlinken, nicht kopieren.

---

## 2. README.md — erlaubt

- Link zu **Releases/latest** (keine feste Versionsnummer in Dateinamen)
- Editionen SOLO / CREW / ORGA (kurz)
- CIG-Disclaimer (ein kompakter Block, EN reicht)
- Datenschutz (3–4 Bulletpoints)
- Verweis auf `LICENSE`
- GitHub Issues für Support
- Autorname (öffentlich gewollt)

---

## 3. README.md — verboten / vermeiden

| Nicht einfügen | Grund |
|----------------|--------|
| E-Mail, Discord, PayPal privat | Spam / Social Engineering |
| Tokens, Passwörter, Keys, `.env` | Sicherheit |
| Supporter-Keys oder Key-Generierung | Missbrauch |
| `$env:SST_EDITION=crew` | Dev-Bypass — nur in `docs/DEVELOPMENT.md` |
| Super-Admin-Recovery-Details | Sicherheit |
| Feste Setup-Dateinamen mit Version (`…_0.15.0.exe`) | veraltet schnell — `…_SOLO_*.exe` + latest-Link |
| Absolute PC-Pfade (`X:\Projektordner\…`) | unnötig, verrät Struktur |
| Vollständiger Haftungstext | steht in `LICENSE` |
| Doppelter EN+DE Disclaimer (lang) | EN-Kurzblock + ein Satz DE reicht |

---

## 4. Bei neuer Version

1. **`config/version.py`** anpassen  
2. **`Changelogs/PATCHNOTES.txt`** ergänzen  
3. **README:** nur bei Bedarf — meist **keine** Versionsnummer ändern (latest-Link reicht)  
4. Optional eine Zeile „Beta“ beibehalten, keine Build-Nummer pflegen  
5. Release bauen → `update-manifest.json` → GitHub Release  
6. **LICENSE** nur ändern, wenn sich Nutzungsbedingungen ändern  

---

## 5. Vor dem Commit (README)

- [ ] Keine Secrets / Keys / privaten Kontakte  
- [ ] Kein Dev-Bypass in README  
- [ ] Download-Link zeigt auf `releases/latest`  
- [ ] CIG-Disclaimer vorhanden  
- [ ] Verweis auf `LICENSE` und `docs/DEVELOPMENT.md`  
- [ ] Länge: ca. 80–120 Zeilen max. (öffentliche Fassung)  

---

## 6. GitHub Repository-Einstellungen (optional)

- **Description:** z. B. *Unofficial Star Citizen Salvage tracker — SOLO free (Beta)*  
- **Website:** Releases-URL  
- **Topics:** `star-citizen`, `salvage`, `pyqt`, `pyside6` (keine offiziellen CIG-Logos als Repo-Avatar)

---

## 7. Cursor / KI

Beim Bearbeiten von `README.md` gilt die Projekt-Regel:  
`.cursor/rules/readme-public.mdc`
