"""Zwischenablage-Helfer."""

from PySide6.QtWidgets import QApplication, QMessageBox, QWidget


def copy_to_clipboard(
    text: str,
    parent: QWidget | None = None,
    *,
    title: str = "Kopiert",
    message: str = "Text wurde in die Zwischenablage kopiert.",
) -> None:
    QApplication.clipboard().setText(text)
    if parent is not None:
        QMessageBox.information(parent, title, message)
