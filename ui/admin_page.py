from pathlib import Path

from PySide6.QtCore import Qt, QUrl
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
    QInputDialog,
    QTabWidget,
    QLabel,
    QSlider,
    QCheckBox,
    QSpinBox,
    QGroupBox,
)

from ui.mobiglas_color_dialog import MobiglasColorDialog
from config.dates import format_datetime
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
from config.version import APP_VERSION
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
    ANIMATION_LABELS,
    DASHBOARD_LAYOUT_LABELS,
    TRANSPARENCY_OPTIONS,
    DASHBOARD_FONT_SCALE_MIN,
    DASHBOARD_FONT_SCALE_MAX,
)


def _secondary_button(text):
    button = QPushButton(text)
    button.setObjectName("secondaryAction")
    return button


def _format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"

    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"

    return f"{size_bytes / (1024 * 1024):.2f} MB"


class AdminPage(QWidget):

    def __init__(self):
        super().__init__()

        self.db = get_database()
        self.current_user = None

        content, layout = page_content_widget()
        layout.addWidget(page_title("EINSTELLUNGEN"))
        layout.addWidget(
            section_accent("◆ SYSTEM & ORGA-VERWALTUNG")
        )
        layout.addLayout(hud_divider())

        self.tabs = QTabWidget()
        self.tabs.setObjectName("settingsTabs")
        configure_aaa_tabs(self.tabs)

        self.users_tab = self._build_users_tab()
        self.roles_tab = self._build_roles_tab()
        self.design_tab = self._build_design_tab()
        self.network_tab = self._build_network_tab()
        self.system_tab = self._build_system_tab()

        self.tabs.addTab(self.users_tab, "Benutzer")
        self.tabs.addTab(self.roles_tab, "Rollen")
        self.tabs.addTab(self.design_tab, "Design")
        self.tabs.addTab(self.network_tab, "Vernetzung")
        self.tabs.addTab(self.system_tab, "System")

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
            subsection_title("◆ BENUTZERÜBERSICHT")
        )

        table_panel, table_layout = page_panel()
        table_layout.setContentsMargins(12, 12, 12, 12)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels([
            "Benutzername",
            "Anzeigename",
            "Rolle",
            "Aktiv",
            "Erstellt am",
        ])
        configure_mobiglas_table(
            self.users_table,
            "dataTable",
        )
        self.users_table.setMinimumHeight(200)

        self.users_empty_panel = empty_info_panel(
            "Keine Benutzer vorhanden.",
            "assets/images/icons/info.svg",
        )

        table_layout.addWidget(self.users_table)
        table_layout.addWidget(self.users_empty_panel)
        self.users_empty_panel.hide()
        layout.addWidget(table_panel)

        user_actions = QHBoxLayout()
        user_actions.setSpacing(10)

        self.edit_display_name_button = _secondary_button(
            "Anzeigename ändern"
        )
        self.edit_display_name_button.clicked.connect(
            self.edit_display_name
        )
        user_actions.addWidget(
            self.edit_display_name_button
        )

        self.reset_password_button = _secondary_button(
            "Passwort zurücksetzen"
        )
        self.reset_password_button.clicked.connect(
            self.reset_password
        )
        user_actions.addWidget(
            self.reset_password_button
        )

        self.change_role_button = _secondary_button(
            "Rolle zuweisen"
        )
        self.change_role_button.clicked.connect(
            self.change_role
        )
        user_actions.addWidget(
            self.change_role_button
        )

        self.toggle_active_button = _secondary_button(
            "Aktiv / Inaktiv"
        )
        self.toggle_active_button.clicked.connect(
            self.toggle_user_active
        )
        user_actions.addWidget(
            self.toggle_active_button
        )

        self.delete_user_button = _secondary_button(
            "Benutzer löschen"
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
            subsection_title("◆ NEUEN BENUTZER ANLEGEN")
        )
        form_layout.addLayout(hud_divider())

        self.new_username = QLineEdit()
        self.new_username.setPlaceholderText("Benutzername")

        self.new_display_name = QLineEdit()
        self.new_display_name.setPlaceholderText(
            "Anzeigename (optional)"
        )

        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.new_password.setPlaceholderText("Passwort")

        self.new_role_combo = QComboBox()

        for label_text, widget in [
            ("Benutzername", self.new_username),
            ("Anzeigename", self.new_display_name),
            ("Passwort", self.new_password),
            ("Rolle", self.new_role_combo),
        ]:
            add_form_field(
                form_layout,
                label_text,
                widget,
            )

        self.create_user_button = primary_button(
            "Benutzer anlegen"
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
        hint = QLabel(
            "Nur die Rolle „Administrator“ ist vordefiniert. "
            "Lege weitere Rollen an und weise Rechte zu — "
            "z. B. Officer, Member oder Guest für deine ORGA."
        )
        hint.setObjectName("mutedLabel")
        hint.setWordWrap(True)
        hint_layout.addWidget(hint)
        layout.addWidget(hint_panel)

        layout.addWidget(
            subsection_title("◆ ROLLENÜBERSICHT")
        )

        table_panel, table_layout = page_panel()
        table_layout.setContentsMargins(12, 12, 12, 12)

        self.roles_table = QTableWidget()
        self.roles_table.setColumnCount(4)
        self.roles_table.setHorizontalHeaderLabels([
            "Rollenname",
            "Beschreibung",
            "Rechte",
            "Benutzer",
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
            "Noch keine Rollen angelegt. "
            "Klicke auf „Neue Rolle“, um die erste Rolle "
            "für deine ORGA zu erstellen.",
            "assets/images/icons/info.svg",
        )

        table_layout.addWidget(self.roles_table)
        table_layout.addWidget(self.roles_empty_panel)
        self.roles_empty_panel.hide()
        layout.addWidget(table_panel)

        role_actions = QHBoxLayout()
        role_actions.setSpacing(10)

        self.create_role_button = primary_button("Neue Rolle")
        self.create_role_button.clicked.connect(
            self.create_role
        )
        role_actions.addWidget(self.create_role_button)

        self.edit_role_button = _secondary_button("Bearbeiten")
        self.edit_role_button.clicked.connect(
            self.edit_role
        )
        role_actions.addWidget(self.edit_role_button)

        self.edit_permissions_button = _secondary_button(
            "Rechte zuweisen"
        )
        self.edit_permissions_button.clicked.connect(
            self.edit_role_permissions
        )
        role_actions.addWidget(
            self.edit_permissions_button
        )

        self.view_role_button = _secondary_button(
            "Rechte anzeigen"
        )
        self.view_role_button.clicked.connect(
            self.view_role_permissions
        )
        role_actions.addWidget(self.view_role_button)

        self.delete_role_button = _secondary_button(
            "Rolle löschen"
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

        layout.addWidget(
            subsection_title("◆ MEIN DESIGN")
        )
        layout.addLayout(hud_divider())

        user_panel, user_layout = info_panel()
        user_layout.setContentsMargins(16, 16, 16, 16)

        self.theme_combo = QComboBox()
        for theme_id, label in ThemeManager.available_themes():
            self.theme_combo.addItem(label, theme_id)

        self.font_size_combo = QComboBox()
        for key, label in FONT_SIZE_LABELS.items():
            self.font_size_combo.addItem(label, key)

        accent_row = QHBoxLayout()
        self.accent_color_input = QLineEdit()
        self.accent_color_input.setPlaceholderText(
            "Standard (Theme-Akzent)"
        )
        self.accent_color_button = _secondary_button(
            "Farbe wählen"
        )
        self.accent_color_button.clicked.connect(
            self._pick_accent_color
        )
        self.accent_clear_button = _secondary_button(
            "Zurücksetzen"
        )
        self.accent_clear_button.clicked.connect(
            lambda: self.accent_color_input.clear()
        )
        accent_row.addWidget(self.accent_color_input, 1)
        accent_row.addWidget(self.accent_color_button)
        accent_row.addWidget(self.accent_clear_button)

        accent_host = QWidget()
        accent_host.setLayout(accent_row)

        self.transparency_combo = QComboBox()
        for value in TRANSPARENCY_OPTIONS:
            self.transparency_combo.addItem(
                f"{value} %",
                value,
            )

        self.animations_combo = QComboBox()
        for key, label in ANIMATION_LABELS.items():
            self.animations_combo.addItem(label, key)

        for label_text, widget in [
            ("Theme", self.theme_combo),
            ("Schriftgröße", self.font_size_combo),
            ("Akzentfarbe", accent_host),
            ("Transparenz", self.transparency_combo),
            ("Animationen", self.animations_combo),
        ]:
            add_form_field(user_layout, label_text, widget)

        preview_hint = QLabel(
            "Änderungen können mit „Vorschau“ sofort getestet "
            "und mit „Speichern“ dauerhaft übernommen werden. "
            "Die Akzentfarbe ersetzt alle Highlight-Farben "
            "(Türkis, Blau, Orange und Gold)."
        )
        preview_hint.setObjectName("mutedLabel")
        preview_hint.setWordWrap(True)
        user_layout.addWidget(preview_hint)

        action_row = QHBoxLayout()
        self.preview_design_button = _secondary_button(
            "Vorschau"
        )
        self.preview_design_button.clicked.connect(
            self.preview_design_settings
        )
        self.save_design_button = primary_button(
            "Speichern"
        )
        self.save_design_button.clicked.connect(
            self.save_design_settings
        )
        action_row.addWidget(self.preview_design_button)
        action_row.addWidget(self.save_design_button)
        action_row.addStretch()
        user_layout.addLayout(action_row)
        layout.addWidget(user_panel)

        layout.addWidget(subsection_title("◆ DASHBOARD"))
        layout.addLayout(hud_divider())

        dashboard_panel, dashboard_layout = info_panel()
        dashboard_layout.setContentsMargins(16, 16, 16, 16)

        self.dashboard_layout_combo = QComboBox()
        for key, label in DASHBOARD_LAYOUT_LABELS.items():
            self.dashboard_layout_combo.addItem(label, key)

        scale_row = QHBoxLayout()
        (
            self.dashboard_font_scale_slider,
            self.dashboard_font_scale_value,
            scale_host,
        ) = self._make_dashboard_scale_row()
        self.dashboard_font_scale_slider.valueChanged.connect(
            self._on_dashboard_widget_scale_changed
        )

        (
            self.dashboard_title_font_scale_slider,
            self.dashboard_title_font_scale_value,
            title_scale_host,
        ) = self._make_dashboard_scale_row()
        self.dashboard_title_font_scale_slider.valueChanged.connect(
            self._on_dashboard_title_scale_changed
        )

        (
            self.dashboard_button_font_scale_slider,
            self.dashboard_button_font_scale_value,
            button_scale_host,
        ) = self._make_dashboard_scale_row()
        self.dashboard_button_font_scale_slider.valueChanged.connect(
            self._on_dashboard_button_scale_changed
        )

        add_form_field(
            dashboard_layout,
            "Dashboard-Layout",
            self.dashboard_layout_combo,
        )
        add_form_field(
            dashboard_layout,
            "Widgets (KPI & Panels)",
            scale_host,
        )
        add_form_field(
            dashboard_layout,
            "Überschrift (SALVAGE-ÜBERSICHT)",
            title_scale_host,
        )
        add_form_field(
            dashboard_layout,
            "Header-Buttons",
            button_scale_host,
        )

        self.dashboard_font_preview = DashboardFontPreviewWidget()
        dashboard_layout.addWidget(self.dashboard_font_preview)

        dashboard_hint = QLabel(
            "Layout und Schriftgrößen können mit „Vorschau“ "
            "sofort getestet und mit „Speichern“ dauerhaft "
            "übernommen werden. Überschrift, Buttons und "
            "Widgets lassen sich unabhängig voneinander "
            "skalieren."
        )
        dashboard_hint.setObjectName("mutedLabel")
        dashboard_hint.setWordWrap(True)
        dashboard_layout.addWidget(dashboard_hint)

        dashboard_action_row = QHBoxLayout()
        self.preview_dashboard_button = _secondary_button(
            "Vorschau"
        )
        self.preview_dashboard_button.clicked.connect(
            self.preview_dashboard_settings
        )
        self.save_dashboard_button = primary_button(
            "Speichern"
        )
        self.save_dashboard_button.clicked.connect(
            self.save_dashboard_settings
        )
        dashboard_action_row.addWidget(
            self.preview_dashboard_button
        )
        dashboard_action_row.addWidget(
            self.save_dashboard_button
        )
        dashboard_action_row.addStretch()
        dashboard_layout.addLayout(dashboard_action_row)

        layout.addWidget(dashboard_panel)

        self.app_defaults_panel, app_layout = info_panel()
        app_layout.setContentsMargins(16, 16, 16, 16)
        app_layout.addWidget(
            subsection_title("◆ APP-STANDARD (ORGANISATION)")
        )
        app_layout.addLayout(hud_divider())

        app_hint = QLabel(
            "Gilt für alle Benutzer ohne eigene Design-Einstellungen. "
            "Nur für Administratoren."
        )
        app_hint.setObjectName("mutedLabel")
        app_hint.setWordWrap(True)
        app_layout.addWidget(app_hint)

        self.app_theme_combo = QComboBox()
        for theme_id, label in ThemeManager.available_themes():
            self.app_theme_combo.addItem(label, theme_id)

        add_form_field(
            app_layout,
            "Standard-Theme",
            self.app_theme_combo,
        )

        self.save_app_defaults_button = primary_button(
            "App-Standard speichern"
        )
        self.save_app_defaults_button.clicked.connect(
            self.save_app_default_settings
        )
        app_layout.addWidget(self.save_app_defaults_button)
        layout.addWidget(self.app_defaults_panel)

        layout.addStretch()
        return tab

    def _pick_accent_color(self):
        current = self.accent_color_input.text().strip()
        initial = (
            QColor(current)
            if current.startswith("#")
            else QColor("#00D9FF")
        )
        color, accepted = MobiglasColorDialog.get_color(
            self,
            "Akzentfarbe wählen",
            initial=initial,
        )
        if accepted and color.isValid():
            self.accent_color_input.setText(
                color.name().upper()
            )

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
            self.transparency_combo,
            effective.get("transparency"),
        )
        self._set_combo_by_data(
            self.animations_combo,
            effective.get("animations"),
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

        app_settings = self.db.settings.get_app_settings()
        self._set_combo_by_data(
            self.app_theme_combo,
            app_settings.get("theme"),
        )

    def _collect_theme_form(self):
        return {
            "theme": self.theme_combo.currentData(),
            "font_size": self.font_size_combo.currentData(),
            "accent_color": (
                self.accent_color_input.text().strip()
            ),
            "transparency": self.transparency_combo.currentData(),
            "animations": self.animations_combo.currentData(),
        }

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

    def _on_dashboard_title_scale_changed(self, scale):
        scale = ThemeManager.normalize_dashboard_font_scale(
            scale
        )
        self._update_dashboard_scale_label(
            self.dashboard_title_font_scale_value,
            scale,
        )

    def _on_dashboard_button_scale_changed(self, scale):
        scale = ThemeManager.normalize_dashboard_font_scale(
            scale
        )
        self._update_dashboard_scale_label(
            self.dashboard_button_font_scale_value,
            scale,
        )

    def _apply_dashboard_layout(self):
        window = self.window()
        if hasattr(window, "get_dashboard_page"):
            window.get_dashboard_page().apply_dashboard_layout()

    def preview_design_settings(self):
        theme = self._collect_theme_form()
        settings = self._merge_effective_settings(theme)
        ThemeManager.apply_settings(settings)
        QMessageBox.information(
            self,
            "Design",
            "Vorschau angewendet. "
            "Mit „Speichern“ dauerhaft übernehmen.",
        )

    def save_design_settings(self):
        if not self.current_user:
            return

        theme = self._collect_theme_form()
        accent = theme.get("accent_color") or None

        self.db.settings.save_user_settings(
            self.current_user["id"],
            {
                "theme": theme["theme"],
                "font_size": theme["font_size"],
                "accent_color": accent,
                "transparency": theme["transparency"],
                "animations": theme["animations"],
            },
        )
        settings = self._merge_effective_settings(theme)
        ThemeManager.apply_settings(settings)

        QMessageBox.information(
            self,
            "Design",
            "Deine Design-Einstellungen wurden gespeichert.",
        )

    def preview_dashboard_settings(self):
        dashboard = self._collect_dashboard_form()
        settings = self._merge_effective_settings(dashboard)
        ThemeManager.apply_settings(settings)
        self._apply_dashboard_layout()
        QMessageBox.information(
            self,
            "Dashboard",
            "Vorschau angewendet. "
            "Wechsle zum Dashboard, um Layout und Schriftgröße "
            "zu sehen. Mit „Speichern“ dauerhaft übernehmen.",
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
            "Dashboard",
            "Deine Dashboard-Einstellungen wurden gespeichert.",
        )

    def save_app_default_settings(self):
        if not has_permission(
            PERM_SETTINGS_MANAGE,
            self.current_user,
        ):
            QMessageBox.warning(
                self,
                "Design",
                "Keine Berechtigung für App-Standards.",
            )
            return

        theme_id = self.app_theme_combo.currentData()
        self.db.settings.set_app_setting("theme", theme_id)

        QMessageBox.information(
            self,
            "Design",
            "App-Standard wurde gespeichert.",
        )

    def _build_network_tab(self):
        tab, layout = self._new_tab()
        layout.addWidget(subsection_title("◆ CREW"))
        layout.addLayout(hud_divider())

        panel, panel_layout = info_panel()

        hint = QLabel(
            "Crew hosten: Code kopieren und teilen. "
            "Crew beitreten: Code vom Host eingeben. "
            "Mehr ist nicht nötig."
        )
        hint.setWordWrap(True)
        hint.setObjectName("mutedLabel")
        panel_layout.addWidget(hint)

        action_row = QHBoxLayout()
        self.network_host_crew_button = primary_button("Crew hosten")
        self.network_host_crew_button.clicked.connect(
            self._one_click_host_crew
        )
        self.network_join_crew_button = _secondary_button(
            "Crew beitreten"
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
        panel_layout.addWidget(QLabel("Beitrittscode"))
        panel_layout.addWidget(self.network_code_label)

        copy_row = QHBoxLayout()
        self.network_copy_code_button = _secondary_button(
            "Code kopieren"
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
            "Modus",
            self.network_mode_label,
        )
        add_form_field(
            panel_layout,
            "Status",
            self.network_host_status,
        )
        add_form_field(
            panel_layout,
            "Verbundene Crew",
            self.network_clients_label,
        )
        layout.addWidget(panel)

        advanced = QGroupBox("Erweitert (optional)")
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
            "Am Salvage-Relay registrieren"
        )
        self.network_use_relay_checkbox.toggled.connect(
            self._on_network_use_relay_changed
        )
        advanced_layout.addWidget(self.network_use_relay_checkbox)

        self.network_upnp_button = _secondary_button(
            "Internet freigeben (UPnP)"
        )
        self.network_upnp_button.clicked.connect(
            self._try_upnp_port_forward
        )
        advanced_layout.addWidget(self.network_upnp_button)

        host_row = QHBoxLayout()
        self.network_start_host_button = _secondary_button(
            "Host manuell starten"
        )
        self.network_start_host_button.clicked.connect(
            self._start_host_from_settings
        )
        self.network_stop_host_button = _secondary_button(
            "Host stoppen"
        )
        self.network_stop_host_button.clicked.connect(
            self._stop_host_from_settings
        )
        host_row.addWidget(self.network_start_host_button)
        host_row.addWidget(self.network_stop_host_button)
        host_row.addStretch()
        advanced_layout.addLayout(host_row)

        layout.addWidget(advanced)
        layout.addStretch()

        self._refresh_network_tab()
        return tab

    def _one_click_host_crew(self):
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
            message=(
                "Crew-Modus aktiv.\n"
                "Code kopiert — an die Crew schicken."
            ),
        )
        self._refresh_network_tab()
        self._notify_main_window_network_changed()

    def _one_click_join_crew(self):
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
            "Vernetzung",
            "Mit Host verbunden.",
        )

    def _copy_network_join_code(self):
        from network.simple_connect import format_simple_invite
        from ui.clipboard_utils import copy_to_clipboard

        code = self.network_code_label.text().strip()
        if not code or code == "—":
            QMessageBox.warning(
                self,
                "Code",
                "Kein Code — zuerst „Crew hosten“ klicken.",
            )
            return
        copy_to_clipboard(
            format_simple_invite(code),
            self,
            message="Code kopiert.",
        )

    def _refresh_network_tab(self):
        from database.access import get_host_server
        from network.connection_guide import normalize_scenario
        from network.network_state import get_network_state

        if not hasattr(self, "network_mode_label"):
            return

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
            "standalone": "Standalone (lokal)",
            "host": "Host",
            "client": "Client",
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
                relay_status = " · Relay aktiv"
            self.network_host_status.setText(
                f"Läuft · Code {server.join_code}{relay_status}"
            )
            if hasattr(self, "network_code_label"):
                self.network_code_label.setText(server.join_code)
            self.network_clients_label.setText(
                ", ".join(state.connected_clients) or "Keine"
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
            self.network_host_status.setText("Nicht aktiv")
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
                    "Salvage-Relay",
                    "Relay-Registrierung fehlgeschlagen. "
                    "Prüfe Relay-Adresse und ob der Relay-Server läuft.",
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
        self.network_upnp_button.setText("UPnP…")
        try:
            ok, message = try_forward_port(port)
        finally:
            self.network_upnp_button.setEnabled(True)
            self.network_upnp_button.setText(
                "Internet freigeben (UPnP)"
            )

        if ok:
            QMessageBox.information(self, "UPnP", message)
        else:
            QMessageBox.warning(self, "UPnP", message)

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
                message = (
                    "Mit Host verbunden. Die Sitzungs-Seite "
                    "wurde in den Client-Modus umgeschaltet."
                )
            elif state.mode == "host":
                message = (
                    "Host-Modus gespeichert. Starte den Server "
                    "unter Vernetzung, wenn die Crew beitritt."
                )
            else:
                message = "Vernetzungseinstellungen gespeichert."

            QMessageBox.information(
                self,
                "Vernetzung",
                message,
            )

    def _notify_main_window_network_changed(self):
        window = self.window()
        if hasattr(window, "apply_network_mode"):
            window.apply_network_mode()
        elif hasattr(window, "refresh_network_display"):
            window.refresh_network_display()

    def _start_host_from_settings(self, *, silent: bool = False):
        from database.access import get_host_server, set_host_server
        from network.host_server import HostServer

        server = get_host_server()
        if server and server.is_running():
            if not silent:
                QMessageBox.information(
                    self,
                    "Host",
                    "Der Host-Server läuft bereits.",
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
                    "Host",
                    "Host-Server konnte nicht gestartet werden.",
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

    def _build_system_tab(self):
        tab, layout = self._new_tab()

        self.login_history_section = QWidget()
        login_history_layout = QVBoxLayout(
            self.login_history_section
        )
        login_history_layout.setContentsMargins(0, 0, 0, 0)
        login_history_layout.setSpacing(8)

        login_history_layout.addWidget(
            subsection_title("◆ LOGIN-HISTORIE")
        )

        history_panel, history_layout = page_panel()
        history_layout.setContentsMargins(12, 12, 12, 12)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels([
            "ID",
            "Benutzer",
            "Anmeldung",
            "Abmeldung",
        ])
        configure_mobiglas_table(
            self.history_table,
            "dataTable",
        )
        self.history_table.setMinimumHeight(220)

        self.history_empty_panel = empty_info_panel(
            "Noch keine Anmeldungen protokolliert.",
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
            subsection_title("◆ DATENSICHERUNG")
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
            "Jetzt Sicherung erstellen"
        )
        self.create_backup_button.clicked.connect(
            self.create_backup_clicked
        )
        main_action_row.addWidget(self.create_backup_button)

        self.restore_backup_button = _secondary_button(
            "Stand wiederherstellen"
        )
        self.restore_backup_button.clicked.connect(
            self.restore_backup_clicked
        )
        main_action_row.addWidget(self.restore_backup_button)

        self.open_backup_folder_button = _secondary_button(
            "Backup-Ordner öffnen"
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
            "Erstellt",
            "Größe",
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
            "Noch keine Sicherungen vorhanden.",
            "assets/images/icons/info.svg",
        )

        data_layout.addWidget(self.backups_table)
        data_layout.addWidget(self.backups_empty_panel)
        self.backups_empty_panel.hide()

        secondary_action_row = QHBoxLayout()
        secondary_action_row.setSpacing(8)

        self.delete_backup_button = _secondary_button(
            "Sicherung löschen"
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
        ) = self._make_collapsible_block("Gefahrenzone")

        danger_hint = QLabel(
            "Löscht alle Sessions, Jobs, Verkäufe und Benutzer "
            "(außer Standard-Admin). Vorher wird automatisch eine "
            "Sicherung erstellt."
        )
        danger_hint.setObjectName("mutedLabel")
        danger_hint.setWordWrap(True)
        danger_layout.addWidget(danger_hint)

        self.reinitialize_database_button = _secondary_button(
            "Alle Tracker-Daten löschen"
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
            "Erweitert (Support)"
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
            "Speicherstand prüfen"
        )
        self.verify_database_button.clicked.connect(
            self.verify_database_clicked
        )
        advanced_button_row.addWidget(
            self.verify_database_button
        )

        self.rerun_migrations_button = _secondary_button(
            "Datenbank aktualisieren"
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
            "Wie viele Sicherungen behalten?"
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

        self.save_backup_settings_button = _secondary_button(
            "Speichern"
        )
        self.save_backup_settings_button.clicked.connect(
            self.save_backup_settings_clicked
        )
        retention_row.addWidget(
            self.save_backup_settings_button
        )
        retention_row.addStretch()
        advanced_layout.addLayout(retention_row)

        retention_hint = QLabel(
            "Älteste Sicherungen werden gelöscht, wenn das Limit "
            "erreicht ist. Vor dem Löschen und Zurückladen wird "
            "automatisch gesichert."
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
                    "Ja" if user[4] else "Nein"
                ),
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
        self._refresh_network_tab()

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
                "Benutzer",
                "Bitte Benutzername eingeben.",
            )
            return

        if not password:
            QMessageBox.warning(
                self,
                "Benutzer",
                "Bitte Passwort eingeben.",
            )
            return

        if role_id is None:
            QMessageBox.warning(
                self,
                "Benutzer",
                "Bitte zuerst eine Rolle anlegen und zuweisen.",
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
                "Benutzer",
                "Benutzer konnte nicht angelegt werden. "
                "Der Name existiert möglicherweise bereits.",
            )
            return

        self.new_username.clear()
        self.new_display_name.clear()
        self.new_password.clear()
        self.refresh_data()

        QMessageBox.information(
            self,
            "Benutzer",
            "Benutzer wurde angelegt.",
        )

    def edit_display_name(self):
        user_id = self.selected_user_id()

        if not user_id:
            QMessageBox.warning(
                self,
                "Benutzer",
                "Bitte einen Benutzer auswählen.",
            )
            return

        row = self.users_table.currentRow()
        current = self.users_table.item(row, 1).text()

        name, ok = QInputDialog.getText(
            self,
            "Anzeigename",
            "Neuer Anzeigename:",
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
                "Benutzer",
                "Bitte einen Benutzer auswählen.",
            )
            return

        password, ok = QInputDialog.getText(
            self,
            "Passwort zurücksetzen",
            "Neues Passwort:",
            QLineEdit.Password,
        )

        if not ok or not password:
            return

        self.db.reset_user_password(
            user_id,
            password,
        )

        QMessageBox.information(
            self,
            "Benutzer",
            "Passwort wurde zurückgesetzt.",
        )

    def change_role(self):
        user_id = self.selected_user_id()

        if not user_id:
            QMessageBox.warning(
                self,
                "Benutzer",
                "Bitte einen Benutzer auswählen.",
            )
            return

        roles = self._assignable_roles()

        if not roles:
            QMessageBox.warning(
                self,
                "Benutzer",
                "Keine zuweisbaren Rollen vorhanden.",
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

        role_name, ok = QInputDialog.getItem(
            self,
            "Rolle zuweisen",
            "Rolle:",
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
                "Benutzer",
                "Deine Rolle wurde aktualisiert. "
                "Navigation und Rechte sind angepasst.",
            )

        self.refresh_data()

    def toggle_user_active(self):
        user_id = self.selected_user_id()

        if not user_id:
            QMessageBox.warning(
                self,
                "Benutzer",
                "Bitte einen Benutzer auswählen.",
            )
            return

        row = self.users_table.currentRow()
        is_active = (
            self.users_table.item(row, 3).text() == "Ja"
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
                "Benutzer",
                "Bitte einen Benutzer auswählen.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Benutzer löschen",
            "Benutzer wirklich löschen?",
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
                "Rolle",
                f"Rolle konnte nicht angelegt werden:\n{error}",
            )
            return

        self.refresh_data()

        QMessageBox.information(
            self,
            "Rolle",
            f"Rolle „{data['role_name']}“ wurde angelegt.",
        )

    def edit_role(self):
        role = self.selected_role()

        if not role:
            QMessageBox.warning(
                self,
                "Rolle",
                "Bitte eine Rolle auswählen.",
            )
            return

        if role["role_name"] == ROLE_ADMIN:
            QMessageBox.information(
                self,
                "Rolle",
                "Die Administrator-Rolle ist "
                "systemseitig festgelegt.",
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
                "Rolle",
                f"Rolle konnte nicht gespeichert werden:\n{error}",
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
                "Rolle",
                "Deine Rechte wurden aus der Datenbank "
                "neu geladen.",
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
                "Rolle",
                "Bitte eine Rolle auswählen.",
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
                "Rolle",
                "Bitte eine Rolle auswählen.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Rolle löschen",
            f"Rolle „{role['role_name']}“ wirklich löschen?",
        )

        if answer != QMessageBox.Yes:
            return

        try:
            self.db.permissions.delete_role(role["id"])
        except Exception as error:
            QMessageBox.warning(
                self,
                "Rolle",
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
                "Status konnte nicht geladen werden"
            )
            self.data_summary_label.setText("")
            return

        if status.get("migration_needed"):
            self.data_health_label.setText(
                "Speicherstand sollte geprüft werden"
            )
            self.data_health_label.setObjectName(
                "warningBannerTitle"
            )
        else:
            self.data_health_label.setText("Alles in Ordnung")
            self.data_health_label.setObjectName("formLabel")

        latest = backup.get("latest_backup")
        latest_label = "—"

        if latest:
            latest_label = latest.get("created_at", "—")

        max_count = backup.get("max_backup_count", 20)
        backup_count = backup.get("backup_count", 0)

        self.data_summary_label.setText(
            f"Programmversion: {APP_VERSION}<br>"
            f"Gespeicherte Sicherungen: {backup_count} "
            f"<span style='color:#D9F4FF;'>"
            f"(max. {max_count})</span><br>"
            f"Letzte Sicherung: {latest_label}"
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
                f"Build: {status.get('build_version', '—')}\n"
                f"Datenstand: {status.get('schema_version', '—')} "
                f"(Ziel: {status.get('target_schema_version', '—')})\n"
                f"Datenbankpfad:\n{db_path}\n"
                f"Sicherungsordner:\n{backup_dir}"
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
                "Einstellungen",
                f"Speichern fehlgeschlagen:\n{error}",
            )
            return

        removed_note = ""
        removed = result.get("removed_count", 0)

        if removed:
            removed_note = (
                f"\n\n{removed} ältere Sicherungen wurden entfernt."
            )

        QMessageBox.information(
            self,
            "Einstellungen",
            "Einstellungen gespeichert."
            f"{removed_note}",
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
                "Sicherung",
                f"Sicherung fehlgeschlagen:\n{error}",
            )
            return

        removed = result.get("removed_count", 0)
        removed_note = ""

        if removed:
            removed_note = (
                f"\n\n{removed} ältere Sicherungen wurden entfernt "
                f"(Aufbewahrungslimit)."
            )

        QMessageBox.information(
            self,
            "Sicherung",
            f"Sicherung erstellt ({result.get('created_at', '—')})."
            f"{removed_note}",
        )
        self.refresh_datensicherung()

    def restore_backup_clicked(self):
        filename = self.selected_backup_filename()
        backup_label = self.selected_backup_label()

        if not filename:
            QMessageBox.warning(
                self,
                "Wiederherstellen",
                "Bitte zuerst eine Sicherung aus der Liste wählen.",
            )
            return

        answer = QMessageBox.warning(
            self,
            "Stand wiederherstellen",
            f"Der aktuelle Stand wird durch diese Sicherung "
            f"ersetzt:\n\n{backup_label}\n\n"
            "Vorher wird automatisch der jetzige Stand "
            "gesichert.\n\n"
            "Alle nicht gesicherten Änderungen gehen verloren.\n\n"
            "Fortfahren?",
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
                "Stand wiederherstellen",
                f"Wiederherstellung fehlgeschlagen:\n{error}",
            )
            return

        self._notify_main_window_database_changed()

        safety_note = ""

        if result.get("pre_restore_backup"):
            safety_note = (
                "\n\nDer bisherige Stand wurde vorher gesichert."
            )

        QMessageBox.information(
            self,
            "Stand wiederherstellen",
            f"Stand wiederhergestellt: {backup_label}"
            f"{safety_note}\n\n"
            "Bitte abmelden und erneut anmelden.",
        )
        self.refresh_datensicherung()

    def open_backup_folder_clicked(self):
        try:
            status = self.db.get_database_backup_status()
        except Exception as error:
            QMessageBox.warning(
                self,
                "Backup-Ordner",
                str(error),
            )
            return

        folder = Path(status.get("backup_directory", ""))

        if not folder:
            QMessageBox.warning(
                self,
                "Backup-Ordner",
                "Backup-Ordner ist nicht bekannt.",
            )
            return

        folder.mkdir(parents=True, exist_ok=True)

        if not QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(folder.resolve()))
        ):
            QMessageBox.warning(
                self,
                "Backup-Ordner",
                f"Ordner konnte nicht geöffnet werden:\n{folder}",
            )

    def delete_backup_clicked(self):
        filename = self.selected_backup_filename()
        backup_label = self.selected_backup_label()

        if not filename:
            QMessageBox.warning(
                self,
                "Sicherung löschen",
                "Bitte zuerst eine Sicherung aus der Liste wählen.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Sicherung löschen",
            f"Diese Sicherung unwiderruflich löschen?\n\n"
            f"{backup_label}",
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
                "Sicherung löschen",
                f"Löschen fehlgeschlagen:\n{error}",
            )
            return

        QMessageBox.information(
            self,
            "Sicherung löschen",
            f"Sicherung gelöscht: {backup_label}",
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
                "Speicherstand prüfen",
                str(error),
            )
            return

        if result.get("ok"):
            QMessageBox.information(
                self,
                "Speicherstand prüfen",
                "Der Speicherstand ist in Ordnung.",
            )
        else:
            QMessageBox.warning(
                self,
                "Speicherstand prüfen",
                "Der Speicherstand sollte aktualisiert werden.\n\n"
                "Bitte „Datenbank aktualisieren“ ausführen.",
            )

        self.refresh_datensicherung()

    def rerun_migrations_clicked(self):
        answer = QMessageBox.question(
            self,
            "Datenbank aktualisieren",
            "Der Speicherstand wird an die aktuelle Programmversion "
            "angepasst. Ihre Daten bleiben erhalten.\n\n"
            "Fortfahren?",
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
                "Datenbank aktualisieren",
                f"Aktualisierung fehlgeschlagen:\n{error}",
            )
            return

        QMessageBox.information(
            self,
            "Datenbank aktualisieren",
            "Speicherstand wurde aktualisiert.",
        )
        self.refresh_datensicherung()

    def reinitialize_database_clicked(self):
        answer = QMessageBox.warning(
            self,
            "Alle Tracker-Daten löschen",
            "Alle Sessions, Jobs, Verkäufe und Benutzer "
            "(außer Standard-Admin) werden unwiderruflich "
            "gelöscht.\n\n"
            "Vorher wird automatisch eine Sicherung erstellt.\n\n"
            "Fortfahren?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        confirmation, ok = QInputDialog.getText(
            self,
            "Alle Tracker-Daten löschen",
            "Zur Bestätigung bitte RESET eingeben:",
        )

        if not ok or confirmation.strip().upper() != "RESET":
            return

        try:
            result = self.db.reinitialize_database()
        except OSError as error:
            QMessageBox.critical(
                self,
                "Alle Tracker-Daten löschen",
                f"Löschen fehlgeschlagen:\n{error}",
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "Alle Tracker-Daten löschen",
                f"Fehler:\n{error}",
            )
            return

        self._notify_main_window_database_changed()

        backup_note = ""

        if result.get("pre_reset_backup"):
            backup_note = (
                "\n\nEine Sicherung wurde vorher erstellt."
            )

        QMessageBox.information(
            self,
            "Alle Tracker-Daten löschen",
            "Alle Tracker-Daten wurden gelöscht."
            f"{backup_note}\n\n"
            "Bitte abmelden und mit dem Standard-Admin erneut "
            "anmelden.",
        )

        self.refresh_datensicherung()
