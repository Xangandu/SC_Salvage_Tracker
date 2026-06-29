"""Datei-Installation für den PySide6-Setup-Assistenten."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import uuid
import zipfile
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

_INSTALLER_DIR = Path(__file__).resolve().parent
_EXE_NAME = "SC_Salvage_Tracker.exe"
_MANIFEST_NAME = ".sst_install.json"
_UNINSTALL_SCRIPT = "uninstall.ps1"
_LOGS_DIR_NAME = "SC Salvage Tracker"
_DB_NAME = "salvage_tracker.db"
_REMEMBER_ME_NAME = "remember_me.json"
_BACKUP_PREFIX = "backup_install_"

EDITION_APP_IDS = {
    "solo": "A7C3E9F1-2B4D-4E8A-9F1C-6D5E8A2B4C7F",
    "crew": "B8D4F0A2-3C5E-4F9B-0A2D-7E6F9B3C5D8E",
    "orga": "C9E5A1B3-4D6F-501C-1B3E-8F7A0C4D6E9F",
}

PUBLISHER = "Christian · Xan-Gan-Du"

DATA_MODE_KEEP = "keep"
DATA_MODE_FRESH = "fresh"


def user_data_dir() -> Path:
    """AppData-Datenordner (wie config.paths.data_dir in der frozen App)."""
    base = os.environ.get(
        "LOCALAPPDATA",
        str(Path.home() / "AppData" / "Local"),
    )
    return Path(base) / _LOGS_DIR_NAME / "data"


def database_path() -> Path:
    return user_data_dir() / _DB_NAME


def backups_dir() -> Path:
    return user_data_dir() / "backups"


def has_existing_user_data() -> bool:
    return database_path().exists()


def _process_base_name() -> str:
    return Path(_EXE_NAME).stem


def is_application_running() -> bool:
    if sys.platform != "win32":
        return False
    process_name = _process_base_name()
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    f"$p = Get-Process -Name '{process_name}' "
                    "-ErrorAction SilentlyContinue; "
                    "if ($p) { exit 0 } else { exit 1 }"
                ),
            ],
            capture_output=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return result.returncode == 0
    except Exception:
        return False


def stop_application() -> None:
    if sys.platform != "win32":
        return
    process_name = _process_base_name()
    try:
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    f"Stop-Process -Name '{process_name}' "
                    "-Force -ErrorAction SilentlyContinue"
                ),
            ],
            capture_output=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except OSError:
        pass


def backup_user_database() -> Path:
    source = database_path()
    if not source.exists():
        raise FileNotFoundError(f"Datenbank nicht gefunden: {source}")

    destination_dir = backups_dir()
    destination_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = destination_dir / f"{_BACKUP_PREFIX}{stamp}.db"
    suffix = 0
    while destination.exists():
        suffix += 1
        destination = destination_dir / f"{_BACKUP_PREFIX}{stamp}_{suffix}.db"

    shutil.copy2(source, destination)
    return destination


def reset_user_data() -> None:
    """Benutzerdaten löschen — vorhandene Backups bleiben erhalten."""
    data_dir = user_data_dir()
    for name in (_DB_NAME, _REMEMBER_ME_NAME):
        path = data_dir / name
        if path.exists():
            path.unlink()


def prepare_user_data_for_install(*, reset: bool) -> Path | None:
    """
    Vor Neuinstallation: optional Backup erstellen und Benutzerdaten zurücksetzen.
    Gibt den Backup-Pfad zurück, wenn ein Backup erstellt wurde.
    """
    if not reset or not has_existing_user_data():
        return None

    if is_application_running():
        stop_application()
        import time

        time.sleep(1)
        if is_application_running():
            raise RuntimeError(
                "SC Salvage Tracker läuft noch. "
                "Bitte die Anwendung beenden und die Installation erneut starten."
            )

    backup_path = backup_user_database()
    reset_user_data()
    return backup_path


def resolve_payload_zip(edition: str) -> Path:
    name = f"payload_{edition}.zip"
    if getattr(sys, "frozen", False):
        for candidate in (
            Path(sys._MEIPASS) / "installer" / name,
            Path(sys._MEIPASS) / name,
        ):
            if candidate.exists():
                return candidate
    local = _INSTALLER_DIR / name
    if local.exists():
        return local
    release_root = _INSTALLER_DIR.parent.parent.parent / "Release" / "app"
    folder_map = {
        "solo": "SC_Salvage_Tracker_SOLO",
        "crew": "SC_Salvage_Tracker_CREW",
        "orga": "SC_Salvage_Tracker_ORGA",
    }
    app_dir = release_root / folder_map.get(edition, folder_map["solo"])
    if app_dir.exists():
        return app_dir
    raise FileNotFoundError(
        f"Installations-Payload nicht gefunden ({name} oder {app_dir})."
    )


def iter_payload_files(payload: Path) -> list[tuple[str, Path]]:
    if payload.is_dir():
        files: list[tuple[str, Path]] = []
        for path in sorted(payload.rglob("*")):
            if path.is_file():
                files.append((path.relative_to(payload).as_posix(), path))
        return files
    with zipfile.ZipFile(payload) as archive:
        return [(name, payload) for name in archive.namelist() if not name.endswith("/")]


def extract_payload(
    payload: Path,
    target: Path,
    *,
    on_file: Callable[[str], None] | None = None,
    on_progress: Callable[[int], None] | None = None,
) -> None:
    target.mkdir(parents=True, exist_ok=True)

    if payload.is_dir():
        files = iter_payload_files(payload)
        total = max(len(files), 1)
        for index, (rel_name, src_path) in enumerate(files, start=1):
            dest = target / rel_name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest)
            if on_file:
                on_file(rel_name)
            if on_progress:
                on_progress(int(index * 100 / total))
        return

    with zipfile.ZipFile(payload) as archive:
        members = [name for name in archive.namelist() if not name.endswith("/")]
        total = max(len(members), 1)
        for index, member in enumerate(members, start=1):
            archive.extract(member, target)
            if on_file:
                on_file(member.replace("/", "\\"))
            if on_progress:
                on_progress(int(index * 100 / total))


def _powershell(command: str) -> None:
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        check=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _desktop_dir() -> Path:
    """Echter Desktop-Ordner (OneDrive-Umleitung, lokalisierte Pfade)."""
    if sys.platform == "win32":
        import ctypes

        buf = ctypes.create_unicode_buffer(260)
        hr = ctypes.windll.shell32.SHGetFolderPathW(None, 0, None, 0, buf)
        if hr == 0:
            path = Path(buf.value)
            if path.exists():
                return path

        import winreg

        for key_name in (
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
        ):
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_name) as key:
                    desktop, _ = winreg.QueryValueEx(key, "Desktop")
                path = Path(os.path.expandvars(str(desktop)))
                if path.exists():
                    return path
            except OSError:
                continue

        onedrive = os.environ.get("OneDrive")
        if onedrive:
            candidate = Path(onedrive) / "Desktop"
            if candidate.exists():
                return candidate

    return Path(os.environ.get("USERPROFILE", "")) / "Desktop"


def _desktop_shortcut_paths(app_name: str) -> list[Path]:
    """Alle bekannten Desktop-Pfade (für Erstellen/Entfernen)."""
    names = {f"{app_name}.lnk"}
    paths: list[Path] = []
    seen: set[Path] = set()

    def add(folder: Path) -> None:
        if not folder:
            return
        for name in names:
            candidate = folder / name
            if candidate not in seen:
                seen.add(candidate)
                paths.append(candidate)

    add(_desktop_dir())
    add(Path(os.environ.get("USERPROFILE", "")) / "Desktop")
    onedrive = os.environ.get("OneDrive")
    if onedrive:
        add(Path(onedrive) / "Desktop")
    return paths


def create_shortcut(
    link_path: Path,
    target: Path,
    *,
    comment: str,
    arguments: str = "",
    working_dir: Path | None = None,
    icon_path: Path | None = None,
) -> None:
    link_path.parent.mkdir(parents=True, exist_ok=True)
    ps_link = str(link_path).replace("'", "''")
    ps_target = str(target).replace("'", "''")
    ps_work = str(working_dir or target.parent).replace("'", "''")
    ps_comment = comment.replace("'", "''")
    ps_args = arguments.replace("'", "''")
    icon_line = ""
    if icon_path is not None and icon_path.exists():
        ps_icon = str(icon_path).replace("'", "''")
        icon_line = f"$s.IconLocation = '{ps_icon},0'; "
    script = (
        f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{ps_link}'); "
        f"$s.TargetPath = '{ps_target}'; "
        f"$s.WorkingDirectory = '{ps_work}'; "
        f"$s.Comment = '{ps_comment}'; "
        f"$s.Arguments = '{ps_args}'; "
        f"{icon_line}"
        f"$s.Save()"
    )
    _powershell(script)


def _start_menu_dir(app_name: str) -> Path:
    return (
        Path(os.environ.get("APPDATA", ""))
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / app_name
    )


def create_start_menu_shortcut(app_name: str, exe_path: Path) -> None:
    create_shortcut(
        _start_menu_dir(app_name) / f"{app_name}.lnk",
        exe_path,
        comment=app_name,
        icon_path=exe_path,
    )


def create_uninstall_shortcut(app_name: str, uninstall_script: Path) -> None:
    powershell = Path(os.environ.get("SystemRoot", r"C:\Windows")) / (
        "System32/WindowsPowerShell/v1.0/powershell.exe"
    )
    create_shortcut(
        _start_menu_dir(app_name) / f"{app_name} deinstallieren.lnk",
        powershell,
        comment=f"{app_name} deinstallieren",
        arguments=(
            f'-NoProfile -ExecutionPolicy Bypass -File "{uninstall_script}"'
        ),
        working_dir=uninstall_script.parent,
    )


def create_desktop_shortcut(app_name: str, exe_path: Path) -> None:
    desktop = _desktop_dir()
    create_shortcut(
        desktop / f"{app_name}.lnk",
        exe_path,
        comment=app_name,
        icon_path=exe_path,
    )


def launch_application(exe_path: Path) -> None:
    os.startfile(str(exe_path))  # noqa: S606


def manifest_path(install_dir: Path) -> Path:
    return install_dir / _MANIFEST_NAME


def edition_app_id(edition: str) -> str:
    return EDITION_APP_IDS.get(edition, EDITION_APP_IDS["solo"])


def write_install_manifest(
    install_dir: Path,
    *,
    app_name: str,
    edition: str,
    version: str,
    build: str,
) -> dict:
    manifest = {
        "app_id": edition_app_id(edition),
        "app_name": app_name,
        "edition": edition,
        "version": version,
        "build": build,
        "publisher": PUBLISHER,
        "install_dir": str(install_dir),
        "exe_name": _EXE_NAME,
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "install_guid": str(uuid.uuid4()),
    }
    manifest_path(install_dir).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return manifest


def read_install_manifest(install_dir: Path) -> dict | None:
    path = manifest_path(install_dir)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_uninstall_script(install_dir: Path, manifest: dict) -> Path:
    script_path = install_dir / _UNINSTALL_SCRIPT
    app_name = manifest["app_name"]
    app_id = manifest["app_id"]
    content = f"""# SC Salvage Tracker — Deinstallation
