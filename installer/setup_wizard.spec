# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

installer_dir = Path(SPECPATH)
project_dir = installer_dir.parent

edition = os.environ.get("SST_SETUP_EDITION", "solo")
payload_name = f"payload_{edition}.zip"
payload_path = installer_dir / payload_name

_bg_custom = installer_dir / "assets" / "install_background.png"
_bg_legacy = installer_dir / "assets" / "install_bg.png"
_app_icon = project_dir / "assets" / "images" / "scst_solo_logo.ico"
if not _app_icon.exists():
    _app_icon = installer_dir / "assets" / "scst_solo_logo.ico"
datas = [
    (str(project_dir / "config"), "config"),
]
if _bg_custom.exists():
    datas.append((str(_bg_custom), "installer/assets"))
else:
    datas.append((str(_bg_legacy), "installer/assets"))
if _app_icon.exists():
    datas.append((str(_app_icon), "installer/assets"))
if payload_path.exists():
    datas.append((str(payload_path), "installer"))

a = Analysis(
    [str(installer_dir / "setup_wizard.py")],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "config.editions",
        "config.version",
        "installer.install_engine",
        "installer.wizard_app",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SC_Salvage_Tracker_Setup",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(_app_icon) if _app_icon.exists() else None,
)
