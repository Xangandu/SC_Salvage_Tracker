from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QGridLayout,
    QPushButton,
    QScrollArea,
    QMessageBox,
    QDialog,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer

from database.access import get_database, get_dashboard_layout_repository
from config.i18n import tr, format_number, status_label
from config.materials import material_total_label, material_label
from config.debug import debug_log
from config.permissions import apply_widget_permissions
from ui.dashboard_widget_registry import widget_definitions
from ui.page_layout import (
    page_title,
    subsection_title,
    section_accent,
    hud_divider,
    primary_button,
    form_label,
)
from ui.dashboard_grid_canvas import DashboardGridCanvas
from ui.dashboard_catalog_panel import DashboardCatalogPanel
from ui.dashboard_preset_dialog import DashboardPresetDialog
from ui.dashboard_grid_utils import default_classic_layout
from ui.dashboard_number_animation import AnimatedDashboardValue
from ui.dashboard_status_animation import DashboardStatusAnimator
from ui.dashboard_fit_label import DashboardFitLabel
from ui.theme_manager import ThemeManager
import auth.session as user_session


def _session_field_column(label_text: str, value_widget: QWidget) -> QWidget:
    """Label über Wert — wie auf der Session-Seite."""
    host = QWidget()
    column = QVBoxLayout(host)
    column.setContentsMargins(0, 0, 0, 0)
    column.setSpacing(2)
    column.addWidget(form_label(label_text))
    column.addWidget(value_widget)
    return host


