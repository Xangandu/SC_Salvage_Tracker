from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout
)

from PySide6.QtCore import Qt, QTimer

from database.access import get_database
from ui.mobiglas_window_frame import (
    MobiglasFramelessMixin,
    apply_mobiglas_window_frame,
)
from ui.window_geometry import (
    restore_dashboard_window_geometry,
    save_dashboard_window_geometry,
    set_dashboard_open_on_startup,
)


class DashboardWindow(MobiglasFramelessMixin, QMainWindow):

    def __init__(
        self,
        dashboard_page
    ):
        super().__init__()

        self.dashboard_page = (
            dashboard_page
        )

        self.setWindowTitle(
            "MobiGlas Salvage-Übersicht"
        )

        self.setObjectName(
            "dashboardWindow"
        )

        self.setMinimumSize(
            960,
            640
        )

        self.setWindowFlag(
            Qt.WindowStaysOnTopHint,
            False
        )

        self.setAttribute(
            Qt.WA_QuitOnClose,
            False,
        )

        self._geometry_timer = QTimer(self)
        self._geometry_timer.setSingleShot(True)
        self._geometry_timer.setInterval(400)
        self._geometry_timer.timeout.connect(
            self._save_geometry
        )

        central_widget = QWidget()
        central_widget.setObjectName("dashboardWindowCentral")

        self.setCentralWidget(
            central_widget
        )

        layout = QVBoxLayout()

        central_widget.setLayout(
            layout
        )

        layout.addWidget(
            self.dashboard_page
        )

        apply_mobiglas_window_frame(
            self,
            title="MobiGlas Salvage-Übersicht",
        )

        restore_dashboard_window_geometry(
            self,
            get_database(),
        )

        self.hide()

    def _save_geometry(self):
        if not self.isVisible():
            return

        save_dashboard_window_geometry(
            self,
            get_database(),
        )

    def _schedule_geometry_save(self):
        if self.isVisible():
            self._geometry_timer.start()

    def moveEvent(self, event):
        super().moveEvent(event)
        self._schedule_geometry_save()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._schedule_geometry_save()

    def show_dashboard(self):
        restore_dashboard_window_geometry(
            self,
            get_database(),
        )

        self.dashboard_page.reload_user_layout()
        self.dashboard_page.refresh_dashboard()

        self.dashboard_page.update()

        title_bar = getattr(self, "_mobiglas_title_bar", None)
        if title_bar is not None:
            title_bar.restore_from_maximize()

        if self.isMinimized():
            self.showNormal()

        self.show()

        self.raise_()

        self.activateWindow()

    def hide_dashboard(self, *, user_action=True):
        self._save_geometry()
        self.dashboard_page.persist_layout()
        self.dashboard_page.mark_as_embedded()

        if user_action:
            set_dashboard_open_on_startup(
                get_database(),
                False,
            )

        self.hide()

    def toggle_visibility(self):

        if self.isVisible():

            self.hide_dashboard()

        else:

            self.show_dashboard()
            
    def set_always_on_top(
        self,
        enabled
    ):

        self.setWindowFlag(
            Qt.WindowStaysOnTopHint,
            enabled
        )

        self.show()
            
    def closeEvent(
        self,
        event
    ):
        self._save_geometry()
        self.dashboard_page.persist_layout()
        self.dashboard_page.refresh_dashboard()

        self.dashboard_page.mark_as_embedded()

        parent_window = (
            self.dashboard_page
            .get_parent_window()
        )

        if parent_window:

            parent_window.btn_dashboard.setText(
                "Übersicht"
            )

        super().closeEvent(
            event
        )
