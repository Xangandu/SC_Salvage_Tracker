"""Katalog aller Dashboard-Widgets."""

from config.materials import material_total_label

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
            "title": "RAFFINERIE",
            "kind": "kpi",
            "default_size": "1x1",
            "sizes": ("1x1", "2x1", "2x2"),
        },
        "active_sessions": {
            "title": "AKTIV",
            "kind": "kpi",
            "default_size": "1x1",
            "sizes": ("1x1", "2x1", "2x2"),
        },
        "total_sessions": {
            "title": "SITZUNGEN",
            "kind": "kpi",
            "default_size": "1x1",
            "sizes": ("1x1", "2x1", "2x2"),
        },
        "sold_sessions": {
            "title": "VERKÄUFE",
            "kind": "kpi",
            "default_size": "1x1",
            "sizes": ("1x1", "2x1", "2x2"),
        },
        "ready_sessions": {
            "title": "LAGER (SCU)",
            "kind": "kpi",
            "default_size": "1x1",
            "sizes": ("1x1", "2x1", "2x2"),
        },
        "total_sales": {
            "title": "UMSATZ",
            "kind": "kpi",
            "default_size": "1x1",
            "sizes": ("1x1", "2x1", "2x2"),
        },
        "total_profit": {
            "title": "GEWINN",
            "kind": "kpi",
            "default_size": "1x1",
            "sizes": ("1x1", "2x1", "2x2"),
        },
        "session": {
            "title": "◆ AKTIVE SITZUNG",
            "kind": "session",
            "default_size": "2x2",
            "sizes": ("2x2",),
        },
        "refinery_stats": {
            "title": "◆ RAFFINERIE-STATISTIK",
            "kind": "refinery_stats",
            "default_size": "2x2",
            "sizes": ("2x2", "2x1"),
        },
    }


ALL_WIDGET_IDS = tuple(widget_definitions().keys())
