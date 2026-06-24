# AGENTS.md

## Cursor Cloud specific instructions

SC Salvage Tracker is a single **PySide6 (Qt 6) desktop GUI app** (German UI) for tracking Star Citizen salvage operations. It uses an embedded **SQLite** database (`data/salvage_tracker.db`, auto-created on first run). There is no web/backend split and no external services; the only "must run" service is the desktop app itself. Optional networking (in-app host server on `47890`, relay via `scripts/start_relay_server.py` on `47900`) is only needed to test multiplayer co-op.

### Environment
- Dependencies are installed into a virtualenv at `.venv` (the startup update script runs `pip install -r requirements.txt` into it). Use `.venv/bin/python` (the repo's `scripts/*.bat`/`.ps1` helpers are Windows-only; on Linux use `.venv/bin/...`).
- Qt needs system libraries (libEGL, libGL, xcb, etc.); these are baked into the VM image. If `import PySide6` fails with `libEGL.so.1: cannot open shared object file`, reinstall the Qt system libs (e.g. `libegl1 libgl1 libxcb-cursor0` and related `libxcb-*`).

### Running the app
- GUI: a VNC desktop is available on display `:1`. Run with `DISPLAY=:1 .venv/bin/python main.py`.
- Headless (no GUI), e.g. importing Qt modules in scripts/CI: set `QT_QPA_PLATFORM=offscreen`.

### First-run / login flow (non-obvious)
On a fresh database the app boots into a setup chain: log in as super admin `superadmin` / `superadmin` → forced password change → "Erstinstallation" wizard creates an organization admin → it then logs you out and you sign in as that new admin (which also forces a one-time password change). To reset to first-run, delete `data/salvage_tracker.db`. Note `data/salvage_tracker.db` is intentionally committed to the repo as seed data — avoid committing test-mutated versions of it (and of `data/remember_me.json`); `git checkout -- data/` to restore.

### Tests & lint
- There is no test framework/lint config. Tests are standalone scripts under `scripts/`. Run individually, e.g. `QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/integration_test_flow.py`. `scripts/test_backup_all.py` runs the full suite (backup phases + integration flow). These tests use throwaway temp databases and do not touch `data/`.
- For a syntax/import sanity check use `.venv/bin/python -m compileall main.py auth config database network ui scripts`.
