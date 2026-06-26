"""Katalog aller Dashboard-Widgets."""

from config.materials import material_total_label
from config.i18n import tr

GRID_COLUMNS = 12
ROW_UNIT_PX = 30
GRID_GAP = 5
GRID_MARGIN = 5
MIME_DASHBOARD_WIDGET = "application/x-sst-dashboard-widget"

SIZE_SPANS = {
    "1x1": (1, 2),
    "2x1": (2, 2),
    "2x2": (3, 4),
}


def _event_local_point(event):
    if hasattr(event, "position"):
        return event.position().toPoint()
    return event.pos()


def _event_global_point(event, widget=None):
    if hasattr(event, "globalPosition"):
        return event.globalPosition().toPoint()
    if hasattr(event, "globalPos"):
        return event.globalPos()
    if widget is not None:
        return widget.mapToGlobal(_event_local_point(event))
    return _event_local_point(event)


def widget_definitions():
    return {
        "status": {
            "title": "STATUS",
            "kind": "kpi",
            "default_size": "1x1",
            "sizes": ("1x1", "2x1", "2x2"),
        },
        "crew": {
            "title": "CREW",
            "kind": "kpi",
            "default_size": "1x1",
            "sizes": ("1x1", "2x1", "2x2"),
        },
        "rmc": {
            "title": material_total_label("RMC"),
            "kind": "kpi",
            "default_size": "1x1",
            "sizes": ("1x1", "2x1", "2x2"),
        },
        "cm": {
            "title": material_total_label("CM"),
            "kind": "kpi",
            "default_size": "1x1",
            "sizes": ("1x1", "2x1", "2x2"),
        },
        "rubble": {
            "title": material_total_label("CM_RUBBLE"),
            "kind": "kpi",
            "default_size": "1x1",
            "sizes": ("1x1", "2x1", "2x2"),
        },
        "scraps": {
            "title": material_total_label("CM_SCRAPS"),
            "kind": "kpi",
            "default_size": "1x1",
            "sizes": ("1x1", "2x1", "2x2"),
        },
        "salvage": {
            "title": material_total_label("CM_SALVAGE"),
            "kind": "kpi",
            "default_size": "1x1",
            "sizes": ("1x1", "2x1", "2x2"),
        },
        "refinery_jobs": {
            "title": tr("dashboard.widget.refinery_jobs"),
            "kind": "kpi",
            "default_size": "1x1",
            "sizes": ("1x1", "2x1", "2x2"),
        },
        "active_sessions": {
            "title": tr("dashboard.widget.active_sessions"),
            "kind": "kpi",
            "default_size": "1x1",
            "sizes": ("1x1", "2x1", "2x2"),
        },
        "total_sessions": {
            "title": tr("dashboard.widget.total_sessions"),
            "kind": "kpi",
            "default_size": "1x1",
            "sizes": ("1x1", "2x1", "2x2"),
        },
        "sold_sessions": {
            "title": tr("dashboard.widget.sold_sessions"),
            "kind": "kpi",
            "default_size": "1x1",
            "sizes": ("1x1", "2x1", "2x2"),
        },
        "ready_sessions": {
            "title": tr("dashboard.widget.ready_sessions"),
            "kind": "kpi",
            "default_size": "1x1",
            "sizes": ("1x1", "2x1", "2x2"),
        },
        "total_sales": {
            "title": tr("dashboard.widget.total_sales"),
            "kind": "kpi",
            "default_size": "1x1",
            "sizes": ("1x1", "2x1", "2x2"),
        },
        "total_profit": {
            "title": tr("dashboard.widget.total_profit"),
            "kind": "kpi",
            "default_size": "1x1",
            "sizes": ("1x1", "2x1", "2x2"),
        },
        "session": {
            "title": tr("dashboard.widget.session"),
            "kind": "session",
            "default_size": "2x2",
            "sizes": ("2x1", "2x2"),
            "reflow": False,
        },
        "refinery_stats": {
            "title": tr("dashboard.widget.refinery_stats"),
            "kind": "refinery_stats",
            "default_size": "2x2",
            "sizes": ("2x2", "2x1"),
        },
    }


ALL_WIDGET_IDS = tuple(widget_definitions().keys())
