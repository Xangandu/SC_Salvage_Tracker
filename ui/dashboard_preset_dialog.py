"""Dialog: System-Presets laden und eigene Presets verwalten."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QListWidget,
    QMessageBox,
)

from config.i18n import tr
from ui.page_layout import (
    page_title,
    hud_divider,
    primary_button,
    page_panel,
    subsection_title,
    add_form_field,
)
from ui.dashboard_layouts import DASHBOARD_LAYOUTS
from ui.dashboard_grid_utils import preset_to_grid
from database.dashboard_layout_repository import (
    MAX_CUSTOM_PRESETS,
)
from ui.mobiglas_window_frame import (
    MobiglasFramelessMixin,
    apply_mobiglas_window_frame,
)


def _secondary_button(text):
    button = QPushButton(text)
    button.setObjectName("secondaryAction")
    return button


class DashboardPresetDialog(MobiglasFramelessMixin, QDialog):

    def __init__(
        self,
        parent,
        layout_repo,
        user_id,
        current_layout=None,
    ):
        super().__init__(parent)
        self.layout_repo = layout_repo
        self.user_id = user_id
        self.selected_layout = None

        self.setObjectName("mobiglasDialog")
        self.setWindowTitle(tr("dashboard.preset.window_title"))
        self.setModal(True)
        self.resize(560, 560)
        self.setMinimumSize(480, 480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        layout.addWidget(page_title(tr("dashboard.preset.title")))
        layout.addLayout(hud_divider())

        layout.addWidget(subsection_title(tr("dashboard.preset.section.system")))
        layout.addLayout(hud_divider())

        system_panel, system_layout = page_panel()
        system_layout.setContentsMargins(16, 16, 16, 16)
        system_layout.setSpacing(10)

        self.system_combo = QComboBox()
        for preset_id in DASHBOARD_LAYOUTS:
            self.system_combo.addItem(
                tr(f"dashboard.preset.{preset_id}.label"),
                preset_id,
            )
        add_form_field(
            system_layout,
            tr("dashboard.preset.label.template"),
            self.system_combo,
        )

        load_system = primary_button(
            tr("dashboard.preset.button.load_template")
        )
        load_system.clicked.connect(self._load_system_preset)
        system_layout.addWidget(load_system)
        layout.addWidget(system_panel)

        layout.addWidget(
            subsection_title(tr("dashboard.preset.section.custom"))
        )
        layout.addLayout(hud_divider())

        custom_panel, custom_layout = page_panel()
        custom_layout.setContentsMargins(16, 16, 16, 16)
        custom_layout.setSpacing(10)

        preset_hint = QLabel(
            tr(
                "dashboard.preset.hint.max",
                max=MAX_CUSTOM_PRESETS,
            )
        )
        preset_hint.setObjectName("mutedLabel")
        preset_hint.setWordWrap(True)
        custom_layout.addWidget(preset_hint)

        self.custom_list = QListWidget()
        self.custom_list.setObjectName("dashboardPresetList")
        self.custom_list.setMinimumHeight(160)
        custom_layout.addWidget(self.custom_list)

        self.preset_name_input = QLineEdit()
        self.preset_name_input.setPlaceholderText(
            tr("dashboard.preset.placeholder.name")
        )
        add_form_field(
            custom_layout,
            tr("dashboard.preset.label.name"),
            self.preset_name_input,
        )

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        save_btn = primary_button(
            tr("dashboard.preset.button.save_current")
        )
        save_btn.clicked.connect(self._save_current_preset)
        load_btn = _secondary_button(
            tr("dashboard.preset.button.load_selected")
        )
        load_btn.clicked.connect(self._load_selected_custom)
        delete_btn = _secondary_button(
            tr("dashboard.preset.button.delete")
        )
        delete_btn.clicked.connect(self._delete_selected_custom)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(load_btn)
        btn_row.addWidget(delete_btn)
        custom_layout.addLayout(btn_row)
        layout.addWidget(custom_panel, 1)

        close_row = QHBoxLayout()
        close_row.addStretch()
        close_btn = _secondary_button(tr("dashboard.preset.button.close"))
        close_btn.clicked.connect(self.reject)
        close_row.addWidget(close_btn)
        layout.addLayout(close_row)

        self._current_layout = current_layout
        self._refresh_custom_list()

        apply_mobiglas_window_frame(
            self,
            title=tr("dashboard.preset.window_title"),
            dialog=True,
        )

    def _refresh_custom_list(self):
        self.custom_list.clear()
        for _id, name, updated in (
            self.layout_repo.list_custom_presets(self.user_id)
        ):
            self.custom_list.addItem(name)

    def _load_system_preset(self):
        preset_id = self.system_combo.currentData()
        self.selected_layout = preset_to_grid(preset_id)
        self.accept()

    def _save_current_preset(self):
        name = self.preset_name_input.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                tr("dashboard.preset.msg.title"),
                tr("dashboard.preset.msg.name_required"),
            )
            return
        if self._current_layout is None:
            QMessageBox.warning(
                self,
                tr("dashboard.preset.msg.title"),
                tr("dashboard.preset.msg.no_layout"),
            )
            return
        try:
            self.layout_repo.save_custom_preset(
                self.user_id,
                name,
                self._current_layout,
            )
        except ValueError as error:
            QMessageBox.warning(
                self,
                tr("dashboard.preset.msg.title"),
                str(error),
            )
            return
        self.preset_name_input.clear()
        self._refresh_custom_list()
        QMessageBox.information(
            self,
            tr("dashboard.preset.msg.title"),
            tr("dashboard.preset.msg.saved", name=name),
        )

    def _load_selected_custom(self):
        item = self.custom_list.currentItem()
        if not item:
            QMessageBox.warning(
                self,
                tr("dashboard.preset.msg.title"),
                tr("dashboard.preset.msg.select"),
            )
            return
        layout = self.layout_repo.get_custom_preset(
            self.user_id,
            item.text(),
        )
        if layout is None:
            QMessageBox.warning(
                self,
                tr("dashboard.preset.msg.title"),
                tr("dashboard.preset.msg.load_failed"),
            )
            return
        self.selected_layout = layout
        self.accept()

    def _delete_selected_custom(self):
        item = self.custom_list.currentItem()
        if not item:
            return
        name = item.text()
        confirm = QMessageBox.question(
            self,
            tr("dashboard.preset.msg.delete_confirm.title"),
            tr("dashboard.preset.msg.delete_confirm", name=name),
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.layout_repo.delete_custom_preset(self.user_id, name)
        self._refresh_custom_list()
