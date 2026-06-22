"""Hilfsfunktionen für Dashboard-Raster-Layouts."""

from ui.dashboard_layouts import (
    DASHBOARD_LAYOUTS,
    SECTION_CARD_KEYS,
)
from ui.dashboard_widget_registry import (
    GRID_COLUMNS,
    SIZE_SPANS,
    widget_definitions,
)

LAYOUT_VERSION = 2
GRID_EPOCH = 4

# Alte Raster-Definitionen (vor kompaktem Redesign)
LEGACY_SPAN_TO_SIZE = {
    (3, 2): "1x1",
    (6, 2): "2x1",
    (6, 4): "2x2",
    (2, 2): "1x1",
    (4, 2): "2x1",
    (5, 4): "2x2",
}


def empty_layout():
    return {
        "version": LAYOUT_VERSION,
        "grid_epoch": GRID_EPOCH,
        "columns": GRID_COLUMNS,
        "placement_mode": "hybrid",
        "widgets": [],
    }


def spans_for_size(size_key):
    return SIZE_SPANS.get(size_key, (1, 2))


def widget_entry(
    widget_id,
    col,
    row,
    size_key="1x1",
):
    col_span, row_span = spans_for_size(size_key)
    return {
        "widget_id": widget_id,
        "col": col,
        "row": row,
        "col_span": col_span,
        "row_span": row_span,
        "size": size_key,
    }


def infer_size_key(entry):
    size = entry.get("size")
    if size in SIZE_SPANS:
        return size

    spans = (entry.get("col_span"), entry.get("row_span"))
    if spans in LEGACY_SPAN_TO_SIZE:
        return LEGACY_SPAN_TO_SIZE[spans]

    for size_key, size_spans in SIZE_SPANS.items():
        if spans == size_spans:
            return size_key

    col_span = entry.get("col_span")
    if col_span is not None:
        for size_key, (span_col, _span_row) in SIZE_SPANS.items():
            if span_col == col_span:
                return size_key

    return widget_definitions().get(
        entry.get("widget_id", ""),
        {},
    ).get("default_size", "1x1")


def layout_needs_migration(layout_data):
    if not layout_data:
        return False

    if layout_data.get("version", 1) < LAYOUT_VERSION:
        return True
    if layout_data.get("grid_epoch", 1) < GRID_EPOCH:
        return True

    for entry in layout_data.get("widgets", []):
        size_key = infer_size_key(entry)
        col_span, _row_span = spans_for_size(size_key)
        if entry.get("col_span") != col_span:
            return True

    return False


def resolve_layout_collisions(widgets):
    placed = []
    for entry in sorted(
        widgets,
        key=lambda item: (item["row"], item["col"]),
    ):
        trial = dict(entry)
        if not can_place(trial, placed):
            col, row = find_next_slot(
                placed,
                trial["col_span"],
                trial["row_span"],
                trial["row"],
            )
            trial["col"] = col
            trial["row"] = row
        placed.append(trial)
    return placed


