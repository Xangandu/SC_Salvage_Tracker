"""Gemeinsame Setup-UI (Demo + produktiver Installer)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config.editions import EDITION_GLOW_RGB, EDITION_SHORT, EDITION_TITLES, edition_title
from config.version import (
    APP_BUILD,
    APP_CODENAME,
    APP_PRODUCT_NAME,
    APP_VERSION,
)
from installer.install_engine import (
    DATA_MODE_FRESH,
    DATA_MODE_KEEP,
    extract_payload,
    finalize_installation,
    has_existing_user_data,
    launch_application,
    prepare_user_data_for_install,
    resolve_payload_zip,
    user_data_dir,
)

_INSTALLER_DIR = Path(__file__).resolve().parent


def _assets_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "installer" / "assets"
    return _INSTALLER_DIR / "assets"


def _background_path() -> Path:
    """Volle Fläche: install_background.png (920×620), sonst install_bg.png."""
    assets = _assets_dir()
    custom = assets / "install_background.png"
    if custom.exists():
        return custom
    return assets / "install_bg.png"


_BG_PATH = _background_path()
_EXE_NAME = "SC_Salvage_Tracker.exe"

# Bildgröße für eigenes Vollflächen-Hintergrundbild (siehe install_background.png)
BG_IMAGE_W = 920
BG_IMAGE_H = 620

_WIN_W = 920
_BG_H = 580
_TITLE_BAR_H = 40
_TITLE_BEVEL_H = 2
_WIN_H = _BG_H + _TITLE_BAR_H
_CONTENT_LEFT = 44
_CONTENT_TOP = 142
_CONTENT_RIGHT = 340
_CONTENT_BOTTOM = 48
_BUTTON_BAR_H = 56
_FONT_SCALE = 1.21  # 2× +10 % (Titelleiste ausgenommen)


def _fs(px: float) -> int:
    """Installer-Schriftgröße (+10 %); Titelleiste nutzt feste Werte."""
    return round(px * _FONT_SCALE)


def _app_icon_path() -> Path | None:
    project = _ROOT / "assets" / "images" / "app_icon.ico"
    if project.exists():
        return project
    installer = _INSTALLER_DIR / "assets" / "app_icon.ico"
    if installer.exists():
        return installer
    if getattr(sys, "frozen", False):
        bundled = Path(sys._MEIPASS) / "installer" / "assets" / "app_icon.ico"
        if bundled.exists():
            return bundled
    return None


def _edition_app_name(edition: str) -> str:
    key = edition if edition in EDITION_TITLES else "solo"
    return f"{APP_PRODUCT_NAME} - {edition_title(key)}"


def _edition_rgb(edition: str) -> tuple[int, int, int]:
    key = edition if edition in EDITION_GLOW_RGB else "solo"
    return EDITION_GLOW_RGB[key]


class _StepIndicator(QWidget):
    _STEPS = (
        "Willkommen",
        "Zielordner",
        "Optionen",
        "Benutzerdaten",
        "Bereit",
        "Installation",
        "Fertig",
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("installerDemoSteps")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(6)
        self._labels: list[QLabel] = []
        for index, name in enumerate(self._STEPS):
            label = QLabel(f"{index + 1}. {name}")
            label.setObjectName("installerDemoStep")
            layout.addWidget(label)
            self._labels.append(label)
        layout.addStretch(1)
        self.set_current(0)

    def set_current(self, index: int) -> None:
        for i, label in enumerate(self._labels):
            label.setProperty("active", i == index)
            label.setProperty("done", i < index)
            label.style().unpolish(label)
            label.style().polish(label)


class _EditionBadge(QLabel):
    def __init__(self, edition: str, parent=None):
        super().__init__(parent)
        short = EDITION_SHORT.get(edition if edition in EDITION_SHORT else "solo", "SOLO")
        self.setText(short)
        self.setObjectName("installerDemoEditionBadge")
        r, g, b = _edition_rgb(edition)
        self.setStyleSheet(
            f"QLabel#installerDemoEditionBadge {{"
            f" color: rgb({r}, {g}, {b});"
            f" border: 1px solid rgb({r}, {g}, {b});"
            f" background: rgba({r}, {g}, {b}, 28);"
            f"}}"
        )


class _WizardPage(QWidget):
    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("installerDemoPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QVBoxLayout()
        header.setContentsMargins(0, 0, 0, 12)
        header.setSpacing(4)

        self._title = QLabel(title)
        self._title.setObjectName("installerDemoPageTitle")
        header.addWidget(self._title)

        self._subtitle = QLabel(subtitle)
        self._subtitle.setObjectName("installerDemoPageSubtitle")
        self._subtitle.setWordWrap(True)
        self._subtitle.setVisible(bool(subtitle))
        header.addWidget(self._subtitle)

        layout.addLayout(header)
        self.body = QVBoxLayout()
        self.body.setSpacing(10)
        layout.addLayout(self.body, 1)


class _SummaryBlock(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("installerDemoSummary")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(14, 12, 14, 12)
        self._layout.setSpacing(8)

    def set_rows(self, rows: list[tuple[str, str]]) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for label, value in rows:
            row = QHBoxLayout()
            row.setSpacing(12)
            key = QLabel(label)
            key.setObjectName("installerDemoSummaryKey")
            key.setFixedWidth(110)
            val = QLabel(value)
            val.setObjectName("installerDemoSummaryVal")
            val.setWordWrap(True)
            row.addWidget(key)
            row.addWidget(val, 1)
            wrap = QWidget()
            wrap.setLayout(row)
            self._layout.addWidget(wrap)


class _InstallerTitleBar(QWidget):
    """Eigene Titelleiste im Installer-Design (ersetzt Windows-Chrome)."""

    def __init__(self, window: QDialog, title: str, parent=None):
        super().__init__(parent)
        self._window = window
        self._drag_start: object | None = None
        self.setObjectName("installerDemoTitleBar")
        self.setFixedHeight(_TITLE_BAR_H)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        bevel = QFrame()
        bevel.setObjectName("installerDemoTitleBevel")
        bevel.setFixedHeight(_TITLE_BEVEL_H)
        bevel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        outer.addWidget(bevel)

        row_host = QWidget()
        row_host.setObjectName("installerDemoTitleRow")
        row_host.setFixedHeight(_TITLE_BAR_H - _TITLE_BEVEL_H)
        row_host.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        row = QHBoxLayout(row_host)
        row.setContentsMargins(14, 0, 0, 0)
        row.setSpacing(10)

        marker = QLabel("◆")
        marker.setObjectName("installerDemoTitleMarker")
        row.addWidget(marker, 0, Qt.AlignmentFlag.AlignVCenter)

        self._title_label = QLabel(title.upper())
        self._title_label.setObjectName("installerDemoTitleLabel")
        self._title_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        row.addWidget(self._title_label, 1, Qt.AlignmentFlag.AlignVCenter)

        self._close_btn = QPushButton("✕")
        self._close_btn.setObjectName("installerDemoTitleClose")
        self._close_btn.setFixedSize(40, 32)
        self._close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.clicked.connect(window.reject)
        row.addWidget(self._close_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        outer.addWidget(row_host)

        for widget in (self, bevel, row_host, marker, self._title_label):
            widget.installEventFilter(self)

    def set_close_enabled(self, enabled: bool) -> None:
        self._close_btn.setEnabled(enabled)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self._begin_window_drag(event)
                return True
        return super().eventFilter(obj, event)

    def _begin_window_drag(self, event) -> None:
        if sys.platform == "win32":
            handle = self._window.windowHandle()
            if handle is not None:
                handle.startSystemMove()
                event.accept()
                return

        if hasattr(event, "globalPosition"):
            global_pos = event.globalPosition().toPoint()
        else:
            global_pos = event.globalPos()
        self._drag_start = global_pos - self._window.frameGeometry().topLeft()
        event.accept()

    def mouseMoveEvent(self, event):
        if (
            event.buttons() & Qt.MouseButton.LeftButton
            and self._drag_start is not None
        ):
            if hasattr(event, "globalPosition"):
                global_pos = event.globalPosition().toPoint()
            else:
                global_pos = event.globalPos()
            self._window.move(global_pos - self._drag_start)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_start = None
        super().mouseReleaseEvent(event)


class InstallerWizardDialog(QDialog):
    _PAGE_WELCOME = 0
    _PAGE_DIR = 1
    _PAGE_TASKS = 2
    _PAGE_DATA = 3
    _PAGE_READY = 4
    _PAGE_INSTALL = 5
    _PAGE_FINISHED = 6

    def __init__(self, edition: str = "solo", *, demo_mode: bool = False):
        super().__init__()
        self._edition = edition
        self._demo_mode = demo_mode
        self._app_name = _edition_app_name(edition)
        self._page_index = 0
        self._install_target: Path | None = None
        self._has_existing_data = (
            not demo_mode and has_existing_user_data()
        )
        self._backup_path: Path | None = None

        title_prefix = "Setup-Demo" if demo_mode else "Setup"
        window_title = f"{title_prefix} — {self._app_name}"
        self.setWindowTitle(window_title)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setFixedSize(_WIN_W, _WIN_H)
        self.setObjectName("installerDemoRoot")

        bg = QLabel(self)
        bg.setObjectName("installerDemoBg")
        bg.setGeometry(0, 0, _WIN_W, _WIN_H)
        bg.setScaledContents(True)
        if _BG_PATH.exists():
            bg.setPixmap(QPixmap(str(_BG_PATH)))
        bg.lower()

        self._title_bar = _InstallerTitleBar(self, window_title)
        self._title_bar.setGeometry(0, 0, _WIN_W, _TITLE_BAR_H)
        self._title_bar.raise_()

        overlay = QWidget(self)
        overlay.setObjectName("installerDemoOverlay")
        overlay.setGeometry(0, _TITLE_BAR_H, _WIN_W, _BG_H)
        overlay.raise_()

        content_w = _WIN_W - _CONTENT_LEFT - _CONTENT_RIGHT
        content_h = _BG_H - _CONTENT_TOP - _BUTTON_BAR_H - _CONTENT_BOTTOM

        content_host = QFrame(overlay)
        content_host.setObjectName("installerDemoContentPanel")
        content_host.setGeometry(_CONTENT_LEFT, _CONTENT_TOP, content_w, content_h)
        content_host.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        content_layout = QVBoxLayout(content_host)
        content_layout.setContentsMargins(16, 14, 16, 14)
        content_layout.setSpacing(0)

        self._steps = _StepIndicator()
        content_layout.addWidget(self._steps)

        self._stack = QStackedWidget()
        self._stack.setObjectName("installerDemoStack")
        content_layout.addWidget(self._stack, 1)

        bar = QFrame(overlay)
        bar.setObjectName("installerDemoButtonBar")
        bar.setGeometry(0, _BG_H - _BUTTON_BAR_H, _WIN_W, _BUTTON_BAR_H)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(24, 10, 24, 10)

        footer_text = (
            f"{APP_CODENAME} · Build {APP_BUILD} · Demo (keine Dateien werden kopiert)"
            if demo_mode
            else f"{APP_CODENAME} · Build {APP_BUILD} · SC Salvage Tracker Setup"
        )
        footer = QLabel(footer_text)
        footer.setObjectName("installerDemoFooter")
        bar_layout.addWidget(footer, 1)

        self._back_btn = QPushButton("◂ ZURÜCK")
        self._back_btn.setObjectName("installerDemoBtnBack")
        self._back_btn.clicked.connect(self._go_back)
        bar_layout.addWidget(self._back_btn)

        self._next_btn = QPushButton("WEITER ▸")
        self._next_btn.setObjectName("installerDemoBtnNext")
        self._next_btn.clicked.connect(self._go_next)
        bar_layout.addWidget(self._next_btn)

        self._cancel_btn = QPushButton("ABBRECHEN")
        self._cancel_btn.setObjectName("installerDemoBtnCancel")
        self._cancel_btn.clicked.connect(self.reject)
        bar_layout.addWidget(self._cancel_btn)

        self._build_pages()
        self._sync_buttons()

    def _build_pages(self):
        welcome = _WizardPage(
            "Willkommen",
            "Der Assistent führt dich durch die Installation.",
        )
        intro = QLabel(
            "Dieser Assistent richtet den Salvage Tracker auf deinem PC ein, "
            "Sitzungen, Raffinerie, Verkäufe, Lager und Crew-Auszahlung."
        )
        intro.setObjectName("installerDemoBody")
        intro.setWordWrap(True)
        welcome.body.addWidget(intro)

        edition_row = QHBoxLayout()
        edition_row.setSpacing(10)
        edition_caption = QLabel("Edition:")
        edition_caption.setObjectName("installerDemoSummaryKey")
        edition_row.addWidget(edition_caption)
        edition_row.addWidget(_EditionBadge(self._edition))
        edition_name = QLabel(self._app_name.split(" - ", 1)[-1])
        edition_name.setObjectName("installerDemoBody")
        edition_row.addWidget(edition_name)
        edition_row.addStretch(1)
        edition_wrap = QWidget()
        edition_wrap.setLayout(edition_row)
        welcome.body.addWidget(edition_wrap)
        welcome.body.addStretch(1)
        self._stack.addWidget(welcome)

        dir_page = _WizardPage(
            "Installationsordner",
            "Wähle, wohin der Salvage Tracker installiert werden soll.",
        )
        dir_hint = QLabel(
            "Der Salvage Tracker wird in folgenden Ordner installiert:"
        )
        dir_hint.setObjectName("installerDemoBody")
        dir_hint.setWordWrap(True)
        dir_page.body.addWidget(dir_hint)

        dir_row = QHBoxLayout()
        default_dir = Path.home() / "AppData" / "Local" / "Programs" / self._app_name
        self._dir_edit = QLineEdit(str(default_dir))
        self._dir_edit.setObjectName("installerDemoDirEdit")
        browse = QPushButton("DURCHSUCHEN …")
        browse.setObjectName("installerDemoBrowse")
        browse.clicked.connect(self._browse_dir)
        dir_row.addWidget(self._dir_edit, 1)
        dir_row.addWidget(browse)
        dir_page.body.addLayout(dir_row)

        space = QLabel("Mindestens 120 MB freier Speicherplatz erforderlich.")
        space.setObjectName("installerDemoMuted")
        dir_page.body.addWidget(space)
        dir_page.body.addStretch(1)
        self._stack.addWidget(dir_page)

        tasks = _WizardPage(
            "Zusätzliche Optionen",
            "Verknüpfungen und Startverhalten nach der Installation.",
        )
        self._desktop_cb = QCheckBox("Desktop-Verknüpfung erstellen")
        self._desktop_cb.setObjectName("installerDemoCheck")
        self._launch_cb = QCheckBox(
            "SC Salvage Tracker nach der Installation starten"
        )
        self._launch_cb.setObjectName("installerDemoCheck")
        self._launch_cb.setChecked(True)
        tasks.body.addWidget(self._desktop_cb)
        tasks.body.addWidget(self._launch_cb)
        tasks.body.addStretch(1)
        self._stack.addWidget(tasks)

        data = _WizardPage(
            "Benutzerdaten",
            "Es wurden bestehende Salvage-Tracker-Daten auf diesem PC gefunden.",
        )
        data_info = QLabel(
            f"Speicherort: {user_data_dir()}\n\n"
            "Bei einer Neuinstallation kannst du die vorhandenen Benutzer, "
            "Sessions und Lagerbestände behalten oder mit Backup neu beginnen."
        )
        data_info.setObjectName("installerDemoBody")
        data_info.setWordWrap(True)
        data.body.addWidget(data_info)

        self._data_keep_radio = QRadioButton(
            "Bestehende Daten behalten (empfohlen bei Update/Neuinstallation)"
        )
        self._data_keep_radio.setObjectName("installerDemoRadio")
        self._data_keep_radio.setChecked(True)
        self._data_fresh_radio = QRadioButton(
            "Neu beginnen — Backup erstellen und Benutzerdaten löschen"
        )
        self._data_fresh_radio.setObjectName("installerDemoRadio")
        data.body.addWidget(self._data_keep_radio)
        data.body.addWidget(self._data_fresh_radio)

        data_warn = QLabel(
            "Beim Neu beginnen werden Benutzer, Sessions und Lager zurückgesetzt. "
            "Ein Backup wird unter data\\backups gespeichert."
        )
        data_warn.setObjectName("installerDemoMuted")
        data_warn.setWordWrap(True)
        data.body.addWidget(data_warn)
        data.body.addStretch(1)
        self._stack.addWidget(data)

        ready = _WizardPage(
            "Bereit zur Installation",
            "Prüfe die Einstellungen und starte die Installation.",
        )
        self._summary = _SummaryBlock()
        ready.body.addWidget(self._summary)
        ready.body.addStretch(1)
        self._stack.addWidget(ready)

        install = _WizardPage(
            "Installation läuft",
            "Dateien werden entpackt, bitte warten …",
        )
        self._progress = QProgressBar()
        self._progress.setObjectName("installerDemoProgress")
        self._progress.setRange(0, 100)
        self._status = QLabel("Starte Installation …")
        self._status.setObjectName("installerDemoMuted")
        self._file_label = QLabel("")
        self._file_label.setObjectName("installerDemoFile")
        install.body.addWidget(self._progress)
        install.body.addWidget(self._status)
        install.body.addWidget(self._file_label)
        install.body.addStretch(1)
        self._stack.addWidget(install)

        done = _WizardPage(
            "Installation abgeschlossen",
            "Der Salvage Tracker ist bereit.",
        )
        finish_text = (
            "Die Installation wurde erfolgreich abgeschlossen (Demo).\n\n"
            "Starte die Anwendung über das Startmenü."
            if self._demo_mode
            else
            "Die Installation wurde erfolgreich abgeschlossen.\n\n"
            "Starte die Anwendung über das Startmenü"
            + (
                " oder die Desktop-Verknüpfung."
                if self._desktop_cb.isChecked()
                else "."
            )
            + "\n\nDeinstallation: Windows „Apps & Features“ oder "
            "Startmenü → „deinstallieren“."
        )
        self._finish_label = QLabel(finish_text)
        self._finish_label.setObjectName("installerDemoBody")
        self._finish_label.setWordWrap(True)
        done.body.addWidget(self._finish_label)
        done.body.addStretch(1)
        self._stack.addWidget(done)

    def _browse_dir(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Installationsordner wählen",
            self._dir_edit.text(),
        )
        if path:
            self._dir_edit.setText(path)

    def _data_mode(self) -> str:
        if self._data_fresh_radio.isChecked():
            return DATA_MODE_FRESH
        return DATA_MODE_KEEP

    def _step_index_for_page(self, page: int) -> int:
        if not self._has_existing_data and page > self._PAGE_DATA:
            return page - 1
        return page

    def _next_page_after(self, page: int) -> int:
        next_page = page + 1
        if next_page == self._PAGE_DATA and not self._has_existing_data:
            next_page += 1
        return next_page

    def _prev_page_before(self, page: int) -> int:
        prev_page = page - 1
        if prev_page == self._PAGE_DATA and not self._has_existing_data:
            prev_page -= 1
        return prev_page

    def _update_summary(self):
        tasks: list[str] = []
        if self._desktop_cb.isChecked():
            tasks.append("Desktop-Verknüpfung")
        if self._launch_cb.isChecked():
            tasks.append("App nach Installation starten")
        if not tasks:
            tasks.append("Keine Zusatzoptionen")

        rows = [
            ("Zielordner", self._dir_edit.text()),
            ("Edition", self._app_name),
            ("Version", f"{APP_VERSION} · Build {APP_BUILD}"),
            ("Optionen", ", ".join(tasks)),
        ]
        if self._has_existing_data:
            if self._data_mode() == DATA_MODE_FRESH:
                rows.append(("Benutzerdaten", "Backup + Neu beginnen"))
            else:
                rows.append(("Benutzerdaten", "Bestehende Daten behalten"))
        self._summary.set_rows(rows)

    def _go_back(self):
        if self._page_index <= self._PAGE_WELCOME:
            return
        if self._page_index == self._PAGE_FINISHED:
            return
        self._page_index = self._prev_page_before(self._page_index)
        self._stack.setCurrentIndex(self._page_index)
        self._sync_buttons()

    def _go_next(self):
        if self._page_index == self._PAGE_READY:
            if (
                self._has_existing_data
                and self._data_mode() == DATA_MODE_FRESH
                and not self._demo_mode
            ):
                answer = QMessageBox.warning(
                    self,
                    "Benutzerdaten zurücksetzen",
                    "Es wird ein Backup erstellt und alle Benutzerdaten gelöscht.\n"
                    "Fortfahren?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if answer != QMessageBox.StandardButton.Yes:
                    return

            self._page_index = self._PAGE_INSTALL
            self._stack.setCurrentIndex(self._page_index)
            self._sync_buttons()
            if self._demo_mode:
                self._simulate_install()
            else:
                self._run_install()
            return

        if self._page_index == self._PAGE_INSTALL:
            return

        if self._page_index == self._PAGE_FINISHED:
            self.accept()
            return

        self._page_index = self._next_page_after(self._page_index)
        if self._page_index == self._PAGE_READY:
            self._update_summary()
        self._stack.setCurrentIndex(self._page_index)
        self._sync_buttons()

    def _simulate_install(self):
        self._progress.setValue(0)
        tick = {"value": 0}
        demo_files = (
            "SC_Salvage_Tracker.exe",
            "assets\\themes\\star_citizen.qss",
            "config\\build_edition.txt",
            "data\\salvage.db",
        )

        def step():
            tick["value"] += 4
            value = tick["value"]
            self._progress.setValue(min(value, 100))
            file_index = min(len(demo_files) - 1, value // 25)
            self._file_label.setText(demo_files[file_index])
            if value < 40:
                self._status.setText("Entpacke Anwendungsdateien …")
            elif value < 75:
                self._status.setText("Registriere Verknüpfungen …")
            elif value < 100:
                self._status.setText("Finalisiere Installation …")
            else:
                timer.stop()
                self._file_label.setText("")
                self._page_index = self._PAGE_FINISHED
                self._stack.setCurrentIndex(self._page_index)
                self._sync_buttons()

        timer = QTimer(self)
        timer.timeout.connect(step)
        timer.start(45)

    def _run_install(self):
        target = Path(self._dir_edit.text().strip())
        self._progress.setValue(0)
        self._status.setText("Starte Installation …")
        self._file_label.setText("")

        try:
            payload = resolve_payload_zip(self._edition)
        except FileNotFoundError as exc:
            QMessageBox.critical(self, "Setup", str(exc))
            self._page_index = self._PAGE_READY
            self._stack.setCurrentIndex(self._page_index)
            self._sync_buttons()
            return

        state = {"progress": 0}

        def on_file(name: str) -> None:
            self._file_label.setText(name)

        def on_progress(value: int) -> None:
            state["progress"] = min(value, 90)
            self._progress.setValue(state["progress"])
            self._status.setText("Entpacke Anwendungsdateien …")

        try:
            if self._has_existing_data and self._data_mode() == DATA_MODE_FRESH:
                self._status.setText("Sichere Benutzerdaten …")
                self._progress.setValue(5)
                self._backup_path = prepare_user_data_for_install(reset=True)
                if self._backup_path is not None:
                    self._file_label.setText(self._backup_path.name)

            extract_payload(
                payload,
                target,
                on_file=on_file,
                on_progress=on_progress,
            )
            self._install_target = target
            exe_path = target / _EXE_NAME

            self._status.setText("Registriere Verknüpfungen …")
            self._progress.setValue(92)
            finalize_installation(
                target,
                app_name=self._app_name,
                edition=self._edition,
                version=APP_VERSION,
                build=APP_BUILD,
                desktop_shortcut=self._desktop_cb.isChecked(),
            )

            self._status.setText("Finalisiere Installation …")
            self._progress.setValue(98)

            if self._launch_cb.isChecked() and exe_path.exists():
                launch_application(exe_path)

            self._progress.setValue(100)
            self._file_label.setText("")
            if self._backup_path is not None:
                self._finish_label.setText(
                    "Die Installation wurde erfolgreich abgeschlossen.\n\n"
                    f"Backup der alten Datenbank: {self._backup_path.name}\n"
                    f"Speicherort: {self._backup_path.parent}\n\n"
                    "Starte die Anwendung über das Startmenü"
                    + (
                        " oder die Desktop-Verknüpfung."
                        if self._desktop_cb.isChecked()
                        else "."
                    )
                    + "\n\nDeinstallation: Windows „Apps & Features“ oder "
                    "Startmenü → „deinstallieren“."
                )
            self._page_index = self._PAGE_FINISHED
            self._stack.setCurrentIndex(self._page_index)
            self._sync_buttons()
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Setup",
                f"Installation fehlgeschlagen:\n{exc}",
            )
            self._page_index = self._PAGE_READY
            self._stack.setCurrentIndex(self._page_index)
            self._sync_buttons()

    def _sync_buttons(self):
        self._steps.set_current(self._step_index_for_page(self._page_index))
        self._back_btn.setEnabled(
            self._PAGE_WELCOME < self._page_index < self._PAGE_FINISHED
        )

        if self._page_index == self._PAGE_READY:
            self._next_btn.setText("INSTALLIEREN ▸")
        elif self._page_index == self._PAGE_FINISHED:
            self._next_btn.setText("FERTIGSTELLEN")
            self._next_btn.setEnabled(True)
        elif self._page_index == self._PAGE_INSTALL:
            self._next_btn.setText("INSTALLIEREN ▸")
            self._next_btn.setEnabled(False)
        else:
            self._next_btn.setText("WEITER ▸")
            self._next_btn.setEnabled(True)

        self._cancel_btn.setEnabled(self._page_index != self._PAGE_INSTALL)
        self._title_bar.set_close_enabled(self._page_index != self._PAGE_INSTALL)


WIZARD_QSS = f"""
QDialog#installerDemoRoot {{ background: #0A0D12; }}
QWidget#installerDemoTitleBar {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 rgba(22, 28, 38, 215),
        stop: 1 rgba(14, 19, 26, 235)
    );
    border-bottom: 1px solid rgba(36, 48, 64, 200);
}}
QFrame#installerDemoTitleBevel {{
    background: #E07A2A;
    border: none;
}}
QWidget#installerDemoTitleRow {{ background: transparent; }}
QLabel#installerDemoTitleMarker {{
    color: #E07A2A;
    font-family: "Segoe UI";
    font-size: 10px;
}}
QLabel#installerDemoTitleLabel {{
    color: #F4F8FC;
    font-family: "Segoe UI";
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
}}
QPushButton#installerDemoTitleClose {{
    background: transparent;
    border: none;
    border-radius: 0;
    color: #93A8BC;
    font-family: "Segoe UI";
    font-size: 12px;
    font-weight: bold;
    padding: 0;
    margin: 0;
}}
QPushButton#installerDemoTitleClose:hover {{
    background: #C42B1C;
    color: #FFFFFF;
}}
QPushButton#installerDemoTitleClose:pressed {{
    background: #9A2218;
    color: #FFFFFF;
}}
QPushButton#installerDemoTitleClose:disabled {{
    background: transparent;
    color: #3D4F63;
}}
QLabel#installerDemoBg {{ background: #0A0D12; }}
QWidget#installerDemoOverlay {{ background: transparent; }}
QWidget#installerDemoPage {{ background: transparent; }}
QFrame#installerDemoContentPanel {{
    background: rgba(10, 13, 18, 0.68);
    border: 1px solid rgba(38, 53, 69, 0.9);
    border-left: 3px solid #E07A2A;
    border-radius: 4px;
}}
QLabel#installerDemoStep {{
    color: #5C7080; font-family: "Segoe UI"; font-size: {_fs(9)}px; padding: 2px 0;
}}
QLabel#installerDemoStep[active="true"] {{ color: #E07A2A; font-weight: bold; }}
QLabel#installerDemoStep[done="true"] {{ color: #93A8BC; }}
QLabel#installerDemoPageTitle {{
    color: #E07A2A; font-family: "Segoe UI"; font-size: {_fs(16)}px; font-weight: bold;
}}
QLabel#installerDemoPageSubtitle, QLabel#installerDemoMuted {{
    color: #93A8BC; font-family: "Segoe UI"; font-size: {_fs(10)}px;
}}
QLabel#installerDemoBody {{
    color: #F2F7FB; font-family: "Segoe UI"; font-size: {_fs(11)}px;
}}
QLabel#installerDemoFile {{
    color: #708696; font-family: "Consolas"; font-size: {_fs(9)}px;
}}
QLabel#installerDemoEditionBadge {{
    font-family: "Segoe UI"; font-size: {_fs(10)}px; font-weight: bold;
    padding: 2px 8px; border-radius: 3px;
}}
QFrame#installerDemoSummary {{
    background: rgba(10, 13, 18, 0.55);
    border: 1px solid #263545; border-radius: 4px;
}}
QLabel#installerDemoSummaryKey {{
    color: #93A8BC; font-family: "Segoe UI"; font-size: {_fs(10)}px;
}}
QLabel#installerDemoSummaryVal {{
    color: #F2F7FB; font-family: "Segoe UI"; font-size: {_fs(10)}px;
}}
QLabel#installerDemoFooter {{
    color: #708696; font-family: "Segoe UI"; font-size: {_fs(9)}px;
}}
QLineEdit#installerDemoDirEdit {{
    background: #30241A; color: #F5EEE6; border: 1px solid #3D4F63;
    border-radius: 4px; padding: 8px 10px; font-family: "Segoe UI"; font-size: {_fs(10)}px;
}}
QCheckBox#installerDemoCheck {{
    color: #F2F7FB; font-family: "Segoe UI"; font-size: {_fs(11)}px;
    spacing: 8px; padding: 4px 0;
}}
QCheckBox#installerDemoCheck::indicator {{
    width: 16px; height: 16px; border: 1px solid #3D4F63;
    border-radius: 3px; background: #1A2330;
}}
QCheckBox#installerDemoCheck::indicator:checked {{
    background: #E07A2A; border-color: #E07A2A;
}}
QRadioButton#installerDemoRadio {{
    color: #F2F7FB; font-family: "Segoe UI"; font-size: {_fs(11)}px;
    spacing: 8px; padding: 4px 0;
}}
QRadioButton#installerDemoRadio::indicator {{
    width: 16px; height: 16px; border: 1px solid #3D4F63;
    border-radius: 8px; background: #1A2330;
}}
QRadioButton#installerDemoRadio::indicator:checked {{
    background: #E07A2A; border-color: #E07A2A;
}}
QProgressBar#installerDemoProgress {{
    background: #1A2330; border: 1px solid #263545; border-radius: 4px;
    min-height: 14px; max-height: 14px; text-align: center; color: #F2F7FB;
}}
QProgressBar#installerDemoProgress::chunk {{
    background: #E07A2A; border-radius: 3px;
}}
QPushButton#installerDemoBtnBack,
QPushButton#installerDemoBtnNext,
QPushButton#installerDemoBtnCancel,
QPushButton#installerDemoBrowse {{
    background: #1E2A38; color: #F2F7FB; border: 1px solid #3D4F63;
    border-radius: 4px; padding: 8px 16px; font-family: "Segoe UI";
    font-size: {_fs(10)}px; font-weight: bold; min-width: 120px;
}}
QPushButton#installerDemoBtnNext {{
    background: #E07A2A; border-color: #E07A2A; color: #0A0D12;
}}
QPushButton#installerDemoBrowse {{ min-width: 130px; }}
QPushButton#installerDemoBtnNext:disabled {{
    background: #3D4F63; border-color: #3D4F63; color: #708696;
}}
QPushButton:hover:enabled {{ border-color: #E07A2A; }}
QFrame#installerDemoButtonBar {{
    background: rgba(10, 13, 18, 0.92); border-top: 1px solid #263545;
}}
"""


def run_wizard(
    *,
    demo_mode: bool,
    edition: str = "solo",
    argv: list[str] | None = None,
) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description=(
            "Interaktive Demo des SC Salvage Tracker Setup-Assistenten."
            if demo_mode
            else "SC Salvage Tracker Setup-Assistent."
        ),
    )
    parser.add_argument(
        "--edition",
        choices=("solo", "crew", "orga"),
        default=edition,
        help="Edition (Standard: solo)",
    )
    args = parser.parse_args(argv)

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", _fs(10)))
    app.setStyleSheet(WIZARD_QSS)

    icon_path = _app_icon_path()
    if icon_path is not None:
        app_icon = QIcon(str(icon_path))
        app.setWindowIcon(app_icon)

    dialog = InstallerWizardDialog(edition=args.edition, demo_mode=demo_mode)
    if icon_path is not None:
        dialog.setWindowIcon(app_icon)
    result = dialog.exec()
    app.quit()
    return 0 if result == QDialog.DialogCode.Accepted else 1
