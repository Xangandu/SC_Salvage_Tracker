from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal, QTimer
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QTabWidget,
    QLabel,
    QSlider,
    QCheckBox,
    QSpinBox,
    QGroupBox,
    QGridLayout,
    QFrame,
)

from ui.mobiglas_color_dialog import MobiglasColorDialog
from ui.mobiglas_input_dialog import (
    MobiglasItemInputDialog,
    MobiglasTextInputDialog,
)
from config.dates import format_datetime
from config.i18n import (
    normalize_language,
    theme_option_label,
    tr,
)
from ui.language_settings_panel import LanguageSettingsPanel
from ui.typography_settings_panel import TypographySettingsPanel
from config.typography import TYPOGRAPHY_SETTINGS_KEY, TYPOGRAPHY_BASELINE_KEY
from database.access import get_database
from config.permissions import (
    has_permission,
    is_administrator,
    role_permissions_exceed_actor,
    PERM_USERS_MANAGE,
    PERM_ROLES_MANAGE,
    PERM_DATABASE_RESET,
    PERM_SETTINGS_MANAGE,
    ROLE_ADMIN,
)
from database.migration_manager import DEFAULT_BACKUP_MAX_COUNT
from config.editions import (
    apply_supporter_key,
    clear_edition_unlock,
    edition_status_lines,
    enforce_standalone_network,
    has_feature,
    unlocked_edition,
)
from config.support import SUPPORT_DONATION_URL, SUPPORT_PROJECT_TAGLINE
from config.version import APP_VERSION, format_version_subtitle
from ui.edition_feature_panel import EditionFeaturePanel
from ui.edition_dialog import show_edition_locked
from ui.table_utils import (
    configure_mobiglas_table,
    finalize_table_columns,
)
from ui.page_layout import (
    build_page_scroll,
    page_content_widget,
    page_title,
    section_accent,
    subsection_title,
    add_form_field,
    form_label,
    info_panel,
    page_panel,
    primary_button,
    empty_info_panel,
    hud_divider,
    configure_aaa_tabs,
)
from ui.role_edit_dialog import RoleEditDialog
from ui.dashboard_font_preview import DashboardFontPreviewWidget
from ui.connection_scenario_panel import ConnectionScenarioPanel
from ui.theme_manager import (
    ThemeManager,
    FONT_SIZE_LABELS,
    FONT_FAMILY_LABELS,
    NAV_WIDTH_LABELS,
    ANIMATION_LABELS,
    DASHBOARD_LAYOUT_LABELS,
    TRANSPARENCY_OPTIONS,
    PANEL_TRANSPARENCY_OPTIONS,
    TABLE_DENSITY_LABELS,
    DASHBOARD_FONT_SCALE_MIN,
    DASHBOARD_FONT_SCALE_MAX,
)


def _secondary_button(text):
    button = QPushButton(text)
    button.setObjectName("secondaryAction")
    return button


def _populate_option_combo(combo, labels_dict, category):
    combo.clear()
    for key, fallback in labels_dict.items():
        combo.addItem(
            theme_option_label(category, key, fallback),
            key,
        )


def _format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"

    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"

    return f"{size_bytes / (1024 * 1024):.2f} MB"