def migrate_layout(layout_data):
    """Alte gespeicherte Layouts auf aktuelles Raster normalisieren."""
    if not layout_data:
        return empty_layout()

    if not layout_needs_migration(layout_data):
        layout = dict(layout_data)
        layout.setdefault("version", LAYOUT_VERSION)
        layout.setdefault("grid_epoch", GRID_EPOCH)
        layout.setdefault("columns", GRID_COLUMNS)
        return layout

    if layout_data.get("grid_epoch", 1) == 3:
        layout = dict(layout_data)
        layout["version"] = LAYOUT_VERSION
        layout["grid_epoch"] = GRID_EPOCH
        layout.setdefault("columns", GRID_COLUMNS)
        return layout

    defs = widget_definitions()
    migrated = []

    for raw in layout_data.get("widgets", []):
        widget_id = raw.get("widget_id")
        if widget_id not in defs:
            continue

        old_col = int(raw.get("col", 0))
        old_row = int(raw.get("row", 0))
        old_col_span = int(raw.get("col_span", 3) or 1)
        size_key = infer_size_key(raw)
        new_col_span, new_row_span = spans_for_size(size_key)

        if old_col_span > 0:
            new_col = int(old_col * new_col_span / old_col_span)
        else:
            new_col = old_col
        new_col = max(0, min(new_col, GRID_COLUMNS - new_col_span))

        migrated.append(
            widget_entry(widget_id, new_col, old_row, size_key)
        )

    layout = {
        "version": LAYOUT_VERSION,
        "grid_epoch": GRID_EPOCH,
        "columns": GRID_COLUMNS,
        "placement_mode": layout_data.get(
            "placement_mode",
            "hybrid",
        ),
        "widgets": resolve_layout_collisions(migrated),
    }

    source_preset = layout_data.get("source_preset")
    if source_preset:
        layout["source_preset"] = source_preset

    return layout


def cells_for_entry(entry):
    cells = set()
    col = entry["col"]
    row = entry["row"]
    for dc in range(entry["col_span"]):
        for dr in range(entry["row_span"]):
            cells.add((col + dc, row + dr))
    return cells


def layout_occupancy(widgets):
    occupied = {}
    for index, entry in enumerate(widgets):
        for cell in cells_for_entry(entry):
            occupied[cell] = index
    return occupied


def can_place(entry, widgets, ignore_index=None):
    if entry["col"] < 0 or entry["row"] < 0:
        return False
    if entry["col"] + entry["col_span"] > GRID_COLUMNS:
        return False

    occ = layout_occupancy(widgets)
    for cell in cells_for_entry(entry):
        holder = occ.get(cell)
        if holder is not None and holder != ignore_index:
            return False
    return True


def find_next_slot(widgets, col_span, row_span, start_row=0):
    row = start_row
    while row < 200:
        col = 0
        while col + col_span <= GRID_COLUMNS:
            trial = {
                "col": col,
                "row": row,
                "col_span": col_span,
                "row_span": row_span,
            }
            if can_place(trial, widgets):
                return col, row
            col += 1
        row += 2
    return 0, row


def preset_to_grid(preset_id):
    config = DASHBOARD_LAYOUTS.get(
        preset_id,
        DASHBOARD_LAYOUTS["classic"],
    )
    cards_filter = config.get("cards")
    layout = empty_layout()
    widgets = []
    cursor_row = 0

    defs = widget_definitions()

    for section in config["order"]:
        if section == "session":
            col_span, row_span = spans_for_size("2x2")
            col, row = find_next_slot(
                widgets,
                col_span,
                row_span,
                cursor_row,
            )
            widgets.append(
                widget_entry("session", col, row, "2x2")
            )
            cursor_row = row + row_span
            continue

        if section == "refinery_stats":
            col_span, row_span = spans_for_size("2x2")
            col, row = find_next_slot(
                widgets,
                col_span,
                row_span,
                cursor_row,
            )
            widgets.append(
                widget_entry("refinery_stats", col, row, "2x2")
            )
            cursor_row = row + row_span
            continue

        section_cards = SECTION_CARD_KEYS.get(section, ())
        if cards_filter is not None:
            allowed = set(
                cards_filter.get(section, section_cards)
            )
            section_cards = tuple(
                c for c in section_cards if c in allowed
            )

        for card_id in section_cards:
            if card_id not in defs:
                continue
            size = defs[card_id]["default_size"]
            col_span, row_span = spans_for_size(size)
            col, row = find_next_slot(
                widgets,
                col_span,
                row_span,
                cursor_row,
            )
            widgets.append(
                widget_entry(card_id, col, row, size)
            )
            cursor_row = max(cursor_row, row)

    layout["widgets"] = widgets
    layout["source_preset"] = preset_id
    return layout


def default_classic_layout():
    return preset_to_grid("classic")
