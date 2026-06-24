# SC Salvage Tracker

A PySide6 (Qt) desktop application for tracking Star Citizen salvage operations
(sessions, refinery jobs, sales, payouts). German UI. Data is stored locally in
SQLite under `data/`. There is no backend service — the only "service" is the
desktop GUI itself. An optional peer-to-peer host/client network mode exists
(`network/`), but it is off by default (standalone mode).

## Cursor Cloud specific instructions

### Running things (Python 3.12, deps in `.venv`)

The startup update script creates `.venv` and installs `requirements.txt`. Use
that interpreter for everything: `.venv/bin/python`.

- Run the app (GUI): `DISPLAY=:1 .venv/bin/python main.py`
  - A VNC X server is already running on display `:1`; the app needs it (or any
    X display) to show windows.
  - For a non-GUI import/smoke check use `QT_QPA_PLATFORM=offscreen`.
- Run all tests: the test suite is plain standalone scripts under `scripts/`
  (no pytest). Run the aggregate backup suite with
  `.venv/bin/python scripts/test_backup_all.py`, plus
  `scripts/integration_test_flow.py`, `scripts/network_workflow_test.py`,
  `scripts/test_initial_setup.py`, `scripts/test_permissions_session.py`,
  `scripts/test_permission_escalation.py`. Each prints `OK`/exits non-zero on
  failure and uses a throwaway temp DB (they do not touch `data/`).
- Lint: there is no configured linter. Use a compile check:
  `.venv/bin/python -m compileall -q main.py ui config database network auth update`.
- Build (Windows installer via PyInstaller) is Windows-only (`installer/*.ps1`,
  `*.iss`); it does not run on this Linux VM. Skip it.

### Non-obvious gotchas

- System Qt libraries are required for PySide6 (e.g. `libegl1`, `libgl1`,
  `libxkbcommon0`, the `libxcb*` set, `libdbus-1-3`, `libfontconfig1`) plus
  `python3.12-venv`. These are OS packages (captured in the VM snapshot), so they
  are intentionally NOT in the update script.
- The app auto-logs in via a saved "remember me" token in
  `data/remember_me.json` (user `Xangandu` / display name `Xan-Gan-Du`,
  Administrator). No password prompt appears on a normal start. To force the
  login dialog, remove/rename `data/remember_me.json`.
- Default super-admin recovery credentials are `superadmin` / `superadmin`
  (see `config/setup.py`), only usable before/at initial setup.
- `data/salvage_tracker.db` is committed and is the live DB the running app
  writes to. Running the app or doing manual GUI testing mutates it; restore it
  with `git checkout -- data/salvage_tracker.db` if you don't want to keep those
  changes. The test scripts use temp DBs and never touch it.
- `ui/update_manager.py` and the `update/` package were missing from the
  original commit even though `ui/main_window.py` / `ui/admin_page.py` import
  them, which blocked startup. They were reconstructed as minimal, no-network
  stubs (the online update check is intentionally skipped — the installed
  version is treated as current). If the real modules are restored, these stubs
  can be replaced.
- The harmless warning `qt.svg: Cannot read file '.../nav_version_divider.svg'`
  on startup is a pre-existing malformed asset and does not affect the app.
