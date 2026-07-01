"""
Stornieren / Löschen von fehlerhaften Workflow-Einträgen.

Soft-Delete mit Bestandsrückbuchung, wo möglich.
"""

import auth.session as user_session
from config.i18n import tr


class CorrectionRepository:
    ACTIVE_REFINERY_STATUSES = ("RUNNING", "READY")

    def __init__(self, db):
        self.db = db
        self.cursor = db.cursor
        self.connection = db.connection

    def _mark_deleted(self, table, record_id):
        columns = self.db._table_columns(table)

        if "is_deleted" not in columns:
            raise ValueError(
                f"Tabelle {table} unterstützt kein Löschen."
            )

        if "deleted_at" in columns:
            self.cursor.execute(f"""
            UPDATE {table}
            SET
                is_deleted = 1,
                deleted_at = datetime('now', 'localtime')
            WHERE id = ?
            """, (record_id,))
        else:
            self.cursor.execute(f"""
            UPDATE {table}
            SET is_deleted = 1
            WHERE id = ?
            """, (record_id,))

    def _storage_sold_quantity(self, storage_item_id):
        if not self.db._table_exists("sale_items"):
            return 0

        sales_deleted = ""

        if "is_deleted" in self.db._table_columns("sales"):
            sales_deleted = "AND COALESCE(s.is_deleted, 0) = 0"

        self.cursor.execute(f"""
        SELECT COALESCE(SUM(si.quantity), 0)
        FROM sale_items si
        INNER JOIN sales s
            ON s.id = si.sale_id
        WHERE si.storage_item_id = ?
        {sales_deleted}
        """, (storage_item_id,))

        return float(self.cursor.fetchone()[0] or 0)

    def _session_has_refinery_jobs(self, session_id):
        if not self.db._table_exists("refinery_job_items"):
            return False

        job_deleted = ""

        if "is_deleted" in self.db._table_columns(
            "refinery_jobs"
        ):
            job_deleted = "AND COALESCE(rj.is_deleted, 0) = 0"

        batch_deleted = ""

        if "is_deleted" in self.db._table_columns(
            "material_batches"
        ):
            batch_deleted = (
                "AND COALESCE(mb.is_deleted, 0) = 0"
            )

        self.cursor.execute(f"""
        SELECT COUNT(*)
        FROM refinery_job_items rji
        INNER JOIN material_batches mb
            ON mb.id = rji.batch_id
        INNER JOIN refinery_jobs rj
            ON rj.id = rji.job_id
        WHERE mb.session_id = ?
        {batch_deleted}
        {job_deleted}
        """, (session_id,))

        return self.cursor.fetchone()[0] > 0

    def _session_has_sales(self, session_id):
        if not self.db._table_exists("sale_items"):
            return False

        sales_deleted = ""

        if "is_deleted" in self.db._table_columns("sales"):
            sales_deleted = "AND COALESCE(s.is_deleted, 0) = 0"

        storage_deleted = ""

        if "is_deleted" in self.db._table_columns(
            "storage_items"
        ):
            storage_deleted = (
                "AND COALESCE(st.is_deleted, 0) = 0"
            )

        self.cursor.execute(f"""
        SELECT COUNT(DISTINCT s.id)
        FROM sales s
        INNER JOIN sale_items si
            ON si.sale_id = s.id
        INNER JOIN storage_items st
            ON st.id = si.storage_item_id
        INNER JOIN material_batches mb
            ON st.source_type = 'SESSION'
            AND st.source_id = mb.id
        WHERE mb.session_id = ?
        {sales_deleted}
        {storage_deleted}
        """, (session_id,))

        if self.cursor.fetchone()[0] > 0:
            return True

        self.cursor.execute(f"""
        SELECT COUNT(DISTINCT s.id)
        FROM sales s
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
        {sales_deleted}
        {storage_deleted}
        """, (session_id,))

        return self.cursor.fetchone()[0] > 0

    def can_delete_session(self, session_id):
        session_columns = self.db._table_columns("sessions")

        if "is_deleted" in session_columns:
            self.cursor.execute("""
            SELECT id, status
            FROM sessions
            WHERE id = ?
            AND is_deleted = 0
            """, (session_id,))
        else:
            self.cursor.execute("""
            SELECT id, status
            FROM sessions
            WHERE id = ?
            """, (session_id,))

        row = self.cursor.fetchone()

        if not row:
            return False, tr("error.session.not_found")

        if self._session_has_refinery_jobs(session_id):
            return False, tr("error.session.has_refinery_jobs")

        if self._session_has_sales(session_id):
            return False, tr("error.session.has_sales")

        return True, None

    def delete_session(self, session_id, updated_by=None):
        if updated_by is None:
            updated_by = user_session.get_user_id()

        ok, reason = self.can_delete_session(session_id)

        if not ok:
            raise ValueError(reason)

        try:
            self.connection.execute("BEGIN IMMEDIATE")

            cost_columns = self.db._table_columns("costs")

            if "is_deleted" in cost_columns:
                if "deleted_at" in cost_columns:
                    self.cursor.execute("""
                    UPDATE costs
                    SET
                        is_deleted = 1,
                        deleted_at = datetime('now', 'localtime')
                    WHERE session_id = ?
                    AND COALESCE(is_deleted, 0) = 0
                    """, (session_id,))
                else:
                    self.cursor.execute("""
                    UPDATE costs
                    SET is_deleted = 1
                    WHERE session_id = ?
                    AND COALESCE(is_deleted, 0) = 0
                    """, (session_id,))

            self.cursor.execute("""
            SELECT id
            FROM material_batches
            WHERE session_id = ?
            AND COALESCE(is_deleted, 0) = 0
            """, (session_id,))

            batch_ids = [
                row[0]
                for row in self.cursor.fetchall()
            ]

            batch_cleanup = self._session_batch_cleanup_amounts(
                batch_ids
            )

            for batch_id in batch_ids:
                self.cursor.execute("""
                SELECT id
                FROM storage_items
                WHERE source_type = 'SESSION'
                AND source_id = ?
                AND COALESCE(is_deleted, 0) = 0
                """, (batch_id,))

                for (storage_id,) in self.cursor.fetchall():
                    self._mark_deleted(
                        "storage_items",
                        storage_id,
                    )

                self._mark_deleted(
                    "material_batches",
                    batch_id,
                )

            self._cleanup_session_stockpiles(
                session_id,
                batch_cleanup,
                updated_by=updated_by,
            )

            self._mark_deleted("sessions", session_id)

            self.connection.commit()

        except Exception:
            self.connection.rollback()
            raise

    def _session_batch_cleanup_amounts(
        self,
        batch_ids: list[int],
    ) -> list[dict]:
        if not batch_ids:
            return []

        batch_columns = self.db._table_columns(
            "material_batches"
        )
        has_remaining = (
            "remaining_quantity" in batch_columns
        )
        qty_sql = (
            "material_batches.remaining_quantity"
            if has_remaining
            else "material_batches.quantity"
        )

        placeholders = ", ".join("?" * len(batch_ids))
        self.cursor.execute(f"""
        SELECT
            material_types.material_code,
            {qty_sql}
        FROM material_batches
        INNER JOIN material_types
            ON material_types.id =
                material_batches.material_type_id
        WHERE material_batches.id IN ({placeholders})
        """, batch_ids)

        return [
            {
                "material_code": row[0],
                "quantity_scu": float(row[1] or 0),
            }
            for row in self.cursor.fetchall()
            if float(row[1] or 0) > 0
        ]

    def _cleanup_session_stockpiles(
        self,
        session_id: int,
        batch_amounts: list[dict],
        *,
        updated_by=None,
    ) -> None:
        if (
            not batch_amounts
            or not hasattr(self.db, "stockpiles")
            or not self.db._table_exists("material_stockpiles")
        ):
            return

        ship = self.db.get_session_ship(session_id)
        if not ship:
            return

        user_id = updated_by or user_session.get_user_id()
        ship_id = ship["ship_id"]

        for entry in batch_amounts:
            material_code = entry["material_code"]
            quantity_scu = float(entry["quantity_scu"] or 0)
            if quantity_scu <= 0:
                continue

            existing = self.db.stockpiles._find_ship_stockpile(
                material_code=material_code,
                ship_id=ship_id,
            )
            if not existing:
                continue

            stockpile_id, current_qty = existing
            new_qty = current_qty - quantity_scu
            now = self.db.stockpiles._now()

            if new_qty <= 1e-9:
                self.cursor.execute("""
                UPDATE material_stockpiles
                SET
                    quantity_scu = 0,
                    is_deleted = 1,
                    deleted_at = datetime('now', 'localtime'),
                    updated_at = datetime('now', 'localtime'),
                    updated_by = ?
                WHERE id = ?
                AND is_deleted = 0
                """, (user_id, stockpile_id))
            else:
                self.cursor.execute("""
                UPDATE material_stockpiles
                SET
                    quantity_scu = ?,
                    updated_at = datetime('now', 'localtime'),
                    updated_by = ?
                WHERE id = ?
                AND is_deleted = 0
                """, (new_qty, user_id, stockpile_id))

    def can_delete_mission_cost(self, cost_id: int):
        cost_columns = self.db._table_columns("costs")
        deleted_filter = ""

        if "is_deleted" in cost_columns:
            deleted_filter = "AND COALESCE(c.is_deleted, 0) = 0"

        self.cursor.execute(f"""
        SELECT
            c.session_id,
            ct.cost_name
        FROM costs c
        JOIN cost_types ct
            ON ct.id = c.cost_type_id
        WHERE c.id = ?
        {deleted_filter}
        """, (cost_id,))

        row = self.cursor.fetchone()
        if not row:
            return False, tr("error.cost.not_found")

        if row[1] != "Mission":
            return False, tr("error.cost.not_mission")

        session_id = row[0]
        self.cursor.execute("""
        SELECT status
        FROM sessions
        WHERE id = ?
        AND COALESCE(is_deleted, 0) = 0
        """, (session_id,))

        session_row = self.cursor.fetchone()
        if not session_row:
            return False, tr("error.session.not_found")

        if session_row[0] not in (
            "ACTIVE",
            "WAITING_FOR_REFINERY",
        ):
            return False, tr("error.cost.session_locked")

        return True, None

    def delete_mission_cost(
        self,
        cost_id: int,
        updated_by=None,
    ) -> None:
        ok, reason = self.can_delete_mission_cost(cost_id)
        if not ok:
            raise ValueError(reason)

        self._mark_deleted("costs", cost_id)
        self.connection.commit()

    def can_reopen_session(self, session_id: int):
        session_columns = self.db._table_columns("sessions")
        deleted_filter = ""

        if "is_deleted" in session_columns:
            deleted_filter = "AND COALESCE(is_deleted, 0) = 0"

        self.cursor.execute(f"""
        SELECT status
        FROM sessions
        WHERE id = ?
        {deleted_filter}
        """, (session_id,))

        row = self.cursor.fetchone()
        if not row:
            return False, tr("error.session.not_found")

        if row[0] != "WAITING_FOR_REFINERY":
            return False, tr("error.session.reopen.not_waiting")

        if self.db.get_active_session():
            return False, tr("error.session.reopen.active_exists")

        return True, None

    def reopen_session(self, session_id: int) -> None:
        ok, reason = self.can_reopen_session(session_id)
        if not ok:
            raise ValueError(reason)

        session_columns = self.db._table_columns("sessions")
        end_clear = ""

        if "end_time" in session_columns:
            end_clear = ", end_time = NULL"

        self.cursor.execute(f"""
        UPDATE sessions
        SET status = 'ACTIVE'
        {end_clear}
        WHERE id = ?
        """, (session_id,))

        self.connection.commit()

    def get_correctable_sessions(self, limit=25):
        session_columns = self.db._table_columns("sessions")
        deleted_filter = ""

        if "is_deleted" in session_columns:
            deleted_filter = "AND COALESCE(is_deleted, 0) = 0"

        name_column = self.db._session_name_column()

        self.cursor.execute(f"""
        SELECT
            id,
            {name_column},
            status,
            start_time
        FROM sessions
        WHERE status IN (
            'ACTIVE',
            'WAITING_FOR_REFINERY'
        )
        {deleted_filter}
        ORDER BY id DESC
        LIMIT ?
        """, (limit,))

        sessions = []

        for row in self.cursor.fetchall():
            session_id = row[0]
            ok, _reason = self.can_delete_session(
                session_id
            )

            if ok:
                sessions.append({
                    "id": session_id,
                    "name": row[1],
                    "status": row[2],
                    "start_time": row[3],
                })

        return sessions

    def can_cancel_refinery_job(self, job_id):
        columns = self.db._table_columns("refinery_jobs")
        deleted_filter = ""

        if "is_deleted" in columns:
            deleted_filter = "AND COALESCE(is_deleted, 0) = 0"

        self.cursor.execute(f"""
        SELECT status
        FROM refinery_jobs
        WHERE id = ?
        {deleted_filter}
        """, (job_id,))

        row = self.cursor.fetchone()

        if not row:
            return False, tr("error.refinery.not_found")

        if row[0] not in self.ACTIVE_REFINERY_STATUSES:
            return False, tr("error.refinery.cancel.only_active")

        return True, None

    def cancel_refinery_job(self, job_id, updated_by=None):
        if updated_by is None:
            updated_by = user_session.get_user_id()

        ok, reason = self.can_cancel_refinery_job(job_id)

        if not ok:
            raise ValueError(reason)

        self.cursor.execute("""
        SELECT
            batch_id,
            input_quantity,
            COALESCE(
                input_material,
                (
                    SELECT material_types.material_code
                    FROM material_batches
                    INNER JOIN material_types
                        ON material_types.id =
                            material_batches.material_type_id
                    WHERE material_batches.id =
                        refinery_job_items.batch_id
                )
            )
        FROM refinery_job_items
        WHERE job_id = ?
        ORDER BY id
        """, (job_id,))

        items = self.cursor.fetchall()

        try:
            self.connection.execute("BEGIN IMMEDIATE")

            for batch_id, input_qty, material_code in items:
                self.db.materials.release_batch_from_refinery(
                    batch_id,
                    float(input_qty),
                    updated_by=updated_by,
                )

                if (
                    material_code
                    and hasattr(self.db, "stockpiles")
                    and self.db._table_exists("material_stockpiles")
                ):
                    self.db.stockpiles.restore_ship_stockpile_from_refinery_cancel(
                        material_code=material_code,
                        quantity_scu=float(input_qty),
                        batch_id=batch_id,
                        created_by=updated_by,
                    )

            self._mark_deleted("refinery_jobs", job_id)

            self.connection.commit()

        except Exception:
            self.connection.rollback()
            raise

    def can_delete_refinery_job(self, job_id):
        columns = self.db._table_columns("refinery_jobs")
        deleted_filter = ""

        if "is_deleted" in columns:
            deleted_filter = "AND COALESCE(is_deleted, 0) = 0"

        self.cursor.execute(f"""
        SELECT status
        FROM refinery_jobs
        WHERE id = ?
        {deleted_filter}
        """, (job_id,))

        row = self.cursor.fetchone()

        if not row:
            return False, tr("error.refinery.not_found")

        if row[0] != "COMPLETED":
            return False, tr("error.refinery.delete.only_completed")

        storage_rows = self.db.materials.get_storage_by_source(
            "REFINERY",
            job_id,
        )

        for storage_row in storage_rows:
            storage_id = storage_row[0]
            sold = self._storage_sold_quantity(storage_id)

            if sold > 0:
                return False, tr("error.refinery.delete.already_sold")

        return True, None

    def delete_refinery_job(self, job_id, updated_by=None):
        if updated_by is None:
            updated_by = user_session.get_user_id()

        ok, reason = self.can_delete_refinery_job(job_id)

        if not ok:
            raise ValueError(reason)

        self.cursor.execute("""
        SELECT batch_id, input_quantity
        FROM refinery_job_items
        WHERE job_id = ?
        ORDER BY id
        """, (job_id,))

        items = self.cursor.fetchall()

        storage_rows = self.db.materials.get_storage_by_source(
            "REFINERY",
            job_id,
        )

        try:
            self.connection.execute("BEGIN IMMEDIATE")

            for storage_row in storage_rows:
                storage_id = storage_row[0]
                self._mark_deleted(
                    "storage_items",
                    storage_id,
                )

            for batch_id, input_qty in items:
                self.db.materials.release_batch_from_refinery(
                    batch_id,
                    float(input_qty),
                    updated_by=updated_by,
                )

            self._mark_deleted("refinery_jobs", job_id)

            session_ids = self.db.refinery._session_ids_for_job(
                job_id
            )

            self.connection.commit()

            for session_id in session_ids:
                self.db.payouts.refresh_session_status(
                    session_id
                )

        except Exception:
            self.connection.rollback()
            raise

    def can_void_sale(self, sale_id):
        if self.db.payouts.sale_has_payout(sale_id):
            return False, tr("error.sale.has_payout_void")

        columns = self.db._table_columns("sales")
        deleted_filter = ""

        if "is_deleted" in columns:
            deleted_filter = "AND COALESCE(is_deleted, 0) = 0"

        self.cursor.execute(f"""
        SELECT id
        FROM sales
        WHERE id = ?
        {deleted_filter}
        """, (sale_id,))

        if not self.cursor.fetchone():
            return False, tr("error.sale.not_found")

        return True, None

    def void_sale(self, sale_id, updated_by=None):
        if updated_by is None:
            updated_by = user_session.get_user_id()

        ok, reason = self.can_void_sale(sale_id)

        if not ok:
            raise ValueError(reason)

        self.cursor.execute("""
        SELECT
            storage_item_id,
            quantity
        FROM sale_items
        WHERE sale_id = ?
        ORDER BY id
        """, (sale_id,))

        sale_items = self.cursor.fetchall()

        try:
            self.connection.execute("BEGIN IMMEDIATE")

            for storage_item_id, quantity in sale_items:
                self.db.materials.restore_storage_quantity(
                    storage_item_id,
                    float(quantity),
                    updated_by=updated_by,
                )
                if hasattr(self.db, "stockpiles"):
                    self.db.stockpiles.restore_stockpile_for_storage_item(
                        storage_item_id,
                        float(quantity),
                        updated_by=updated_by,
                    )

            self._mark_deleted("sales", sale_id)

            self.connection.commit()

            self.db.payouts.refresh_sessions_for_sale(
                sale_id
            )

        except Exception:
            self.connection.rollback()
            raise

    def can_void_payout(self, payout_id):
        columns = self.db._table_columns("payouts")
        deleted_filter = ""

        if "is_deleted" in columns:
            deleted_filter = "AND COALESCE(is_deleted, 0) = 0"

        self.cursor.execute(f"""
        SELECT sale_id
        FROM payouts
        WHERE id = ?
        {deleted_filter}
        """, (payout_id,))

        row = self.cursor.fetchone()

        if not row:
            return False, tr("error.payout.not_found")

        return True, None

    def void_payout(self, payout_id, updated_by=None):
        ok, reason = self.can_void_payout(payout_id)

        if not ok:
            raise ValueError(reason)

        self.cursor.execute("""
        SELECT sale_id
        FROM payouts
        WHERE id = ?
        """, (payout_id,))

        row = self.cursor.fetchone()
        sale_id = row[0]

        try:
            self.connection.execute("BEGIN IMMEDIATE")
            self._mark_deleted("payouts", payout_id)
            self.connection.commit()

            self.db.payouts.refresh_sessions_for_sale(
                sale_id
            )

        except Exception:
            self.connection.rollback()
            raise