param([switch]$Quiet)

Add-Type -AssemblyName System.Windows.Forms | Out-Null

$AppName = '{app_name.replace("'", "''")}'
$InstallDir = '{str(install_dir).replace("'", "''")}'
$AppId = '{app_id}'
$LogsDir = Join-Path $env:LOCALAPPDATA 'SC Salvage Tracker\\logs'

if (-not $Quiet) {{
    $answer = [System.Windows.Forms.MessageBox]::Show(
        "Möchtest du $AppName wirklich deinstallieren?",
        "Deinstallation",
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Question
    )
    if ($answer -ne [System.Windows.Forms.DialogResult]::Yes) {{ exit 1 }}
}}

$StartMenuDir = Join-Path $env:APPDATA "Microsoft\\Windows\\Start Menu\\Programs\\$AppName"
$DesktopLink = Join-Path ([Environment]::GetFolderPath('Desktop')) "$AppName.lnk"
$RegistryKey = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\$AppId"

foreach ($path in @($DesktopLink, $StartMenuDir)) {{
    if (Test-Path $path) {{ Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction SilentlyContinue }}
}}

if (Test-Path $LogsDir) {{ Remove-Item -LiteralPath $LogsDir -Recurse -Force -ErrorAction SilentlyContinue }}

if (Test-Path $InstallDir) {{ Remove-Item -LiteralPath $InstallDir -Recurse -Force -ErrorAction SilentlyContinue }}

