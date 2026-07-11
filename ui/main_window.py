from ui.session_page import SessionPage
from ui.statistics_page import StatisticsPage
from ui.history_page import HistoryPage
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from ui.refinery_page import RefineryPage
from ui.storage_page import StoragePage
from ui.refinery_live_sync import RefineryLiveSync
from ui.sales_page import SalesPage
from ui.admin_page import AdminPage
from ui.changelog_dialog import (
    ChangelogDialog
)

from ui.nav_brand_logo import (
    rebuild_nav_brand_header,
    refresh_nav_brand_logo,
    sync_nav_brand_badge_after_theme,
)
from config.editions import (
    EDITION_GLOW_RGB,
    edition_short_label,
    effective_edition,
    resolve_app_name,
)
from config.i18n import tr
from config.permissions import can_access

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget,
    QFrame,
)

from ui.nav_button_icons import configure_nav_button
from ui.dashboard_page import DashboardPage

from ui.dashboard_window import (
    DashboardWindow
)
from ui.mobiglas_window_frame import (
    MobiglasFramelessMixin,
    apply_mobiglas_window_frame,
)
from ui.page_layout import (
    build_nav_divider,
    build_nav_scroll,
    hud_divider,
)
from ui.update_manager import UpdateManager
from ui.window_geometry import (
    MAIN_WINDOW_MIN_SIZE,
    restore_window_geometry,
    save_window_geometry,
    dashboard_open_on_startup,
    set_dashboard_open_on_startup,
    save_last_nav_page,
    load_last_nav_page,
)
from ui.nav_metrics import (
    NAV_DIVIDER_PADDING,
    NAV_MIDDLE_KEYS,
    NAV_SETTINGS_DIVIDER_AFTER,
    apply_nav_panel_metrics,
)


