"""Dashboard: nächste Aktionen und Operations-Zeilen (Hybrid-Ansicht)."""

from __future__ import annotations

from config.i18n import tr, format_number, format_scu, format_scu_delta
from config.materials import (
    RAW_CM_MATERIAL_CODES,
    REFINED_SELLABLE_CODES,
    material_label,
)
from config.i18n import status_label as i18n_status_label
from config.storage_idle import IDLE_WARNING_DAYS, format_relative_activity
from config.dates import format_datetime


class DashboardOperationsRepository:
    PRIORITY_PAYOUT = 10
    PRIORITY_REFINERY_READY = 20
    PRIORITY_SALE_READY = 30
    PRIORITY_REFINERY_RUNNING = 40
    PRIORITY_STORAGE_IDLE = 50
    PRIORITY_SESSION_ACTIVE = 60

    def __init__(self, db):
        self.db = db

    @property
    def cursor(self):
        db = self.db
        ensure = getattr(db, "_ensure_cursor", None)
        if callable(ensure):
            ensure()
        return db.cursor

    def build_snapshot(self) -> dict:
        rows = self.collect_action_rows()

        summary = self._build_summary()
        next_action = self._build_next_action(rows)

        return {
            "next_action": next_action,
            "rows": rows,
            "summary": summary,
            "materials": self._build_materials(),
            "session": self._build_session_snapshot(),
            "refinery_stats": self.db.get_refinery_statistics(),
        }

    def _build_summary(self) -> dict:
        return {
            "total_sales": self.db.get_total_sales_value(),
            "total_profit": self.db.get_total_profit(),
            "open_refinery_jobs": self.db.get_open_refinery_jobs(),
            "active_sessions": self.db.get_active_session_count(),
            "total_sessions": self.db.get_total_session_count(),
            "sold_sessions": self._count_sessions_by_status("SOLD"),
            "idle_warnings": self.db.count_stockpile_idle_warnings(),
            "sellable_scu": self.db.get_sellable_storage_total_scu(),
        }

    def _count_sessions_by_status(self, status: str) -> int:
        deleted = ""
        if "is_deleted" in self.db._table_columns("sessions"):
            deleted = "AND is_deleted = 0"

        self.cursor.execute(f"""
        SELECT COUNT(*)
        FROM sessions
        WHERE status = ?
        {deleted}
        """, (status,))

        return int(self.cursor.fetchone()[0] or 0)

    def _build_materials(self) -> dict:
        stockpile_map: dict[str, float] = {}
        if self.db._table_exists("material_stockpiles"):
            for entry in self.db.get_stockpile_totals():
                stockpile_map[entry["material_code"]] = float(
                    entry.get("quantity_scu") or 0
                )

        def sellable_total(code: str) -> float:
            if self.db._table_exists("material_stockpiles"):
                from config.materials import REFINED_SELLABLE_CODES

                if code in REFINED_SELLABLE_CODES:
                    return (
                        self.db.stockpiles.sellable_quantity(code)
                        + self.db.materials.global_pool_quantity(code)
                    )
            legacy = float(self.db.get_storage_balance(code) or 0)
            stock = stockpile_map.get(code, 0.0)
            return legacy + stock

        return {
            "RMC": sellable_total("RMC"),
            "CM": sellable_total("CM"),
            "CM_RUBBLE": float(
                self.db.get_global_batch_available("CM_RUBBLE") or 0
            ),
            "CM_SCRAPS": float(
                self.db.get_global_batch_available("CM_SCRAPS") or 0
            ),
            "CM_SALVAGE": float(
                self.db.get_global_batch_available("CM_SALVAGE") or 0
            ),
        }

    def _build_session_snapshot(self) -> dict:
        session = self.db.get_dashboard_session()
        if not session:
            return {
                "active": False,
                "status": "IDLE",
                "status_label": i18n_status_label("IDLE"),
                "name": tr("dashboard.session.none"),
                "crew_count": 0,
                "refinery_jobs": 0,
                "materials": {},
            }

        session_id, name, status = session[0], session[1], session[2]
        materials: dict[str, float] = {}

        for code in REFINED_SELLABLE_CODES:
            materials[code] = float(
                self.db.get_session_captured_total(session_id, code) or 0
            )

        materials["CM"] = float(
            self.db.get_refined_cm_total(session_id) or 0
        )

        for code in RAW_CM_MATERIAL_CODES:
            if code == "CM":
                continue
            materials[code] = float(
                self.db.get_session_batch_available(session_id, code) or 0
            )

        return {
            "active": status == "ACTIVE",
            "session_id": session_id,
            "status": status,
            "status_label": i18n_status_label(status),
            "name": name or "—",
            "crew_count": len(self.db.get_crew_members(session_id)),
            "refinery_jobs": self._count_session_open_refinery(session_id),
            "materials": materials,
        }

    def _count_session_open_refinery(self, session_id: int) -> int:
        if not self.db._table_exists("refinery_jobs"):
            return 0

        deleted = ""
        if "is_deleted" in self.db._table_columns("refinery_jobs"):
            deleted = "AND refinery_jobs.is_deleted = 0"

        self.cursor.execute(f"""
        SELECT COUNT(DISTINCT refinery_jobs.id)
        FROM refinery_jobs
        INNER JOIN refinery_job_items
            ON refinery_job_items.job_id = refinery_jobs.id
        INNER JOIN material_batches
            ON material_batches.id = refinery_job_items.batch_id
        WHERE material_batches.session_id = ?
        AND refinery_jobs.status IN ('RUNNING', 'READY')
        {deleted}
        """, (session_id,))

        return int(self.cursor.fetchone()[0] or 0)

    def _build_next_action(self, rows: list[dict]) -> dict | None:
        if not rows:
            return {
                "message": tr("dashboard.next_action.all_clear"),
            }

        top = rows[0]
        return {
            "message": top.get("headline") or top["status_label"],
        }

    def _session_name(self, session_id: int | None) -> str:
        if not session_id:
            return "—"

        name_col = self.db._session_name_column()
        self.cursor.execute(f"""
        SELECT {name_col}
        FROM sessions
        WHERE id = ?
        """, (session_id,))

        row = self.cursor.fetchone()
        return row[0] if row else f"#{session_id}"

    def _unpaid_sale_rows(self) -> list[dict]:
        if not self.db._table_exists("sales"):
            return []

        payout_deleted = ""
        if self.db._table_exists("payouts"):
            if "is_deleted" in self.db._table_columns("payouts"):
                payout_deleted = "AND p.is_deleted = 0"

        sales_deleted = ""
        if "is_deleted" in self.db._table_columns("sales"):
            sales_deleted = "AND s.is_deleted = 0"

        self.cursor.execute(f"""
        SELECT
            s.id,
            s.location,
            s.total_amount,
            mt.material_code,
            si.quantity,
            mb.session_id
        FROM sales s
        LEFT JOIN payouts p
            ON p.sale_id = s.id
            {payout_deleted}
        INNER JOIN sale_items si
            ON si.sale_id = s.id
        INNER JOIN storage_items st
            ON st.id = si.storage_item_id
        INNER JOIN material_types mt
            ON mt.id = st.material_type_id
        LEFT JOIN material_batches mb
            ON st.source_type = 'SESSION'
            AND st.source_id = mb.id
        WHERE p.id IS NULL
        {sales_deleted}
        ORDER BY s.id DESC
        """)

        rows = []
        for sale_id, location, total_amount, code, qty, session_id in (
            self.cursor.fetchall()
        ):
            session_label = self._session_name(session_id)
            rows.append({
                "priority": self.PRIORITY_PAYOUT,
                "kind": "payout",
                "status_label": tr("dashboard.action.payout_pending"),
                "headline": tr(
                    "dashboard.next_action.payout",
                    material=material_label(code),
                    session=session_label,
                ),
                "material_code": code,
                "material_label": material_label(code),
                "quantity_scu": float(qty or 0),
                "context_label": location or "—",
                "detail_label": tr(
                    "dashboard.action.detail.session",
                    session=session_label,
                ),
                "sort_key": f"payout-{sale_id}-{code}",
            })

        return rows

    def _refinery_rows(self) -> list[dict]:
        if not hasattr(self.db, "refinery"):
            return []

        rows = []
        for job in self.db.refinery.get_active_jobs():
            status = job.get("status") or "RUNNING"
            station = job.get("refinery_name") or "—"
            if status == "READY":
                priority = self.PRIORITY_REFINERY_READY
                status_label = tr("dashboard.action.refinery_ready")
                headline = tr(
                    "dashboard.next_action.refinery_ready",
                    station=station,
                )
            else:
                priority = self.PRIORITY_REFINERY_RUNNING
                status_label = tr("dashboard.action.refinery_running")
                headline = None

            input_scu = sum(
                float(line.get("input_quantity") or 0)
                for line in job.get("items") or []
            )

            rows.append({
                "priority": priority,
                "kind": "refinery",
                "status_label": status_label,
                "headline": headline,
                "material_label": tr("dashboard.action.refinery_material"),
                "quantity_scu": input_scu,
                "context_label": station,
                "detail_label": tr(
                    "dashboard.action.detail.job",
                    job_id=job.get("id"),
                ),
                "sort_key": f"refinery-{job.get('id')}",
            })

        return rows

    def _stockpile_stored_when(self, entry: dict) -> str:
        return format_relative_activity(
            entry.get("last_activity_at") or entry.get("created_at"),
        )

    def _sale_ready_headline(
        self,
        material_code: str,
        location: str,
        when: str,
    ) -> str:
        return tr(
            "dashboard.next_action.sale",
            material=material_label(material_code),
            location=location,
            when=when,
        )

    def _sellable_stockpile_material_codes(self) -> set[str]:
        if not self.db._table_exists("material_stockpiles"):
            return set()

        codes: set[str] = set()
        for entry in self.db.list_material_stockpiles():
            code = entry.get("material_code")
            if code not in REFINED_SELLABLE_CODES:
                continue
            if float(entry.get("quantity_scu") or 0) <= 0:
                continue
            codes.add(code)
        return codes

    def _resolve_storage_source_location(
        self,
        source_type: str | None,
        source_id: int | None,
    ) -> str:
        if source_type == "REFINERY" and source_id:
            return self._refinery_source_label(source_id) or "—"

        if source_type == "SESSION" and source_id:
            self.cursor.execute("""
            SELECT session_id
            FROM material_batches
            WHERE id = ?
            """, (source_id,))
            batch_row = self.cursor.fetchone()
            if batch_row and batch_row[0]:
                ship = self.db.get_session_ship(batch_row[0])
                if ship:
                    return tr(
                        "storage.location.ship",
                        ship=ship.get("ship_name") or "—",
                    )

        return "—"

    def _legacy_sale_context(self, material_code: str) -> tuple[str, str]:
        rows = self.db.materials._storage_rows_for_material(
            material_code,
            global_pool_only=True,
        )
        if not rows:
            return ("—", "—")

        storage_item_id = rows[0][0]
        self.cursor.execute("""
        SELECT source_type, source_id, created_at
        FROM storage_items
        WHERE id = ?
        """, (storage_item_id,))
        row = self.cursor.fetchone()
        if not row:
            return ("—", "—")

        location = self._resolve_storage_source_location(
            row[0],
            row[1],
        )
        when = format_relative_activity(row[2])
        return (location, when)

    def _sellable_stockpile_rows(self) -> list[dict]:
        if not self.db._table_exists("material_stockpiles"):
            return []

        stockpiles = self.db.list_material_stockpiles(
            sort_by=self.db.stockpiles.SORT_AGE,
        )

        rows = []
        for entry in stockpiles:
            code = entry.get("material_code")
            if code not in REFINED_SELLABLE_CODES:
                continue

            qty = float(entry.get("quantity_scu") or 0)
            if qty <= 0:
                continue

            context = self._stockpile_location_label(entry)
            when = self._stockpile_stored_when(entry)

            session_id = entry.get("session_id")
            detail = ""
            if session_id:
                detail = tr(
                    "dashboard.action.detail.session",
                    session=self._session_name(session_id),
                )

            rows.append({
                "priority": self.PRIORITY_SALE_READY,
                "kind": "sale_stockpile",
                "status_label": tr("dashboard.action.sale_ready"),
                "headline": self._sale_ready_headline(
                    code,
                    context,
                    when,
                ),
                "material_code": code,
                "material_label": material_label(code),
                "quantity_scu": qty,
                "context_label": context,
                "detail_label": detail,
                "sort_key": f"0-stockpile-{entry.get('id')}",
            })

        return rows

    def _sellable_legacy_storage_rows(self) -> list[dict]:
        stockpile_codes = self._sellable_stockpile_material_codes()
        inventory = self.db.get_dashboard_storage_inventory()
        rows = []

        for entry in inventory:
            code = entry.get("material_code")
            if code not in REFINED_SELLABLE_CODES:
                continue
            if code in stockpile_codes:
                continue

            location, when = self._legacy_sale_context(code)
            rows.append({
                "priority": self.PRIORITY_SALE_READY,
                "kind": "sale_legacy",
                "status_label": tr("dashboard.action.sale_ready"),
                "headline": self._sale_ready_headline(
                    code,
                    location,
                    when,
                ),
                "material_code": code,
                "material_label": material_label(code),
                "quantity_scu": float(entry.get("quantity") or 0),
                "context_label": location,
                "detail_label": tr("dashboard.action.detail.legacy"),
                "sort_key": f"1-legacy-{code}",
            })

        return rows

    def _idle_stockpile_rows(self) -> list[dict]:
        if not self.db._table_exists("material_stockpiles"):
            return []

        stockpiles = self.db.list_material_stockpiles(
            warnings_only=True,
            sort_by=self.db.stockpiles.SORT_AGE,
        )

        rows = []
        for entry in stockpiles:
            context = entry.get("location_label") or "—"
            if entry.get("location_kind") == "SHIP":
                context = tr(
                    "storage.location.ship",
                    ship=entry.get("ship_name") or "—",
                )

            rows.append({
                "priority": self.PRIORITY_STORAGE_IDLE,
                "kind": "storage_idle",
                "status_label": tr("dashboard.action.storage_idle"),
                "headline": tr(
                    "dashboard.next_action.storage_idle",
                    count=1,
                    days=IDLE_WARNING_DAYS,
                ),
                "material_code": entry.get("material_code"),
                "material_label": material_label(
                    entry.get("material_code") or "—"
                ),
                "quantity_scu": float(entry.get("quantity_scu") or 0),
                "context_label": context,
                "detail_label": tr("dashboard.action.detail.idle"),
                "sort_key": f"idle-{entry.get('id')}",
            })

        return rows

    def _active_session_rows(self) -> list[dict]:
        session = self.db.get_active_session()
        if not session:
            return []

        session_id, session_name, status = session[0], session[1], session[2]
        status_text = tr(
            f"status.{status}",
            default=status,
        )

        materials = []
        for code in (*REFINED_SELLABLE_CODES, *RAW_CM_MATERIAL_CODES):
            if code in REFINED_SELLABLE_CODES:
                qty = self.db.get_session_captured_total(
                    session_id,
                    code,
                )
            elif code == "CM":
                qty = self.db.get_refined_cm_total(session_id)
            else:
                qty = self.db.get_session_batch_available(
                    session_id,
                    code,
                )
            if qty and qty > 0:
                materials.append(
                    f"{material_label(code)} {format_number(qty, 0)}"
                )

        detail = ", ".join(materials) if materials else "—"

        return [{
            "priority": self.PRIORITY_SESSION_ACTIVE,
            "kind": "session_active",
            "status_label": status_text,
            "headline": None,
            "material_label": tr("dashboard.action.session"),
            "quantity_scu": 0.0,
            "context_label": session_name or "—",
            "detail_label": detail,
            "sort_key": f"session-{session_id}",
            "quantity_display": detail,
        }]

    _KIND_TO_CONTEXT = {
        "payout": "payout",
        "refinery": "refinery",
        "sale_stockpile": "sales",
        "sale_legacy": "sales",
        "storage_idle": "storage",
        "session_active": "session",
    }

    def collect_action_rows(self) -> list[dict]:
        rows: list[dict] = []
        rows.extend(self._unpaid_sale_rows())
        rows.extend(self._refinery_rows())
        rows.extend(self._sellable_stockpile_rows())
        rows.extend(self._sellable_legacy_storage_rows())
        rows.extend(self._idle_stockpile_rows())
        rows.extend(self._active_session_rows())
        rows.sort(
            key=lambda row: (
                row["priority"],
                row.get("sort_key") or "",
            )
        )
        return rows

    def build_global_alert(self) -> dict | None:
        rows = self.collect_action_rows()
        if not rows:
            return None

        top = rows[0]
        kind = top.get("kind") or ""
        return {
            "message": top.get("headline") or top.get("status_label") or "",
            "target_context": self._KIND_TO_CONTEXT.get(
                kind,
                "overview",
            ),
            "action_label": tr("dashboard.alert.show"),
        }

    def build_context(self, context_key: str) -> dict:
        builders = {
            "overview": self.build_overview_context,
            "session": self.build_session_context,
            "refinery": self.build_refinery_context,
            "storage": self.build_storage_context,
            "sales": self.build_sales_context,
            "payout": self.build_payout_context,
            "history": self.build_history_context,
        }
        builder = builders.get(context_key, self.build_overview_context)
        return builder()

    def build_overview_context(self) -> dict:
        rows = self.collect_action_rows()
        summary = self._build_summary()
        table_rows = []
        for row in rows[:12]:
            qty = row.get("quantity_display")
            if not qty:
                qty = format_scu(row.get("quantity_scu", 0))
            table_rows.append((
                row.get("status_label") or "—",
                row.get("material_label") or "—",
                qty,
                row.get("context_label") or "—",
            ))
        return {
            "actions": table_rows,
            "summary": summary,
        }

    def build_session_context(self) -> dict:
        snapshot = self._build_session_snapshot()
        materials = snapshot.get("materials") or {}
        snapshot["session_scu_total"] = sum(materials.values())
        snapshot["locations"] = self._build_session_locations(
            snapshot.get("session_id"),
            materials,
        )
        snapshot["processes"] = self._build_session_processes(
            snapshot.get("session_id"),
            snapshot.get("status"),
        )
        mission_costs = self._build_session_mission_costs(
            snapshot.get("session_id"),
        )
        refinery_costs = self._build_session_refinery_costs(
            snapshot.get("session_id"),
        )
        combined_session_costs = (
            float(mission_costs.get("session_costs_table_total") or 0)
            + float(refinery_costs.get("refinery_costs_total") or 0)
        )
        mission_costs["session_costs_total"] = combined_session_costs
        snapshot.update(mission_costs)
        snapshot.update(refinery_costs)
        return snapshot

    def _build_session_mission_costs(
        self,
        session_id: int | None,
    ) -> dict:
        empty = {
            "mission_costs_total": 0.0,
            "session_costs_table_total": 0.0,
            "session_costs_total": 0.0,
            "mission_costs": [],
        }
        if not session_id:
            return empty

        costs = self.db.get_session_costs(session_id)
        mission_rows = [
            row for row in costs
            if row[0] == "Mission"
        ]
        mission_total = sum(float(row[1] or 0) for row in mission_rows)
        session_table_total = float(
            self.db.get_total_costs(session_id) or 0
        )

        items: list[tuple[str, str]] = []
        for index, (_, amount, paid_by) in enumerate(
            mission_rows,
            start=1,
        ):
            items.append((
                tr(
                    "session.mission.line",
                    index=index,
                    amount=format_number(amount),
                    paid_by=paid_by or "—",
                ),
                "",
            ))

        return {
            "mission_costs_total": mission_total,
            "session_costs_table_total": session_table_total,
            "session_costs_total": session_table_total,
            "mission_costs": items,
        }

    def _build_session_refinery_costs(
        self,
        session_id: int | None,
    ) -> dict:
        empty = {
            "refinery_costs_total": 0.0,
            "refinery_costs": [],
        }
        if not session_id:
            return empty
        if not self.db._table_exists("refinery_jobs"):
            return empty

        job_columns = self.db._table_columns("refinery_jobs")
        if "cost" not in job_columns:
            return empty

        deleted = ""
        if "is_deleted" in job_columns:
            deleted = "AND rj.is_deleted = 0"

        paid_by_sql = (
            "COALESCE(rj.cost_paid_by, '')"
            if "cost_paid_by" in job_columns
            else "''"
        )

        self.cursor.execute(f"""
        SELECT DISTINCT
            rj.id,
            COALESCE(NULLIF(TRIM(rj.station), ''), '—'),
            COALESCE(rj.cost, 0),
            {paid_by_sql}
        FROM refinery_jobs rj
        INNER JOIN refinery_job_items rji
            ON rji.job_id = rj.id
        INNER JOIN material_batches mb
            ON mb.id = rji.batch_id
        WHERE mb.session_id = ?
        AND COALESCE(rj.cost, 0) > 0
        {deleted}
        ORDER BY rj.id
        """, (session_id,))

        rows = self.cursor.fetchall()
        refinery_total = sum(float(row[2] or 0) for row in rows)

        items: list[tuple[str, str]] = []
        for job_id, station, cost, paid_by in rows:
            items.append((
                tr(
                    "session.refinery.line",
                    job_id=job_id,
                    amount=format_number(cost),
                    station=station or "—",
                    paid_by=paid_by or "—",
                ),
                "",
            ))

        return {
            "refinery_costs_total": refinery_total,
            "refinery_costs": items,
        }

    def _build_session_locations(
        self,
        session_id: int | None,
        materials: dict[str, float],
    ) -> list[tuple[str, str, int]]:
        if not session_id:
            return []

        entries: list[tuple[str, float, str]] = []

        if self.db._table_exists("material_stockpiles"):
            for entry in self.db.list_material_stockpiles():
                qty = float(entry.get("quantity_scu") or 0)
                if qty <= 0:
                    continue
                if entry.get("session_id") != session_id:
                    if entry.get("location_kind") != "SHIP":
                        continue
                if entry.get("location_kind") == "SHIP":
                    label = tr(
                        "storage.location.ship",
                        ship=entry.get("ship_name") or "—",
                    )
                else:
                    label = entry.get("location_label") or "—"
                code = entry.get("material_code") or "—"
                detail = (
                    f"{material_label(code)} "
                    f"{format_scu(qty)}"
                )
                entries.append((label, qty, detail))

        if hasattr(self.db, "refinery"):
            for job in self.db.refinery.get_active_jobs():
                job_id = job.get("id")
                if job_id is None:
                    continue
                if session_id not in self.db.refinery._session_ids_for_job(
                    job_id,
                ):
                    continue
                input_scu = sum(
                    float(line.get("input_quantity") or 0)
                    for line in job.get("items") or []
                )
                if input_scu <= 0:
                    continue
                station = job.get("refinery_name") or "—"
                status = job.get("status") or "RUNNING"
                label = tr(
                    "dashboard.context.refinery_station",
                    station=station,
                )
                detail = tr(
                    "dashboard.context.refinery_job_detail",
                    job_id=job_id,
                    status=status,
                    scu=format_number(input_scu),
                )
                entries.append((label, input_scu, detail))

        batch_scu = sum(
            materials.get(code, 0)
            for code in RAW_CM_MATERIAL_CODES
            if code != "CM"
        )
        if batch_scu > 0:
            parts = [
                f"{material_label(code)} {format_number(materials[code])}"
                for code in RAW_CM_MATERIAL_CODES
                if code != "CM" and materials.get(code, 0) > 0
            ]
            entries.append((
                tr("dashboard.context.session_batches"),
                batch_scu,
                " · ".join(parts),
            ))

        if not entries:
            parts = [
                f"{material_label(code)} {format_number(qty)}"
                for code, qty in materials.items()
                if qty > 0
            ]
            if parts:
                unassigned_total = sum(
                    qty for qty in materials.values() if qty > 0
                )
                entries.append((
                    tr("dashboard.context.session_materials"),
                    unassigned_total,
                    " · ".join(parts),
                ))

        if not entries:
            return []

        location_total = sum(qty for _, qty, _ in entries)
        result = []
        for label, qty, detail in entries:
            if location_total <= 0:
                pct = 0
            elif len(entries) == 1:
                pct = 100
            else:
                pct = min(
                    100,
                    int(round(100 * qty / location_total)),
                )
            result.append((label, detail, pct))
        return result

    def _build_session_processes(
        self,
        session_id: int | None,
        status: str | None,
    ) -> list[dict]:
        processes: list[dict] = []
        if not session_id:
            return processes

        if status and status not in ("ACTIVE", "IDLE"):
            processes.append({
                "kind": "status",
                "title": i18n_status_label(status),
                "detail": tr("dashboard.context.process_status"),
            })

        return processes

    def build_refinery_context(self) -> dict:
        stats = self.db.get_refinery_statistics()
        jobs = []
        open_count = 0
        ready_count = 0
        total_input = 0.0
        total_output = 0.0

        if hasattr(self.db, "refinery"):
            for job in self.db.refinery.get_active_jobs():
                status = job.get("status") or "RUNNING"
                input_scu = sum(
                    float(line.get("input_quantity") or 0)
                    for line in job.get("items") or []
                )
                output_scu = sum(
                    float(line.get("output_quantity") or 0)
                    for line in job.get("items") or []
                )
                open_count += 1
                total_input += input_scu
                total_output += output_scu
                if status == "READY":
                    ready_count += 1
                material_codes = {
                    line.get("input_material")
                    for line in job.get("items") or []
                    if line.get("input_material")
                }
                material = ", ".join(
                    material_label(code)
                    for code in sorted(material_codes)
                ) or "—"
                jobs.append({
                    "id": job.get("id"),
                    "station": job.get("refinery_name") or "—",
                    "status": status,
                    "status_label": (
                        tr("dashboard.action.refinery_ready")
                        if status == "READY"
                        else tr("dashboard.action.refinery_running")
                    ),
                    "input_scu": input_scu,
                    "output_scu": output_scu,
                    "material": material,
                    "start_time": job.get("start_time"),
                    "end_time": job.get("end_time"),
                    "job": job,
                })

        by_material = []
        for row in stats.get("by_material") or []:
            eff = row.get("efficiency_percent")
            by_material.append((
                row.get("material_code") or "—",
                float(eff) if eff is not None else 0.0,
                int(row.get("job_count") or 0),
            ))

        return {
            "open_jobs": open_count,
            "ready_jobs": ready_count,
            "avg_efficiency": stats.get("avg_efficiency_percent") or 0,
            "total_input": total_input,
            "total_output": total_output,
            "jobs": jobs,
            "by_material": by_material,
        }

    def _storage_event_type_label(self, event_type: str) -> str:
        return tr(
            f"storage.history.type.{event_type}",
            default=event_type or "—",
        )

    def _stockpile_location_label(self, entry: dict) -> str:
        if entry.get("location_kind") == "SHIP":
            return tr(
                "storage.location.ship",
                ship=entry.get("ship_name") or "—",
            )
        return entry.get("location_label") or "—"

    def _refinery_source_label(self, job_id: int | None) -> str | None:
        if not job_id or not self.db._table_exists("refinery_jobs"):
            return None

        self.cursor.execute("""
        SELECT station
        FROM refinery_jobs
        WHERE id = ?
        """, (job_id,))
        row = self.cursor.fetchone()
        if not row or not row[0]:
            return None

        return tr(
            "dashboard.context.refinery_station",
            station=row[0],
        )

    def _first_deposit_events_by_stockpile(self) -> dict[int, dict]:
        if not self.db._table_exists("material_stockpile_events"):
            return {}

        self.cursor.execute("""
        SELECT
            stockpile_id,
            from_label,
            to_label,
            created_at
        FROM material_stockpile_events
        WHERE is_deleted = 0
        AND event_type = 'DEPOSIT'
        ORDER BY created_at ASC
        """)

        deposits: dict[int, dict] = {}
        for stockpile_id, from_label, to_label, created_at in (
            self.cursor.fetchall()
        ):
            if stockpile_id is None or stockpile_id in deposits:
                continue
            deposits[stockpile_id] = {
                "from_label": from_label,
                "to_label": to_label,
                "created_at": created_at,
            }
        return deposits

    def _build_storage_inventory(self) -> list[tuple[str, str, str]]:
        inventory: list[tuple[str, str, str, str]] = []
        deposits = self._first_deposit_events_by_stockpile()

        if self.db._table_exists("material_stockpiles"):
            for entry in self.db.list_material_stockpiles(
                sort_by=self.db.stockpiles.SORT_AGE,
            ):
                qty = float(entry.get("quantity_scu") or 0)
                if qty <= 0:
                    continue

                stockpile_id = entry.get("id")
                deposit = deposits.get(stockpile_id) or {}
                deposited_at = (
                    deposit.get("created_at")
                    or entry.get("created_at")
                )
                when = (
                    format_datetime(deposited_at)
                    if deposited_at
                    else "—"
                )

                source = (deposit.get("from_label") or "").strip()
                if not source:
                    source = (
                        self._refinery_source_label(
                            entry.get("refinery_job_id"),
                        )
                        or "—"
                    )

                location = self._stockpile_location_label(entry)
                stored_since = format_relative_activity(
                    entry.get("last_activity_at") or deposited_at,
                )
                code = entry.get("material_code") or "—"
                detail = tr(
                    "dashboard.context.storage_inventory_detail",
                    material=material_label(code),
                    quantity=format_scu(qty),
                    source=source,
                    location=location,
                    stored_since=stored_since,
                )
                inventory.append((
                    deposited_at or "",
                    when,
                    self._storage_event_type_label("DEPOSIT"),
                    detail,
                ))

        for entry in self.db.get_dashboard_storage_inventory():
            qty = float(entry.get("quantity") or 0)
            if qty <= 0:
                continue

            code = entry.get("material_code") or "—"
            detail = tr(
                "dashboard.context.storage_inventory_detail",
                material=material_label(code),
                quantity=format_scu(qty),
                source=tr("dashboard.action.legacy_storage"),
                location=tr("dashboard.action.legacy_storage"),
                stored_since="—",
            )
            inventory.append((
                "",
                "—",
                tr("dashboard.action.legacy_storage"),
                detail,
            ))

        inventory.sort(key=lambda row: row[0], reverse=True)
        return [(when, title, detail) for _, when, title, detail in inventory]

    def build_storage_context(self) -> dict:
        total_scu = 0.0

        if self.db._table_exists("material_stockpiles"):
            for entry in self.db.list_material_stockpiles():
                qty = float(entry.get("quantity_scu") or 0)
                if qty <= 0:
                    continue
                total_scu += qty

        for entry in self.db.get_dashboard_storage_inventory():
            code = entry.get("material_code")
            qty = float(entry.get("quantity") or 0)
            if qty <= 0:
                continue
            total_scu += qty

        inventory = self._build_storage_inventory()

        events = []
        for event in self.db.list_stockpile_events(limit=8):
            when = format_datetime(event.get("created_at"))
            event_type = event.get("event_type") or ""
            title = self._storage_event_type_label(event_type)
            code = event.get("material_code") or "—"
            delta = float(event.get("quantity_delta") or 0)
            loc = (
                event.get("location_label")
                or event.get("to_label")
                or "—"
            )
            source = (event.get("from_label") or "").strip()
            if event_type == "DEPOSIT" and source:
                detail = tr(
                    "dashboard.context.storage_deposit_event_detail",
                    material=material_label(code),
                    delta=format_scu_delta(delta),
                    source=source,
                    location=loc,
                )
            else:
                detail = tr(
                    "dashboard.context.storage_event_detail",
                    material=material_label(code),
                    delta=format_scu_delta(delta),
                    location=loc,
                )
            events.append((when, title, detail))

        return {
            "total_scu": total_scu,
            "idle_warnings": self.db.count_stockpile_idle_warnings(),
            "inventory": inventory,
            "recent_events": events,
        }

    def build_sales_context(self) -> dict:
        items = []
        total_scu = 0.0

        for row in self._sellable_stockpile_rows():
            qty = float(row.get("quantity_scu") or 0)
            total_scu += qty
            items.append((
                row.get("material_label") or "—",
                row.get("context_label") or "—",
                qty,
                0.0,
            ))

        for row in self._sellable_legacy_storage_rows():
            qty = float(row.get("quantity_scu") or 0)
            total_scu += qty
            items.append((
                row.get("material_label") or "—",
                row.get("context_label") or "—",
                qty,
                0.0,
            ))

        pending_count = 0
        pending_amount = 0.0
        if self.db._table_exists("sales"):
            deleted = ""
            if "is_deleted" in self.db._table_columns("sales"):
                deleted = "AND s.is_deleted = 0"
            self.cursor.execute(f"""
            SELECT COUNT(*), COALESCE(SUM(s.total_amount), 0)
            FROM sales s
            LEFT JOIN payouts p ON p.sale_id = s.id
            WHERE p.id IS NULL
            {deleted}
            """)
            row = self.cursor.fetchone()
            if row:
                pending_count = int(row[0] or 0)
                pending_amount = float(row[1] or 0)

        return {
            "ready_total_scu": total_scu,
            "ready_value_estimate": 0.0,
            "items": items,
            "pending_sales": pending_count,
            "pending_amount": pending_amount,
        }

    def build_payout_context(self) -> dict:
        items = []
        sale_totals: dict[int, float] = {}

        if not self.db._table_exists("sales"):
            return {
                "open_count": 0,
                "open_total": 0.0,
                "items": [],
            }

        payout_deleted = ""
        if self.db._table_exists("payouts"):
            if "is_deleted" in self.db._table_columns("payouts"):
                payout_deleted = "AND p.is_deleted = 0"

        sales_deleted = ""
        if "is_deleted" in self.db._table_columns("sales"):
            sales_deleted = "AND s.is_deleted = 0"

        self.cursor.execute(f"""
        SELECT
            s.id,
            s.location,
            s.total_amount,
            mt.material_code,
            si.quantity,
            mb.session_id
        FROM sales s
        LEFT JOIN payouts p
            ON p.sale_id = s.id
            {payout_deleted}
        INNER JOIN sale_items si ON si.sale_id = s.id
        INNER JOIN storage_items st ON st.id = si.storage_item_id
        INNER JOIN material_types mt ON mt.id = st.material_type_id
        LEFT JOIN material_batches mb
            ON st.source_type = 'SESSION'
            AND st.source_id = mb.id
        WHERE p.id IS NULL
        {sales_deleted}
        ORDER BY s.id DESC
        """)

        for sale_id, location, amount, code, qty, session_id in (
            self.cursor.fetchall()
        ):
            sale_totals[sale_id] = float(amount or 0)
            items.append((
                self._session_name(session_id),
                material_label(code),
                float(qty or 0),
                float(amount or 0),
                location or "—",
            ))

        return {
            "open_count": len(sale_totals),
            "open_total": sum(sale_totals.values()),
            "items": items,
        }

    def build_history_context(self) -> dict:
        from collections import defaultdict

        summary = self._build_summary()
        recent = []
        for sale in self.db.get_sales_history(limit=8):
            items_text = ", ".join(
                f"{material_label(item['material_code'])} "
                f"{format_number(item['quantity'], 0)}"
                for item in sale.get("items") or []
            )
            recent.append((
                str(sale.get("sale_date") or "—")[:10],
                tr("dashboard.context.history_sale"),
                tr(
                    "dashboard.context.history_sale_detail",
                    location=sale.get("location") or "—",
                    amount=f"{sale.get('total_amount', 0):,.0f}".replace(",", "."),
                    materials=items_text or "—",
                ),
            ))

        monthly: dict[str, float] = defaultdict(float)
        for sale in self.db.get_sales_history(limit=500):
            date = str(sale.get("sale_date") or "")[:7]
            if date:
                monthly[date] += float(sale.get("total_amount") or 0)

        monthly_rows = sorted(monthly.items())[-6:]

        return {
            "sold_sessions": summary["sold_sessions"],
            "total_sessions": summary["total_sessions"],
            "total_revenue": summary["total_sales"],
            "recent": recent,
            "monthly_revenue": monthly_rows,
        }
