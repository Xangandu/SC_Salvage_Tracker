"""Gemeinsames Seiten-Layout für MobiGlas-Oberflächen."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from config.paths import asset_path


def configure_aaa_tabs(tab_widget):
    """Launcher-Stil: flache Tab-Leiste ohne Qt-Standard-Rahmen."""
    tab_widget.setDocumentMode(True)
    bar = tab_widget.tabBar()
    bar.setExpanding(False)
    bar.setDrawBase(False)
    bar.setUsesScrollButtons(True)


def build_page_scroll(
    content_widget,
    scroll_object_name="pageScroll",
):
    scroll = QScrollArea()
    scroll.setObjectName(scroll_object_name)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setWidget(content_widget)
    return scroll


def page_content_widget():
    content = QWidget()
    content.setObjectName("pageContent")

    layout = QVBoxLayout(content)
    layout.setContentsMargins(24, 20, 24, 20)
    layout.setSpacing(16)

    return content, layout


def wrap_page(content_widget):
    outer = QWidget()
    outer_layout = QVBoxLayout(outer)
    outer_layout.setContentsMargins(0, 0, 0, 0)
    outer_layout.addWidget(
        build_page_scroll(content_widget)
    )
    return outer


def page_title(text):
    label = QLabel(text)
    label.setObjectName("pageTitle")
    return label


def section_accent(text):
    label = QLabel(text)
    label.setObjectName("sectionAccent")
    return label


def subsection_title(text):
    label = QLabel(text)
    label.setObjectName("subSectionTitle")
    return label


def form_label(text):
    label = QLabel(text)
    label.setObjectName("formLabel")
    return label


def add_form_field(layout, label_text, widget):
    layout.addWidget(form_label(label_text))
    layout.addWidget(widget)


def info_panel():
    panel = QFrame()
    panel.setObjectName("infoPanel")
    panel_layout = QVBoxLayout(panel)
    panel_layout.setSpacing(10)
    return panel, panel_layout


def page_panel():
    panel = QFrame()
    panel.setObjectName("pagePanel")
    panel_layout = QVBoxLayout(panel)
    panel_layout.setSpacing(10)
    return panel, panel_layout


def primary_button(text):
    button = QPushButton(text)
    button.setObjectName("primaryAction")
    return button


def svg_icon_widget(icon_path, size=32, object_name=None):
    from PySide6.QtSvgWidgets import QSvgWidget

    widget = QSvgWidget(str(asset_path(icon_path)))
    if object_name:
        widget.setObjectName(object_name)
    widget.setFixedSize(size, size)
    widget.setAttribute(
        Qt.WidgetAttribute.WA_TranslucentBackground,
    )
    return widget


def empty_info_panel(message, icon_path=None):
    widget = QWidget()
    widget.setObjectName("emptyInfoPanel")

    row = QHBoxLayout(widget)
    row.setContentsMargins(12, 10, 12, 10)

    if icon_path:
        row.addWidget(
            svg_icon_widget(icon_path, size=32)
        )

    text_label = QLabel(message)
    text_label.setObjectName("emptyInfo")
    text_label.setWordWrap(True)
    row.addWidget(text_label, 1)

    return widget


def hud_divider():
    row = QHBoxLayout()
    row.setSpacing(8)

    left = QFrame()
    left.setObjectName("hudLine")
    left.setFrameShape(QFrame.Shape.HLine)

    center = QLabel("▪")
    center.setObjectName("hudMarker")
    center.setAlignment(Qt.AlignmentFlag.AlignCenter)

    right = QFrame()
    right.setObjectName("hudLine")
    right.setFrameShape(QFrame.Shape.HLine)

    row.addWidget(left, 1)
    row.addWidget(center, 0)
    row.addWidget(right, 1)

    return row


def hud_divider_vertical(*, compact: bool = False):
    col = QVBoxLayout()
    col.setSpacing(2 if compact else 8)
    col.setContentsMargins(0, 0, 0, 0)

    top = QFrame()
    top.setObjectName("hudLineVertical")
    top.setFrameShape(QFrame.Shape.VLine)
    if compact:
        top.setFixedHeight(6)

    center = QLabel("▪")
    center.setObjectName("hudMarkerCompact" if compact else "hudMarker")
    center.setAlignment(Qt.AlignmentFlag.AlignCenter)

    bottom = QFrame()
    bottom.setObjectName("hudLineVertical")
    bottom.setFrameShape(QFrame.Shape.VLine)
    if compact:
        bottom.setFixedHeight(6)

    if compact:
        col.addWidget(top, 0, Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(center, 0, Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(bottom, 0, Qt.AlignmentFlag.AlignHCenter)
    else:
        col.addWidget(top, 1)
        col.addWidget(center, 0)
        col.addWidget(bottom, 1)

    return col


def hud_divider_vertical_widget(*, width: int = 10) -> QWidget:
    host = QWidget()
    host.setObjectName("hudDividerVerticalHost")
    host.setAutoFillBackground(False)
    host.setFixedWidth(width)
    host.setSizePolicy(
        QSizePolicy.Policy.Fixed,
        QSizePolicy.Policy.Expanding,
    )
    host.setLayout(hud_divider_vertical(compact=False))
    return host


def nav_edition_divider(edition_label):
    """HUD-Linie mit Edition-Badge mittig (ersetzt den Trennpunkt)."""
    row = QHBoxLayout()
    row.setSpacing(6)
    row.setContentsMargins(0, 2, 0, 0)

    left = QFrame()
    left.setObjectName("hudLine")
    left.setFrameShape(QFrame.Shape.HLine)

    right = QFrame()
    right.setObjectName("hudLine")
    right.setFrameShape(QFrame.Shape.HLine)

    row.addWidget(left, 1)
    row.addWidget(edition_label, 0, Qt.AlignmentFlag.AlignHCenter)
    row.addWidget(right, 1)

    return row


def nav_version_divider():
    from PySide6.QtSvgWidgets import QSvgWidget

    host = QWidget()
    host.setObjectName("navVersionDividerHost")

    row = QHBoxLayout(host)
    row.setContentsMargins(10, 10, 10, 2)
    row.setSpacing(0)

    divider = QSvgWidget(
        str(asset_path("assets/images/nav_version_divider.svg"))
    )
    divider.setObjectName("navVersionDivider")
    divider.setFixedHeight(22)
    divider.setAttribute(
        Qt.WidgetAttribute.WA_TranslucentBackground,
    )
    divider.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Fixed,
    )

    row.addWidget(divider, 1)
    return host