if (Test-Path $RegistryKey) {{ Remove-Item -LiteralPath $RegistryKey -Recurse -Force -ErrorAction SilentlyContinue }}

if (-not $Quiet) {{
    [System.Windows.Forms.MessageBox]::Show(
        "$AppName wurde deinstalliert.",
        "Deinstallation",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Information
    ) | Out-Null
}}
"""
    script_path.write_text(content, encoding="utf-8")
    return script_path


def register_uninstall(manifest: dict, *, install_dir: Path, exe_path: Path) -> None:
    import winreg

    app_id = manifest["app_id"]
    uninstall_script = install_dir / _UNINSTALL_SCRIPT
    key_path = rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{app_id}"

    uninstall_cmd = (
        f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File '
        f'"{uninstall_script}"'
    )
    quiet_cmd = f"{uninstall_cmd} -Quiet"

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, manifest["app_name"])
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, manifest["version"])
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, manifest["publisher"])
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, uninstall_cmd)
        winreg.SetValueEx(key, "QuietUninstallString", 0, winreg.REG_SZ, quiet_cmd)
        if exe_path.exists():
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(exe_path))
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)


def finalize_installation(
    install_dir: Path,
    *,
    app_name: str,
    edition: str,
    version: str,
    build: str,
    desktop_shortcut: bool,
) -> None:
    exe_path = install_dir / _EXE_NAME
    manifest = write_install_manifest(
        install_dir,
        app_name=app_name,
        edition=edition,
        version=version,
        build=build,
    )
    uninstall_script = write_uninstall_script(install_dir, manifest)
    register_uninstall(manifest, install_dir=install_dir, exe_path=exe_path)
    create_start_menu_shortcut(app_name, exe_path)
    create_uninstall_shortcut(app_name, uninstall_script)
    if desktop_shortcut:
        create_desktop_shortcut(app_name, exe_path)


def remove_shortcuts(app_name: str) -> None:
    for desktop in _desktop_shortcut_paths(app_name):
        if desktop.exists():
            desktop.unlink()
    menu_dir = _start_menu_dir(app_name)
    if menu_dir.exists():
        shutil.rmtree(menu_dir, ignore_errors=True)


def remove_logs_dir() -> None:
    logs_dir = Path(os.environ.get("LOCALAPPDATA", "")) / _LOGS_DIR_NAME / "logs"
    if logs_dir.exists():
        shutil.rmtree(logs_dir, ignore_errors=True)


def unregister_uninstall(app_id: str) -> None:
    import winreg

    key_path = rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{app_id}"
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
    except OSError:
        pass


def uninstall_installation(install_dir: Path, *, quiet: bool = False) -> None:
    manifest = read_install_manifest(install_dir)
    if manifest is None:
        raise FileNotFoundError(
            f"Keine Installationsdaten gefunden unter {install_dir}."
        )

    app_name = manifest["app_name"]
    app_id = manifest["app_id"]

    remove_shortcuts(app_name)
    remove_logs_dir()

    if install_dir.exists():
        shutil.rmtree(install_dir, ignore_errors=True)

    unregister_uninstall(app_id)

    if not quiet:
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.information(
            None,
            "Deinstallation",
            f"{app_name} wurde deinstalliert.",
        )


def _parse_install_dir_arg(argv: list[str]) -> Path | None:
    for index, arg in enumerate(argv):
        if arg == "--install-dir" and index + 1 < len(argv):
            return Path(argv[index + 1])
        if arg.startswith("--install-dir="):
            value = arg.split("=", 1)[1].strip().strip('"')
            if value:
                return Path(value)
    return None


def find_install_dir_from_registry(edition: str) -> Path | None:
    import winreg

    app_id = edition_app_id(edition)
    key_path = rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{app_id}"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            location, _ = winreg.QueryValueEx(key, "InstallLocation")
    except OSError:
        return None
    if not location:
        return None
    path = Path(location)
    return path if path.exists() else None


def resolve_install_dir(argv: list[str], edition: str) -> Path | None:
    explicit = _parse_install_dir_arg(argv)
    if explicit is not None:
        return explicit
    return find_install_dir_from_registry(edition)


def default_install_dir(app_name: str) -> Path:
    return Path.home() / "AppData" / "Local" / "Programs" / app_name


def resolve_target_install_dir(
    edition: str,
    argv: list[str],
    *,
    app_name: str,
) -> Path:
    existing = resolve_install_dir(argv, edition)
    if existing is not None:
        return existing
    return default_install_dir(app_name)


def is_silent_install_argv(argv: list[str]) -> bool:
    for arg in argv:
        token = arg.strip().lower()
        if token in ("/verysilent", "/silent", "/quiet", "--quiet", "-quiet"):
            return True
        normalized = token.lstrip("/-")
        if normalized in ("verysilent", "silent", "quiet", "suppressmsgboxes"):
            return True
    return False


def run_silent_install(
    edition: str,
    argv: list[str] | None = None,
) -> int:
    """Headless Update/Neuinstallation (In-App-Update, /VERYSILENT, --quiet)."""
    import time

    from config.editions import edition_title
    from config.version import APP_BUILD, APP_PRODUCT_NAME, APP_VERSION

    argv = list(argv or [])
    app_name = f"{APP_PRODUCT_NAME} - {edition_title(edition)}"
    target = resolve_target_install_dir(edition, argv, app_name=app_name)

    if is_application_running():
        stop_application()
        for _ in range(20):
            time.sleep(0.25)
            if not is_application_running():
                break
        if is_application_running():
            raise RuntimeError(
                "SC Salvage Tracker läuft noch — Installation abgebrochen."
            )

    payload = resolve_payload_zip(edition)
    extract_payload(payload, target)

    desktop_shortcut = any(
        path.exists() for path in _desktop_shortcut_paths(app_name)
    )
    finalize_installation(
        target,
        app_name=app_name,
        edition=edition,
        version=APP_VERSION,
        build=APP_BUILD,
        desktop_shortcut=desktop_shortcut,
    )
    return 0
