"""Dialoge für verfügbare Updates und Download-Fortschritt."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config.update import UpdateManifest
from config.version import format_version_subtitle
from ui.mobiglas_window_frame import (
    MobiglasFramelessMixin,
    apply_mobiglas_window_frame,
)
from ui.page_layout import (
    configure_aaa_tabs,
    hud_divider,
    page_title,
    primary_button,
)


class UpdateDialogResult:
    INSTALL = 1
    LATER = 2
    SKIP = 3


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024 * 1024:
        return f"{max(size_bytes // 1024, 1)} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def _notes_tab(manifest: UpdateManifest, language: str) -> QWidget:
    tab = QWidget()
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(0, 8, 0, 0)
    layout.setSpacing(8)

    notes = manifest.notes(language)
    if not notes:
        empty = QLabel("Keine Release Notes verfügbar.")
        empty.setObjectName("mutedLabel")
        layout.addWidget(empty)
        return tab

    title = QLabel(notes.title)
    title.setObjectName("formLabel")
    title.setWordWrap(True)
    layout.addWidget(title)

    summary = QLabel(notes.summary)
    summary.setObjectName("mutedLabel")
    summary.setWordWrap(True)
    layout.addWidget(summary)

    if notes.highlights:
        highlights = QTextEdit()
        highlights.setObjectName("changelogView")
        highlights.setReadOnly(True)
        highlights.setMinimumHeight(160)
        lines = "\n".join(
            f"• {item}" for item in notes.highlights
        )
        highlights.setPlainText(lines)
        layout.addWidget(highlights)

    layout.addStretch()
    return tab


class UpdateAvailableDialog(MobiglasFramelessMixin, QDialog):

    def __init__(
        self,
        manifest: UpdateManifest,
        parent=None,
    ):
        super().__init__(parent)

        self.manifest = manifest
        self.result_action = UpdateDialogResult.LATER

        self.setObjectName("mobiglasDialog")
        self.setWindowTitle("Update verfügbar")
        self.resize(760, 560)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(page_title("UPDATE VERFÜGBAR"))

        version_line = QLabel(
            f"{manifest.version_display} · Build {manifest.build} · "
            f"{manifest.codename}"
        )
        version_line.setObjectName("mutedLabel")
        layout.addWidget(version_line)

        local_line = QLabel(
            f"Aktuell installiert: {format_version_subtitle()}"
        )
        local_line.setObjectName("mutedLabel")
        layout.addWidget(local_line)

        size_line = QLabel(
            f"Download: {manifest.download.filename} "
            f"({_format_size(manifest.download.size_bytes)})"
        )
        size_line.setObjectName("mutedLabel")
        layout.addWidget(size_line)
        layout.addLayout(hud_divider())

        tabs = QTabWidget()
        tabs.setObjectName("changelogTabs")
        configure_aaa_tabs(tabs)
        tabs.addTab(_notes_tab(manifest, "de"), "Deutsch")
        tabs.addTab(_notes_tab(manifest, "en"), "English")
        layout.addWidget(tabs, 1)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)

        self.install_button = primary_button("Jetzt installieren")
        self.install_button.clicked.connect(self._choose_install)
        button_row.addWidget(self.install_button)

        if not manifest.mandatory:
            later_button = QPushButton("Später")
            later_button.setObjectName("secondaryAction")
            later_button.clicked.connect(self._choose_later)
            button_row.addWidget(later_button)

            skip_button = QPushButton("Diese Version überspringen")
            skip_button.setObjectName("secondaryAction")
            skip_button.clicked.connect(self._choose_skip)
            button_row.addWidget(skip_button)

        button_row.addStretch()
        layout.addLayout(button_row)

        self.setLayout(layout)
        apply_mobiglas_window_frame(
            self,
            title="Update verfügbar",
            dialog=True,
        )

    def _choose_install(self):
        self.result_action = UpdateDialogResult.INSTALL
        self.accept()

    def _choose_later(self):
        self.result_action = UpdateDialogResult.LATER
        self.reject()

    def _choose_skip(self):
        self.result_action = UpdateDialogResult.SKIP
        self.reject()


class UpdateDownloadDialog(MobiglasFramelessMixin, QDialog):

    def __init__(self, manifest: UpdateManifest, parent=None):
        super().__init__(parent)

        self.setObjectName("mobiglasDialog")
        self.setWindowTitle("Update wird heruntergeladen")
        self.setModal(True)
        self.resize(520, 180)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        layout.addWidget(page_title("DOWNLOAD"))

        self.status_label = QLabel(
            f"{manifest.download.filename} wird geladen …"
        )
        self.status_label.setObjectName("mutedLabel")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("updateProgressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)
        apply_mobiglas_window_frame(
            self,
            title="Download",
            dialog=True,
        )

    def set_progress(self, received: int, total: int):
        if total <= 0:
            self.progress_bar.setRange(0, 0)
            self.status_label.setText(
                f"{received // (1024 * 1024)} MB heruntergeladen …"
            )
            return

        percent = min(100, int(received * 100 / total))
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(percent)
        self.status_label.setText(
            f"{_format_size(received)} / {_format_size(total)} "
            f"({percent} %)"
        )
