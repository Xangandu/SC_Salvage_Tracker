"""Raster-Canvas für das modulare Dashboard."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QMimeData, QRect, QPoint
from PySide6.QtGui import QDrag, QPainter, QPen, QColor, QBrush
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QPushButton,
    QMenu,
    QSizePolicy,
)

from ui.dashboard_grid_utils import (
    can_place,
    empty_layout,
    infer_size_key,
    resolve_layout_collisions,
    spans_for_size,
    widget_entry,
    migrate_layout,
)
from ui.dashboard_size_utils import (
    next_larger_size,
    widget_needs_wider_size,
)
from ui.dashboard_widget_registry import (
    GRID_COLUMNS,
    GRID_GAP,
    GRID_MARGIN,
    MIME_DASHBOARD_WIDGET,
    widget_definitions,
    _event_local_point,
    _event_global_point,
)
from ui.theme_manager import ThemeManager

MIN_GRID_ROWS = 12


class PlacedWidgetFrame(QFrame):

    remove_requested = Signal(str)

    def __init__(
        self,
        widget_id,
        inner_widget,
        edit_mode_provider,
        canvas,
        parent=None,
    ):
        super().__init__(parent)
        self.widget_id = widget_id
        self._canvas = canvas
        self.setObjectName("dashboardPlacedWidget")
        self._edit_mode_provider = edit_mode_provider
        self._drag_start = None
        self.setAcceptDrops(True)
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )

        self._inner_widget = inner_widget
        self._inner_widget.setParent(self)
        self._inner_widget.setMinimumSize(0, 0)
        self._inner_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Minimum,
        )

        self.remove_button = QPushButton("×", self)
        self.remove_button.setObjectName("dashboardWidgetRemove")
        self.remove_button.setFixedSize(18, 18)
        self.remove_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_button.clicked.connect(
            lambda: self.remove_requested.emit(self.widget_id)
        )
        self._sync_edit_chrome()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._inner_widget.setGeometry(0, 0, self.width(), self.height())
        margin = 4
        self.remove_button.move(
            max(margin, self.width() - self.remove_button.width() - margin),
            margin,
        )
        self.remove_button.raise_()

    def _sync_edit_chrome(self):
        editing = self._edit_mode_provider()
        self.remove_button.setVisible(editing)

    def refresh_edit_chrome(self):
        self._sync_edit_chrome()

    def dragEnterEvent(self, event):
        self._canvas._handle_drag_enter(event, self)

    def dragMoveEvent(self, event):
        self._canvas._handle_drag_move(event, self)

    def dragLeaveEvent(self, event):
        self._canvas._handle_drag_leave(event)

    def dropEvent(self, event):
        self._canvas._handle_drop(event, self)

    def _start_drag(self, hot_spot):
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(
            MIME_DASHBOARD_WIDGET,
            self.widget_id.encode("utf-8"),
        )
        mime.setText(f"move:{self.widget_id}")
        drag.setMimeData(mime)

        pixmap = self.grab()
        if not pixmap.isNull():
            drag.setPixmap(pixmap)
            drag.setHotSpot(hot_spot)

        drag.exec(Qt.DropAction.MoveAction)

    def mousePressEvent(self, event):
        if (
            not self._edit_mode_provider()
            or event.button() != Qt.MouseButton.LeftButton
        ):
            super().mousePressEvent(event)
            return
        self._drag_start = _event_local_point(event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            not self._edit_mode_provider()
            or self._drag_start is None
            or not (event.buttons() & Qt.MouseButton.LeftButton)
        ):
            super().mouseMoveEvent(event)
            return

        if (
            _event_local_point(event) - self._drag_start
        ).manhattanLength() < 12:
            return

        self._start_drag(self._drag_start)
        self._drag_start = None


class DashboardGridCanvas(QWidget):

    layout_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboardGridCanvas")
        self.setAcceptDrops(True)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self._edit_mode = False
        self._pool: dict[str, QWidget] = {}
        self._stash = QWidget(self)
        self._stash.setObjectName("dashboardWidgetStash")
        self._stash.setAttribute(
            Qt.WidgetAttribute.WA_DontShowOnScreen,
            True,
        )
        self._stash.hide()

        self._layout_data = empty_layout()
        self._base_sizes: dict[str, str] = {}
        self._wrappers: dict[str, PlacedWidgetFrame] = {}
        self._drag_preview = None
        self._last_host_pos = QPoint()
        self._last_grid_width = -1

        self._grid_host = QWidget(self)
        self._grid_host.setObjectName("dashboardGridHost")
        self._grid_host.setAcceptDrops(True)
        self._grid_host.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self._grid_spacing = GRID_GAP
        self._grid_margins = GRID_MARGIN

        host_layout = QVBoxLayout(self)
        host_layout.setContentsMargins(0, 0, 0, 0)
        host_layout.addWidget(self._grid_host, 1)

        self._grid_host.dragEnterEvent = self._host_drag_enter
        self._grid_host.dragMoveEvent = self._host_drag_move
        self._grid_host.dragLeaveEvent = self._host_drag_leave
        self._grid_host.dropEvent = self._host_drop

        self._apply_grid_minimum_size()

    def _apply_grid_minimum_size(self):
        self._sync_grid_host_height()

    def _sync_grid_host_height(self):
        floor = (
            self._row_block_height(MIN_GRID_ROWS)
            + self._grid_margins * 2
        )
        self._grid_host.setMinimumHeight(max(floor, self.height()))

    def _grid_paint_height(self):
        host_geom = self._grid_host.geometry()
        floor = self._row_block_height(MIN_GRID_ROWS)
        canvas_inner = self.height() - host_geom.y() - self._grid_margins * 2
        host_inner = host_geom.height() - self._grid_margins * 2
        return max(int(canvas_inner), int(host_inner), floor)

    def set_widget_pool(self, pool):
        self._pool = pool
        for widget in pool.values():
            widget.setParent(self._stash)
            widget.setMinimumSize(0, 0)

    def set_edit_mode(self, enabled):
        self._edit_mode = enabled
        for wrapper in self._wrappers.values():
            wrapper.refresh_edit_chrome()
        self._sync_grid_host_height()
        self.update()

    def get_layout_data(self):
        widgets = []
        for entry in self._layout_data.get("widgets", []):
            widget_id = entry["widget_id"]
            base_size = self._base_sizes.get(
                widget_id,
                infer_size_key(entry),
            )
            col_span, row_span = spans_for_size(base_size)
            widgets.append(
                {
                    "widget_id": widget_id,
                    "col": entry["col"],
                    "row": entry["row"],
                    "col_span": col_span,
                    "row_span": row_span,
                    "size": base_size,
                }
            )
        return {
            "version": self._layout_data.get("version", 1),
            "grid_epoch": self._layout_data.get("grid_epoch", 1),
            "columns": GRID_COLUMNS,
            "placement_mode": self._layout_data.get(
                "placement_mode",
                "hybrid",
            ),
            "widgets": widgets,
        }

    def _sync_base_sizes(self):
        self._base_sizes = {
            entry["widget_id"]: infer_size_key(entry)
            for entry in self._layout_data.get("widgets", [])
        }

    def load_layout_data(self, layout_data):
        self._layout_data = migrate_layout(
            dict(layout_data or empty_layout())
        )
        self._sync_base_sizes()
        self._rebuild_grid()

    def widgets_on_canvas(self):
        return {
            entry["widget_id"]
            for entry in self._layout_data.get("widgets", [])
        }

    def remove_widget(self, widget_id):
        entries = self._layout_data.get("widgets", [])
        self._layout_data["widgets"] = [
            e for e in entries if e["widget_id"] != widget_id
        ]
        self._base_sizes.pop(widget_id, None)
        self._detach_wrapper(widget_id)
        self.layout_changed.emit()

    def add_widget_at(
        self,
        widget_id,
        col,
        row,
        size_key,
        *,
        replace=False,
    ):
        if widget_id not in widget_definitions():
            return False

        if widget_id in self.widgets_on_canvas() and not replace:
            return False

        if replace:
            self.remove_widget(widget_id)

        entry = widget_entry(widget_id, col, row, size_key)
        if not can_place(entry, self._layout_data["widgets"]):
            return False

        self._layout_data.setdefault("widgets", []).append(entry)
        self._base_sizes[widget_id] = size_key
        self._mount_entry(entry)
        self.layout_changed.emit()
        return True

    def move_widget(self, widget_id, col, row):
        for index, entry in enumerate(
            self._layout_data.get("widgets", [])
        ):
            if entry["widget_id"] != widget_id:
                continue
            trial = dict(entry)
            trial["col"] = col
            trial["row"] = row
            if not can_place(
                trial,
                self._layout_data["widgets"],
                ignore_index=index,
            ):
                return False
            entry["col"] = col
            entry["row"] = row
            size_key = infer_size_key(entry)
            entry["size"] = size_key
            col_span, min_row_span = spans_for_size(size_key)
            entry["col_span"] = col_span
            entry["row_span"] = max(
                int(entry.get("row_span") or min_row_span),
                min_row_span,
            )
            self._apply_wrapper_geometry(entry)
            self.layout_changed.emit()
            return True
        return False

    def _detach_wrapper(self, widget_id):
        wrapper = self._wrappers.pop(widget_id, None)
        if wrapper is None:
            return
        inner = self._pool.get(widget_id)
        if inner is not None:
            inner.setParent(self._stash)
        wrapper.deleteLater()

    def _mount_entry(self, entry):
        widget_id = entry["widget_id"]
        inner = self._pool.get(widget_id)
        if inner is None:
            return

        wrapper = PlacedWidgetFrame(
            widget_id,
            inner,
            lambda: self._edit_mode,
            self,
            parent=self._grid_host,
        )
        wrapper.remove_requested.connect(self.remove_widget)
        self._wrappers[widget_id] = wrapper
        self._apply_wrapper_geometry(entry)
        wrapper.show()

    def _apply_wrapper_geometry(self, entry):
        wrapper = self._wrappers.get(entry["widget_id"])
        if wrapper is None:
            return
        rect = self._cell_rect_on_host(
            entry["col"],
            entry["row"],
            entry["col_span"],
            entry["row_span"],
        )
        wrapper.setFixedSize(rect.size())
        wrapper.move(rect.topLeft())
        wrapper._inner_widget.setGeometry(
            0,
            0,
            rect.width(),
            rect.height(),
        )

    def _apply_all_geometries(self):
        for entry in self._layout_data.get("widgets", []):
            self._apply_wrapper_geometry(entry)

    def _row_unit_px(self):
        return ThemeManager.effective_row_unit_px()

    def _row_block_height(self, row_span):
        spacing = self._grid_spacing
        row_unit = self._row_unit_px()
        return row_span * row_unit + max(0, row_span - 1) * spacing

    def _height_to_row_span(self, pixel_height):
        if pixel_height <= 0:
            return 1
        span = 1
        while self._row_block_height(span) < pixel_height:
            span += 1
            if span > 64:
                break
        return span

    def _measure_content_height(self, inner, width):
        width = max(int(width), 24)
        inner.setFixedWidth(width)
        layout = inner.layout()
        if layout is not None:
            layout.invalidate()
            layout.activate()
            margins = layout.contentsMargins()
            inner_w = max(
                width - margins.left() - margins.right(),
                1,
            )
            total = margins.top() + margins.bottom()
            spacing = layout.spacing()
            first = True
            for index in range(layout.count()):
                item = layout.itemAt(index)
                if item is None:
                    continue
                widget = item.widget()
                if widget is not None:
                    if hasattr(widget, "heightForWidth"):
                        wrapped = widget.heightForWidth(inner_w)
                        if wrapped > 0:
                            block_h = wrapped
                        else:
                            block_h = widget.sizeHint().height()
                    else:
                        block_h = widget.sizeHint().height()
                    block_h = max(
                        block_h,
                        widget.minimumSizeHint().height(),
                    )
                else:
                    block_h = item.sizeHint().height()
                if not first:
                    total += spacing
                first = False
                total += block_h
            return max(total, 1)

        inner.adjustSize()
        hint = inner.sizeHint()
        min_hint = inner.minimumSizeHint()
        return max(hint.height(), min_hint.height(), 1)

    def reflow_content_sizes(self):
        if getattr(self, "_reflow_guard", False):
            return
        self._reflow_guard = True
        try:
            self._reflow_content_sizes_impl()
        finally:
            self._reflow_guard = False

    def _reflow_content_sizes_impl(self):
        widgets = self._layout_data.get("widgets", [])
        if not widgets:
            return

        host_w = self._grid_host.width()
        if host_w <= 0:
            return

        spacing, cell_w, _inner_w = self._grid_metrics()
        pad_v, pad_h = ThemeManager.dashboard_card_padding()
        updated = []

        for entry in widgets:
            trial = dict(entry)
            inner = self._pool.get(entry["widget_id"])
            widget_id = entry["widget_id"]
            base_size = self._base_sizes.get(
                widget_id,
                infer_size_key(entry),
            )
            size_key = base_size
            col_span, min_row_span = spans_for_size(size_key)
            trial["size"] = base_size
            effective_size = base_size

            widget_def = widget_definitions().get(widget_id, {})
            if widget_def.get("reflow") is False:
                trial["col_span"] = col_span
                trial["row_span"] = min_row_span
                if inner is not None:
                    inner.setMinimumWidth(0)
                    inner.setMaximumWidth(16777215)
                updated.append(trial)
                continue

            if inner is None:
                trial["col_span"] = col_span
                updated.append(trial)
                continue

            allowed_sizes = widget_def.get(
                "sizes",
                ("1x1", "2x1", "2x2"),
            )
            while True:
                col_span, min_row_span = spans_for_size(
                    effective_size,
                )
                block_w = self._block_width(
                    cell_w,
                    spacing,
                    col_span,
                )
                content_width = max(
                    int(block_w) - pad_h * 2,
                    24,
                )
                if not widget_needs_wider_size(
                    inner,
                    content_width,
                ):
                    break
                larger = next_larger_size(
                    effective_size,
                    allowed_sizes,
                )
                if larger is None or larger == effective_size:
                    break
                effective_size = larger

            col_span, min_row_span = spans_for_size(effective_size)
            trial["col_span"] = col_span

            block_w = self._block_width(
                cell_w,
                spacing,
                col_span,
            )
            content_width = max(int(block_w) - pad_h * 2, 24)
            content_h = self._measure_content_height(
                inner,
                content_width,
            )
            total_h = content_h + pad_v * 2 + 2
            content_row_span = self._height_to_row_span(total_h)
            trial["row_span"] = max(
                min_row_span,
                content_row_span,
            )
            inner.setMinimumWidth(0)
            inner.setMaximumWidth(16777215)
            updated.append(trial)

        self._layout_data["widgets"] = resolve_layout_collisions(
            updated
        )
        self._apply_all_geometries()
        self._sync_grid_host_height()
        self.update()

    def _rebuild_grid(self):
        self.setUpdatesEnabled(False)
        self._grid_host.setUpdatesEnabled(False)
        try:
            for widget_id in list(self._wrappers.keys()):
                self._detach_wrapper(widget_id)

            for entry in self._layout_data.get("widgets", []):
                self._mount_entry(entry)

            self._apply_grid_minimum_size()
            self.reflow_content_sizes()
        finally:
            self._grid_host.setUpdatesEnabled(True)
            self.setUpdatesEnabled(True)
            self.update()

    def _grid_metrics(self):
        host_w = max(self._grid_host.width(), 200)
        inner_w = host_w - self._grid_margins * 2
        inner_w = max(inner_w, 1)
        spacing = self._grid_spacing
        cell_w = (
            inner_w - spacing * (GRID_COLUMNS - 1)
        ) / GRID_COLUMNS
        cell_w = max(cell_w, 1)
        return spacing, cell_w, inner_w

    def _grid_width(self, cell_w, spacing):
        return (
            GRID_COLUMNS * cell_w + (GRID_COLUMNS - 1) * spacing
        )

    def _block_width(self, cell_w, spacing, col_span):
        return (
            col_span * cell_w + max(0, col_span - 1) * spacing
        )

    def _cell_rect_on_host(self, col, row, col_span=1, row_span=1):
        spacing, cell_w, _inner_w = self._grid_metrics()
        pitch_x = cell_w + spacing
        pitch_y = self._row_unit_px() + spacing
        x = self._grid_margins + col * pitch_x
        y = self._grid_margins + row * pitch_y
        width = self._block_width(cell_w, spacing, col_span)
        height = self._row_block_height(row_span)
        return QRect(int(x), int(y), int(width), int(height))

    def _cell_at_host(self, host_pos: QPoint, col_span=1, row_span=1):
        spacing, cell_w, inner_w = self._grid_metrics()
        pitch_x = cell_w + spacing
        pitch_y = self._row_unit_px() + spacing
        grid_w = self._grid_width(cell_w, spacing)
        block_w = self._block_width(cell_w, spacing, col_span)
        block_h = self._row_block_height(row_span)

        rel_x = host_pos.x() - self._grid_margins
        rel_y = host_pos.y() - self._grid_margins
        rel_x = max(0.0, min(rel_x, grid_w - 1))
        rel_y = max(0.0, rel_y)

        max_col = max(0, GRID_COLUMNS - col_span)
        col = int((rel_x + pitch_x * 0.5 - block_w * 0.5) / pitch_x)
        row = int((rel_y + pitch_y * 0.5 - block_h * 0.5) / pitch_y)
        col = max(0, min(col, max_col))
        row = max(0, row)
        return col, row

    def _host_pos_from_event(self, event, source_widget):
        global_pos = _event_global_point(event, source_widget)
        return self._grid_host.mapFromGlobal(global_pos)

    def _resolve_drop_cell(
        self,
        col_span,
        row_span,
        saved_preview,
        host_pos,
    ):
        if saved_preview and saved_preview.get("valid"):
            if (
                saved_preview.get("col_span") == col_span
                and saved_preview.get("row_span") == row_span
            ):
                return saved_preview["col"], saved_preview["row"]
        return self._cell_at_host(host_pos, col_span, row_span)

    def _spans_for_mime(self, mime, widget_id):
        if mime.text().startswith("move:"):
            for entry in self._layout_data.get("widgets", []):
                if entry["widget_id"] == widget_id:
                    return entry["col_span"], entry["row_span"]

        defs = widget_definitions().get(widget_id, {})
        return spans_for_size(defs.get("default_size", "1x1"))

    def _ignore_index_for_move(self, mime, widget_id):
        if not mime.text().startswith("move:"):
            return None
        for index, entry in enumerate(
            self._layout_data.get("widgets", [])
        ):
            if entry["widget_id"] == widget_id:
                return index
        return None

    def _update_drag_preview(self, event, source_widget):
        mime = event.mimeData()
        if not mime.hasFormat(MIME_DASHBOARD_WIDGET):
            self._drag_preview = None
            return

        widget_id = bytes(mime.data(MIME_DASHBOARD_WIDGET)).decode(
            "utf-8"
        )
        col_span, row_span = self._spans_for_mime(mime, widget_id)
        host_pos = self._host_pos_from_event(event, source_widget)
        self._last_host_pos = host_pos
        col, row = self._cell_at_host(host_pos, col_span, row_span)
        trial = {
            "widget_id": widget_id,
            "col": col,
            "row": row,
            "col_span": col_span,
            "row_span": row_span,
        }
        valid = can_place(
            trial,
            self._layout_data.get("widgets", []),
            ignore_index=self._ignore_index_for_move(mime, widget_id),
        )
        self._drag_preview = {
            "col": col,
            "row": row,
            "col_span": col_span,
            "row_span": row_span,
            "valid": valid,
        }

    def _clear_drag_preview(self):
        if self._drag_preview is not None:
            self._drag_preview = None
            self.update()

    def _pick_size(self, widget_id, global_pos):
        defs = widget_definitions()[widget_id]
        sizes = defs.get("sizes", ("1x1",))
        if len(sizes) == 1:
            return sizes[0]

        menu = QMenu(self)
        for size_key in sizes:
            menu.addAction(size_key)
        action = menu.exec(global_pos)
        if action is None:
            return None
        return action.text()

    def _handle_drag_enter(self, event, source_widget):
        if event.mimeData().hasFormat(MIME_DASHBOARD_WIDGET):
            self._update_drag_preview(event, source_widget)
            event.acceptProposedAction()
            return
        event.ignore()

    def _handle_drag_move(self, event, source_widget):
        if event.mimeData().hasFormat(MIME_DASHBOARD_WIDGET):
            self._update_drag_preview(event, source_widget)
            event.acceptProposedAction()
            self.update()
            return
        event.ignore()

    def _handle_drag_leave(self, _event):
        pass

    def _handle_drop(self, event, source_widget):
        saved_preview = self._drag_preview
        self._clear_drag_preview()
        mime = event.mimeData()
        if not mime.hasFormat(MIME_DASHBOARD_WIDGET):
            event.ignore()
            return

        widget_id = bytes(mime.data(MIME_DASHBOARD_WIDGET)).decode(
            "utf-8"
        )
        host_pos = self._last_host_pos
        if host_pos.isNull():
            host_pos = self._host_pos_from_event(event, source_widget)

        if mime.text().startswith("move:"):
            col_span = 3
            row_span = 2
            for entry in self._layout_data.get("widgets", []):
                if entry["widget_id"] == widget_id:
                    col_span = entry["col_span"]
                    row_span = entry["row_span"]
                    break
            col, row = self._resolve_drop_cell(
                col_span,
                row_span,
                saved_preview,
                host_pos,
            )
            if self.move_widget(widget_id, col, row):
                event.acceptProposedAction()
            else:
                event.ignore()
            return

        if widget_id in self.widgets_on_canvas():
            event.ignore()
            return

        size_key = self._pick_size(
            widget_id,
            _event_global_point(event, source_widget),
        )
        if size_key is None:
            event.ignore()
            return

        col_span, row_span = spans_for_size(size_key)
        col, row = self._resolve_drop_cell(
            col_span,
            row_span,
            saved_preview,
            host_pos,
        )

        if self.add_widget_at(widget_id, col, row, size_key):
            event.acceptProposedAction()
        else:
            event.ignore()

    def _host_drag_enter(self, event):
        self._handle_drag_enter(event, self._grid_host)

    def _host_drag_move(self, event):
        self._handle_drag_move(event, self._grid_host)

    def _host_drag_leave(self, event):
        self._handle_drag_leave(event)

    def _host_drop(self, event):
        self._handle_drop(event, self._grid_host)

    def dragEnterEvent(self, event):
        self._handle_drag_enter(event, self)

    def dragMoveEvent(self, event):
        self._handle_drag_move(event, self)

    def dragLeaveEvent(self, event):
        self._handle_drag_leave(event)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._handle_drop(event, self)

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_grid_host_height()
        self.reflow_content_sizes()
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_grid_host_height()
        if event.size().width() != self._last_grid_width:
            self._last_grid_width = event.size().width()
            self._apply_all_geometries()
            self.reflow_content_sizes()
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._edit_mode:
            return

        painter = QPainter(self)
        host_geom = self._grid_host.geometry()
        if host_geom.width() <= 0:
            painter.end()
            return

        spacing, cell_w, _inner_w = self._grid_metrics()
        pitch_x = cell_w + spacing
        pitch_y = self._row_unit_px() + spacing
        grid_w = int(self._grid_width(cell_w, spacing))

        x0 = host_geom.x() + self._grid_margins
        y0 = host_geom.y() + self._grid_margins
        height = self._grid_paint_height()

        pen = QPen(QColor(51, 72, 92, 48))
        pen.setWidth(1)
        painter.setPen(pen)

        for col in range(GRID_COLUMNS + 1):
            x = int(x0 + col * pitch_x)
            painter.drawLine(x, y0, x, y0 + height)

        row = 0
        while row * pitch_y <= height:
            y = int(y0 + row * pitch_y)
            painter.drawLine(x0, y, x0 + grid_w, y)
            row += 1

        preview = self._drag_preview
        if preview is not None:
            rect = self._cell_rect_on_host(
                preview["col"],
                preview["row"],
                preview["col_span"],
                preview["row_span"],
            )
            rect.translate(host_geom.topLeft())
            if preview["valid"]:
                fill = QColor(224, 122, 42, 28)
                border = QColor(224, 122, 42, 140)
            else:
                fill = QColor(255, 80, 80, 22)
                border = QColor(255, 80, 80, 90)
            painter.fillRect(rect, QBrush(fill))
            pen = QPen(border)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(rect.adjusted(0, 0, -1, -1))

        painter.end()
