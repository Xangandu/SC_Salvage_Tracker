"""Erstellt ein vollständiges ZIP-Backup des gesamten SC_Salvage_Tracker-Projekts."""

from __future__ import annotations

import zipfile
from datetime import datetime
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    backup_dir = root / "Backups"
    backup_dir.mkdir(exist_ok=True)

    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    archive = backup_dir / f"SC_Salvage_Tracker_FullBackup_{stamp}.zip"

    exclude_dirs = {
        "Backups",
        "__pycache__",
        ".git",
        ".cursor",
        ".venv",
        "venv",
        "node_modules",
        "build",
        "dist",
    }

    file_count = 0
    total_bytes = 0

    with zipfile.ZipFile(
        archive,
        "w",
        zipfile.ZIP_DEFLATED,
        compresslevel=6,
    ) as zf:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in exclude_dirs for part in path.parts):
                continue
            try:
                if path.resolve() == archive.resolve():
                    continue
            except OSError:
                continue

            arcname = Path("SC_Salvage_Tracker") / path.relative_to(root)
            zf.write(path, arcname.as_posix())
            file_count += 1
            total_bytes += path.stat().st_size

    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    archive_mb = archive.stat().st_size / (1024 * 1024)
    source_mb = total_bytes / (1024 * 1024)

    manifest = backup_dir / f"SC_Salvage_Tracker_FullBackup_{stamp}.txt"
    manifest.write_text(
        "\n".join([
            "SC Salvage Tracker - Vollständiges Projekt-Backup",
            f"Erstellt: {created}",
            f"Quelle: {root}",
            f"Archiv: {archive.name}",
            f"Dateien: {file_count}",
            f"Unkomprimiert: {source_mb:.1f} MB",
            f"Archivgröße: {archive_mb:.1f} MB",
            f"Ausgeschlossen: {', '.join(sorted(exclude_dirs))}",
            "",
        ]),
        encoding="utf-8",
    )

    print("=" * 60)
    print("BACKUP FERTIG")
    print(f"  Archiv:   {archive}")
    print(f"  Manifest: {manifest}")
    print(f"  Dateien:  {file_count}")
    print(f"  Größe:    {archive_mb:.1f} MB (Quelle: {source_mb:.1f} MB)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
