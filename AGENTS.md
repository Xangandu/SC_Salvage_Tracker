# AGENTS.md

## Cursor Cloud specific instructions

### What this is
SC Salvage Tracker — a **PySide6 (Qt 6) desktop GUI application** (Python, German UI) for tracking
Star Citizen salvage/mining operations. It is a single desktop app with an embedded **SQLite**
database (`data/salvage_tracker.db`, auto-created and schema-migrated on first launch). There is no
mandatory backend service or external database server. All networking (host/client co-op, relay
tunnel) is **optional** and only needed to exercise the multiplayer path.

### Running the app (GUI)
This is a Qt GUI app and needs a display. A VNC desktop is available on `DISPLAY=:1` in this
environment — run the app against it so it is visible/testable:

```bash
DISPLAY=:1 .venv/bin/python main.py
```

On a headless box without that desktop, wrap with Xvfb instead: `xvfb-run -a .venv/bin/python main.py`.

System packages required for Qt to run headlessly (already installed in the snapshot; reinstall only
if missing): `xvfb`, `libegl1`, `libgl1`, `libxkbcommon0`, `libxcb-cursor0`, and the other `libxcb-*`
helpers, plus `python3-venv`.

### Login / first-run flow (non-obvious)
- Default super-admin credentials are `superadmin` / `superadmin` (see `config/setup.py`).
- The **super-admin can only be used for initial setup and recovery — it cannot open the main app**.
  After a fresh DB, log in as `superadmin`, complete the initial-setup wizard ("Erstinstallation") to
  create an organization admin user, then log in as that new user to reach the main window.
- The committed `data/salvage_tracker.db` already has setup complete with an org user `Xangandu`
  (password unknown) plus `superadmin`. If you need to test the full login → main-window flow and do
  not have a usable org-user password, delete `data/salvage_tracker.db` (and `data/remember_me.json`)
  to trigger the fresh setup wizard, then restore them afterward with `git checkout -- data/`.

### Important: the SQLite DB and several data files are git-tracked
`data/salvage_tracker.db`, `data/remember_me.json`, `data/ships.json`, and the `data/network/*`
certs are committed. Running the app **mutates these tracked files**. After manual GUI testing,
restore them so you don't commit unrelated data changes:

```bash
git checkout -- data/ && git clean -fd data/
```

### Tests
No formal test framework (pytest etc.) is configured. Standalone test/verification scripts live in
`scripts/` and are run directly with the venv Python; each prints `OK`/exits non-zero on failure:

```bash
.venv/bin/python scripts/integration_test_flow.py      # core business-logic flow (temp DB)
.venv/bin/python scripts/test_backup_all.py            # runs backup tests + integration flow
.venv/bin/python scripts/test_initial_setup.py
.venv/bin/python scripts/test_permissions_session.py
.venv/bin/python scripts/test_permission_escalation.py
```
These use temporary databases and do not touch `data/`.

### Lint / build
- **Lint:** no linter (ruff/flake8/etc.) is configured. A reasonable sanity proxy is
  `.venv/bin/python -m compileall -q main.py ui auth config database network scripts`.
- **Build:** the production build (PyInstaller + Inno Setup) targets Windows only and is not needed
  for development. Do not run it on Linux.

### Optional dependencies
`requirements-optional.txt` (UPnP via `miniupnpc`) is **Windows-only** and is intentionally skipped
on Linux (the requirement marker excludes Linux). Skipping it does not affect normal app behavior.
