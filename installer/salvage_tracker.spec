# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

project_dir = Path(SPECPATH).parent

block_cipher = None

bundle_data = [
    (str(project_dir / "assets"), "assets"),
    (str(project_dir / "ui" / "themes"), "ui/themes"),
    (str(project_dir / "database" / "schema"), "database/schema"),
    (str(project_dir / "Changelogs"), "Changelogs"),
    (str(project_dir / "config" / "build_edition.txt"), "config"),
]

a = Analysis(
    [str(project_dir / "main.py")],
    pathex=[str(project_dir)],
    binaries=[],
    datas=bundle_data,
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtNetwork",
        "PySide6.QtSvg",
        "PySide6.QtSvgWidgets",
        "sqlite3",
        "cryptography",
        "network",
        "network.host_server",
        "network.client_connection",
        "network.remote_database",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SC_Salvage_Tracker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_dir / "assets" / "images" / "app_icon.ico")
    if (project_dir / "assets" / "images" / "app_icon.ico").exists()
    else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SC_Salvage_Tracker",
)
