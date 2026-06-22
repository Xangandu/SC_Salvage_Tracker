from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout
)

from PySide6.QtCore import Qt

from ui.mobiglas_window_frame import (
    MobiglasFramelessMixin,
    apply_mobiglas_window_frame,
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

        self.resize(
            1800,
            1000
        )
        
        self.setWindowFlag(
            Qt.WindowStaysOnTopHint,
            False
        )

        self.setAttribute(
            Qt.WA_QuitOnClose,
            False,
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

        self.hide()

    def show_dashboard(self):

        self.dashboard_page.apply_dashboard_layout()
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

    def hide_dashboard(self):

        self.dashboard_page.mark_as_embedded()

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

        self.dashboard_page.apply_dashboard_layout()
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