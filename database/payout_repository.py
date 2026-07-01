"""
Gewinnverteilung: Verkauf → Sessions (via Lager-Trace) → Kosten → Crew-Auszahlung.
"""

import auth.session as user_session

from config.i18n import tr
from config.materials import REFINED_SELLABLE_CODES


UNASSIGNED_COST_PAYERS = frozenset({
    "",
    "SYSTEM",
    "Unbekannt",
})


class PayoutRepository:
    def __init__(self, db):
        self.db = db
        self.cursor = db.cursor
        self.connection = db.connection

    def _payout_deleted_filter(self, alias="p"):
        if "is_deleted" in self.db._table_columns("payouts"):
            return f"AND {alias}.is_deleted = 0"

        return ""

    def trace_sale_session_ids(self, sale_id):
        session_ids = set()

        self.cursor.execute("""
        SELECT DISTINCT material_batches.session_id
        FROM sale_items
        INNER JOIN storage_items
            ON storage_items.id =
                sale_items.storage_item_id
        INNER JOIN material_batches
            ON storage_items.source_type = 'SESSION'
            AND storage_items.source_id =
                material_batches.id
        WHERE sale_items.sale_id = ?
        """, (sale_id,))

        for row in self.cursor.fetchall():
            if row[0] is not None:
                session_ids.add(row[0])

        self.cursor.execute("""
        SELECT DISTINCT material_batches.session_id
        FROM sale_items
        INNER JOIN storage_items
            ON storage_items.id =
                sale_items.storage_item_id
        INNER JOIN refinery_jobs
            ON storage_items.source_type = 'REFINERY'
            AND storage_items.source_id =
                refinery_jobs.id
        INNER JOIN refinery_job_items
            ON refinery_job_items.job_id =
                refinery_jobs.id
        INNER JOIN material_batches
            ON material_batches.id =
                refinery_job_items.batch_id
        WHERE sale_items.sale_id = ?
        """, (sale_id,))

        for row in self.cursor.fetchall():
            if row[0] is not None:
                session_ids.add(row[0])

        return sorted(session_ids)

    def trace_sale_refinery_job_ids(self, sale_id):
        if not self.db._table_exists("refinery_jobs"):
            return []

        self.cursor.execute("""
        SELECT DISTINCT refinery_jobs.id
        FROM sale_items
        INNER JOIN storage_items
            ON storage_items.id =
                sale_items.storage_item_id
        INNER JOIN refinery_jobs
            ON storage_items.source_type = 'REFINERY'
            AND storage_items.source_id =
                refinery_jobs.id
        WHERE sale_items.sale_id = ?
        """, (sale_id,))

        return sorted(row[0] for row in self.cursor.fetchall())

    def sale_has_payout(self, sale_id):
        if not self.db._table_exists("payouts"):
            return False

        deleted_filter = self._payout_deleted_filter()

        self.cursor.execute(f"""
        SELECT COUNT(*)
        FROM payouts p
        WHERE p.sale_id = ?
        {deleted_filter}
        """, (sale_id,))

        return self.cursor.fetchone()[0] > 0

    def get_sale_summary(self, sale_id):
        if not self.db._table_exists("sales"):
            return None

        deleted_filter = ""

        if "is_deleted" in self.db._table_columns("sales"):
            deleted_filter = "AND s.is_deleted = 0"

        self.cursor.execute(f"""
        SELECT
            s.id,
            s.location,
            s.sale_date,
            s.total_amount,
            COALESCE(u.username, '—')
        FROM sales s
        LEFT JOIN users u
            ON u.id = s.created_by
        WHERE s.id = ?
        {deleted_filter}
        """, (sale_id,))

        row = self.cursor.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "location": row[1],
            "sale_date": row[2],
            "total_amount": row[3],
            "created_by": row[4],
        }

    def get_unpaid_sales(self, limit=50):
        if not self.db._table_exists("sales"):
            return []

        sales_deleted = ""

        if "is_deleted" in self.db._table_columns("sales"):
            sales_deleted = "AND s.is_deleted = 0"

        payout_deleted = self._payout_deleted_filter("p")

        self.cursor.execute(f"""
        SELECT
            s.id,
            s.location,
            s.sale_date,
            s.total_amount,
            COALESCE(u.username, '—')
        FROM sales s
        LEFT JOIN users u
            ON u.id = s.created_by
        LEFT JOIN payouts p
            ON p.sale_id = s.id
            {payout_deleted}
        WHERE p.id IS NULL
        {sales_deleted}
        ORDER BY s.id DESC
        LIMIT ?
        """, (limit,))

        return [
            {
                "id": row[0],
                "location": row[1],
                "sale_date": row[2],
                "total_amount": row[3],
                "created_by": row[4],
            }
            for row in self.cursor.fetchall()
        ]

    def _sessions_with_settled_costs(
        self,
        exclude_sale_id=None,
    ):
        if not self.db._table_exists("payouts"):
            return set()

        deleted_filter = self._payout_deleted_filter("p")

        self.cursor.execute(f"""
        SELECT DISTINCT p.sale_id
        FROM payouts p
        WHERE 1=1
        {deleted_filter}
        """)

        settled_sessions = set()

        for row in self.cursor.fetchall():
            paid_sale_id = row[0]

            if (
                exclude_sale_id is not None
                and paid_sale_id == exclude_sale_id
            ):
                continue

            settled_sessions.update(
                self.trace_sale_session_ids(
                    paid_sale_id
                )
            )

        return settled_sessions

    def _refinery_jobs_with_settled_costs(
        self,
        exclude_sale_id=None,
    ):
        if not self.db._table_exists("payouts"):
            return set()

        deleted_filter = self._payout_deleted_filter("p")

        self.cursor.execute(f"""
        SELECT DISTINCT p.sale_id
        FROM payouts p
        WHERE 1=1
        {deleted_filter}
        """)

        settled_jobs = set()

        for row in self.cursor.fetchall():
            paid_sale_id = row[0]

            if (
                exclude_sale_id is not None
                and paid_sale_id == exclude_sale_id
            ):
                continue

            settled_jobs.update(
                self.trace_sale_refinery_job_ids(
                    paid_sale_id
                )
            )

        return settled_jobs

    def _match_crew_member(self, payer, crew):
        payer = (payer or "").strip()

        if not payer:
            return payer

        for member in crew:
            if member.lower() == payer.lower():
                return member

        return payer

    def _apply_cost_payer_overrides(
        self,
        refunds,
        overrides,
    ):
        if not overrides:
            return dict(refunds)

        merged = dict(refunds)

        for old_payer, new_payer in overrides.items():
            amount = merged.pop(old_payer, 0)

            if not amount:
                continue

            new_payer = new_payer.strip()
            merged[new_payer] = (
                merged.get(new_payer, 0) + amount
            )

        return merged

    def _normalize_refunds(
        self,
        refunds,
        crew,
        cost_payer_overrides=None,
    ):
        normalized = self._apply_cost_payer_overrides(
            refunds,
            cost_payer_overrides,
        )
        resolved = {}

        for payer, amount in normalized.items():
            member = self._match_crew_member(
                payer,
                crew,
            )
            resolved[member] = (
                resolved.get(member, 0) + amount
            )

        return resolved

    def _unassigned_cost_payers(self, refunds):
        return sorted(
            payer
            for payer in refunds
            if payer in UNASSIGNED_COST_PAYERS
            and refunds.get(payer, 0) > 0
        )

    def _cost_refunds_for_sessions(
        self,
        session_ids,
    ):
        refunds = {}

        for session_id in session_ids:
            for paid_by, amount in self.db.get_cost_refunds(
                session_id
            ):
                refunds[paid_by] = (
                    refunds.get(paid_by, 0) + amount
                )

        return refunds

    def _refinery_cost_refunds_for_jobs(
        self,
        job_ids,
    ):
        if not job_ids:
            return {}

        columns = self.db._table_columns("refinery_jobs")

        if "cost_paid_by" not in columns:
            return {}

        deleted_filter = ""

        if "is_deleted" in columns:
            deleted_filter = "AND is_deleted = 0"

        placeholders = ", ".join(
            "?" for _ in job_ids
        )

        self.cursor.execute(f"""
        SELECT
            COALESCE(cost_paid_by, ''),
            COALESCE(SUM(cost), 0)
        FROM refinery_jobs
        WHERE id IN ({placeholders})
        AND cost > 0
        {deleted_filter}
        GROUP BY COALESCE(cost_paid_by, '')
        """, job_ids)

        return {
            row[0]: row[1]
            for row in self.cursor.fetchall()
        }

    def _total_refinery_costs_for_jobs(self, job_ids):
        if not job_ids:
            return 0

        columns = self.db._table_columns("refinery_jobs")
        deleted_filter = ""

        if "is_deleted" in columns:
            deleted_filter = "AND is_deleted = 0"

        placeholders = ", ".join(
            "?" for _ in job_ids
        )

        self.cursor.execute(f"""
        SELECT COALESCE(SUM(cost), 0)
        FROM refinery_jobs
        WHERE id IN ({placeholders})
        {deleted_filter}
        """, job_ids)

        return float(self.cursor.fetchone()[0] or 0)

    def _crew_for_sessions(self, session_ids):
        crew = set()

        for session_id in session_ids:
            for row in self.db.get_crew_members(
                session_id
            ):
                crew.add(row[0])

        return sorted(crew)

    def _total_costs_for_sessions(self, session_ids):
        total = 0

        for session_id in session_ids:
            total += self.db.get_total_costs(
                session_id
            )

        return total

    def calculate_payout_proposal(
        self,
        sale_id,
        cost_payer_overrides=None,
    ):
        sale = self.get_sale_summary(sale_id)

        if not sale:
            raise ValueError(tr("error.sale.not_found"))

        if self.sale_has_payout(sale_id):
            raise ValueError(tr("error.payout.already_exists"))

        session_ids = self.trace_sale_session_ids(
            sale_id
        )
        settled_sessions = (
            self._sessions_with_settled_costs(
                exclude_sale_id=sale_id,
            )
        )
        cost_session_ids = [
            sid
            for sid in session_ids
            if sid not in settled_sessions
        ]

        refinery_job_ids = (
            self.trace_sale_refinery_job_ids(
                sale_id
            )
        )
        settled_refinery = (
            self._refinery_jobs_with_settled_costs(
                exclude_sale_id=sale_id,
            )
        )
        cost_refinery_job_ids = [
            job_id
            for job_id in refinery_job_ids
            if job_id not in settled_refinery
        ]

        revenue = float(sale["total_amount"])
        session_costs = self._total_costs_for_sessions(
            cost_session_ids
        )
        refinery_costs = self._total_refinery_costs_for_jobs(
            cost_refinery_job_ids
        )
        total_costs = session_costs + refinery_costs
        raw_refunds = self._cost_refunds_for_sessions(
            cost_session_ids
        )
        raw_refinery_refunds = (
            self._refinery_cost_refunds_for_jobs(
                cost_refinery_job_ids
            )
        )

        for payer, amount in raw_refinery_refunds.items():
            raw_refunds[payer] = (
                raw_refunds.get(payer, 0) + amount
            )

        crew = self._crew_for_sessions(session_ids)
        refunds = self._normalize_refunds(
            raw_refunds,
            crew,
            cost_payer_overrides,
        )
        unassigned = self._unassigned_cost_payers(
            refunds
        )

        share_pool = revenue - total_costs
        equal_share = 0

        if crew and share_pool != 0:
            equal_share = share_pool / len(crew)

        amounts = {}

        for member in crew:
            amounts[member] = (
                equal_share
                + refunds.get(member, 0)
            )

        for payer, refund in refunds.items():
            if payer not in amounts:
                amounts[payer] = refund

        items = [
            {
                "crew_member": name,
                "amount": round(amount, 2),
            }
            for name, amount in sorted(
                amounts.items()
            )
        ]

        distributed = sum(
            item["amount"] for item in items
        )

        warning = None

        if not session_ids:
            warning = tr("error.payout.no_sessions_trace")
        elif unassigned:
            labels = ", ".join(unassigned)
            warning = tr(
                "error.payout.select_cost_payer",
                labels=labels,
            )

        return {
            "sale_id": sale_id,
            "sale": sale,
            "session_ids": session_ids,
            "cost_session_ids": cost_session_ids,
            "refinery_job_ids": refinery_job_ids,
            "cost_refinery_job_ids": cost_refinery_job_ids,
            "revenue": revenue,
            "session_costs": session_costs,
            "refinery_costs": refinery_costs,
            "total_costs": total_costs,
            "share_pool": share_pool,
            "equal_share": equal_share,
            "refunds": refunds,
            "raw_refunds": raw_refunds,
            "unassigned_cost_payers": unassigned,
            "crew": crew,
            "items": items,
            "distributed_total": distributed,
            "warning": warning,
        }

    def create_payout(
        self,
        sale_id,
        items,
        created_by=None,
        notes=None,
        approved_by=None,
    ):
        if created_by is None:
            created_by = user_session.get_user_id()

        if approved_by is None:
            from config.permissions import (
                has_permission,
                PERM_PAYOUTS_APPROVE,
            )

            if has_permission(PERM_PAYOUTS_APPROVE):
                approved_by = created_by

        if self.sale_has_payout(sale_id):
            raise ValueError(tr("error.payout.already_exists"))

        if not items:
            raise ValueError(tr("error.payout.items_required"))

        normalized = []

        for item in items:
            member = (
                item["crew_member"].strip()
            )
            amount = float(item["amount"])

            if not member:
                raise ValueError(tr("error.payout.member_empty"))

            if amount < 0:
                raise ValueError(
                    tr("error.payout.amount_not_negative")
                )

            normalized.append({
                "crew_member": member,
                "amount": amount,
            })

        payout_id = self.db.materials.create_payout(
            sale_id,
            normalized,
            created_by=created_by,
            notes=notes,
            approved_by=approved_by,
        )
        self.refresh_sessions_for_sale(sale_id)
        return payout_id

    def refresh_sessions_for_sale(self, sale_id):
        for session_id in self.trace_sale_session_ids(
            sale_id
        ):
            self.refresh_session_status(session_id)

    def session_has_unsold_sellable_inventory(
        self,
        session_id,
    ):
        if (
            not self.db._table_exists("material_stockpiles")
            or not hasattr(self.db, "stockpiles")
        ):
            return False

        return (
            self.db.stockpiles.session_sellable_quantity(session_id)
            > 1e-9
        )

    def session_has_unpaid_sales(self, session_id):
        if not self.db._table_exists("sales"):
            return False

        sales_deleted = ""

        if "is_deleted" in self.db._table_columns("sales"):
            sales_deleted = "AND s.is_deleted = 0"

        payout_deleted = self._payout_deleted_filter("p")

        self.cursor.execute(f"""
        SELECT DISTINCT s.id
        FROM sales s
        LEFT JOIN payouts p
            ON p.sale_id = s.id
            {payout_deleted}
        INNER JOIN sale_items si
            ON si.sale_id = s.id
        INNER JOIN storage_items st
            ON st.id = si.storage_item_id
        INNER JOIN material_batches mb
            ON st.source_type = 'SESSION'
            AND st.source_id = mb.id
        WHERE mb.session_id = ?
        AND p.id IS NULL
        {sales_deleted}
        """, (session_id,))

        if self.cursor.fetchall():
            return True

        self.cursor.execute(f"""
        SELECT DISTINCT s.id
        FROM sales s
        LEFT JOIN payouts p
            ON p.sale_id = s.id
            {payout_deleted}
        INNER JOIN sale_items si
            ON si.sale_id = s.id
        INNER JOIN storage_items st
            ON st.id = si.storage_item_id
        INNER JOIN refinery_jobs rj
            ON st.source_type = 'REFINERY'
            AND st.source_id = rj.id
        INNER JOIN refinery_job_items rji
            ON rji.job_id = rj.id
        INNER JOIN material_batches mb
            ON mb.id = rji.batch_id
        WHERE mb.session_id = ?
        AND p.id IS NULL
        {sales_deleted}
        """, (session_id,))

        return bool(self.cursor.fetchall())

    def refresh_session_status(self, session_id):
        self.cursor.execute("""
        SELECT status
        FROM sessions
        WHERE id = ?
        """, (session_id,))

        row = self.cursor.fetchone()

        if not row:
            return

        status = row[0]

        if status in ("SOLD", "CLOSED"):
            return

        if status == "ACTIVE":
            # Laufende Sitzung — Status nur über „Sitzung beenden“ ändern.
            return

        if self.session_has_unpaid_sales(session_id):
            new_status = "WAITING_FOR_PAYOUT"
        elif self.session_has_unsold_sellable_inventory(
            session_id
        ):
            new_status = (
                "ACTIVE"
                if status == "ACTIVE"
                else "WAITING_FOR_SALE"
            )
        elif (
            hasattr(self.db, "refinery")
            and self.db.refinery.session_has_pending_refinery(
                session_id
            )
        ):
            new_status = (
                "ACTIVE"
                if status == "ACTIVE"
                else "WAITING_FOR_REFINERY"
            )
        else:
            new_status = "SOLD"

        if new_status == status:
            return

        session_columns = self.db._table_columns("sessions")
        set_parts = [
            "status = ?",
            "updated_at = datetime('now', 'localtime')",
        ]
        params = [new_status]

        if (
            new_status == "SOLD"
            and "end_time" in session_columns
        ):
            set_parts.insert(
                1,
                "end_time = COALESCE("
                "end_time, datetime('now', 'localtime'))",
            )

        params.append(session_id)

        self.cursor.execute(f"""
        UPDATE sessions
        SET {", ".join(set_parts)}
        WHERE id = ?
        """, params)

        self.connection.commit()

    def get_payout_history(
        self,
        limit=100,
        restrict_to_user_id=None,
    ):
        if not self.db._table_exists("payouts"):
            return []

        deleted_filter = ""

        if "is_deleted" in self.db._table_columns(
            "payouts"
        ):
            deleted_filter = "p.is_deleted = 0"

        filters = []

        if deleted_filter:
            filters.append(deleted_filter)

        params = []

        if restrict_to_user_id is not None:
            filters.append(
                "(p.created_by = ? OR s.created_by = ?)"
            )
            params.extend([
                restrict_to_user_id,
                restrict_to_user_id,
            ])

        where_clause = ""

        if filters:
            where_clause = "WHERE " + " AND ".join(filters)

        params.append(limit)

        self.cursor.execute(f"""
        SELECT
            p.id,
            p.sale_id,
            s.total_amount,
            s.location,
            s.sale_date,
            p.created_at,
            COALESCE(u.username, '—'),
            COALESCE(ua.username, '—')
        FROM payouts p
        INNER JOIN sales s
            ON s.id = p.sale_id
        LEFT JOIN users u
            ON u.id = p.created_by
        LEFT JOIN users ua
            ON ua.id = p.approved_by
        {where_clause}
        ORDER BY p.id DESC
        LIMIT ?
        """, params)

        history = []

        for row in self.cursor.fetchall():
            payout_id = row[0]

            self.cursor.execute("""
            SELECT
                crew_member,
                amount
            FROM payout_items
            WHERE payout_id = ?
            ORDER BY id
            """, (payout_id,))

            items = [
                {
                    "crew_member": item[0],
                    "amount": item[1],
                }
                for item in self.cursor.fetchall()
            ]

            history.append({
                "id": payout_id,
                "sale_id": row[1],
                "sale_amount": row[2],
                "location": row[3],
                "sale_date": row[4],
                "created_at": row[5],
                "created_by": row[6],
                "approved_by": row[7],
                "items": items,
                "payout_total": sum(
                    i["amount"] for i in items
                ),
            })

        return history

    def get_total_payouts_value(self):
        if not self.db._table_exists("payout_items"):
            return 0

        deleted_filter = ""

        if "is_deleted" in self.db._table_columns(
            "payouts"
        ):
            deleted_filter = """
            AND payout_id IN (
                SELECT id FROM payouts
                WHERE is_deleted = 0
            )
            """

        self.cursor.execute(f"""
        SELECT COALESCE(SUM(amount), 0)
        FROM payout_items
        WHERE 1=1
        {deleted_filter}
        """)

        return self.cursor.fetchone()[0]

    def get_crew_payout_totals(self):
        if not self.db._table_exists("payout_items"):
            return []

        deleted_filter = ""

        if "is_deleted" in self.db._table_columns(
            "payouts"
        ):
            deleted_filter = """
            AND payout_items.payout_id IN (
                SELECT id FROM payouts
                WHERE is_deleted = 0
            )
            """

        self.cursor.execute(f"""
        SELECT
            payout_items.crew_member,
            COALESCE(SUM(payout_items.amount), 0)
        FROM payout_items
        WHERE 1=1
        {deleted_filter}
        GROUP BY payout_items.crew_member
        ORDER BY payout_items.crew_member
        """)

        return [
            {
                "crew_member": row[0],
                "total": row[1],
            }
            for row in self.cursor.fetchall()
        ]
