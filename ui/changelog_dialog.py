from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QTabWidget,
    QWidget,
)

from config.i18n import tr
from config.version import (
    APP_NAME,
    format_version_subtitle,
)
from config.release_notes import (
    load_patchnotes,
    load_roadmap,
)
from ui.page_layout import (
    page_title,
    hud_divider,
    configure_aaa_tabs,
)
from ui.mobiglas_window_frame import (
    MobiglasFramelessMixin,
    apply_mobiglas_window_frame,
)


class ChangelogDialog(MobiglasFramelessMixin, QDialog):

    def __init__(self):

        super().__init__()

        self.setObjectName("mobiglasDialog")
        self.setWindowTitle(tr("changelog.title"))

        self.resize(920, 640)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = page_title(
            tr("changelog.page_title", app_name=APP_NAME)
        )
        layout.addWidget(title)

        subtitle = QLabel(format_version_subtitle())
        subtitle.setObjectName("mutedLabel")
        layout.addWidget(subtitle)
        layout.addLayout(hud_divider())

        tabs = QTabWidget()
        tabs.setObjectName("changelogTabs")
        configure_aaa_tabs(tabs)

        patchnotes_view = QTextEdit()
        patchnotes_view.setObjectName("changelogView")
        patchnotes_view.setReadOnly(True)
        patchnotes_view.setPlainText(load_patchnotes())

        roadmap_view = QTextEdit()
        roadmap_view.setObjectName("changelogView")
        roadmap_view.setReadOnly(True)
        roadmap_view.setPlainText(load_roadmap())

        tabs.addTab(patchnotes_view, tr("changelog.tab.patchnotes"))
        tabs.addTab(roadmap_view, tr("changelog.tab.roadmap"))
        layout.addWidget(tabs)

        self.setLayout(layout)

        apply_mobiglas_window_frame(
            self,
            title=tr("changelog.title"),
            dialog=True,
        )
