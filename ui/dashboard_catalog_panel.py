"""Widget-Katalog (rechte Seitenleiste im Bearbeiten-Modus)."""

from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
)

from ui.page_layout import hud_divider
from config.i18n import tr
from ui.dashboard_widget_registry import (
    MIME_DASHBOARD_WIDGET,
    widget_definitions,
    _event_local_point,
)


def _style_property(widget, name, value):
    widget.setProperty(name, value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


class CatalogDragItem(QFrame):

    def __init__(self, widget_id, title, parent=None):
        super().__init__(parent)
        self.widget_id = widget_id
        self.setObjectName("dashboardCatalogItem")
        self.setCursor(Qt.CursorShape.OpenHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 7)
        label = QLabel(title.upper())
        label.setObjectName("dashboardCatalogLabel")
        layout.addWidget(label)

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        hot_spot = _event_local_point(event)
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(
            MIME_DASHBOARD_WIDGET,
            self.widget_id.encode("utf-8"),
        )
        mime.setText(f"new:{self.widget_id}")
        drag.setMimeData(mime)

        pixmap = self.grab()
        if not pixmap.isNull():
            drag.setPixmap(pixmap)
            drag.setHotSpot(hot_spot)

        drag.exec(Qt.DropAction.CopyAction)


class DashboardCatalogPanel(QWidget):

    widget_returned = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboardCatalogPanel")
        self.setMinimumWidth(220)
        self.setMaximumWidth(280)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(8)

        title = QLabel(tr("dashboard.catalog.title"))
        title.setObjectName("dashboardCatalogTitle")
        outer.addWidget(title)
        outer.addLayout(hud_divider())

        hint = QLabel(tr("dashboard.catalog.hint"))
        hint.setObjectName("dashboardCatalogHint")
        hint.setWordWrap(True)
        outer.addWidget(hint)

        self._drop_zone = QFrame()
        self._drop_zone.setObjectName("dashboardCatalogDrop")
        self._drop_zone.setAcceptDrops(True)
        drop_layout = QVBoxLayout(self._drop_zone)
        drop_layout.setContentsMargins(8, 8, 8, 8)
        drop_label = QLabel(tr("dashboard.catalog.drop"))
        drop_label.setObjectName("dashboardCatalogDropLabel")
        drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_label.setWordWrap(True)
        drop_layout.addWidget(drop_label)
        outer.addWidget(self._drop_zone)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setObjectName("dashboardCatalogScroll")
        scroll.viewport().setObjectName("dashboardCatalogScrollViewport")
        scroll.viewport().setAutoFillBackground(False)

        host = QWidget()
        host.setObjectName("dashboardCatalogList")
        self._list_layout = QVBoxLayout(host)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(6)
        self._list_layout.addStretch()

        scroll.setWidget(host)
        outer.addWidget(scroll, 1)

        self._items: dict[str, CatalogDragItem] = {}
        self._build_items()

        self._drop_zone.dragEnterEvent = self._on_drop_enter
        self._drop_zone.dragMoveEvent = self._on_drop_enter
        self._drop_zone.dragLeaveEvent = self._on_drop_leave
        self._drop_zone.dropEvent = self._on_drop

    def _build_items(self):
        defs = widget_definitions()
        for widget_id, meta in defs.items():
            item = CatalogDragItem(widget_id, meta["title"])
            self._items[widget_id] = item
            self._list_layout.insertWidget(
                self._list_layout.count() - 1,
                item,
            )

    def sync_availability(self, on_canvas_ids):
        for widget_id, item in self._items.items():
            item.setEnabled(widget_id not in on_canvas_ids)

    def _on_drop_enter(self, event):
        if event.mimeData().text().startswith("move:"):
            _style_property(self._drop_zone, "dragActive", "true")
            event.acceptProposedAction()
            return
        event.ignore()

    def _on_drop_leave(self, event):
        _style_property(self._drop_zone, "dragActive", "false")
        event.accept()

    def _on_drop(self, event):
        _style_property(self._drop_zone, "dragActive", "false")
        text = event.mimeData().text()
        if not text.startswith("move:"):
            event.ignore()
            return
        widget_id = text.split(":", 1)[1]
        self.widget_returned.emit(widget_id)
        event.acceptProposedAction()