class DashboardPage(QWidget):

    def __init__(self):
        super().__init__()
        self.setObjectName("dashboardPage")

        self.db = get_database()
        self._current_user = None
        self._edit_mode = False
        self._saved_layout_snapshot = None

        self.dashboard_mode = "EMBEDDED"
        self.dashboard_detached = False
        self.parent_window = None
        self.detached_window = None

        self._widget_pool: dict[str, QFrame] = {}
        self._last_session_status = None
        self._status_cycle_animating = False
        self._layout_dirty = False
        self._layout_autosave_timer = QTimer(self)
        self._layout_autosave_timer.setSingleShot(True)
        self._layout_autosave_timer.setInterval(400)
        self._layout_autosave_timer.timeout.connect(
            self._autosave_layout
        )
        self._build_widget_pool()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header_host = QWidget()
        header_host.setObjectName("dashboardHeader")
        header_layout = QHBoxLayout(header_host)
        header_layout.setContentsMargins(24, 18, 24, 8)

        title_block = QVBoxLayout()
        title_block.setSpacing(4)
        self._title = page_title(tr("dashboard.title"))
        self._subtitle = section_accent(tr("dashboard.subtitle"))
        title_block.addWidget(self._title)
        title_block.addWidget(self._subtitle)
        header_layout.addLayout(title_block)
        header_layout.addStretch()

        self.preset_button = QPushButton(tr("dashboard.button.presets"))
        self.preset_button.setObjectName("secondaryAction")
        self.preset_button.clicked.connect(self._open_presets)

        self.edit_toggle_button = QPushButton(tr("dashboard.button.customize"))
        self.edit_toggle_button.setObjectName("secondaryAction")
        self.edit_toggle_button.clicked.connect(
            self._toggle_edit_mode
        )

        self.save_layout_button = primary_button(tr("dashboard.button.save"))
        self.save_layout_button.clicked.connect(
            self._save_layout
        )
        self.save_layout_button.hide()

        self.cancel_layout_button = QPushButton(tr("dashboard.button.cancel"))
        self.cancel_layout_button.setObjectName("secondaryAction")
        self.cancel_layout_button.clicked.connect(
            self._cancel_edit
        )
        self.cancel_layout_button.hide()

        header_layout.addWidget(self.preset_button)
        header_layout.addWidget(self.edit_toggle_button)
        header_layout.addWidget(self.cancel_layout_button)
        header_layout.addWidget(self.save_layout_button)
        root.addWidget(header_host)
        root.addLayout(hud_divider())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        scroll = QScrollArea()
        scroll.setObjectName("dashboardScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.viewport().setObjectName("dashboardScrollViewport")
        scroll.viewport().setAutoFillBackground(False)

        self.canvas = DashboardGridCanvas()
        self.canvas.set_widget_pool(self._widget_pool)
        scroll.setWidget(self.canvas)

        self.catalog = DashboardCatalogPanel()
        self.catalog.hide()
        self.catalog.widget_returned.connect(
            self.canvas.remove_widget
        )
        self.canvas.layout_changed.connect(
            self._sync_catalog
        )
        self.canvas.layout_changed.connect(
            self._on_layout_changed
        )

        body.addWidget(scroll, 1)
        body.addWidget(self.catalog)
        root.addLayout(body, 1)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(3000)
        self._refresh_timer.timeout.connect(
            self.refresh_dashboard
        )

        self._load_initial_layout()
        self.refresh_dashboard()
        ThemeManager.refresh_dashboard_font_scale()

    def reload_user_layout(self):
        if self._edit_mode:
            return

        user_id = self._user_id()
        if user_id is None:
            return

        saved = self._layout_repo().get_active_layout(user_id)
        if saved is not None:
            self.canvas.load_layout_data(saved)
            self._saved_layout_snapshot = saved
            self._layout_dirty = False
        else:
            layout = default_classic_layout()
            self.canvas.load_layout_data(layout)
            self._saved_layout_snapshot = layout
            self._layout_dirty = False

        self._sync_catalog()
        self._update_layout_dirty_hint()
        self.canvas.reflow_content_sizes()

    def persist_layout(self):
        user_id = self._user_id()
        if user_id is None:
            return False

        layout = self.canvas.get_layout_data()
        self._layout_repo().save_active_layout(
            user_id,
            layout,
        )
        self._saved_layout_snapshot = layout
        self._layout_dirty = False
        self._update_layout_dirty_hint()
        return True

    def _autosave_layout(self):
        if not self._layout_dirty:
            return

        if self.persist_layout():
            debug_log("Dashboard-Layout automatisch gespeichert")

    def _on_layout_changed(self):
        if not self._edit_mode:
            return

        self._layout_dirty = True
        self._update_layout_dirty_hint()
        self._layout_autosave_timer.start()

    def _update_layout_dirty_hint(self):
        if self._edit_mode and self._layout_dirty:
            self.edit_toggle_button.setText(
                tr("dashboard.button.customize_dirty")
            )
        else:
            self.edit_toggle_button.setText(
                tr("dashboard.button.customize")
            )

    def apply_font_scale(self, scales=None):
        ThemeManager.apply_dashboard_fonts(self, scales)

    def _refresh_refinery_stats(self):
        stats = self.db.get_refinery_statistics()
        if not stats.get("job_count"):
            self.refinery_stats_label.setText(
                tr("dashboard.refinery_stats.empty")
            )
            return

        avg = stats.get("avg_efficiency_percent")
        avg_text = (
            f"{format_number(avg, 1)} %"
            if avg is not None
            else "—"
        )

        lines = [
            tr(
                "dashboard.refinery_stats.jobs",
                count=stats["job_count"],
            ),
            tr(
                "dashboard.refinery_stats.io",
                input_scu=format_number(stats["total_input"]),
                output_scu=format_number(stats["total_output"]),
            ),
            tr(
                "dashboard.refinery_stats.efficiency",
                value=avg_text,
            ),
        ]

        if stats.get("by_material"):
            lines.append("")
            lines.append(tr("dashboard.refinery_stats.by_material"))
            for row in stats["by_material"]:
                eff = row.get("efficiency_percent")
                eff_label = (
                    f"{format_number(eff, 1)} %"
                    if eff is not None
                    else "—"
                )
                lines.append(
                    tr(
                        "dashboard.refinery_stats.detail_line",
                        label=material_label(row["material_code"]),
                        efficiency=eff_label,
                        count=row["job_count"],
                    )
                )

        if stats.get("by_method"):
            lines.append("")
            lines.append(tr("dashboard.refinery_stats.by_method"))
            for row in stats["by_method"]:
                eff = row.get("efficiency_percent")
                eff_label = (
                    f"{format_number(eff, 1)} %"
                    if eff is not None
                    else "—"
                )
                lines.append(
                    tr(
                        "dashboard.refinery_stats.detail_line",
                        label=row["refinery_method"],
                        efficiency=eff_label,
                        count=row["job_count"],
                    )
                )

        self.refinery_stats_label.setText("\n".join(lines))

    def _build_widget_pool(self):
        defs = widget_definitions()
        idle_text = status_label("IDLE")

        self.status_value = DashboardFitLabel(
            idle_text,
            max_lines=2,
        )
        self.crew_value = AnimatedDashboardValue("0")
        self.rmc_value = AnimatedDashboardValue("0 SCU")
        self.cm_value = AnimatedDashboardValue("0 SCU")
        self.rubble_value = AnimatedDashboardValue("0 SCU")
        self.scraps_value = AnimatedDashboardValue("0 SCU")
        self.salvage_value = AnimatedDashboardValue("0 SCU")
        self.active_sessions_value = AnimatedDashboardValue("0")
        self.total_sessions_value = AnimatedDashboardValue("0")
        self.sold_sessions_value = AnimatedDashboardValue("0")
        self.ready_sessions_value = AnimatedDashboardValue("0")
        self.refinery_jobs_value = AnimatedDashboardValue("0")
        self.total_sales_value = AnimatedDashboardValue("0")
        self.total_profit_value = AnimatedDashboardValue("0")

        kpi_specs = [
            ("status", defs["status"]["title"], self.status_value),
            ("crew", defs["crew"]["title"], self.crew_value),
            ("rmc", defs["rmc"]["title"], self.rmc_value),
            ("cm", defs["cm"]["title"], self.cm_value),
            (
                "rubble",
                defs["rubble"]["title"],
                self.rubble_value,
            ),
            (
                "scraps",
                defs["scraps"]["title"],
                self.scraps_value,
            ),
            (
                "salvage",
                defs["salvage"]["title"],
                self.salvage_value,
            ),
            (
                "refinery_jobs",
                defs["refinery_jobs"]["title"],
                self.refinery_jobs_value,
            ),
            (
                "active_sessions",
                defs["active_sessions"]["title"],
                self.active_sessions_value,
            ),
            (
                "total_sessions",
                defs["total_sessions"]["title"],
                self.total_sessions_value,
            ),
            (
                "sold_sessions",
                defs["sold_sessions"]["title"],
                self.sold_sessions_value,
            ),
            (
                "ready_sessions",
                defs["ready_sessions"]["title"],
                self.ready_sessions_value,
            ),
            (
                "total_sales",
                defs["total_sales"]["title"],
                self.total_sales_value,
            ),
            (
                "total_profit",
                defs["total_profit"]["title"],
                self.total_profit_value,
            ),
        ]

        for card_id, title, value in kpi_specs:
            accent = card_id == "total_profit"
            card = self._create_card(
                title,
                value,
                accent=accent,
            )
            if card_id == "status":
                value.setObjectName("cardValue")
            self._widget_pool[card_id] = card

        self.session_label = QLabel(tr("dashboard.session.none"))
        self.session_label.setObjectName("displayValue")
        self.session_label.setWordWrap(True)

        self.crew_info_label = AnimatedDashboardValue("0")
        self.crew_info_label.setObjectName("displayValue")

        self.status_info_label = DashboardFitLabel(
            idle_text,
            max_lines=2,
        )
        self.status_info_label.setObjectName("displayValue")

        self.rmc_info_label = AnimatedDashboardValue("0 SCU")
        self.rmc_info_label.setObjectName("displayValue")
        self.cm_info_label = AnimatedDashboardValue("0 SCU")
        self.cm_info_label.setObjectName("displayValue")
        self.refinery_info_label = AnimatedDashboardValue("0")
        self.refinery_info_label.setObjectName("displayValue")
        self.session_rubble_info_label = AnimatedDashboardValue("0 SCU")
        self.session_rubble_info_label.setObjectName("displayValue")
        self.session_scraps_info_label = AnimatedDashboardValue("0 SCU")
        self.session_scraps_info_label.setObjectName("displayValue")
        self.session_salvage_info_label = AnimatedDashboardValue("0 SCU")
        self.session_salvage_info_label.setObjectName("displayValue")

        self.refinery_stats_label = QLabel(
            tr("dashboard.refinery_stats.empty_short")
        )
        self.refinery_stats_label.setWordWrap(True)

        session_panel = QFrame(self)
        session_panel.setObjectName("dashboardSessionPanel")
        session_panel.setMinimumSize(0, 0)
        session_panel.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Preferred,
        )
        session_layout = QVBoxLayout(session_panel)
        session_layout.setContentsMargins(0, 0, 0, 0)
        session_layout.setSpacing(10)

        session_layout.addWidget(
            subsection_title(tr("dashboard.session.active"))
        )
        session_layout.addLayout(hud_divider())

        session_layout.addWidget(
            _session_field_column(
                tr("dashboard.label.ship"),
                self.session_label,
            )
        )
        session_layout.addWidget(
            _session_field_column(
                tr("dashboard.label.status"),
                self.status_info_label,
            )
        )

        meta_row = QHBoxLayout()
        meta_row.setSpacing(16)
        meta_row.addWidget(
            _session_field_column(
                tr("dashboard.label.crew"),
                self.crew_info_label,
            ),
            1,
        )
        meta_row.addWidget(
            _session_field_column(
                tr("dashboard.label.refinery"),
                self.refinery_info_label,
            ),
            1,
        )
        session_layout.addLayout(meta_row)

        materials_title = QLabel(tr("dashboard.session.materials"))
        materials_title.setObjectName("cardTitle")
        session_layout.addWidget(materials_title)

        materials_grid_host = QWidget()
        materials_grid = QGridLayout(materials_grid_host)
        materials_grid.setContentsMargins(0, 0, 0, 0)
        materials_grid.setHorizontalSpacing(16)
        materials_grid.setVerticalSpacing(8)

        material_fields = [
            (material_label("RMC"), self.rmc_info_label),
            (material_label("CM"), self.cm_info_label),
            (material_label("CM_RUBBLE"), self.session_rubble_info_label),
            (material_label("CM_SCRAPS"), self.session_scraps_info_label),
            (material_label("CM_SALVAGE"), self.session_salvage_info_label),
        ]
        for index, (title, value) in enumerate(material_fields):
            row = index // 2
            col = index % 2
            materials_grid.addWidget(
                _session_field_column(title, value),
                row,
                col,
            )
        materials_grid.setColumnStretch(0, 1)
        materials_grid.setColumnStretch(1, 1)
        session_layout.addWidget(materials_grid_host)

        self._widget_pool["session"] = session_panel

        refinery_stats_panel = QFrame(self)
        refinery_stats_panel.setObjectName("dashboardSessionPanel")
        refinery_stats_layout = QVBoxLayout(refinery_stats_panel)
        refinery_stats_layout.setContentsMargins(0, 0, 0, 0)
        refinery_stats_layout.setSpacing(8)
        refinery_heading = subsection_title(
            tr("dashboard.refinery_stats.title")
        )
        refinery_stats_layout.addWidget(refinery_heading)
        refinery_stats_layout.addLayout(hud_divider())
        self.refinery_stats_label.setObjectName("statValue")
        refinery_stats_layout.addWidget(self.refinery_stats_label)
        self._widget_pool["refinery_stats"] = refinery_stats_panel

    def _layout_repo(self):
        return get_dashboard_layout_repository(self.db)

    def _user_id(self):
        user = self._current_user or user_session.get_user()
        if not user:
            return None
        return user.get("id")

    def _load_initial_layout(self):
        user_id = self._user_id()
        if user_id is not None:
            saved = self._layout_repo().get_active_layout(
                user_id
            )
            if saved is not None:
                self.canvas.load_layout_data(saved)
                self._saved_layout_snapshot = saved
                self._sync_catalog()
                return

        self.canvas.load_layout_data(default_classic_layout())
        self._saved_layout_snapshot = None
        self._sync_catalog()

    def _sync_catalog(self):
        self.catalog.sync_availability(
            self.canvas.widgets_on_canvas()
        )

    def _toggle_edit_mode(self):
        if self._edit_mode:
            return
        self._enter_edit_mode()

    def _enter_edit_mode(self):
        self._edit_mode = True
        self._saved_layout_snapshot = (
            self.canvas.get_layout_data()
        )
        self.canvas.set_edit_mode(True)
        self.catalog.show()
        self.edit_toggle_button.hide()
        self.save_layout_button.show()
        self.cancel_layout_button.show()
        self.preset_button.setEnabled(True)
        self._layout_dirty = False
        self._update_layout_dirty_hint()

    def _leave_edit_mode(self):
        self._edit_mode = False
        self.canvas.set_edit_mode(False)
        self.catalog.hide()
        self.edit_toggle_button.show()
        self.edit_toggle_button.setText(tr("dashboard.button.customize"))
        self.save_layout_button.hide()
        self.cancel_layout_button.hide()
        if self._layout_dirty:
            self.persist_layout()

    def _save_layout(self):
        user_id = self._user_id()
        if user_id is None:
            QMessageBox.warning(
                self,
                tr("nav.dashboard"),
                tr("dashboard.msg.no_user"),
            )
            return

        if not self.persist_layout():
            return

        self._leave_edit_mode()
        QMessageBox.information(
            self,
            tr("nav.dashboard"),
            tr("dashboard.msg.layout_saved"),
        )

    def _cancel_edit(self):
        if self._saved_layout_snapshot is not None:
            self.canvas.load_layout_data(
                self._saved_layout_snapshot
            )
        self._layout_dirty = False
        self._update_layout_dirty_hint()
        self._leave_edit_mode()
        self._sync_catalog()

    def _open_presets(self):
        user_id = self._user_id()
        if user_id is None:
            return

        if not self._edit_mode:
            self._enter_edit_mode()

        dialog = DashboardPresetDialog(
            self,
            self._layout_repo(),
            user_id,
            current_layout=self.canvas.get_layout_data(),
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        if dialog.selected_layout is None:
            return

        self.canvas.load_layout_data(dialog.selected_layout)
        self._sync_catalog()

    def showEvent(self, event):
        super().showEvent(event)
        if not self._edit_mode:
            self.reload_user_layout()
        self.refresh_dashboard()
        self._refresh_timer.start()

    def hideEvent(self, event):
        self._refresh_timer.stop()
        self.persist_layout()
        super().hideEvent(event)

    def apply_permissions(self, user, page_name="dashboard"):
        self._current_user = user
        apply_widget_permissions(self, user, page_name)

        can_use = bool(user)
        for button in (
            self.preset_button,
            self.edit_toggle_button,
            self.save_layout_button,
            self.cancel_layout_button,
        ):
            button.setEnabled(can_use)

        if user and not self._edit_mode:
            self.reload_user_layout()

    def apply_dashboard_layout(self, layout_id=None):
        """Legacy-Hook — Presets über Preset-Dialog."""
        debug_log(
            "apply_dashboard_layout (legacy)",
            layout_id,
        )

    def _create_card(self, title, value, *, accent=False):
        card = QFrame(self)
        card.setMinimumSize(0, 0)
        card.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Minimum,
        )
        card.setObjectName("dashboardKpiCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title_label = subsection_title(title.upper())
        divider_host = QWidget()
        divider_host.setLayout(hud_divider())

        if accent:
            value.setObjectName("profitLabel")
        else:
            value.setObjectName("cardValue")
        value.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        value.setWordWrap(True)
        value.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Minimum,
        )

        layout.addWidget(title_label)
        layout.addWidget(divider_host)
        layout.addWidget(
            value,
            0,
            Qt.AlignmentFlag.AlignTop,
        )
        return card

    def _set_session_ship_text(self, text: str, *, active: bool):
        self.session_label.setText(text)
        self.session_label.setObjectName(
            "displayValue" if active else "mutedLabel"
        )
        self.session_label.style().unpolish(self.session_label)
        self.session_label.style().polish(self.session_label)

    def _update_session_status(self, status_code, status_text):
        previous = self._last_session_status
        status_card = self._widget_pool.get("status")

        self.status_value.setText(status_text)
        self.status_info_label.setText(status_text)

        if (
            previous is not None
            and previous != status_code
            and status_card is not None
        ):
            DashboardStatusAnimator.pulse(
                status_card,
                self.status_value,
                status_code,
                status_text,
            )

        self._last_session_status = status_code

    def on_payout_saved(self):
        self.refresh_dashboard()
        self.start_payout_cycle_complete_animation()

    def start_payout_cycle_complete_animation(self):
        status_card = self._widget_pool.get("status")
        if status_card is None:
            return

        idle_text = status_label("IDLE")
        payout_text = status_label("WAITING_FOR_PAYOUT")
        complete_text = tr("dashboard.status.cycle_complete")

        self._status_cycle_animating = True

        def on_finished():
            self._status_cycle_animating = False
            self._last_session_status = "IDLE"
            self.status_value.setText(idle_text)
            self.status_info_label.setText(idle_text)
            self.refresh_dashboard()

        DashboardStatusAnimator.cycle_complete(
            status_card,
            self.status_value,
            payout_text,
            complete_text,
            on_finished,
        )

    def refresh_dashboard(self):
        debug_log("REFRESH_DASHBOARD WIRD AUSGEFÜHRT")

        open_refinery_jobs = self.db.get_open_refinery_jobs()
        sold_sessions = self.db.get_sales_count()
        active_sessions = self.db.get_active_session_count()
        total_sessions = self.db.get_total_session_count()
        storage_scu = self.db.get_sellable_storage_total_scu()
        total_sales = self.db.get_total_sales_value()
        total_profit = self.db.get_total_profit()

        rmc_storage = self.db.get_storage_balance("RMC")
        cm_storage = self.db.get_storage_balance("CM")

        lifetime_rubble = self.db.get_global_batch_available(
            "CM_RUBBLE"
        )
        lifetime_scraps = self.db.get_global_batch_available(
            "CM_SCRAPS"
        )
        lifetime_salvage = self.db.get_global_batch_available(
            "CM_SALVAGE"
        )

        self.rmc_value.animate_to(rmc_storage, suffix=" SCU")
        self.cm_value.animate_to(cm_storage, suffix=" SCU")
        self.rubble_value.animate_to(lifetime_rubble, suffix=" SCU")
        self.scraps_value.animate_to(lifetime_scraps, suffix=" SCU")
        self.salvage_value.animate_to(lifetime_salvage, suffix=" SCU")
        self.sold_sessions_value.animate_to(sold_sessions)
        self.active_sessions_value.animate_to(active_sessions)
        self.total_sessions_value.animate_to(total_sessions)
        self.ready_sessions_value.animate_to(storage_scu)
        self.refinery_jobs_value.animate_to(open_refinery_jobs)
        self.total_sales_value.animate_to(
            total_sales, suffix=" aUEC"
        )
        self.total_profit_value.animate_to(
            total_profit, suffix=" aUEC"
        )

        self._refresh_refinery_stats()

        session = self.db.get_dashboard_session()

        if not session:
            if not self._status_cycle_animating:
                self._update_session_status("IDLE", status_label("IDLE"))
            self.crew_value.animate_to(0)
            self._set_session_ship_text(
                tr("dashboard.session.none"),
                active=False,
            )
            self.crew_info_label.animate_to(0)
            self.rmc_info_label.animate_to(0, suffix=" SCU")
            self.cm_info_label.animate_to(0, suffix=" SCU")
            self.session_rubble_info_label.animate_to(0, suffix=" SCU")
            self.session_scraps_info_label.animate_to(0, suffix=" SCU")
            self.session_salvage_info_label.animate_to(0, suffix=" SCU")
            self.refinery_info_label.animate_to(
                open_refinery_jobs,
                suffix=tr("dashboard.refinery.open_suffix"),
            )
            self.canvas.reflow_content_sizes()
            return

        session_id = session[0]
        ship_name = session[1]
        status = session[2]
        status_text = status_label(status)

        session_rmc = self.db.get_session_captured_total(
            session_id,
            "RMC",
        )
        session_cm = self.db.get_refined_cm_total(session_id)
        session_rubble = self.db.get_session_batch_available(
            session_id,
            "CM_RUBBLE",
        )
        session_scraps = self.db.get_session_batch_available(
            session_id,
            "CM_SCRAPS",
        )
        session_salvage = self.db.get_session_batch_available(
            session_id,
            "CM_SALVAGE",
        )
        crew = self.db.get_crew_members(session_id)

        if not self._status_cycle_animating:
            self._update_session_status(status, status_text)
        self.crew_value.animate_to(len(crew))
        self._set_session_ship_text(ship_name, active=True)
        self.crew_info_label.animate_to(len(crew))
        self.rmc_info_label.animate_to(
            session_rmc, suffix=" SCU", decimals=1
        )
        self.cm_info_label.animate_to(
            session_cm, suffix=" SCU", decimals=1
        )
        self.session_rubble_info_label.animate_to(
            session_rubble, suffix=" SCU", decimals=1
        )
        self.session_scraps_info_label.animate_to(
            session_scraps, suffix=" SCU", decimals=1
        )
        self.session_salvage_info_label.animate_to(
            session_salvage, suffix=" SCU", decimals=1
        )
        self.refinery_info_label.animate_to(
            open_refinery_jobs,
            suffix=tr("dashboard.refinery.open_suffix"),
        )
        self.canvas.reflow_content_sizes()

    def detach_dashboard(self):
        self.dashboard_mode = "DETACHED"
        self.dashboard_detached = True

    def attach_dashboard(self):
        self.dashboard_mode = "EMBEDDED"
        self.dashboard_detached = False

    def is_dashboard_detached(self):
        return self.dashboard_detached

    def set_parent_window(self, parent_window):
        self.parent_window = parent_window

    def get_parent_window(self):
        return self.parent_window

    def can_detach(self):
        return self.parent_window is not None

    def can_attach(self):
        return self.is_detached

    def get_dashboard_mode(self):
        return self.dashboard_mode

    def has_parent_window(self):
        return self.parent_window is not None

    def get_detached_window(self):
        return self.detached_window

    def set_detached_window(self, window):
        self.detached_window = window

    def clear_detached_window(self):
        self.detached_window = None

    def has_detached_window(self):
        return self.detached_window is not None

    def mark_as_detached(self):
        self.detach_dashboard()

    def mark_as_embedded(self):
        self.attach_dashboard()

    def is_embedded(self):
        return self.dashboard_mode == "EMBEDDED"

    def is_detached(self):
        return self.dashboard_mode == "DETACHED"

    def toggle_dashboard_mode(self):
        if self.is_detached():
            self.attach_dashboard()
        else:
            self.detach_dashboard()

    def reset_dashboard_mode(self):
        self.dashboard_mode = "EMBEDDED"
        self.dashboard_detached = False

    def has_valid_parent(self):
        return self.parent_window is not None

    def has_valid_dashboard_window(self):
        return self.detached_window is not None

    def can_toggle_dashboard(self):
        return self.has_valid_parent()

    def is_ready_for_detach(self):
        return self.has_valid_parent() and not self.is_detached()

    def is_ready_for_attach(self):
        return (
            self.has_valid_dashboard_window()
            and self.is_detached()
        )

    def get_dashboard_state(self):
        return {
            "mode": self.dashboard_mode,
            "detached": self.is_detached(),
            "has_parent": self.has_valid_parent(),
            "has_window": self.has_valid_dashboard_window(),
        }

    def reset_window_references(self):
        self.detached_window = None
        self.parent_window = None
