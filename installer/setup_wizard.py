"""Produktiver SC Salvage Tracker Setup-Assistent (PySide6, Demo-UI)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from PySide6.QtWidgets import QApplication, QMessageBox

from config.editions import EDITION_TITLES, edition_title
from config.version import APP_PRODUCT_NAME
from installer.install_engine import (
    is_silent_install_argv,
    resolve_install_dir,
    run_silent_install,
    uninstall_installation,
)
from installer.wizard_app import run_wizard


def _edition_app_name(edition: str) -> str:
    key = edition if edition in EDITION_TITLES else "solo"
    return f"{APP_PRODUCT_NAME} - {edition_title(key)}"


def _parse_edition(argv: list[str]) -> str:
    for index, arg in enumerate(argv):
        if arg == "--edition" and index + 1 < len(argv):
            return argv[index + 1]
    return "solo"


def _run_uninstall(argv: list[str]) -> int:
    edition = _parse_edition(argv)
    quiet = "--quiet" in argv
    install_dir = resolve_install_dir(argv, edition)

    if install_dir is None:
        if not quiet:
            QApplication(sys.argv)
            QMessageBox.warning(
                None,
                "Deinstallation",
                f"Keine Installation von {_edition_app_name(edition)} gefunden.",
            )
        return 1

    if not quiet:
        QApplication(sys.argv)
        answer = QMessageBox.question(
            None,
            "Deinstallation",
            f"Möchtest du {_edition_app_name(edition)} wirklich deinstallieren?\n\n"
            f"Ordner: {install_dir}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return 1

    try:
        uninstall_installation(install_dir, quiet=quiet)
    except Exception as exc:
        if not quiet:
            QMessageBox.critical(
                None,
                "Deinstallation",
                f"Deinstallation fehlgeschlagen:\n{exc}",
            )
        return 1

    return 0


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if "--uninstall" in argv:
        return _run_uninstall(argv)

    if is_silent_install_argv(argv):
        edition = _parse_edition(argv)
        try:
            return run_silent_install(edition, argv)
        except Exception as exc:
            print(f"Stille Installation fehlgeschlagen: {exc}", file=sys.stderr)
            return 1

    edition = _parse_edition(argv)
    return run_wizard(demo_mode=False, edition=edition, argv=argv)


if __name__ == "__main__":
    raise SystemExit(main())