class AdminPage(QWidget):

    edition_unlock_changed = Signal()

    def __init__(self):
        super().__init__()

        self.db = get_database()
        self.current_user = None
        self.update_manager = None

        content, layout = page_content_widget()
        layout.addWidget(page_title(tr("admin.title")))
        layout.addWidget(
            section_accent(tr("admin.subtitle"))
        )
        layout.addLayout(hud_divider())

        self.tabs = QTabWidget()
        self.tabs.setObjectName("settingsTabs")
        configure_aaa_tabs(self.tabs)

        self.users_tab = self._build_users_tab()
        self.roles_tab = self._build_roles_tab()
        self.design_tab = self._build_design_tab()
        self.network_tab = self._build_network_tab()
        self.support_tab = self._build_support_tab()
        self.system_tab = self._build_system_tab()
        self.language_tab = self._build_language_tab()

        self.tabs.addTab(self.users_tab, tr("admin.tab.users"))
        self.tabs.addTab(self.roles_tab, tr("admin.tab.roles"))
        self.tabs.addTab(self.design_tab, tr("admin.tab.design"))
        self.tabs.addTab(self.network_tab, tr("admin.tab.network"))
        self.tabs.addTab(self.support_tab, tr("admin.tab.support"))
        self.tabs.addTab(self.system_tab, tr("admin.tab.system"))
        self.tabs.addTab(self.language_tab, tr("admin.tab.language"))

        layout.addWidget(self.tabs)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(build_page_scroll(content))

        self.load_role_combos()
        self.refresh_data()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_data()
        self.load_design_settings()
        self.refresh_language_settings()
        self.refresh_support_tab()

    def _new_tab(self):
        tab = QWidget()
        tab.setObjectName("settingsTabContent")
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        return tab, layout

    def _build_users_tab(self):
        tab, layout = self._new_tab()

        layout.addWidget(
            subsection_title(tr("admin.users.section"))
        )

        table_panel, table_layout = page_panel()
        table_layout.setContentsMargins(12, 12, 12, 12)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels([
            tr("admin.users.col.username"),
            tr("admin.users.col.display_name"),
            tr("admin.users.col.role"),
            tr("admin.users.col.active"),
            tr("admin.users.col.created"),
        ])
        configure_mobiglas_table(
            self.users_table,
            "dataTable",
        )
        self.users_table.setMinimumHeight(200)

        self.users_empty_panel = empty_info_panel(
            tr("admin.users.empty"),
            "assets/images/icons/info.svg",
        )

        table_layout.addWidget(self.users_table)
        table_layout.addWidget(self.users_empty_panel)
        self.users_empty_panel.hide()
        layout.addWidget(table_panel)

        user_actions = QHBoxLayout()
        user_actions.setSpacing(10)

        self.edit_display_name_button = _secondary_button(
            tr("admin.users.edit_display_name")
        )
        self.edit_display_name_button.clicked.connect(
            self.edit_display_name
        )
        user_actions.addWidget(
            self.edit_display_name_button
        )

        self.reset_password_button = _secondary_button(
            tr("admin.users.reset_password")
        )
        self.reset_password_button.clicked.connect(
            self.reset_password
        )
        user_actions.addWidget(
            self.reset_password_button
        )

        self.change_role_button = _secondary_button(
            tr("admin.users.assign_role")
        )
        self.change_role_button.clicked.connect(
            self.change_role
        )
        user_actions.addWidget(
            self.change_role_button
        )

        self.toggle_active_button = _secondary_button(
            tr("admin.users.toggle_active")
        )
        self.toggle_active_button.clicked.connect(
            self.toggle_user_active
        )
        user_actions.addWidget(
            self.toggle_active_button
        )

        self.delete_user_button = _secondary_button(
            tr("admin.users.delete")
        )
        self.delete_user_button.clicked.connect(
            self.delete_user
        )
        user_actions.addWidget(
            self.delete_user_button
        )
        user_actions.addStretch()
        layout.addLayout(user_actions)

        form_panel, form_layout = info_panel()
        form_layout.addWidget(
            subsection_title(tr("admin.users.create.section"))
        )
        form_layout.addLayout(hud_divider())

        self.new_username = QLineEdit()
        self.new_username.setPlaceholderText(
            tr("admin.users.placeholder.username")
        )

        self.new_display_name = QLineEdit()
        self.new_display_name.setPlaceholderText(
            tr("admin.users.placeholder.display_name")
        )

        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.new_password.setPlaceholderText(
            tr("admin.users.placeholder.password")
        )

        self.new_role_combo = QComboBox()

        for label_text, widget in [
            (tr("admin.users.label.username"), self.new_username),
            (tr("admin.users.label.display_name"), self.new_display_name),
            (tr("admin.users.label.password"), self.new_password),
            (tr("admin.users.label.role"), self.new_role_combo),
        ]:
            add_form_field(
                form_layout,
                label_text,
                widget,
            )

        self.create_user_button = primary_button(
            tr("admin.users.create.button")
        )
        self.create_user_button.clicked.connect(
            self.create_user
        )
        form_layout.addWidget(self.create_user_button)
        layout.addWidget(form_panel)
        layout.addStretch()

        return tab

    def _build_roles_tab(self):
        tab, layout = self._new_tab()

        hint_panel, hint_layout = info_panel()
        hint = QLabel(tr("admin.roles.hint"))
        hint.setObjectName("mutedLabel")
        hint.setWordWrap(True)
        hint_layout.addWidget(hint)
        layout.addWidget(hint_panel)

        layout.addWidget(
            subsection_title(tr("admin.roles.section"))
        )

        table_panel, table_layout = page_panel()
        table_layout.setContentsMargins(12, 12, 12, 12)

        self.roles_table = QTableWidget()
        self.roles_table.setColumnCount(4)
        self.roles_table.setHorizontalHeaderLabels([
            tr("admin.roles.col.name"),
            tr("admin.roles.col.description"),
            tr("admin.roles.col.permissions"),
            tr("admin.roles.col.users"),
        ])
        configure_mobiglas_table(
            self.roles_table,
            "dataTable",
        )
        self.roles_table.setMinimumHeight(220)
        self.roles_table.doubleClicked.connect(
            self._on_role_double_clicked
        )

        self.roles_empty_panel = empty_info_panel(
            tr("admin.roles.empty"),
            "assets/images/icons/info.svg",
        )

        table_layout.addWidget(self.roles_table)
        table_layout.addWidget(self.roles_empty_panel)
        self.roles_empty_panel.hide()
        layout.addWidget(table_panel)

        role_actions = QHBoxLayout()
        role_actions.setSpacing(10)

        self.create_role_button = primary_button(tr("admin.roles.new"))
        self.create_role_button.clicked.connect(
            self.create_role
        )
        role_actions.addWidget(self.create_role_button)

        self.edit_role_button = _secondary_button(tr("admin.roles.edit"))
        self.edit_role_button.clicked.connect(
            self.edit_role
        )
        role_actions.addWidget(self.edit_role_button)

        self.edit_permissions_button = _secondary_button(
            tr("admin.roles.assign_permissions")
        )
        self.edit_permissions_button.clicked.connect(
            self.edit_role_permissions
        )
        role_actions.addWidget(
            self.edit_permissions_button
        )

        self.view_role_button = _secondary_button(
            tr("admin.roles.view_permissions")
        )
        self.view_role_button.clicked.connect(
            self.view_role_permissions
        )
        role_actions.addWidget(self.view_role_button)

        self.delete_role_button = _secondary_button(
            tr("admin.roles.delete")
        )
        self.delete_role_button.clicked.connect(
            self.delete_role
        )
        role_actions.addWidget(self.delete_role_button)
        role_actions.addStretch()
        layout.addLayout(role_actions)
        layout.addStretch()

        return tab

    def _build_design_tab(self):
        tab, layout = self._new_tab()
        layout.setContentsMargins(12, 12, 12, 12)

        self.design_sub_tabs = QTabWidget()
        self.design_sub_tabs.setObjectName("designSubTabs")
        configure_aaa_tabs(self.design_sub_tabs)

        self.design_sub_tabs.addTab(
            self._build_design_appearance_page(),
            tr("admin.design.tab.appearance"),
        )
        self.design_sub_tabs.addTab(
            self._build_design_density_page(),
            tr("admin.design.tab.density"),
        )
        self.design_sub_tabs.addTab(
            self._build_design_colors_page(),
            tr("admin.design.tab.colors"),
        )
        self.design_sub_tabs.addTab(
            self._build_design_typography_page(),
            tr("admin.design.tab.typography"),
        )
        self.design_sub_tabs.addTab(
            self._build_design_dashboard_page(),
            tr("admin.design.tab.dashboard"),
        )
        self.design_sub_tabs.addTab(
            self._build_design_org_page(),
            tr("admin.design.tab.organization"),
        )

        layout.addWidget(self.design_sub_tabs)
        return tab

    def _build_language_tab(self):
        tab, layout = self._new_tab()

        panel, panel_layout = page_panel()
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(12)

        panel_layout.addWidget(
            subsection_title(tr("admin.language.section"))
        )
        panel_layout.addLayout(hud_divider())

        self.language_settings_panel = LanguageSettingsPanel()
        panel_layout.addWidget(self.language_settings_panel)

        layout.addWidget(panel)
        layout.addStretch()
        return tab

    def refresh_language_settings(self):
        if not hasattr(self, "language_settings_panel"):
            return
        main_window = self.window()
        if self.current_user and main_window is not None:
            self.language_settings_panel.bind(
                self.db,
                self.current_user,
                main_window,
            )

    def _build_design_appearance_page(self):
        page = QWidget()
        page.setObjectName("designSubPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        panel, panel_layout = page_panel()
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(12)

        panel_layout.addWidget(
            subsection_title(tr("admin.design.section.appearance"))
        )
        panel_layout.addLayout(hud_divider())

        self.theme_combo = QComboBox()
        for theme_id, label in ThemeManager.available_themes():
            self.theme_combo.addItem(label, theme_id)

        self.font_size_combo = QComboBox()
        _populate_option_combo(
            self.font_size_combo,
            FONT_SIZE_LABELS,
            "font_size",
        )

        self.font_family_combo = QComboBox()
        for key, label in FONT_FAMILY_LABELS.items():
            self.font_family_combo.addItem(label, key)

        self.animations_combo = QComboBox()
        _populate_option_combo(
            self.animations_combo,
            ANIMATION_LABELS,
            "animation",
        )

        self.nav_width_combo = QComboBox()
        _populate_option_combo(
            self.nav_width_combo,
            NAV_WIDTH_LABELS,
            "nav_width",
        )

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(14)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        appearance_fields = [
            (tr("admin.design.label.theme"), self.theme_combo),
            (tr("admin.design.label.font_size"), self.font_size_combo),
            (tr("admin.design.label.font_family"), self.font_family_combo),
            (tr("admin.design.label.animations"), self.animations_combo),
            (tr("admin.design.label.nav_width"), self.nav_width_combo),
        ]
        for index, (label_text, widget) in enumerate(
            appearance_fields
        ):
            row = index // 2
            col = index % 2
            cell = QVBoxLayout()
            cell.setSpacing(6)
            cell.addWidget(form_label(label_text))
            cell.addWidget(widget)
            grid.addLayout(cell, row, col)

        panel_layout.addLayout(grid)

        hint = QLabel(tr("admin.design.hint.appearance"))
        hint.setObjectName("mutedLabel")
        hint.setWordWrap(True)
        panel_layout.addWidget(hint)

        panel_layout.addLayout(
            self._design_action_row(
                self.preview_design_settings,
                self.save_design_settings,
            )
        )
        layout.addWidget(panel)
        layout.addStretch()
        return page

    def _build_design_density_page(self):
        page = QWidget()
        page.setObjectName("designSubPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        panel, panel_layout = page_panel()
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(12)

        panel_layout.addWidget(
            subsection_title(tr("admin.design.section.density"))
        )
        panel_layout.addLayout(hud_divider())

        self.table_density_combo = QComboBox()
        _populate_option_combo(
            self.table_density_combo,
            TABLE_DENSITY_LABELS,
            "table_density",
        )

        self.window_transparency_combo = QComboBox()
        for value in TRANSPARENCY_OPTIONS:
            self.window_transparency_combo.addItem(
                f"{value} %",
                value,
            )

        self.panel_transparency_combo = QComboBox()
        for value in PANEL_TRANSPARENCY_OPTIONS:
            self.panel_transparency_combo.addItem(
                f"{value} %",
                value,
            )

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(14)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        density_fields = [
            (tr("admin.design.label.table_density"), self.table_density_combo),
            (tr("admin.design.label.window_transparency"), self.window_transparency_combo),
            (tr("admin.design.label.panel_transparency"), self.panel_transparency_combo),
        ]
        for index, (label_text, widget) in enumerate(
            density_fields
        ):
            row = index // 2
            col = index % 2
            cell = QVBoxLayout()
            cell.setSpacing(6)
            cell.addWidget(form_label(label_text))
            cell.addWidget(widget)
            grid.addLayout(cell, row, col)

        panel_layout.addLayout(grid)

        hint = QLabel(tr("admin.design.hint.density"))
        hint.setObjectName("mutedLabel")
        hint.setWordWrap(True)
        panel_layout.addWidget(hint)

        panel_layout.addLayout(
            self._design_action_row(
                self.preview_design_settings,
                self.save_design_settings,
            )
        )
        layout.addWidget(panel)
        layout.addStretch()
        return page

    def _build_design_colors_page(self):
        page = QWidget()
        page.setObjectName("designSubPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        panel, panel_layout = page_panel()
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(12)

        panel_layout.addWidget(
            subsection_title(tr("admin.design.section.colors"))
        )
        panel_layout.addLayout(hud_divider())

        (
            self.accent_color_input,
            accent_widget,
        ) = self._build_color_control(
            tr("admin.design.color.accent"),
            tr("admin.design.color.default_accent"),
            "#00D9FF",
            tr("admin.design.color.pick_accent"),
        )
        (
            self.label_color_input,
            label_widget,
        ) = self._build_color_control(
            tr("admin.design.color.label"),
            tr("admin.design.color.default_label"),
            "#E07A2A",
            tr("admin.design.color.pick_label"),
        )
        (
            self.primary_button_color_input,
            primary_widget,
        ) = self._build_color_control(
            tr("admin.design.color.primary"),
            tr("admin.design.color.default_primary"),
            "#E8893A",
            tr("admin.design.color.pick_primary"),
        )
        (
            self.secondary_button_color_input,
            secondary_widget,
        ) = self._build_color_control(
            tr("admin.design.color.secondary"),
            tr("admin.design.color.default_secondary"),
            "#141C26",
            tr("admin.design.color.pick_secondary"),
        )

        color_grid = QGridLayout()
        color_grid.setHorizontalSpacing(20)
        color_grid.setVerticalSpacing(16)
        color_grid.setColumnStretch(0, 1)
        color_grid.setColumnStretch(1, 1)
        color_grid.addWidget(accent_widget, 0, 0)
        color_grid.addWidget(label_widget, 0, 1)
        color_grid.addWidget(primary_widget, 1, 0)
        color_grid.addWidget(secondary_widget, 1, 1)
        panel_layout.addLayout(color_grid)

        hint = QLabel(tr("admin.design.hint.colors"))
        hint.setObjectName("mutedLabel")
        hint.setWordWrap(True)
        panel_layout.addWidget(hint)

        panel_layout.addLayout(
            self._design_action_row(
                self.preview_design_settings,
                self.save_design_settings,
            )
        )
        layout.addWidget(panel)
        layout.addStretch()
        return page

    def _build_design_typography_page(self):
        page = QWidget()
        page.setObjectName("designSubPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        panel, panel_layout = page_panel()
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(12)

        panel_layout.addWidget(
            subsection_title(tr("admin.design.section.typography"))
        )
        panel_layout.addLayout(hud_divider())

        self.typography_panel = TypographySettingsPanel()
        panel_layout.addWidget(self.typography_panel)

        panel_layout.addLayout(
            self._design_action_row(
                self.preview_typography_settings,
                self.save_typography_settings,
            )
        )
        layout.addWidget(panel)
        layout.addStretch()
        return page

    def _build_design_dashboard_page(self):
        page = QWidget()
        page.setObjectName("designSubPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        dashboard_panel, dashboard_layout = page_panel()
        dashboard_layout.setContentsMargins(20, 20, 20, 20)
        dashboard_layout.setSpacing(12)

        dashboard_layout.addWidget(
            subsection_title(tr("admin.design.section.dashboard"))
        )
        dashboard_layout.addLayout(hud_divider())

        self.dashboard_layout_combo = QComboBox()
        for key, label in DASHBOARD_LAYOUT_LABELS.items():
            self.dashboard_layout_combo.addItem(label, key)

        (
            self.dashboard_font_scale_slider,
            self.dashboard_font_scale_value,
            scale_host,
        ) = self._make_dashboard_scale_row()
        self.dashboard_font_scale_slider.valueChanged.connect(
            self._on_dashboard_widget_scale_changed
        )
        self.dashboard_font_scale_slider.sliderReleased.connect(
            self._finalize_dashboard_scale_preview
        )

        (
            self.dashboard_title_font_scale_slider,
            self.dashboard_title_font_scale_value,
            title_scale_host,
        ) = self._make_dashboard_scale_row()
        self.dashboard_title_font_scale_slider.valueChanged.connect(
            self._on_dashboard_title_scale_changed
        )
        self.dashboard_title_font_scale_slider.sliderReleased.connect(
            self._finalize_dashboard_scale_preview
        )

        (
            self.dashboard_button_font_scale_slider,
            self.dashboard_button_font_scale_value,
            button_scale_host,
        ) = self._make_dashboard_scale_row()
        self.dashboard_button_font_scale_slider.valueChanged.connect(
            self._on_dashboard_button_scale_changed
        )
        self.dashboard_button_font_scale_slider.sliderReleased.connect(
            self._finalize_dashboard_scale_preview
        )

        self._dashboard_scale_live_timer = QTimer(self)
        self._dashboard_scale_live_timer.setSingleShot(True)
        self._dashboard_scale_live_timer.setInterval(8)
        self._dashboard_scale_live_timer.timeout.connect(
            self._apply_dashboard_scale_live
        )

        dash_grid = QGridLayout()
        dash_grid.setHorizontalSpacing(20)
        dash_grid.setVerticalSpacing(14)
        dash_grid.setColumnStretch(0, 1)
        dash_grid.setColumnStretch(1, 1)

        layout_cell = QVBoxLayout()
        layout_cell.setSpacing(6)
        layout_cell.addWidget(form_label(tr("admin.design.label.dashboard_layout")))
        layout_cell.addWidget(self.dashboard_layout_combo)
        dash_grid.addLayout(layout_cell, 0, 0, 1, 2)

        for row_index, (label_text, host) in enumerate(
            (
                (tr("admin.design.label.dashboard_widgets"), scale_host),
                (
                    tr("admin.design.label.dashboard_title"),
                    title_scale_host,
                ),
                (tr("admin.design.label.dashboard_buttons"), button_scale_host),
            ),
            start=1,
        ):
            cell = QVBoxLayout()
            cell.setSpacing(6)
            cell.addWidget(form_label(label_text))
            cell.addWidget(host)
            dash_grid.addLayout(
                cell,
                row_index,
                0,
                1,
                2,
            )

        dashboard_layout.addLayout(dash_grid)

        self.dashboard_font_preview = DashboardFontPreviewWidget()
        dashboard_layout.addWidget(self.dashboard_font_preview)

        dashboard_hint = QLabel(tr("admin.design.hint.dashboard"))
        dashboard_hint.setObjectName("mutedLabel")
        dashboard_hint.setWordWrap(True)
        dashboard_layout.addWidget(dashboard_hint)

        dashboard_layout.addLayout(
            self._design_action_row(
                self.preview_dashboard_settings,
                self.save_dashboard_settings,
            )
        )
        layout.addWidget(dashboard_panel)
        layout.addStretch()
        return page

    def _build_design_org_page(self):
        page = QWidget()
        page.setObjectName("designSubPage")
        self.design_org_page = page
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.app_defaults_panel, app_layout = page_panel()
        app_layout.setContentsMargins(20, 20, 20, 20)
        app_layout.setSpacing(12)
        app_layout.addWidget(
            subsection_title(tr("admin.design.section.organization"))
        )
        app_layout.addLayout(hud_divider())

        app_hint = QLabel(tr("admin.design.hint.organization"))
        app_hint.setObjectName("mutedLabel")
        app_hint.setWordWrap(True)
        app_layout.addWidget(app_hint)

        self.app_theme_combo = QComboBox()
        for theme_id, label in ThemeManager.available_themes():
            self.app_theme_combo.addItem(label, theme_id)

        add_form_field(
            app_layout,
            tr("admin.design.label.default_theme"),
            self.app_theme_combo,
        )

        self.save_app_defaults_button = primary_button(
            tr("admin.design.save_app_defaults")
        )
        self.save_app_defaults_button.clicked.connect(
            self.save_app_default_settings
        )
        app_layout.addWidget(self.save_app_defaults_button)
        layout.addWidget(self.app_defaults_panel)
        layout.addStretch()
        return page

    def _design_action_row(self, preview_callback, save_callback):
        row = QHBoxLayout()
        row.setSpacing(12)
        preview_button = _secondary_button(tr("common.preview"))
        preview_button.clicked.connect(preview_callback)
        save_button = primary_button(tr("common.save"))
        save_button.clicked.connect(save_callback)
        row.addWidget(preview_button)
        row.addWidget(save_button)
        row.addStretch()
        return row

    def _build_color_control(
        self,
        label_text,
        placeholder,
        default_hex,
        picker_title,
    ):
        container = QFrame()
        container.setObjectName("designColorControl")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(form_label(label_text))

        row = QHBoxLayout()
        row.setSpacing(8)

        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        line_edit.setMinimumHeight(40)

        pick_button = _secondary_button(tr("common.choose"))
        pick_button.setFixedWidth(92)
        pick_button.clicked.connect(
            lambda: self._pick_color_value(
                line_edit,
                picker_title,
                default_hex,
            )
        )

        swatch = QPushButton()
        swatch.setObjectName("designColorSwatch")
        swatch.setFixedSize(40, 40)
        swatch.setCursor(Qt.CursorShape.PointingHandCursor)
        swatch.setToolTip(tr("admin.design.color.pick_tooltip"))
        swatch.clicked.connect(pick_button.click)

        clear_button = _secondary_button("↺")
        clear_button.setFixedWidth(40)
        clear_button.setToolTip(tr("admin.design.color.reset_tooltip"))
        clear_button.clicked.connect(line_edit.clear)

        def refresh_swatch():
            self._apply_color_swatch(
                swatch,
                line_edit.text().strip(),
                default_hex,
            )

        line_edit.textChanged.connect(
            lambda _text: refresh_swatch()
        )
        line_edit._design_color_swatch = swatch
        line_edit._design_color_fallback = default_hex
        refresh_swatch()

        row.addWidget(swatch)
        row.addWidget(line_edit, 1)
        row.addWidget(pick_button)
        row.addWidget(clear_button)
        layout.addLayout(row)

        return line_edit, container

    def _apply_color_swatch(
        self,
        swatch,
        color_text,
        fallback_hex,
    ):
        color = QColor(color_text)
        if not color.isValid():
            color = QColor(fallback_hex)
        swatch.setStyleSheet(
            "QPushButton#designColorSwatch {"
            f"background-color: {color.name()};"
            "border: 1px solid #33485C;"
            "border-radius: 8px;"
            "padding: 0;"
            "min-width: 40px;"
            "max-width: 40px;"
            "min-height: 40px;"
            "max-height: 40px;"
            "}"
            "QPushButton#designColorSwatch:hover {"
            f"border: 1px solid #42D4F5;"
            "}"
        )

    def _refresh_design_color_swatches(self):
        for line_edit in (
            self.accent_color_input,
            self.label_color_input,
            self.primary_button_color_input,
            self.secondary_button_color_input,
        ):
            swatch = getattr(
                line_edit,
                "_design_color_swatch",
                None,
            )
            fallback = getattr(
                line_edit,
                "_design_color_fallback",
                "#888888",
            )
            if swatch is not None:
                self._apply_color_swatch(
                    swatch,
                    line_edit.text().strip(),
                    fallback,
                )

    def set_update_manager(self, manager):
        self.update_manager = manager
        self.refresh_updates_section()

    def refresh_updates_section(self):
        if not hasattr(self, "update_version_label"):
            return

        from update.service import (
            get_last_check,
            is_auto_check_enabled,
        )

        self.update_version_label.setText(
            tr("admin.system.updates.installed", version=format_version_subtitle())
        )

        last_check = get_last_check(self.db)
        if last_check:
            status = (
                tr(
                "admin.system.updates.last_check",
                datetime=format_datetime(last_check, with_seconds=True),
            )
            )
        else:
            status = tr("admin.system.updates.no_check")

        self.update_auto_check.blockSignals(True)
        self.update_auto_check.setChecked(
            is_auto_check_enabled(self.db)
        )
        self.update_auto_check.blockSignals(False)

        if (
            self.update_manager
            and self.update_manager.pending_update
        ):
            pending = self.update_manager.pending_update
            status = (
                tr(
                "admin.system.updates.available",
                version=pending.version_display,
                build=pending.build,
                status=status,
            )
            )

        self.update_status_label.setText(status)
        if hasattr(self, "update_check_button"):
            self.update_check_button.setEnabled(True)

    def _save_update_auto_check(self, enabled: bool):
        if self.update_manager:
            self.update_manager.set_auto_check(enabled)
        else:
            from update.service import set_auto_check_enabled

            set_auto_check_enabled(self.db, enabled)

    def check_updates_clicked(self):
        if not self.update_manager:
            QMessageBox.information(
                self,
                tr("admin.system.updates.dialog.title"),
                tr("admin.system.updates.msg.not_ready"),
            )
            return

        if hasattr(self, "update_status_label"):
            self.update_status_label.setText(tr("admin.system.updates.checking"))
        if hasattr(self, "update_check_button"):
            self.update_check_button.setEnabled(False)

        self.update_manager.check_for_updates(silent=False)

    def _pick_color_value(
        self,
        line_edit,
        title,
        default_hex,
    ):
        current = line_edit.text().strip()
        initial = (
            QColor(current)
            if current.startswith("#")
            else QColor(default_hex)
        )
        color, accepted = MobiglasColorDialog.get_color(
            self,
            title,
            initial=initial,
        )
        if accepted and color.isValid():
            line_edit.setText(color.name().upper())

    def _load_color_input(self, line_edit, user_settings, key):
        value = user_settings.get(key)
        if value:
            line_edit.setText(value)
            return

        app_value = self.db.settings.get_app_setting(
            key,
            "",
        )
        line_edit.setText(app_value or "")

    @staticmethod
    def _optional_color(value):
        cleaned = (value or "").strip()
        return cleaned or None

    def _set_combo_by_data(self, combo, value):
        if value is None:
            return
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def load_design_settings(self):
        if not self.current_user:
            return

        user_settings = (
            self.db.settings.get_user_settings(
                self.current_user["id"]
            )
        )
        effective = (
            self.db.settings.resolve_effective_settings(
                self.current_user["id"]
            )
        )

        self._set_combo_by_data(
            self.theme_combo,
            effective.get("theme"),
        )
        self._set_combo_by_data(
            self.font_size_combo,
            effective.get("font_size"),
        )
        self._set_combo_by_data(
            self.font_family_combo,
            effective.get("font_family"),
        )
        self._set_combo_by_data(
            self.table_density_combo,
            effective.get("table_density"),
        )
        self._set_combo_by_data(
            self.window_transparency_combo,
            effective.get("transparency"),
        )
        self._set_combo_by_data(
            self.panel_transparency_combo,
            effective.get("panel_transparency"),
        )
        self._set_combo_by_data(
            self.animations_combo,
            effective.get("animations"),
        )
        self._set_combo_by_data(
            self.nav_width_combo,
            effective.get("nav_width"),
        )
        self._set_combo_by_data(
            self.dashboard_layout_combo,
            effective.get("dashboard_layout"),
        )

        scales = ThemeManager.resolve_dashboard_scales(
            effective
        )
        self._load_dashboard_scale_slider(
            self.dashboard_font_scale_slider,
            self.dashboard_font_scale_value,
            scales["dashboard_font_scale"],
        )
        self._load_dashboard_scale_slider(
            self.dashboard_title_font_scale_slider,
            self.dashboard_title_font_scale_value,
            scales["dashboard_title_font_scale"],
        )
        self._load_dashboard_scale_slider(
            self.dashboard_button_font_scale_slider,
            self.dashboard_button_font_scale_value,
            scales["dashboard_button_font_scale"],
        )
        self.dashboard_font_preview.set_scale(
            scales["dashboard_font_scale"]
        )

        accent = user_settings.get("accent_color")
        if accent:
            self.accent_color_input.setText(accent)
        else:
            app_accent = self.db.settings.get_app_setting(
                "accent_color",
                "",
            )
            self.accent_color_input.setText(app_accent or "")

        self._load_color_input(
            self.label_color_input,
            user_settings,
            "label_color",
        )
        self._load_color_input(
            self.primary_button_color_input,
            user_settings,
            "primary_button_color",
        )
        self._load_color_input(
            self.secondary_button_color_input,
            user_settings,
            "secondary_button_color",
        )

        app_settings = self.db.settings.get_app_settings()
        self._set_combo_by_data(
            self.app_theme_combo,
            app_settings.get("theme"),
        )
        self._refresh_design_color_swatches()
        self.typography_panel.load_from_settings(
            effective.get(TYPOGRAPHY_SETTINGS_KEY, ""),
            typography_baseline_json=effective.get(
                TYPOGRAPHY_BASELINE_KEY,
                "",
            ),
            theme_id=effective.get("theme", "star_citizen"),
            global_family_id=effective.get("font_family", "oxanium"),
        )

    def _collect_theme_form(self):
        effective = (
            self.db.settings.resolve_effective_settings(
                self.current_user["id"]
            )
            if self.current_user
            else {}
        )
        return {
            "language": normalize_language(
                effective.get("language")
            ),
            "theme": self.theme_combo.currentData(),
            "font_size": self.font_size_combo.currentData(),
            "font_family": self.font_family_combo.currentData(),
            "accent_color": (
                self.accent_color_input.text().strip()
            ),
            "label_color": (
                self.label_color_input.text().strip()
            ),
            "primary_button_color": (
                self.primary_button_color_input.text().strip()
            ),
            "secondary_button_color": (
                self.secondary_button_color_input.text().strip()
            ),
            "transparency": (
                self.window_transparency_combo.currentData()
            ),
            "panel_transparency": (
                self.panel_transparency_combo.currentData()
            ),
            "table_density": (
                self.table_density_combo.currentData()
            ),
            "animations": self.animations_combo.currentData(),
            "nav_width": self.nav_width_combo.currentData(),
        }

    def _apply_layout_to_main_window(self, settings):
        window = self.window()
        if window is not None and hasattr(
            window,
            "apply_nav_width",
        ):
            window.apply_nav_width(
                settings.get("nav_width", "normal")
            )

    def _make_dashboard_scale_row(self):
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(
            DASHBOARD_FONT_SCALE_MIN,
            DASHBOARD_FONT_SCALE_MAX,
        )
        slider.setSingleStep(5)
        slider.setTickInterval(25)
        slider.setTickPosition(
            QSlider.TickPosition.TicksBelow
        )
        value_label = QLabel()
        value_label.setMinimumWidth(56)
        row = QHBoxLayout()
        row.addWidget(slider, 1)
        row.addWidget(value_label)
        host = QWidget()
        host.setLayout(row)
        return slider, value_label, host

    def _load_dashboard_scale_slider(
        self,
        slider,
        value_label,
        scale,
    ):
        scale = ThemeManager.normalize_dashboard_font_scale(
            scale
        )
        slider.blockSignals(True)
        slider.setValue(scale)
        slider.blockSignals(False)
        self._update_dashboard_scale_label(value_label, scale)

    def _collect_dashboard_form(self):
        return {
            "dashboard_layout": (
                self.dashboard_layout_combo.currentData()
            ),
            "dashboard_font_scale": (
                self.dashboard_font_scale_slider.value()
            ),
            "dashboard_title_font_scale": (
                self.dashboard_title_font_scale_slider.value()
            ),
            "dashboard_button_font_scale": (
                self.dashboard_button_font_scale_slider.value()
            ),
        }

    def _schedule_dashboard_scale_live(self):
        self._dashboard_scale_live_timer.start()

    def _apply_dashboard_scale_live(self):
        ThemeManager.refresh_dashboard_font_scale(
            self._collect_dashboard_form(),
            live_preview=True,
        )

    def _finalize_dashboard_scale_preview(self):
        self._dashboard_scale_live_timer.stop()
        ThemeManager.refresh_dashboard_font_scale(
            self._collect_dashboard_form(),
            live_preview=False,
        )

    def _refresh_dashboard_font_live(self):
        self._schedule_dashboard_scale_live()

    def _merge_effective_settings(self, overrides):
        if not self.current_user:
            return dict(overrides)
        effective = (
            self.db.settings.resolve_effective_settings(
                self.current_user["id"]
            )
        )
        effective.update(overrides)
        return effective

    def _update_dashboard_scale_label(self, label, scale):
        label.setText(
            f"{ThemeManager.normalize_dashboard_font_scale(scale)} %"
        )

    def _on_dashboard_widget_scale_changed(self, scale):
        scale = ThemeManager.normalize_dashboard_font_scale(
            scale
        )
        self._update_dashboard_scale_label(
            self.dashboard_font_scale_value,
            scale,
        )
        self.dashboard_font_preview.set_scale(scale)
        self._schedule_dashboard_scale_live()

    def _on_dashboard_title_scale_changed(self, scale):
        scale = ThemeManager.normalize_dashboard_font_scale(
            scale
        )
        self._update_dashboard_scale_label(
            self.dashboard_title_font_scale_value,
            scale,
        )
        self._schedule_dashboard_scale_live()

    def _on_dashboard_button_scale_changed(self, scale):
        scale = ThemeManager.normalize_dashboard_font_scale(
            scale
        )
        self._update_dashboard_scale_label(
            self.dashboard_button_font_scale_value,
            scale,
        )
        self._schedule_dashboard_scale_live()

    def _apply_dashboard_layout(self):
        window = self.window()
        if hasattr(window, "get_dashboard_page"):
            window.get_dashboard_page().apply_dashboard_layout()

    def preview_typography_settings(self):
        settings = self._merge_effective_settings({
            TYPOGRAPHY_SETTINGS_KEY: (
                self.typography_panel.collect_overrides_json()
            ),
        })
        ThemeManager.apply_settings(settings)
        QMessageBox.information(
            self,
            tr("admin.design.dialog.title"),
            tr("admin.design.msg.preview"),
        )

    def save_typography_settings(self):
        if not self.current_user:
            return

        typography_json = self.typography_panel.collect_overrides_json()
        self.db.settings.save_user_settings(
            self.current_user["id"],
            {
                TYPOGRAPHY_SETTINGS_KEY: typography_json,
                TYPOGRAPHY_BASELINE_KEY: typography_json,
            },
        )
        settings = self._merge_effective_settings({
            TYPOGRAPHY_SETTINGS_KEY: typography_json,
            TYPOGRAPHY_BASELINE_KEY: typography_json,
        })
        ThemeManager.apply_settings(settings)
        self.typography_panel.load_from_settings(
            typography_json,
            typography_baseline_json=typography_json,
            theme_id=settings.get("theme", "star_citizen"),
            global_family_id=settings.get("font_family", "oxanium"),
        )
        QMessageBox.information(
            self,
            tr("admin.design.dialog.title"),
            tr("admin.design.msg.saved"),
        )

    def preview_design_settings(self):
        theme = self._collect_theme_form()
        settings = self._merge_effective_settings(theme)
        ThemeManager.apply_settings(settings)
        self._apply_layout_to_main_window(settings)
        QMessageBox.information(
            self,
            tr("admin.design.dialog.title"),
            tr("admin.design.msg.preview"),
        )

    def save_design_settings(self):
        if not self.current_user:
            return

        theme = self._collect_theme_form()
        accent = theme.get("accent_color") or None
        selected_language = normalize_language(theme.get("language"))

        self.db.settings.save_user_settings(
            self.current_user["id"],
            {
                "language": selected_language,
                "theme": theme["theme"],
                "font_size": theme["font_size"],
                "font_family": theme["font_family"],
                "accent_color": accent,
                "label_color": self._optional_color(
                    theme.get("label_color")
                ),
                "primary_button_color": self._optional_color(
                    theme.get("primary_button_color")
                ),
                "secondary_button_color": self._optional_color(
                    theme.get("secondary_button_color")
                ),
                "nav_width": theme["nav_width"],
                "transparency": theme["transparency"],
                "panel_transparency": theme["panel_transparency"],
                "table_density": theme["table_density"],
                "animations": theme["animations"],
            },
        )
        settings = self._merge_effective_settings(theme)
        ThemeManager.apply_settings(settings)
        self._apply_layout_to_main_window(settings)

        QMessageBox.information(
            self,
            tr("admin.design.dialog.title"),
            tr("admin.design.msg.saved"),
        )

    def preview_dashboard_settings(self):
        dashboard = self._collect_dashboard_form()
        settings = self._merge_effective_settings(dashboard)
        ThemeManager.apply_settings(settings)
        self._apply_dashboard_layout()
        QMessageBox.information(
            self,
            tr("admin.dashboard.dialog.title"),
            tr("admin.dashboard.msg.preview"),
        )

    def save_dashboard_settings(self):
        if not self.current_user:
            return

        dashboard = self._collect_dashboard_form()

        self.db.settings.save_user_settings(
            self.current_user["id"],
            {
                "dashboard_layout": (
                    dashboard["dashboard_layout"]
                ),
                "dashboard_font_scale": (
                    dashboard["dashboard_font_scale"]
                ),
                "dashboard_title_font_scale": (
                    dashboard["dashboard_title_font_scale"]
                ),
                "dashboard_button_font_scale": (
                    dashboard["dashboard_button_font_scale"]
                ),
            },
        )
        settings = self._merge_effective_settings(dashboard)
        ThemeManager.apply_settings(settings)
        self._apply_dashboard_layout()

        QMessageBox.information(
            self,
            tr("admin.dashboard.dialog.title"),
            tr("admin.dashboard.msg.saved"),
        )

    def save_app_default_settings(self):
        if not has_permission(
            PERM_SETTINGS_MANAGE,
            self.current_user,
        ):
            QMessageBox.warning(
                self,
                tr("admin.design.dialog.title"),
                tr("admin.design.msg.no_app_defaults_permission"),
            )
            return

        theme_id = self.app_theme_combo.currentData()
        self.db.settings.set_app_setting("theme", theme_id)

        QMessageBox.information(
            self,
            tr("admin.design.dialog.title"),
            tr("admin.design.msg.app_defaults_saved"),
        )

    def _build_network_tab(self):
        tab, layout = self._new_tab()
        layout.addWidget(subsection_title(tr("admin.network.section")))
        layout.addLayout(hud_divider())

        self.network_edition_panel = EditionFeaturePanel(
            "network.crew_edition",
            self.db,
            tab,
        )
        content = self.network_edition_panel.content_layout

        panel, panel_layout = info_panel()

        hint = QLabel(
            tr("admin.network.hint")
        )
        hint.setWordWrap(True)
        hint.setObjectName("mutedLabel")
        panel_layout.addWidget(hint)

        action_row = QHBoxLayout()
        self.network_host_crew_button = primary_button(tr("admin.network.host_crew"))
        self.network_host_crew_button.clicked.connect(
            self._one_click_host_crew
        )
        self.network_join_crew_button = _secondary_button(
            tr("admin.network.join_crew")
        )
        self.network_join_crew_button.clicked.connect(
            self._one_click_join_crew
        )
        action_row.addWidget(self.network_host_crew_button)
        action_row.addWidget(self.network_join_crew_button)
        action_row.addStretch()
        panel_layout.addLayout(action_row)

        self.network_code_label = QLabel("—")
        self.network_code_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.network_code_label.setStyleSheet(
            "font-size: 32px; letter-spacing: 8px; padding: 8px;"
        )
        panel_layout.addWidget(form_label(tr("admin.network.join_code")))
        panel_layout.addWidget(self.network_code_label)

        copy_row = QHBoxLayout()
        self.network_copy_code_button = _secondary_button(
            tr("admin.network.copy_code")
        )
        self.network_copy_code_button.clicked.connect(
            self._copy_network_join_code
        )
        copy_row.addWidget(self.network_copy_code_button)
        copy_row.addStretch()
        panel_layout.addLayout(copy_row)

        self.network_mode_label = QLineEdit()
        self.network_mode_label.setReadOnly(True)
        self.network_host_status = QLineEdit()
        self.network_host_status.setReadOnly(True)
        self.network_clients_label = QLineEdit()
        self.network_clients_label.setReadOnly(True)

        add_form_field(
            panel_layout,
            tr("admin.network.mode"),
            self.network_mode_label,
        )
        add_form_field(
            panel_layout,
            tr("admin.network.status"),
            self.network_host_status,
        )
        add_form_field(
            panel_layout,
            tr("admin.network.connected_crew"),
            self.network_clients_label,
        )
        content.addWidget(panel)

        advanced = QGroupBox(tr("admin.network.advanced"))
        advanced.setCheckable(True)
        advanced.setChecked(False)
        advanced_layout = QVBoxLayout(advanced)

        self.network_scenario_panel = ConnectionScenarioPanel(
            role="host",
            show_invite=True,
        )
        self.network_scenario_panel.scenario_changed.connect(
            self._on_network_scenario_changed
        )
        advanced_layout.addWidget(self.network_scenario_panel)

        self.network_use_relay_checkbox = QCheckBox(
            tr("admin.network.relay_register")
        )
        self.network_use_relay_checkbox.toggled.connect(
            self._on_network_use_relay_changed
        )
        advanced_layout.addWidget(self.network_use_relay_checkbox)

        self.network_upnp_button = _secondary_button(
            tr("admin.network.upnp")
        )
        self.network_upnp_button.clicked.connect(
            self._try_upnp_port_forward
        )
        advanced_layout.addWidget(self.network_upnp_button)

        host_row = QHBoxLayout()
        self.network_start_host_button = _secondary_button(
            tr("admin.network.start_host")
        )
        self.network_start_host_button.clicked.connect(
            self._start_host_from_settings
        )
        self.network_stop_host_button = _secondary_button(
            tr("admin.network.stop_host")
        )
        self.network_stop_host_button.clicked.connect(
            self._stop_host_from_settings
        )
        host_row.addWidget(self.network_start_host_button)
        host_row.addWidget(self.network_stop_host_button)
        host_row.addStretch()
        advanced_layout.addLayout(host_row)

        content.addWidget(advanced)
        content.addStretch()
        layout.addWidget(self.network_edition_panel, 1)

        self._refresh_network_tab()
        return tab

    def _require_crew_edition(self, feature_id: str = "network.crew_edition") -> bool:
        if has_feature(feature_id, self.db):
            return True
        show_edition_locked(self, feature_id)
        return False

    def _one_click_host_crew(self):
        if not self._require_crew_edition("network.host"):
            return
        from network.simple_connect import (
            apply_host_simple_defaults,
            format_simple_invite,
            generate_join_code,
        )
        from ui.clipboard_utils import copy_to_clipboard

        code = self.db.settings.get_app_setting(
            "network_join_code",
            "",
        ).strip().upper()
        if not code:
            code = generate_join_code()

        apply_host_simple_defaults(self.db, code)
        self._start_host_from_settings(silent=True)

        copy_to_clipboard(
            format_simple_invite(code),
            self,
            message=tr("admin.network.msg.host_mode_active"),
        )
        self._refresh_network_tab()
        self._notify_main_window_network_changed()

    def _one_click_join_crew(self):
        if not self._require_crew_edition("network.client"):
            return
        from database.access import (
            get_client_connection,
            set_client_connection,
            set_database,
        )
        from ui.quick_join_dialog import QuickJoinDialog

        dialog = QuickJoinDialog(self.db, self)
        if not dialog.exec():
            return

        if dialog._client_connection:
            set_client_connection(dialog._client_connection)
            set_database(get_database())

        self._refresh_network_tab()
        self._notify_main_window_network_changed()
        QMessageBox.information(
            self,
            tr("admin.network.dialog.title"),
            tr("admin.network.msg.connected"),
        )

    def _copy_network_join_code(self):
        from network.simple_connect import format_simple_invite
        from ui.clipboard_utils import copy_to_clipboard

        code = self.network_code_label.text().strip()
        if not code or code == "—":
            QMessageBox.warning(
                self,
                tr("admin.network.code.dialog.title"),
                tr("admin.network.msg.no_code"),
            )
            return
        copy_to_clipboard(
            format_simple_invite(code),
            self,
            message=tr("admin.network.msg.code_copied"),
        )

    def _refresh_network_tab(self):
        from database.access import get_host_server
        from network.connection_guide import normalize_scenario
        from network.network_state import get_network_state

        if not hasattr(self, "network_mode_label"):
            return

        if hasattr(self, "network_edition_panel"):
            self.network_edition_panel.refresh()

        if hasattr(self, "network_scenario_panel"):
            saved = normalize_scenario(
                self.db.settings.get_app_setting(
                    "network_connection_scenario",
                    "lan",
                )
            )
            self.network_scenario_panel.blockSignals(True)
            self.network_scenario_panel.set_scenario(saved)
            from network.connection_guide import (
                default_relay_host,
                default_relay_port,
            )

            self.network_scenario_panel.set_relay_defaults(
                relay_host=self.db.settings.get_app_setting(
                    "network_relay_host",
                    default_relay_host(),
                ),
                relay_port=int(
                    self.db.settings.get_app_setting(
                        "network_relay_port",
                        str(default_relay_port()),
                    )
                ),
            )
            self.network_scenario_panel.blockSignals(False)

        if hasattr(self, "network_use_relay_checkbox"):
            use_relay = (
                self.db.settings.get_app_setting(
                    "network_use_relay",
                    "0",
                )
                == "1"
            )
            self.network_use_relay_checkbox.blockSignals(True)
            self.network_use_relay_checkbox.setChecked(use_relay)
            self.network_use_relay_checkbox.blockSignals(False)

        if hasattr(self, "network_upnp_button"):
            from network.connection_guide import SCENARIO_INTERNET

            scenario = normalize_scenario(
                self.db.settings.get_app_setting(
                    "network_connection_scenario",
                    "lan",
                )
            )
            self.network_upnp_button.setVisible(
                scenario == SCENARIO_INTERNET
            )

        state = get_network_state()
        server = get_host_server()
        mode_labels = {
            "standalone": tr("admin.network.mode.standalone"),
            "host": tr("admin.network.mode.host"),
            "client": tr("admin.network.mode.client"),
        }
        self.network_mode_label.setText(
            mode_labels.get(state.mode, state.mode)
        )

        if server and server.is_running():
            addrs = ", ".join(server.addresses)
            relay_status = ""
            from database.access import get_host_relay_bridge

            bridge = get_host_relay_bridge()
            if bridge and bridge.is_active:
                relay_status = tr("admin.network.status.relay_active")
            self.network_host_status.setText(
                tr(
                    "admin.network.status.running",
                    code=server.join_code,
                    relay=relay_status,
                )
            )
            if hasattr(self, "network_code_label"):
                self.network_code_label.setText(server.join_code)
            self.network_clients_label.setText(
                ", ".join(state.connected_clients)
                or tr("admin.network.status.none")
            )
            if hasattr(self, "network_scenario_panel"):
                use_tls = self.db.settings.get_app_setting(
                    "network_use_tls",
                    "1",
                ) == "1"
                self.network_scenario_panel.set_host_invite_context(
                    port=server.port,
                    join_code=server.join_code,
                    use_tls=use_tls,
                    addresses=server.addresses,
                )
        else:
            self.network_host_status.setText(
                tr("admin.network.status.inactive")
            )
            self.network_clients_label.setText("—")
            if hasattr(self, "network_code_label"):
                saved_code = self.db.settings.get_app_setting(
                    "network_join_code",
                    "",
                ).strip().upper()
                self.network_code_label.setText(
                    saved_code or "—"
                )

    def _on_network_scenario_changed(self, scenario: str) -> None:
        from network.connection_guide import (
            SCENARIO_INTERNET,
            is_relay_scenario,
        )

        self.db.settings.set_app_setting(
            "network_connection_scenario",
            scenario,
        )
        if hasattr(self, "network_scenario_panel"):
            relay_host = self.network_scenario_panel.invite_address()
            relay_port = self.network_scenario_panel.relay_port()
            self.db.settings.set_app_setting(
                "network_relay_host",
                relay_host,
            )
            self.db.settings.set_app_setting(
                "network_relay_port",
                str(relay_port),
            )
        if is_relay_scenario(scenario):
            self.db.settings.set_app_setting("network_use_relay", "1")
            if hasattr(self, "network_use_relay_checkbox"):
                self.network_use_relay_checkbox.blockSignals(True)
                self.network_use_relay_checkbox.setChecked(True)
                self.network_use_relay_checkbox.blockSignals(False)
        if hasattr(self, "network_upnp_button"):
            self.network_upnp_button.setVisible(
                scenario == SCENARIO_INTERNET
            )

    def _on_network_use_relay_changed(self, checked: bool) -> None:
        self.db.settings.set_app_setting(
            "network_use_relay",
            "1" if checked else "0",
        )
        from database.access import get_host_server
        from network.host_relay import (
            start_host_relay_if_enabled,
            stop_host_relay,
        )

        server = get_host_server()
        if checked and server and server.is_running():
            bridge = start_host_relay_if_enabled(self.db, server)
            if not bridge:
                QMessageBox.warning(
                    self,
                    tr("admin.network.relay.dialog.title"),
                    tr("admin.network.msg.relay_failed")
                    + tr("admin.network.relay.check_hint"),
                )
        elif not checked:
            stop_host_relay()
        self._refresh_network_tab()

    def _try_upnp_port_forward(self) -> None:
        from network.upnp_forward import try_forward_port

        port = int(
            self.db.settings.get_app_setting(
                "network_host_port",
                "47890",
            )
        )
        self.network_upnp_button.setEnabled(False)
        self.network_upnp_button.setText(tr("admin.network.upnp.progress"))
        try:
            ok, message = try_forward_port(port)
        finally:
            self.network_upnp_button.setEnabled(True)
            self.network_upnp_button.setText(
                tr("admin.network.upnp")
            )

        if ok:
            QMessageBox.information(self, tr("admin.network.upnp.dialog.title"), message)
        else:
            QMessageBox.warning(self, tr("admin.network.upnp.dialog.title"), message)

    def _open_connection_assistant(self):
        from ui.connection_assistant_dialog import (
            ConnectionAssistantDialog,
        )

        dialog = ConnectionAssistantDialog(self.db, self)
        if dialog.exec():
            self._refresh_network_tab()
            self._notify_main_window_network_changed()

            from database.access import get_client_connection
            from network.network_state import get_network_state

            state = get_network_state()
            if (
                get_client_connection()
                and get_client_connection().is_connected
            ):
                message = tr("admin.network.msg.client_connected")
            elif state.mode == "host":
                message = tr("admin.network.msg.host_saved")
            else:
                message = tr("admin.network.msg.settings_saved")

            QMessageBox.information(
                self,
                tr("admin.network.dialog.title"),
                message,
            )

    def _notify_main_window_network_changed(self):
        window = self.window()
        if hasattr(window, "apply_network_mode"):
            window.apply_network_mode()
        elif hasattr(window, "refresh_network_display"):
            window.refresh_network_display()

    def _start_host_from_settings(self, *, silent: bool = False):
        if not self._require_crew_edition("network.host"):
            return

        from database.access import get_host_server, set_host_server
        from network.host_server import HostServer

        server = get_host_server()
        if server and server.is_running():
            if not silent:
                QMessageBox.information(
                    self,
                    tr("admin.network.host.dialog.title"),
                    tr("admin.network.msg.host_running"),
                )
            return

        port = int(
            self.db.settings.get_app_setting(
                "network_host_port",
                "47890",
            )
        )
        join_code = self.db.settings.get_app_setting(
            "network_join_code",
            "",
        )
        use_tls = self.db.settings.get_app_setting(
            "network_use_tls",
            "1",
        ) == "1"

        if not server:
            server = HostServer(self.db)
            set_host_server(server)

        if server.start(
            port=port,
            join_code=join_code or None,
            use_tls=use_tls,
        ):
            self.db.settings.set_app_setting(
                "network_mode",
                "host",
            )
            from network.host_relay import start_host_relay_if_enabled

            start_host_relay_if_enabled(self.db, server)
            self._refresh_network_tab()
            self._notify_main_window_network_changed()
        else:
            if not silent:
                QMessageBox.warning(
                    self,
                    tr("admin.network.host.dialog.title"),
                    tr("admin.network.msg.host_start_failed"),
                )

    def _stop_host_from_settings(self):
        from database.access import get_host_server
        from network.network_state import get_network_state

        server = get_host_server()
        if server and server.is_running():
            server.stop()

        from network.host_relay import stop_host_relay

        stop_host_relay()

        state = get_network_state()
        state.mode = "standalone"
        self.db.settings.set_app_setting(
            "network_mode",
            "standalone",
        )
        self._refresh_network_tab()
        self._notify_main_window_network_changed()

    def _make_collapsible_block(
        self,
        title,
        *,
        start_open=False,
    ):
        toggle = QGroupBox(title)
        toggle.setCheckable(True)
        toggle.setChecked(start_open)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 8, 0, 0)
        content_layout.setSpacing(10)
        content.setVisible(start_open)
        toggle.toggled.connect(content.setVisible)

        return toggle, content, content_layout

    def _build_support_tab(self):
        tab, layout = self._new_tab()
        layout.addWidget(subsection_title(tr("admin.support.section.project")))
        layout.addLayout(hud_divider())

        intro, intro_layout = info_panel()
        intro_body = QLabel(
            tr("admin.support.intro", tagline=SUPPORT_PROJECT_TAGLINE)
        )
        intro_body.setWordWrap(True)
        intro_body.setObjectName("mutedLabel")
        intro_layout.addWidget(intro_body)
        layout.addWidget(intro)

        layout.addWidget(subsection_title(tr("admin.support.section.edition")))
        layout.addLayout(hud_divider())

        status_panel, status_layout = info_panel()
        self.support_build_label = QLineEdit()
        self.support_build_label.setReadOnly(True)
        self.support_unlock_label = QLineEdit()
        self.support_unlock_label.setReadOnly(True)
        self.support_effective_label = QLineEdit()
        self.support_effective_label.setReadOnly(True)

        add_form_field(
            status_layout,
            tr("admin.support.label.installation"),
            self.support_build_label,
        )
        add_form_field(
            status_layout,
            tr("admin.support.label.unlock"),
            self.support_unlock_label,
        )
        add_form_field(
            status_layout,
            tr("admin.support.label.active"),
            self.support_effective_label,
        )
        layout.addWidget(status_panel)

        layout.addWidget(subsection_title(tr("admin.support.section.key")))
        layout.addLayout(hud_divider())

        key_panel, key_layout = info_panel()
        key_hint = QLabel(
            tr("admin.support.key.hint")
        )
        key_hint.setWordWrap(True)
        key_hint.setObjectName("mutedLabel")
        key_layout.addWidget(key_hint)

        self.support_key_input = QLineEdit()
        self.support_key_input.setPlaceholderText(
            tr("admin.support.placeholder.key")
        )
        add_form_field(
            key_layout,
            tr("admin.support.label.key"),
            self.support_key_input,
        )

        key_actions = QHBoxLayout()
        self.support_apply_key_button = primary_button(tr("admin.support.unlock"))
        self.support_apply_key_button.clicked.connect(
            self._apply_support_key
        )
        self.support_clear_key_button = _secondary_button(
            tr("admin.support.clear_unlock")
        )
        self.support_clear_key_button.clicked.connect(
            self._clear_support_unlock
        )
        key_actions.addWidget(self.support_apply_key_button)
        key_actions.addWidget(self.support_clear_key_button)
        key_actions.addStretch()
        key_layout.addLayout(key_actions)
        layout.addWidget(key_panel)

        layout.addWidget(subsection_title(tr("admin.support.section.donate")))
        layout.addLayout(hud_divider())

        donate_panel, donate_layout = info_panel()
        donate_text = QLabel(
            tr("admin.support.donate.hint")
        )
        donate_text.setWordWrap(True)
        donate_text.setObjectName("mutedLabel")
        donate_layout.addWidget(donate_text)

        donate_row = QHBoxLayout()
        self.support_donate_button = primary_button(tr("admin.support.donate.button"))
        self.support_donate_button.clicked.connect(
            self._open_support_donation_link
        )
        donate_row.addWidget(self.support_donate_button)
        donate_row.addStretch()
        donate_layout.addLayout(donate_row)
        layout.addWidget(donate_panel)

        layout.addStretch()
        self.refresh_support_tab()
        return tab

    def refresh_support_tab(self):
        if not hasattr(self, "support_build_label"):
            return

        build_label, unlock_label, effective_label = edition_status_lines(
            self.db
        )
        self.support_build_label.setText(build_label)
        self.support_unlock_label.setText(unlock_label)
        self.support_effective_label.setText(effective_label)

        has_unlock = unlocked_edition(self.db) is not None
        self.support_clear_key_button.setEnabled(has_unlock)

        if SUPPORT_DONATION_URL.strip():
            self.support_donate_button.setEnabled(True)
            self.support_donate_button.setToolTip(SUPPORT_DONATION_URL)
        else:
            self.support_donate_button.setEnabled(False)
            self.support_donate_button.setToolTip(
                tr("admin.support.donate.tooltip_pending")
            )

    def _apply_support_key(self):
        if not has_permission(
            PERM_SETTINGS_MANAGE,
            self.current_user,
        ):
            QMessageBox.warning(
                self,
                tr("admin.support.key.dialog.title"),
                tr("admin.support.msg.admin_only"),
            )
            return

        raw_key = self.support_key_input.text().strip()
        if not raw_key:
            QMessageBox.warning(
                self,
                tr("admin.support.key.dialog.title"),
                tr("admin.support.msg.key_required"),
            )
            return

        ok, message = apply_supporter_key(self.db, raw_key)
        if not ok:
            QMessageBox.warning(self, tr("admin.support.key.dialog.title"), message)
            return

        self.support_key_input.clear()
        self.refresh_support_tab()
        if hasattr(self, "network_edition_panel"):
            self.network_edition_panel.refresh()
        self._refresh_network_tab()
        self.edition_unlock_changed.emit()
        QMessageBox.information(self, tr("admin.support.key.dialog.title"), message)

    def _clear_support_unlock(self):
        if not has_permission(
            PERM_SETTINGS_MANAGE,
            self.current_user,
        ):
            return

        if unlocked_edition(self.db) is None:
            return

        answer = QMessageBox.question(
            self,
            tr("admin.support.msg.clear_title"),
            tr("admin.support.msg.clear_confirm"),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        clear_edition_unlock(self.db)
        self.refresh_support_tab()
        if hasattr(self, "network_edition_panel"):
            self.network_edition_panel.refresh()
        self._refresh_network_tab()
        self.edition_unlock_changed.emit()
        QMessageBox.information(
            self,
            tr("admin.support.msg.cleared_title"),
            tr("admin.support.msg.cleared"),
        )

    def _open_support_donation_link(self):
        url = (SUPPORT_DONATION_URL or "").strip()
        if not url:
            return
        QDesktopServices.openUrl(QUrl(url))

    def _build_system_tab(self):
        tab, layout = self._new_tab()

        self.updates_section = QWidget()
        updates_section_layout = QVBoxLayout(self.updates_section)
        updates_section_layout.setContentsMargins(0, 0, 0, 0)
        updates_section_layout.setSpacing(8)

        updates_section_layout.addWidget(
            subsection_title(tr("admin.system.section.updates"))
        )
        updates_section_layout.addLayout(hud_divider())

        updates_panel, updates_layout = info_panel()
        updates_layout.setContentsMargins(16, 16, 16, 16)

        self.update_version_label = QLabel()
        self.update_version_label.setObjectName("formLabel")
        self.update_version_label.setWordWrap(True)
        updates_layout.addWidget(self.update_version_label)

        self.update_status_label = QLabel()
        self.update_status_label.setObjectName("mutedLabel")
        self.update_status_label.setWordWrap(True)
        updates_layout.addWidget(self.update_status_label)

        self.update_auto_check = QCheckBox(
            tr("admin.system.updates.auto_check")
        )
        self.update_auto_check.toggled.connect(
            self._save_update_auto_check
        )
        updates_layout.addWidget(self.update_auto_check)

        update_action_row = QHBoxLayout()
        self.update_check_button = primary_button(
            tr("admin.system.updates.check_button")
        )
        self.update_check_button.clicked.connect(
            self.check_updates_clicked
        )
        update_action_row.addWidget(self.update_check_button)
        update_action_row.addStretch()
        updates_layout.addLayout(update_action_row)

        update_hint = QLabel(
            tr("admin.system.updates.hint")
        )
        update_hint.setObjectName("mutedLabel")
        update_hint.setWordWrap(True)
        updates_layout.addWidget(update_hint)

        updates_section_layout.addWidget(updates_panel)
        layout.addWidget(self.updates_section)

        self.login_history_section = QWidget()
        login_history_layout = QVBoxLayout(
            self.login_history_section
        )
        login_history_layout.setContentsMargins(0, 0, 0, 0)
        login_history_layout.setSpacing(8)

        login_history_layout.addWidget(
            subsection_title(tr("admin.system.section.login_history"))
        )

        history_panel, history_layout = page_panel()
        history_layout.setContentsMargins(12, 12, 12, 12)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels([
            tr("admin.system.history.col.id"),
            tr("admin.system.history.col.user"),
            tr("admin.system.history.col.login"),
            tr("admin.system.history.col.logout"),
        ])
        configure_mobiglas_table(
            self.history_table,
            "dataTable",
        )
        self.history_table.setMinimumHeight(220)

        self.history_empty_panel = empty_info_panel(
            tr("admin.system.history.empty"),
            "assets/images/icons/info.svg",
        )

        history_layout.addWidget(self.history_table)
        history_layout.addWidget(self.history_empty_panel)
        self.history_empty_panel.hide()
        login_history_layout.addWidget(history_panel)

        layout.addWidget(self.login_history_section)

        self.datensicherung_section = QWidget()
        datensicherung_layout = QVBoxLayout(
            self.datensicherung_section
        )
        datensicherung_layout.setContentsMargins(0, 0, 0, 0)
        datensicherung_layout.setSpacing(8)

        datensicherung_layout.addWidget(
            subsection_title(tr("admin.system.section.backup"))
        )
        datensicherung_layout.addLayout(hud_divider())

        data_panel, data_layout = page_panel()
        data_layout.setContentsMargins(12, 12, 12, 12)

        self.data_health_label = QLabel()
        data_layout.addWidget(self.data_health_label)

        self.data_summary_label = QLabel()
        self.data_summary_label.setWordWrap(True)
        self.data_summary_label.setTextFormat(
            Qt.TextFormat.RichText
        )
        data_layout.addWidget(self.data_summary_label)

        main_action_row = QHBoxLayout()
        main_action_row.setSpacing(8)

        self.create_backup_button = primary_button(
            tr("admin.system.backup.create")
        )
        self.create_backup_button.clicked.connect(
            self.create_backup_clicked
        )
        main_action_row.addWidget(self.create_backup_button)

        self.restore_backup_button = _secondary_button(
            tr("admin.system.backup.restore")
        )
        self.restore_backup_button.clicked.connect(
            self.restore_backup_clicked
        )
        main_action_row.addWidget(self.restore_backup_button)

        self.open_backup_folder_button = _secondary_button(
            tr("admin.system.backup.open_folder")
        )
        self.open_backup_folder_button.clicked.connect(
            self.open_backup_folder_clicked
        )
        main_action_row.addWidget(
            self.open_backup_folder_button
        )

        main_action_row.addStretch()
        data_layout.addLayout(main_action_row)

        self.backups_table = QTableWidget()
        self.backups_table.setColumnCount(2)
        self.backups_table.setHorizontalHeaderLabels([
            tr("admin.system.backup.col.created"),
            tr("admin.system.backup.col.size"),
        ])
        configure_mobiglas_table(
            self.backups_table,
            "dataTable",
        )
        self.backups_table.setMinimumHeight(180)
        self.backups_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.backups_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        self.backups_empty_panel = empty_info_panel(
            tr("admin.system.backup.empty"),
            "assets/images/icons/info.svg",
        )

        data_layout.addWidget(self.backups_table)
        data_layout.addWidget(self.backups_empty_panel)
        self.backups_empty_panel.hide()

        secondary_action_row = QHBoxLayout()
        secondary_action_row.setSpacing(8)

        self.delete_backup_button = _secondary_button(
            tr("admin.system.backup.delete")
        )
        self.delete_backup_button.clicked.connect(
            self.delete_backup_clicked
        )
        secondary_action_row.addWidget(self.delete_backup_button)
        secondary_action_row.addStretch()
        data_layout.addLayout(secondary_action_row)

        (
            self.danger_zone_toggle,
            self.danger_zone_content,
            danger_layout,
        ) = self._make_collapsible_block(tr("admin.system.backup.danger_zone"))

        danger_hint = QLabel(
            tr("admin.system.backup.danger_hint")
        )
        danger_hint.setObjectName("mutedLabel")
        danger_hint.setWordWrap(True)
        danger_layout.addWidget(danger_hint)

        self.reinitialize_database_button = _secondary_button(
            tr("admin.system.backup.reinitialize")
        )
        self.reinitialize_database_button.clicked.connect(
            self.reinitialize_database_clicked
        )
        danger_layout.addWidget(
            self.reinitialize_database_button,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )

        data_layout.addWidget(self.danger_zone_toggle)
        data_layout.addWidget(self.danger_zone_content)

        (
            self.advanced_support_toggle,
            self.advanced_support_content,
            advanced_layout,
        ) = self._make_collapsible_block(
            tr("admin.system.backup.advanced")
        )

        self.db_advanced_status_label = QLabel()
        self.db_advanced_status_label.setObjectName("mutedLabel")
        self.db_advanced_status_label.setWordWrap(True)
        advanced_layout.addWidget(
            self.db_advanced_status_label
        )

        advanced_button_row = QHBoxLayout()
        advanced_button_row.setSpacing(8)

        self.verify_database_button = _secondary_button(
            tr("admin.system.backup.verify")
        )
        self.verify_database_button.clicked.connect(
            self.verify_database_clicked
        )
        advanced_button_row.addWidget(
            self.verify_database_button
        )

        self.rerun_migrations_button = _secondary_button(
            tr("admin.system.backup.migrate")
        )
        self.rerun_migrations_button.clicked.connect(
            self.rerun_migrations_clicked
        )
        advanced_button_row.addWidget(
            self.rerun_migrations_button
        )

        advanced_button_row.addStretch()
        advanced_layout.addLayout(advanced_button_row)

        retention_row = QHBoxLayout()
        retention_row.setSpacing(12)

        retention_label = QLabel(
            tr("admin.system.backup.retention")
        )
        retention_label.setObjectName("mutedLabel")
        retention_row.addWidget(retention_label)

        self.backup_max_count_spin = QSpinBox()
        self.backup_max_count_spin.setMinimumWidth(72)
        self.backup_max_count_spin.setRange(
            1,
            DEFAULT_BACKUP_MAX_COUNT,
        )
        retention_row.addWidget(self.backup_max_count_spin)

        self.save_backup_settings_button = _secondary_button(tr("common.save"))
        self.save_backup_settings_button.clicked.connect(
            self.save_backup_settings_clicked
        )
        retention_row.addWidget(
            self.save_backup_settings_button
        )
        retention_row.addStretch()
        advanced_layout.addLayout(retention_row)

        retention_hint = QLabel(
            tr("admin.system.backup.retention_hint")
        )
        retention_hint.setObjectName("mutedLabel")
        retention_hint.setWordWrap(True)
        advanced_layout.addWidget(retention_hint)

        data_layout.addWidget(self.advanced_support_toggle)
        data_layout.addWidget(self.advanced_support_content)

        datensicherung_layout.addWidget(data_panel)
        layout.addWidget(self.datensicherung_section)
        layout.addStretch()

        return tab

    def apply_permissions(
        self,
        user,
        page_name="settings",
    ):
        self.current_user = user

        can_users = has_permission(
            PERM_USERS_MANAGE,
            user,
        )
        can_roles = has_permission(
            PERM_ROLES_MANAGE,
            user,
        )
        can_reset = has_permission(
            PERM_DATABASE_RESET,
            user,
        )
        can_settings = has_permission(
            PERM_SETTINGS_MANAGE,
            user,
        )

        users_index = self.tabs.indexOf(self.users_tab)
        roles_index = self.tabs.indexOf(self.roles_tab)
        design_index = self.tabs.indexOf(self.design_tab)
        system_index = self.tabs.indexOf(self.system_tab)

        self.tabs.setTabVisible(users_index, can_users)
        self.tabs.setTabVisible(roles_index, can_roles)
        self.tabs.setTabVisible(design_index, True)
        self.tabs.setTabVisible(
            system_index,
            can_users or can_reset,
        )

        self.app_defaults_panel.setVisible(can_settings)
        self.save_app_defaults_button.setEnabled(
            can_settings
        )
        self.app_theme_combo.setEnabled(can_settings)
        if hasattr(self, "support_apply_key_button"):
            self.support_apply_key_button.setEnabled(can_settings)
            self.support_key_input.setEnabled(can_settings)
            self.support_clear_key_button.setEnabled(
                can_settings and unlocked_edition(self.db) is not None
            )
        if hasattr(self, "design_sub_tabs") and hasattr(
            self,
            "design_org_page",
        ):
            org_index = self.design_sub_tabs.indexOf(
                self.design_org_page
            )
            if org_index >= 0:
                self.design_sub_tabs.setTabVisible(
                    org_index,
                    can_settings,
                )

        self.load_design_settings()

        user_buttons = (
            self.edit_display_name_button,
            self.reset_password_button,
            self.change_role_button,
            self.toggle_active_button,
            self.delete_user_button,
            self.create_user_button,
        )

        for button in user_buttons:
            button.setEnabled(can_users)

        for field in (
            self.new_username,
            self.new_display_name,
            self.new_password,
            self.new_role_combo,
        ):
            field.setEnabled(can_users)

        self.users_table.setEnabled(can_users)

        role_buttons = (
            self.create_role_button,
            self.edit_role_button,
            self.edit_permissions_button,
            self.delete_role_button,
        )

        for button in role_buttons:
            button.setEnabled(can_roles)

        self.view_role_button.setEnabled(
            can_roles or can_users
        )
        self.roles_table.setEnabled(
            can_roles or can_users
        )

        self.history_table.setEnabled(can_users)

        for button in (
            self.verify_database_button,
            self.rerun_migrations_button,
            self.reinitialize_database_button,
            self.create_backup_button,
            self.restore_backup_button,
            self.open_backup_folder_button,
            self.delete_backup_button,
            self.save_backup_settings_button,
        ):
            button.setEnabled(can_reset)

        self.backup_max_count_spin.setEnabled(can_reset)
        self.backups_table.setEnabled(can_reset)

        if hasattr(self, "login_history_section"):
            self.login_history_section.setVisible(can_users)

        if hasattr(self, "datensicherung_section"):
            self.datensicherung_section.setVisible(can_reset)

        self.refresh_language_settings()

        if can_users and not can_roles:
            self.tabs.setCurrentWidget(self.users_tab)
        elif can_roles and not can_users:
            self.tabs.setCurrentWidget(self.roles_tab)
        elif not can_users and not can_roles:
            self.tabs.setCurrentWidget(self.design_tab)

    def load_role_combos(self):
        self.new_role_combo.clear()

        for role in self._assignable_roles():
            self.new_role_combo.addItem(
                role[1],
                role[0],
            )

    def _grantable_permissions(self):
        if not self.current_user:
            return set()

        return self.db.permissions.get_actor_permissions(
            self.current_user
        )

    def _assignable_roles(self):
        roles = self.db.get_roles()

        if not self.current_user or is_administrator(
            self.current_user
        ):
            return roles

        assignable = []

        for role in roles:
            role_id = role[0]
            role_name = role[1]

            if role_name == ROLE_ADMIN:
                continue

            role_perms = (
                self.db.permissions.get_permissions_for_role(
                    role_id
                )
            )
            actor_grantable = (
                self.db.permissions.get_actor_permissions(
                    self.current_user
                )
            )

            if role_permissions_exceed_actor(
                self.current_user,
                role_perms,
                actor_grantable=actor_grantable,
            ):
                continue

            assignable.append(role)

        return assignable

    def _sync_current_user_session(self):
        main = self.window()

        if not main or not hasattr(
            main,
            "refresh_current_user_from_db",
        ):
            return False

        if not main.refresh_current_user_from_db():
            return False

        self.current_user = main.current_user
        self.apply_permissions(
            self.current_user,
            "settings",
        )
        return True

    def refresh_users(self):
        users = self.db.get_all_users()
        has_users = len(users) > 0

        self.users_table.setVisible(has_users)
        self.users_empty_panel.setVisible(not has_users)
        self.users_table.setRowCount(len(users))

        for row, user in enumerate(users):
            self.users_table.setItem(
                row,
                0,
                QTableWidgetItem(user[1]),
            )
            self.users_table.setItem(
                row,
                1,
                QTableWidgetItem(user[2]),
            )
            self.users_table.setItem(
                row,
                2,
                QTableWidgetItem(user[3]),
            )
            self.users_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    tr("common.yes") if user[4] else tr("common.no")
                ),
            )
            self.users_table.item(row, 3).setData(
                Qt.ItemDataRole.UserRole,
                bool(user[4]),
            )
            self.users_table.setItem(
                row,
                4,
                QTableWidgetItem(
                    format_datetime(user[5])
                ),
            )
            self.users_table.item(
                row,
                0,
            ).setData(256, user[0])

        finalize_table_columns(self.users_table)

    def refresh_roles(self):
        roles = (
            self.db.permissions.get_roles_with_permission_counts()
        )
        has_roles = len(roles) > 0

        self.roles_table.setVisible(has_roles)
        self.roles_empty_panel.setVisible(not has_roles)
        self.roles_table.setRowCount(len(roles))

        for row, role in enumerate(roles):
            self.roles_table.setItem(
                row,
                0,
                QTableWidgetItem(role["role_name"]),
            )
            self.roles_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    role["description"] or "—"
                ),
            )
            self.roles_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    str(role["permission_count"])
                ),
            )
            self.roles_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    str(role["user_count"])
                ),
            )
            self.roles_table.item(
                row,
                0,
            ).setData(256, role["id"])
            self.roles_table.item(
                row,
                0,
            ).setData(257, role["role_name"])

        finalize_table_columns(self.roles_table)
        self.load_role_combos()

    def refresh_login_history(self):
        history = self.db.get_login_history()
        has_history = len(history) > 0

        self.history_table.setVisible(has_history)
        self.history_empty_panel.setVisible(not has_history)
        self.history_table.setRowCount(len(history))

        for row, entry in enumerate(history):
            self.history_table.setItem(
                row,
                0,
                QTableWidgetItem(str(entry[0])),
            )
            self.history_table.setItem(
                row,
                1,
                QTableWidgetItem(entry[1] or "-"),
            )
            self.history_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    format_datetime(entry[2])
                ),
            )
            self.history_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    format_datetime(entry[3])
                ),
            )

        finalize_table_columns(self.history_table)

    def refresh_data(self):
        self.refresh_users()
        self.refresh_roles()
        self.refresh_login_history()
        self.refresh_datensicherung()
        self.refresh_updates_section()
        self._refresh_network_tab()
        self.refresh_language_settings()

    def selected_user_id(self):
        row = self.users_table.currentRow()

        if row < 0:
            return None

        item = self.users_table.item(row, 0)

        if not item:
            return None

        return item.data(256)

    def selected_role(self):
        row = self.roles_table.currentRow()

        if row < 0:
            return None

        name_item = self.roles_table.item(row, 0)

        if not name_item:
            return None

        desc_item = self.roles_table.item(row, 1)

        return {
            "id": name_item.data(256),
            "role_name": name_item.data(257),
            "description": (
                desc_item.text()
                if desc_item and desc_item.text() != "—"
                else ""
            ),
        }

    def create_user(self):
        username = self.new_username.text().strip()
        display_name = (
            self.new_display_name.text().strip()
            or username
        )
        password = self.new_password.text().strip()
        role_id = self.new_role_combo.currentData()

        if not username:
            QMessageBox.warning(
                self,
                tr("admin.users.dialog.title"),
                tr("admin.users.msg.username_required"),
            )
            return

        if not password:
            QMessageBox.warning(
                self,
                tr("admin.users.dialog.title"),
                tr("admin.users.msg.password_required"),
            )
            return

        if role_id is None:
            QMessageBox.warning(
                self,
                tr("admin.users.dialog.title"),
                tr("admin.users.msg.role_required"),
            )
            return

        try:
            self.db.create_user(
                username,
                password,
                role_id,
                display_name=display_name,
            )
        except ValueError as error:
            QMessageBox.warning(
                self,
                "Benutzer",
                str(error),
            )
            return
        except Exception:
            QMessageBox.warning(
                self,
                tr("admin.users.dialog.title"),
                tr("admin.users.msg.create_failed"),
            )
            return

        self.new_username.clear()
        self.new_display_name.clear()
        self.new_password.clear()
        self.refresh_data()

        QMessageBox.information(
            self,
            tr("admin.users.dialog.title"),
            tr("admin.users.msg.created"),
        )

    def edit_display_name(self):
        user_id = self.selected_user_id()

        if not user_id:
            QMessageBox.warning(
                self,
                tr("admin.users.dialog.title"),
                tr("admin.users.msg.select_user"),
            )
            return

        row = self.users_table.currentRow()
        current = self.users_table.item(row, 1).text()

        name, ok = MobiglasTextInputDialog.get_text(
            self,
            tr("admin.users.msg.display_name_title"),
            tr("admin.users.msg.display_name_prompt"),
            QLineEdit.EchoMode.Normal,
            current,
        )

        if not ok or not name.strip():
            return

        self.db.update_user_display_name(
            user_id,
            name.strip(),
        )
        self.refresh_users()

    def reset_password(self):
        user_id = self.selected_user_id()

        if not user_id:
            QMessageBox.warning(
                self,
                tr("admin.users.dialog.title"),
                tr("admin.users.msg.select_user"),
            )
            return

        password, ok = MobiglasTextInputDialog.get_text(
            self,
            tr("admin.users.msg.reset_password_title"),
            tr("admin.users.msg.reset_password_prompt"),
            QLineEdit.EchoMode.Password,
        )

        if not ok or not password:
            return

        self.db.reset_user_password(
            user_id,
            password,
        )

        QMessageBox.information(
            self,
            tr("admin.users.dialog.title"),
            tr("admin.users.msg.password_reset"),
        )

    def change_role(self):
        user_id = self.selected_user_id()

        if not user_id:
            QMessageBox.warning(
                self,
                tr("admin.users.dialog.title"),
                tr("admin.users.msg.select_user"),
            )
            return

        roles = self._assignable_roles()

        if not roles:
            QMessageBox.warning(
                self,
                tr("admin.users.dialog.title"),
                tr("admin.users.msg.no_assignable_roles"),
            )
            return

        role_names = [role[1] for role in roles]
        current_row = self.users_table.currentRow()
        current_role = self.users_table.item(
            current_row,
            2,
        ).text()

        default_index = (
            role_names.index(current_role)
            if current_role in role_names
            else 0
        )

        role_name, ok = MobiglasItemInputDialog.get_item(
            self,
            tr("admin.users.msg.assign_role_title"),
            tr("admin.users.msg.assign_role_prompt"),
            role_names,
            default_index,
            False,
        )

        if not ok:
            return

        role_id = next(
            role[0]
            for role in roles
            if role[1] == role_name
        )

        try:
            self.db.update_user_role(
                user_id,
                role_id,
            )
        except ValueError as error:
            QMessageBox.warning(
                self,
                "Benutzer",
                str(error),
            )
            return

        if (
            self.current_user
            and self.current_user.get("id") == user_id
        ):
            self._sync_current_user_session()
            QMessageBox.information(
                self,
                tr("admin.users.dialog.title"),
                tr("admin.users.msg.role_updated"),
            )

        self.refresh_data()

    def toggle_user_active(self):
        user_id = self.selected_user_id()

        if not user_id:
            QMessageBox.warning(
                self,
                tr("admin.users.dialog.title"),
                tr("admin.users.msg.select_user"),
            )
            return

        row = self.users_table.currentRow()
        is_active = bool(
            self.users_table.item(row, 3).data(
                Qt.ItemDataRole.UserRole
            )
        )

        self.db.set_user_active(
            user_id,
            0 if is_active else 1,
        )
        self.refresh_users()

    def delete_user(self):
        user_id = self.selected_user_id()

        if not user_id:
            QMessageBox.warning(
                self,
                tr("admin.users.dialog.title"),
                tr("admin.users.msg.select_user"),
            )
            return

        answer = QMessageBox.question(
            self,
            tr("admin.users.msg.delete_title"),
            tr("admin.users.msg.delete_confirm"),
        )

        if answer != QMessageBox.Yes:
            return

        self.db.delete_user(user_id)
        self.refresh_data()

    def create_role(self):
        dialog = RoleEditDialog(
            parent=self,
            permissions=[],
            grantable_permissions=sorted(
                self._grantable_permissions()
            ),
        )

        if dialog.exec() != RoleEditDialog.DialogCode.Accepted:
            return

        data = dialog.result_data()

        try:
            role_id = self.db.permissions.create_role(
                data["role_name"],
                data["description"],
            )
            self.db.permissions.set_role_permissions(
                role_id,
                data["permissions"],
            )
        except Exception as error:
            QMessageBox.warning(
                self,
                tr("admin.roles.dialog.title"),
                tr("admin.roles.msg.create_failed", error=error),
            )
            return

        self.refresh_data()

        QMessageBox.information(
            self,
            tr("admin.roles.dialog.title"),
            tr("admin.roles.msg.created", name=data["role_name"]),
        )

    def edit_role(self):
        role = self.selected_role()

        if not role:
            QMessageBox.warning(
                self,
                tr("admin.roles.dialog.title"),
                tr("admin.roles.msg.select_role"),
            )
            return

        if role["role_name"] == ROLE_ADMIN:
            QMessageBox.information(
                self,
                tr("admin.roles.dialog.title"),
                tr("admin.roles.msg.admin_locked_short"),
            )
            return

        permissions = (
            self.db.permissions.get_role_permissions(
                role["id"]
            )
        )

        dialog = RoleEditDialog(
            parent=self,
            role=role,
            permissions=permissions,
            grantable_permissions=sorted(
                self._grantable_permissions()
            ),
        )

        if dialog.exec() != RoleEditDialog.DialogCode.Accepted:
            return

        data = dialog.result_data()

        try:
            self.db.permissions.update_role(
                role["id"],
                role_name=data["role_name"],
                description=data["description"],
            )
            self.db.permissions.set_role_permissions(
                role["id"],
                data["permissions"],
            )
        except Exception as error:
            QMessageBox.warning(
                self,
                tr("admin.roles.dialog.title"),
                tr("admin.roles.msg.save_failed", error=error),
            )
            return

        self.refresh_data()

        if (
            self.current_user
            and self.current_user.get("role_id") == role["id"]
        ):
            self._sync_current_user_session()
            QMessageBox.information(
                self,
                tr("admin.roles.dialog.title"),
                tr("admin.roles.msg.permissions_reloaded"),
            )

    def edit_role_permissions(self):
        self.edit_role()

    def _on_role_double_clicked(self, index):
        if not index.isValid():
            return

        self.roles_table.selectRow(index.row())
        self.edit_role()

    def view_role_permissions(self):
        role = self.selected_role()

        if not role:
            QMessageBox.warning(
                self,
                tr("admin.roles.dialog.title"),
                tr("admin.roles.msg.select_role"),
            )
            return

        permissions = (
            self.db.permissions.get_role_permissions(
                role["id"]
            )
        )

        dialog = RoleEditDialog(
            parent=self,
            role=role,
            permissions=permissions,
            read_only=True,
        )
        dialog.exec()

    def delete_role(self):
        role = self.selected_role()

        if not role:
            QMessageBox.warning(
                self,
                tr("admin.roles.dialog.title"),
                tr("admin.roles.msg.select_role"),
            )
            return

        answer = QMessageBox.question(
            self,
            tr("admin.roles.msg.delete_title"),
            tr("admin.roles.msg.delete_confirm", name=role["role_name"]),
        )

        if answer != QMessageBox.Yes:
            return

        try:
            self.db.permissions.delete_role(role["id"])
        except Exception as error:
            QMessageBox.warning(
                self,
                tr("admin.roles.dialog.title"),
                str(error),
            )
            return

        self.refresh_data()

    def refresh_datensicherung(self):
        if not hasattr(self, "data_summary_label"):
            return

        try:
            status = self.db.get_schema_status()
            backup = self.db.get_database_backup_status()
        except Exception:
            self.data_health_label.setText(
                tr("admin.system.backup.status.load_failed")
            )
            self.data_summary_label.setText("")
            return

        if status.get("migration_needed"):
            self.data_health_label.setText(
                tr("admin.system.backup.status.needs_check")
            )
            self.data_health_label.setObjectName(
                "warningBannerTitle"
            )
        else:
            self.data_health_label.setText(
                tr("admin.system.backup.status.ok")
            )
            self.data_health_label.setObjectName("formLabel")

        latest = backup.get("latest_backup")
        latest_label = "—"

        if latest:
            latest_label = latest.get("created_at", "—")

        max_count = backup.get("max_backup_count", 20)
        backup_count = backup.get("backup_count", 0)

        self.data_summary_label.setText(
            tr(
                "admin.system.backup.summary",
                version=APP_VERSION,
                count=backup_count,
                max_count=max_count,
                latest=latest_label,
            )
        )
        self.data_health_label.style().unpolish(
            self.data_health_label
        )
        self.data_health_label.style().polish(
            self.data_health_label
        )

        if hasattr(self, "db_advanced_status_label"):
            db_path = status.get("database_path") or "—"
            backup_dir = backup.get("backup_directory") or "—"

            self.db_advanced_status_label.setText(
                tr(
                    "admin.system.backup.advanced_status",
                    build=status.get("build_version", "—"),
                    schema=status.get("schema_version", "—"),
                    target_schema=status.get(
                        "target_schema_version",
                        "—",
                    ),
                    db_path=db_path,
                    backup_dir=backup_dir,
                )
            )

        self.refresh_backup_settings()
        self.refresh_backup_list()

    def refresh_backup_settings(self):
        if not hasattr(self, "backup_max_count_spin"):
            return

        try:
            status = self.db.get_database_backup_status()
        except Exception:
            return

        self.backup_max_count_spin.blockSignals(True)
        self.backup_max_count_spin.setValue(
            status.get(
                "max_backup_count",
                DEFAULT_BACKUP_MAX_COUNT,
            )
        )
        self.backup_max_count_spin.blockSignals(False)

    def save_backup_settings_clicked(self):
        try:
            current = self.db.get_database_backup_status()
            result = self.db.save_database_backup_settings(
                max_count=self.backup_max_count_spin.value(),
                auto_before_reset=current.get(
                    "auto_before_reset",
                    True,
                ),
                auto_before_restore=current.get(
                    "auto_before_restore",
                    True,
                ),
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                tr("admin.system.settings.dialog.title"),
                tr("admin.system.settings.msg.save_failed", error=error),
            )
            return

        removed_note = ""
        removed = result.get("removed_count", 0)

        if removed:
            removed_note = tr(
                "admin.system.backup.msg.removed_note",
                count=removed,
            )

        QMessageBox.information(
            self,
            tr("admin.system.settings.dialog.title"),
            tr("admin.system.settings.msg.saved") + removed_note,
        )
        self.refresh_datensicherung()

    def refresh_backup_list(self):
        if not hasattr(self, "backups_table"):
            return

        try:
            backups = self.db.list_database_backups()
        except Exception:
            self.backups_table.setRowCount(0)
            self.backups_table.hide()
            self.backups_empty_panel.show()
            return

        has_backups = len(backups) > 0
        self.backups_table.setVisible(has_backups)
        self.backups_empty_panel.setVisible(not has_backups)
        self.backups_table.setRowCount(len(backups))

        for row, entry in enumerate(backups):
            created_at = entry.get("created_at", "")
            created_item = QTableWidgetItem(created_at)
            created_item.setData(
                Qt.ItemDataRole.UserRole,
                entry.get("filename"),
            )
            self.backups_table.setItem(row, 0, created_item)
            self.backups_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    _format_file_size(
                        entry.get("size_bytes", 0)
                    )
                ),
            )

        finalize_table_columns(self.backups_table)

    def selected_backup_filename(self):
        row = self.backups_table.currentRow()

        if row < 0:
            return None

        item = self.backups_table.item(row, 0)

        if not item:
            return None

        return item.data(Qt.ItemDataRole.UserRole)

    def selected_backup_label(self):
        row = self.backups_table.currentRow()

        if row < 0:
            return None

        item = self.backups_table.item(row, 0)

        if not item:
            return None

        return item.text()

    def create_backup_clicked(self):
        try:
            result = self.db.create_database_backup(
                reason="manual",
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                tr("admin.system.backup.dialog.title"),
                tr("admin.system.backup.msg.create_failed", error=error),
            )
            return

        removed = result.get("removed_count", 0)
        removed_note = ""

        if removed:
            removed_note = tr(
                "admin.system.backup.msg.removed_note",
                count=removed,
            )

        QMessageBox.information(
            self,
            tr("admin.system.backup.dialog.title"),
            tr(
                "admin.system.backup.msg.created",
                created_at=result.get("created_at", "—"),
            )
            + removed_note,
        )
        self.refresh_datensicherung()

    def restore_backup_clicked(self):
        filename = self.selected_backup_filename()
        backup_label = self.selected_backup_label()

        if not filename:
            QMessageBox.warning(
                self,
                tr("admin.system.restore.dialog.title"),
                tr("admin.system.restore.msg.select_first"),
            )
            return

        answer = QMessageBox.warning(
            self,
            tr("admin.system.restore.msg.confirm_title"),
            tr(
                "admin.system.restore.msg.confirm_long",
                label=backup_label,
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        try:
            result = self.db.restore_from_backup(filename)
        except Exception as error:
            QMessageBox.critical(
                self,
                tr("admin.system.restore.msg.confirm_title"),
                tr("admin.system.restore.msg.failed", error=error),
            )
            return

        self._notify_main_window_database_changed()

        safety_note = ""

        if result.get("pre_restore_backup"):
            safety_note = tr("admin.system.restore.msg.safety_note")

        QMessageBox.information(
            self,
            tr("admin.system.restore.msg.confirm_title"),
            tr("admin.system.restore.msg.success", label=backup_label)
            + safety_note
            + "\n\n"
            + tr("admin.system.restore.msg.relogin"),
        )
        self.refresh_datensicherung()

    def open_backup_folder_clicked(self):
        try:
            status = self.db.get_database_backup_status()
        except Exception as error:
            QMessageBox.warning(
                self,
                tr("admin.system.backup_folder.dialog.title"),
                str(error),
            )
            return

        folder = Path(status.get("backup_directory", ""))

        if not folder:
            QMessageBox.warning(
                self,
                tr("admin.system.backup_folder.dialog.title"),
                tr("admin.system.backup_folder.msg.unknown"),
            )
            return

        folder.mkdir(parents=True, exist_ok=True)

        if not QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(folder.resolve()))
        ):
            QMessageBox.warning(
                self,
                tr("admin.system.backup_folder.dialog.title"),
                tr(
                    "admin.system.backup_folder.msg.open_failed",
                    folder=folder,
                ),
            )

    def delete_backup_clicked(self):
        filename = self.selected_backup_filename()
        backup_label = self.selected_backup_label()

        if not filename:
            QMessageBox.warning(
                self,
                tr("admin.system.backup_delete.dialog.title"),
                tr("admin.system.backup_delete.msg.select_first"),
            )
            return

        answer = QMessageBox.question(
            self,
            tr("admin.system.backup_delete.dialog.title"),
            tr(
                "admin.system.backup_delete.msg.confirm",
                label=backup_label,
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        try:
            self.db.delete_database_backup(filename)
        except Exception as error:
            QMessageBox.critical(
                self,
                tr("admin.system.backup_delete.dialog.title"),
                tr("admin.system.backup_delete.msg.failed", error=error),
            )
            return

        QMessageBox.information(
            self,
            tr("admin.system.backup_delete.dialog.title"),
            tr(
                "admin.system.backup_delete.msg.success",
                label=backup_label,
            ),
        )
        self.refresh_datensicherung()

    def _notify_main_window_database_changed(self):
        from database.access import get_database, set_database

        db = get_database()
        set_database(db)
        self.db = db

        window = self.window()
        if hasattr(window, "_refresh_page_databases"):
            window._refresh_page_databases()

    def verify_database_clicked(self):
        try:
            result = self.db.verify_database()
        except Exception as error:
            QMessageBox.warning(
                self,
                tr("admin.system.verify.dialog.title"),
                str(error),
            )
            return

        if result.get("ok"):
            QMessageBox.information(
                self,
                tr("admin.system.verify.dialog.title"),
                tr("admin.system.verify.msg.ok"),
            )
        else:
            QMessageBox.warning(
                self,
                tr("admin.system.verify.dialog.title"),
                tr("admin.system.verify.msg.needs_update")
                + "\n\n"
                + tr("admin.system.verify.msg.update_action"),
            )

        self.refresh_datensicherung()

    def rerun_migrations_clicked(self):
        answer = QMessageBox.question(
            self,
            tr("admin.system.migrate.dialog.title"),
            tr("admin.system.migrate.msg.confirm_long"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        try:
            self.db.rerun_migrations()
        except Exception as error:
            QMessageBox.critical(
                self,
                tr("admin.system.migrate.dialog.title"),
                tr("admin.system.migrate.msg.failed", error=error),
            )
            return

        QMessageBox.information(
            self,
            tr("admin.system.migrate.dialog.title"),
            tr("admin.system.migrate.msg.success"),
        )
        self.refresh_datensicherung()

    def reinitialize_database_clicked(self):
        answer = QMessageBox.warning(
            self,
            tr("admin.system.reinitialize.dialog.title"),
            tr("admin.system.reinitialize.msg.confirm_long"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        confirmation, ok = MobiglasTextInputDialog.get_text(
            self,
            tr("admin.system.reinitialize.dialog.title"),
            tr("admin.system.reinitialize.msg.confirm_input"),
        )

        if not ok or confirmation.strip().upper() != "RESET":
            return

        try:
            result = self.db.reinitialize_database()
        except OSError as error:
            QMessageBox.critical(
                self,
                tr("admin.system.reinitialize.dialog.title"),
                tr("admin.system.reinitialize.msg.failed", error=error),
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                tr("admin.system.reinitialize.dialog.title"),
                tr("admin.system.reinitialize.msg.error", error=error),
            )
            return

        self._notify_main_window_database_changed()

        backup_note = ""

        if result.get("pre_reset_backup"):
            backup_note = tr("admin.system.reinitialize.msg.backup_note")

        QMessageBox.information(
            self,
            tr("admin.system.reinitialize.dialog.title"),
            tr("admin.system.reinitialize.msg.success")
            + backup_note
            + "\n\n"
            + tr("admin.system.reinitialize.msg.login_hint"),
        )

        self._restart_application_after_database_reset()

    def _restart_application_after_database_reset(self):
        import auth.session as user_session
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication

        from auth.app_restart import (
            restart_application,
            shutdown_before_restart,
        )
        from auth.remember_me import clear_remember_data

        user_session.clear_session()
        clear_remember_data()

        def _do_restart():
            shutdown_before_restart()
            restart_application()
            app = QApplication.instance()
            if app is not None:
                app.quit()

        QTimer.singleShot(150, _do_restart)