class MainWindow(MobiglasFramelessMixin, QMainWindow):

    def __init__(
        self,
        user,
        on_logout=None,
        is_network_client=False,
    ):
        super().__init__()

        from database.access import get_database

        db = get_database()
        self.db = db
        if hasattr(db, "permissions"):
            user = db.permissions.ensure_user_permissions(user)

        self.current_user = user
        self.current_role = user["role_name"]
        self.on_logout = on_logout
        self.logged_out = False
        self.is_network_client = is_network_client
        self._wired_host_server = None
        self._wired_client_connection = None

        app_name = resolve_app_name(db)
        self.setObjectName("mainWindow")
        self.setWindowTitle(app_name)
        self.setMinimumSize(MAIN_WINDOW_MIN_SIZE)

        central_widget = QWidget()
        central_widget.setObjectName("mainCentral")
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        nav_widget = QWidget()
        nav_widget.setObjectName("navPanel")
        self.nav_widget = nav_widget

        nav_layout = QVBoxLayout()
        nav_widget.setLayout(nav_layout)
        nav_layout.setSpacing(6)
        self._nav_layout = nav_layout

        brand_block = QWidget()
        brand_block.setObjectName("navBrandBlock")
        self._nav_brand_block = brand_block
        brand_outer = QVBoxLayout(brand_block)
        brand_outer.setContentsMargins(12, 0, 12, 4)
        brand_outer.setSpacing(0)

        brand_card = QFrame()
        brand_card.setObjectName("navBrandCard")
        brand_layout = QVBoxLayout(brand_card)
        brand_layout.setContentsMargins(14, 14, 14, 12)
        brand_layout.setSpacing(0)

        self._nav_width = "normal"
        self._nav_brand_header_host = QWidget()
        self._nav_brand_header_layout = QVBoxLayout(
            self._nav_brand_header_host
        )
        self._nav_brand_header_layout.setContentsMargins(0, 0, 0, 0)
        self._nav_brand_header_layout.setSpacing(0)
        self._nav_brand_logo_label = None
        self.edition_badge_host = None
        self.edition_badge = None
        self._apply_nav_brand_header()

        user_panel = QFrame()
        user_panel.setObjectName("navUserPanel")
        user_panel_layout = QVBoxLayout(user_panel)
        user_panel_layout.setContentsMargins(10, 10, 10, 10)
        user_panel_layout.setSpacing(4)

        user_heading = QLabel(tr("nav.user"))
        user_heading.setObjectName("navUserHeading")
        user_heading.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        display_name = (
            user.get("display_name")
            or user["username"]
        )
        self.user_label = QLabel(display_name)
        self.user_label.setObjectName("navUserName")
        self.user_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.role_label = QLabel(self.current_role.upper())
        self.role_label.setObjectName("navRoleBadge")
        self.role_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.network_label = QLabel("")
        self.network_label.setObjectName("navNetworkBadge")
        self.network_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )
        self.network_label.setWordWrap(True)
        self._update_network_label()

        brand_layout.addWidget(self._nav_brand_header_host)
        brand_layout.addSpacing(8)

        user_panel_layout.addWidget(user_heading)
        user_panel_layout.addWidget(self.user_label)
        user_panel_layout.addWidget(self.role_label)
        user_panel_layout.addWidget(self.network_label)

        brand_layout.addWidget(user_panel)
        brand_outer.addWidget(brand_card)

        self.btn_dashboard = QPushButton(tr("dashboard.nav.embedded"))
        configure_nav_button(self.btn_dashboard, "dashboard")
        self.btn_dashboard.setProperty("dashboardWindowVisible", "false")

        self.btn_session = QPushButton(tr("nav.session"))
        configure_nav_button(self.btn_session, "session")

        self.btn_refinery = QPushButton(tr("nav.refinery"))
        configure_nav_button(self.btn_refinery, "refinery")

        self.btn_storage = QPushButton(tr("nav.storage"))
        configure_nav_button(self.btn_storage, "storage")

        self.btn_sales = QPushButton(tr("nav.sales"))
        configure_nav_button(self.btn_sales, "sales")

        self.btn_stats = QPushButton(tr("nav.payout"))
        configure_nav_button(self.btn_stats, "payout")

        self.btn_history = QPushButton(tr("nav.history"))
        configure_nav_button(self.btn_history, "history")

        self.btn_admin = QPushButton(tr("nav.settings"))
        configure_nav_button(self.btn_admin, "settings")

        self.pages = QStackedWidget()
        self.pages.setObjectName("contentStack")

        self.dashboard_page = DashboardPage()

        self.dashboard_page.set_parent_window(
            self
        )

        self.dashboard_window = (
            DashboardWindow(
                self.dashboard_page
            )
        )

        self.dashboard_page.set_detached_window(
            self.dashboard_window
        )

        self.session_page = SessionPage(
            is_network_client=self.is_network_client,
        )
        self.refinery_page = RefineryPage()
        self.storage_page = StoragePage()
        self.storage_page.idle_warnings_changed.connect(
            self._refresh_storage_idle_badge
        )
        self.sales_page = SalesPage()
        self.statistics_page = StatisticsPage()
        self.history_page = HistoryPage()
        self.admin_page = AdminPage()

        self.refinery_live_sync = RefineryLiveSync(self)
        self.refinery_page.attach_live_sync(
            self.refinery_live_sync
        )
        self.refinery_live_sync.jobs_updated.connect(
            self.dashboard_page.refresh_refinery_kpis
        )
        self.refinery_live_sync.start()

        self.pages.addWidget(
            QWidget()
        )

        self.pages.addWidget(
            self.session_page
        )

        self.pages.addWidget(self.refinery_page)
        self.pages.addWidget(self.storage_page)
        self.pages.addWidget(self.sales_page)
        self.pages.addWidget(self.statistics_page)
        self.pages.addWidget(self.history_page)
        self.pages.addWidget(self.admin_page)

        self.btn_dashboard.clicked.connect(
            self.toggle_dashboard_window
        )

        self.btn_session.clicked.connect(
            lambda: self.switch_page(
                self.session_page,
                self.btn_session
            )
        )

        self.btn_refinery.clicked.connect(
            lambda: self.switch_page(
                self.refinery_page,
                self.btn_refinery
            )
        )

        self.btn_storage.clicked.connect(
            lambda: self.switch_page(
                self.storage_page,
                self.btn_storage
            )
        )

        self.btn_sales.clicked.connect(
            lambda: self.switch_page(
                self.sales_page,
                self.btn_sales
            )
        )

        self.btn_stats.clicked.connect(
            lambda: self.switch_page(
                self.statistics_page,
                self.btn_stats
            )
        )

        self.btn_history.clicked.connect(
            lambda: self.switch_page(
                self.history_page,
                self.btn_history
            )
        )

        self.btn_admin.clicked.connect(
            lambda: self.switch_page(
                self.admin_page,
                self.btn_admin
            )
        )

        nav_layout.addWidget(brand_block)

        nav_layout.addSpacing(6)
        nav_layout.addWidget(build_nav_divider())
        nav_layout.addSpacing(6)

        nav_scroll_content = QWidget()
        nav_scroll_content.setObjectName("navScrollContent")
        nav_scroll_layout = QVBoxLayout(nav_scroll_content)
        nav_scroll_layout.setContentsMargins(0, 0, 0, 0)
        nav_scroll_layout.setSpacing(4)
        self._nav_scroll_layout = nav_scroll_layout

        self.nav_buttons = {
            "dashboard": self.btn_dashboard,
            "session": self.btn_session,
            "refinery": self.btn_refinery,
            "storage": self.btn_storage,
            "sales": self.btn_sales,
            "statistics": self.btn_stats,
            "history": self.btn_history,
            "settings": self.btn_admin,
        }

        nav_scroll_layout.addWidget(self.btn_dashboard)
        nav_scroll_layout.addSpacing(NAV_DIVIDER_PADDING)
        nav_scroll_layout.addWidget(build_nav_divider())
        nav_scroll_layout.addSpacing(NAV_DIVIDER_PADDING)

        self._nav_middle_section = QWidget()
        self._nav_middle_section.setObjectName("navMiddleSection")
        self._nav_middle_layout = QVBoxLayout(self._nav_middle_section)
        self._nav_middle_layout.setContentsMargins(0, 0, 0, 0)
        self._nav_middle_layout.setSpacing(4)
        self._nav_middle_layout.addStretch(1)
        for key in NAV_MIDDLE_KEYS:
            self._nav_middle_layout.addWidget(self.nav_buttons[key])
        self._nav_middle_layout.addStretch(1)
        nav_scroll_layout.addWidget(self._nav_middle_section, 1)

        nav_scroll_layout.addWidget(build_nav_divider())
        nav_scroll_layout.addSpacing(NAV_SETTINGS_DIVIDER_AFTER)
        nav_scroll_layout.addWidget(self.btn_admin)

        self._refresh_nav_visibility()

        self.storage_idle_badge = QPushButton()
        self.storage_idle_badge.setObjectName("navStorageBadge")
        self.storage_idle_badge.setCursor(Qt.PointingHandCursor)
        self.storage_idle_badge.setVisible(False)
        self.storage_idle_badge.clicked.connect(
            lambda: self.switch_page(
                self.storage_page,
                self.btn_storage,
            )
        )
        nav_scroll_layout.addWidget(self.storage_idle_badge)

        self.update_badge = QPushButton(
            tr("nav.badge.update_available")
        )
        self.update_badge.setObjectName("navUpdateBadge")
        self.update_badge.setCursor(Qt.PointingHandCursor)
        self.update_badge.setVisible(False)
        self.update_badge.clicked.connect(
            self._show_pending_update
        )
        nav_scroll_layout.addWidget(self.update_badge)

        nav_layout.addWidget(build_nav_scroll(nav_scroll_content), 1)

        main_layout.addWidget(nav_widget, 1)
        main_layout.addWidget(self.pages, 5)

        self.apply_permissions()

        self._geometry_timer = QTimer(self)
        self._geometry_timer.setSingleShot(True)
        self._geometry_timer.setInterval(400)
        self._geometry_timer.timeout.connect(
            self._persist_window_geometry
        )

        start_page, start_button = self._startup_page()
        self.set_active_button(start_button)
        self.pages.setCurrentWidget(start_page)
        self._load_page_data(start_page)

        title_bar = apply_mobiglas_window_frame(
            self,
            title=resolve_app_name(self.db),
        )
        title_bar.add_action_button(
            tr("nav.version_info"),
            self.show_changelog,
        )
        title_bar.add_action_button(
            tr("nav.logout"),
            self.logout,
        )

        self._wire_network_events()

        self.update_manager = UpdateManager(db, self)
        self.admin_page.set_update_manager(self.update_manager)
        self.admin_page.edition_unlock_changed.connect(
            self.refresh_edition_state
        )
        self.update_manager.check_completed.connect(
            self.admin_page.refresh_updates_section
        )
        self.update_manager.update_available.connect(
            self._show_update_badge
        )
        self.update_manager.update_cleared.connect(
            self._hide_update_badge
        )
        QTimer.singleShot(
            2000,
            self.update_manager.run_startup_check,
        )

        settings = db.settings.resolve_effective_settings(
            user["id"]
        )
        self.apply_nav_width(settings.get("nav_width", "normal"))
        restore_window_geometry(self, db)

        if dashboard_open_on_startup(db):
            QTimer.singleShot(0, self.show_dashboard_window)
        else:
            QTimer.singleShot(0, self.sync_dashboard_nav_state)

    def sync_dashboard_nav_state(self) -> None:
        """Übersicht-Nav: Text, Farbe und Symbol an Fenster-Sichtbarkeit."""
        visible = self.dashboard_window.isVisible()
        self.btn_dashboard.setText(
            tr("dashboard.nav.detached")
            if visible
            else tr("dashboard.nav.embedded")
        )
        self.btn_dashboard.setProperty(
            "dashboardWindowVisible",
            "true" if visible else "false",
        )
        style = self.btn_dashboard.style()
        if style is not None:
            style.unpolish(self.btn_dashboard)
            style.polish(self.btn_dashboard)
        self.btn_dashboard.update()

    def on_dashboard_window_close_requested(self) -> None:
        """X auf dem Übersicht-Fenster — gleicher Zustand wie Nav-Toggle."""
        if not self.dashboard_window.isVisible():
            self.sync_dashboard_nav_state()
            return
        self.hide_dashboard_window()

    def _sync_dashboard_nav_background(self) -> None:
        self.sync_dashboard_nav_state()

    def apply_nav_width(self, nav_width: str = "normal"):
        self._nav_width = nav_width
        apply_nav_panel_metrics(
            self.nav_widget,
            self._nav_layout,
            self._nav_scroll_layout,
            self.nav_buttons,
            badge_buttons=[
                self.storage_idle_badge,
                self.update_badge,
            ],
            brand_block=self._nav_brand_block,
            nav_middle_layout=self._nav_middle_layout,
            nav_width=nav_width,
        )
        if self._nav_brand_logo_label is not None:
            refresh_nav_brand_logo(
                self._nav_brand_logo_label,
                effective_edition(self.db),
                nav_width,
            )

    def refresh_network_display(self):
        """Navigations-Anzeige und Client-/Host-UI aktualisieren."""
        self.apply_network_mode()

    def apply_network_mode(self):
        """Client-Modus und Seiten an aktuellen Verbindungszustand anpassen."""
        from database.access import get_client_connection

        connection = get_client_connection()
        is_client = (
            connection is not None
            and connection.is_connected
        )
        mode_changed = is_client != self.is_network_client

        if mode_changed:
            self.is_network_client = is_client
            self.session_page.set_network_client_mode(is_client)

        self._refresh_page_databases()
        self._wire_network_events()
        self._update_network_label()

        if mode_changed and is_client:
            self._on_network_data_changed()

    def _refresh_page_databases(self):
        from database.access import get_database

        db = get_database()
        for page in (
            self.session_page,
            self.refinery_page,
            self.sales_page,
            self.statistics_page,
            self.history_page,
            self.dashboard_page,
            self.admin_page,
        ):
            if hasattr(page, "db"):
                page.db = db

    def _wire_network_events(self):
        from database.access import get_client_connection, get_host_server

        connection = get_client_connection()
        if connection is not self._wired_client_connection:
            if self._wired_client_connection is not None:
                for signal, slot in (
                    (
                        self._wired_client_connection.disconnected,
                        self._on_client_disconnected,
                    ),
                    (
                        self._wired_client_connection.data_changed,
                        self._on_network_data_changed,
                    ),
                ):
                    try:
                        signal.disconnect(slot)
                    except (RuntimeError, TypeError):
                        pass

            self._wired_client_connection = connection
            if connection:
                connection.disconnected.connect(
                    self._on_client_disconnected
                )
                connection.data_changed.connect(
                    self._on_network_data_changed
                )

        server = get_host_server()
        if server is self._wired_host_server:
            return

        if self._wired_host_server is not None:
            old = self._wired_host_server
            for signal, slot in (
                (old.started, self._on_host_network_event),
                (old.stopped, self._on_host_network_event),
                (old.client_connected, self._on_host_network_event),
                (old.client_disconnected, self._on_host_network_event),
                (old.data_changed, self._on_network_data_changed),
            ):
                try:
                    signal.disconnect(slot)
                except (RuntimeError, TypeError):
                    pass

        self._wired_host_server = server
        if not server:
            return

        server.started.connect(self._on_host_network_event)
        server.stopped.connect(self._on_host_network_event)
        server.client_connected.connect(
            self._on_host_network_event
        )
        server.client_disconnected.connect(
            self._on_host_network_event
        )
        server.data_changed.connect(
            self._on_network_data_changed
        )

    def _on_host_network_event(self, *_args):
        self._update_network_label()
        if hasattr(self, "admin_page"):
            self.admin_page._refresh_network_tab()

    def _on_client_disconnected(self):
        self.apply_network_mode()

    def refresh_edition_state(self):
        """Nach Supporter-Key: Titel, Badge und gesperrte Bereiche aktualisieren."""
        edition_key = effective_edition(self.db)
        app_name = resolve_app_name(self.db)

        self.setWindowTitle(app_name)
        title_bar = getattr(self, "_mobiglas_title_bar", None)
        if title_bar is not None:
            title_bar.set_title(app_name)

        self._apply_nav_brand_header()

        if hasattr(self, "admin_page"):
            self.admin_page.refresh_support_tab()
            if hasattr(self.admin_page, "network_edition_panel"):
                self.admin_page.network_edition_panel.refresh()
            self.admin_page._refresh_network_tab()

        self._update_network_label()

    def _apply_nav_brand_header(self):
        refs = rebuild_nav_brand_header(
            self._nav_brand_header_host,
            self._nav_brand_header_layout,
            self.db,
            edition_short_label_fn=edition_short_label,
            nav_width=self._nav_width,
        )
        self._nav_brand_logo_label = refs["logo_label"]
        self.edition_badge_host = refs["badge_host"]
        self.edition_badge = refs["badge"]

        if self.edition_badge_host is not None and self.edition_badge is not None:
            edition_key = effective_edition(self.db)
            self._apply_edition_badge_glow(edition_key)

    def _apply_edition_badge_glow(self, edition_key: str):
        if self.edition_badge_host is None or self.edition_badge is None:
            return

        rgb = EDITION_GLOW_RGB.get(edition_key, EDITION_GLOW_RGB["solo"])
        sync_nav_brand_badge_after_theme(
            self.edition_badge_host,
            self.edition_badge,
        )
        effect = QGraphicsDropShadowEffect(self.edition_badge_host)
        effect.setBlurRadius(40)
        effect.setOffset(0, 0)
        effect.setColor(QColor(*rgb, 255))
        self.edition_badge_host.setGraphicsEffect(effect)
        self.edition_badge_host.style().unpolish(self.edition_badge_host)
        self.edition_badge_host.style().polish(self.edition_badge_host)
        self.edition_badge.style().unpolish(self.edition_badge)
        self.edition_badge.style().polish(self.edition_badge)
        QTimer.singleShot(
            0,
            lambda: sync_nav_brand_badge_after_theme(
                self.edition_badge_host,
                self.edition_badge,
            ),
        )

    def _show_update_badge(self, manifest):
        self.update_badge.setText(
            tr("nav.badge.update", version=manifest.version_display)
        )
        self.update_badge.setVisible(True)

    def _hide_update_badge(self):
        self.update_badge.setVisible(False)

    def _show_pending_update(self):
        self.update_manager.show_pending_update()

    def _update_network_label(self):
        from database.access import get_host_server
        from network.network_state import get_network_state

        state = get_network_state()
        if state.is_client():
            host = state.host_address or tr(
                "nav.network.host_fallback"
            )
            self.network_label.setText(
                tr(
                    "nav.network.client",
                    host=host,
                    port=state.host_port,
                )
            )
            self.network_label.setVisible(True)
            return

        server = get_host_server()
        if server and server.is_running():
            clients = len(state.connected_clients)
            addrs = ", ".join(server.addresses[:2])
            self.network_label.setText(
                tr(
                    "nav.network.host",
                    addresses=addrs,
                    port=server.port,
                    code=server.join_code,
                    clients=clients,
                )
            )
            self.network_label.setVisible(True)
            return

        if state.mode == "host" or state.host_running:
            self.network_label.setText(
                tr("nav.network.host_inactive")
            )
            self.network_label.setVisible(True)
            return

        self.network_label.setText("")

        self.network_label.setVisible(False)

    def _refresh_storage_idle_badge(self, count=None):
        if count is None:
            from database.access import get_database

            count = get_database().count_stockpile_idle_warnings()

        if count <= 0:
            self.storage_idle_badge.setVisible(False)
            return

        self.storage_idle_badge.setText(
            tr("nav.badge.storage_idle", count=count)
        )
        self.storage_idle_badge.setVisible(True)

    def _on_network_data_changed(self):
        self.session_page.refresh_session()
        self.refinery_page.load_data()
        self.storage_page.load_data()
        self._refresh_storage_idle_badge()
        self.sales_page.load_data()
        self.statistics_page.refresh_data()
        self.history_page.refresh_history()
        if self.dashboard_page.isVisible() or (
            self.dashboard_window.isVisible()
        ):
            self.dashboard_page.refresh_dashboard(animated=False)

        self._update_network_label()

    def _default_page(self):
        if can_access(
            self.current_user,
            "session",
        ):
            return self.session_page

        if can_access(
            self.current_user,
            "statistics",
        ):
            return self.statistics_page

        return self.history_page

    _NAV_PAGE_MAP = {
        "session": ("session", "session_page", "btn_session"),
        "refinery": ("refinery", "refinery_page", "btn_refinery"),
        "storage": ("storage", "storage_page", "btn_storage"),
        "sales": ("sales", "sales_page", "btn_sales"),
        "statistics": ("statistics", "statistics_page", "btn_stats"),
        "history": ("history", "history_page", "btn_history"),
        "settings": ("settings", "admin_page", "btn_admin"),
    }

    def _page_nav_key(self, page) -> str | None:
        for key, (_perm, attr, _btn) in self._NAV_PAGE_MAP.items():
            if page is getattr(self, attr, None):
                return key
        return None

    def _startup_page(self):
        user_id = self.current_user.get("id")
        saved_key = (
            load_last_nav_page(self.db, user_id)
            if user_id is not None
            else None
        )
        if saved_key and saved_key in self._NAV_PAGE_MAP:
            perm, page_attr, btn_attr = self._NAV_PAGE_MAP[saved_key]
            if can_access(self.current_user, perm):
                return (
                    getattr(self, page_attr),
                    getattr(self, btn_attr),
                )
        page = self._default_page()
        return page, self._button_for_page(page)

    def _persist_window_geometry(self):
        save_window_geometry(self, self.db)

    def moveEvent(self, event):
        super().moveEvent(event)
        self._geometry_timer.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._geometry_timer.start()

    def changeEvent(self, event):
        super().changeEvent(event)
        from PySide6.QtCore import QEvent

        if event.type() == QEvent.Type.WindowStateChange:
            self._geometry_timer.start()

    def _button_for_page(self, page):
        mapping = {
            self.session_page: self.btn_session,
            self.refinery_page: self.btn_refinery,
            self.storage_page: self.btn_storage,
            self.sales_page: self.btn_sales,
            self.statistics_page: self.btn_stats,
            self.history_page: self.btn_history,
            self.admin_page: self.btn_admin,
        }

        return mapping.get(
            page,
            self.btn_history,
        )

    def apply_permissions(self):
        pages = [
            (self.session_page, "session"),
            (self.refinery_page, "refinery"),
            (self.storage_page, "storage"),
            (self.sales_page, "sales"),
            (self.statistics_page, "statistics"),
            (self.history_page, "history"),
            (self.admin_page, "settings"),
            (self.dashboard_page, "dashboard"),
        ]

        for page, page_name in pages:
            if hasattr(page, "apply_permissions"):
                page.apply_permissions(
                    self.current_user,
                    page_name,
                )

        self._refresh_nav_visibility()

    def refresh_current_user_from_db(self):
        from database.access import get_database
        import auth.session as user_session

        if not self.current_user:
            return False

        db = get_database()
        refreshed = db.permissions.refresh_session_user(
            self.current_user["id"]
        )

        if not refreshed:
            return False

        self.current_user = refreshed
        self.current_role = refreshed["role_name"]
        self.user_label.setText(refreshed["username"])
        self.role_label.setText(refreshed["role_name"])
        self.apply_permissions()
        return True

    def _refresh_nav_visibility(self):
        for page_name, button in self.nav_buttons.items():
            button.setVisible(
                can_access(
                    self.current_user,
                    page_name,
                )
            )

    def _close_detached_dashboard(self, *, user_action=True):
        if not self.dashboard_window.isVisible():
            return

        self.dashboard_window.hide_dashboard(
            user_action=user_action
        )

    def closeEvent(self, event):
        from database.access import get_database

        db = get_database()
        if self.dashboard_window.isVisible():
            set_dashboard_open_on_startup(db, True)
        self._close_detached_dashboard(user_action=False)
        self.dashboard_page.persist_layout()
        save_window_geometry(self, db)
        super().closeEvent(event)

    def logout(self):
        self.logged_out = True

        self._close_detached_dashboard()

        self.close()

        if self.on_logout:
            self.on_logout()

    def request_language_restart(self):
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication
        from auth.app_restart import restart_application, shutdown_before_restart

        if hasattr(self, "dashboard_page"):
            self.dashboard_page.persist_layout()
        save_window_geometry(self, self.db)

        def _do_restart():
            shutdown_before_restart()
            restart_application()
            QApplication.instance().quit()

        QTimer.singleShot(150, _do_restart)

    def switch_page(
        self,
        page,
        button
    ):
        self._load_page_data(page)

        self.pages.setCurrentWidget(page)

        context_key = self._page_context_key(page)
        if context_key is not None:
            self.dashboard_page.set_context_from_nav(context_key)

        self.set_active_button(button)

        page_key = self._page_nav_key(page)
        user_id = self.current_user.get("id")
        if page_key and user_id is not None:
            save_last_nav_page(self.db, user_id, page_key)

    def _load_page_data(self, page):
        if page == self.sales_page:
            self.sales_page.load_data()

        if page == self.session_page:
            self.session_page.refresh_session()

        if page == self.refinery_page:
            self.refinery_page.load_data()

        if page == self.storage_page:
            self.storage_page.load_data()

        if page == self.statistics_page:
            self.statistics_page.refresh_data()

        if page == self.history_page:
            self.history_page.refresh_history()

        if page == self.admin_page:
            self.admin_page.refresh_data()
            self.admin_page.refresh_language_settings()

    def _page_context_key(self, page) -> str | None:
        mapping = {
            self.session_page: "session",
            self.refinery_page: "refinery",
            self.storage_page: "storage",
            self.sales_page: "sales",
            self.statistics_page: "payout",
            self.history_page: "history",
        }
        return mapping.get(page)

    def switch_dashboard_context(self, context_key: str):
        page_map = {
            "session": (self.session_page, self.btn_session),
            "refinery": (self.refinery_page, self.btn_refinery),
            "storage": (self.storage_page, self.btn_storage),
            "sales": (self.sales_page, self.btn_sales),
            "payout": (self.statistics_page, self.btn_stats),
            "history": (self.history_page, self.btn_history),
        }
        target = page_map.get(context_key)
        if target is not None:
            page, button = target
            self.switch_page(page, button)
            return

        self.dashboard_page.set_context(context_key, force=True)
        if self.dashboard_window.isVisible():
            self.dashboard_page.refresh_dashboard()

    def set_active_button(
        self,
        active_button
    ):
        for button in self.nav_buttons.values():
            should_be_active = button is active_button
            if button.property("active") == should_be_active:
                continue

            button.setProperty("active", should_be_active)
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()

    def get_dashboard_page(self):

        return self.dashboard_page

    def is_dashboard_detached(self):

        return (
            self.dashboard_page
            .is_dashboard_detached()
        )

    def get_dashboard_mode(self):

        return (
            self.dashboard_page
            .get_dashboard_mode()
        )

    def has_detached_dashboard(self):

        return (
            self.dashboard_page
            .get_detached_window()
            is not None
        )

    def show_dashboard_window(self):

        self.dashboard_page.apply_permissions(
            self.current_user,
            "dashboard",
        )

        if (
            self.dashboard_page
            .is_ready_for_detach()
        ):

            self.dashboard_page.mark_as_detached()

        context_key = self._page_context_key(
            self.pages.currentWidget()
        )
        if context_key is not None:
            self.dashboard_page.set_context_from_nav(context_key)

        set_dashboard_open_on_startup(self.db, True)
        self.dashboard_window.show_dashboard()
        self.sync_dashboard_nav_state()

    def hide_dashboard_window(self):

        if (
            self.dashboard_page
            .is_ready_for_attach()
        ):

            self.dashboard_page.mark_as_embedded()

        set_dashboard_open_on_startup(self.db, False)
        self.dashboard_window.hide_dashboard()
        self.sync_dashboard_nav_state()

    def toggle_dashboard_window(self):

        if (
            self.dashboard_page
            .is_detached()
        ):

            self.hide_dashboard_window()

        else:

            self.show_dashboard_window()

    def get_detached_dashboard(self):

        return (
            self.dashboard_page
            .get_detached_window()
        )

    def set_detached_dashboard(
        self,
        window
    ):

        self.dashboard_page.set_detached_window(
            window
        )

    def clear_detached_dashboard(self):

        self.dashboard_page.clear_detached_window()

    def show_changelog(self):

        dialog = ChangelogDialog()

        dialog.exec()
