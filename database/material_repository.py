"""
Material-Fluss im Datenmodell (0.8.x):

Mission -> Session -> Material Batch -> Storage
  RMC ........................... direkt verkaufbar
  CM Rubble / Scraps / Salvage .. Rohmaterial (Raffinerie-Input)
                                      |
                                      v
                               Refinery -> CM (raffiniert, verkaufbar)
                                      |
                                      v
                               Sale -> Payout
"""

from config.debug import debug_log
from config.i18n import tr
from config.materials import REFINED_SELLABLE_CODES, material_label


class MaterialRepository:
    def __init__(self, db):
        self.db = db
        self.cursor = db.cursor
        self.connection = db.connection

    def get_material_type_id(self, material_code):
        self.cursor.execute("""
        SELECT id
        FROM material_types
        WHERE material_code = ?
        """, (material_code,))

        row = self.cursor.fetchone()

        if row:
            return row[0]

        self.cursor.execute("""
        INSERT INTO material_types (
            material_code,
            material_name,
            created_at
        )
        VALUES (?, ?, datetime('now', 'localtime'))
        """, (material_code, material_code))

        self.connection.commit()

        return self.cursor.lastrowid

    def create_batch_from_session(
        self,
        session_id,
        material_code,
        quantity,
        created_by=None,
        notes=None,
    ):
        if quantity is None or quantity <= 0:
            return None, None

        material_type_id = self.get_material_type_id(
            material_code
        )

        use_stockpile = (
            hasattr(self.db, "stockpiles")
            and self.db._table_exists("material_stockpiles")
        )

        try:
            self.connection.execute("BEGIN IMMEDIATE")

            batch_columns = self.db._table_columns(
                "material_batches"
            )
            has_remaining = (
                "remaining_quantity" in batch_columns
            )

            self.cursor.execute(f"""
            SELECT id
            FROM material_batches
            WHERE session_id = ?
            AND material_type_id = ?
            AND is_deleted = 0
            AND {"remaining_quantity > 0" if has_remaining else "quantity > 0"}
            ORDER BY id ASC
            LIMIT 1
            """, (session_id, material_type_id))

            existing = self.cursor.fetchone()
            if existing:
                batch_id = int(existing[0])
                if has_remaining:
                    self.cursor.execute("""
                    UPDATE material_batches
                    SET
                        quantity = quantity + ?,
                        remaining_quantity = remaining_quantity + ?,
                        updated_at = datetime('now', 'localtime'),
                        updated_by = ?
                    WHERE id = ?
                    AND is_deleted = 0
                    """, (
                        quantity,
                        quantity,
                        created_by,
                        batch_id,
                    ))
                else:
                    self.cursor.execute("""
                    UPDATE material_batches
                    SET
                        quantity = quantity + ?,
                        updated_at = datetime('now', 'localtime'),
                        updated_by = ?
                    WHERE id = ?
                    AND is_deleted = 0
                    """, (
                        quantity,
                        created_by,
                        batch_id,
                    ))
            else:
                if has_remaining:
                    self.cursor.execute("""
                    INSERT INTO material_batches (
                        session_id,
                        material_type_id,
                        quantity,
                        remaining_quantity,
                        notes,
                        created_at,
                        created_by
                    )
                    VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'), ?)
                    """, (
                        session_id,
                        material_type_id,
                        quantity,
                        quantity,
                        notes,
                        created_by,
                    ))
                else:
                    self.cursor.execute("""
                    INSERT INTO material_batches (
                        session_id,
                        material_type_id,
                        quantity,
                        notes,
                        created_at,
                        created_by
                    )
                    VALUES (?, ?, ?, ?, datetime('now', 'localtime'), ?)
                    """, (
                        session_id,
                        material_type_id,
                        quantity,
                        notes,
                        created_by,
                    ))

                batch_id = self.cursor.lastrowid

            storage_id = None

            if use_stockpile:
                ship = self.db.get_session_ship(session_id)
                if not ship:
                    raise ValueError(tr("error.session.ship_not_found"))

                storage_id = self.db.stockpiles.deposit_session_capture(
                    material_code=material_code,
                    quantity_scu=quantity,
                    session_id=session_id,
                    batch_id=batch_id,
                    ship_id=ship["ship_id"],
                    ship_name=ship["ship_name"],
                    created_by=created_by,
                )
            else:
                storage_id = self.add_to_storage(
                    material_type_id,
                    quantity,
                    source_type="SESSION",
                    source_id=batch_id,
                    created_by=created_by,
                )

            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

        return batch_id, storage_id

    def reserve_batch_for_refinery(
        self,
        batch_id,
        quantity,
        updated_by=None,
    ):
        if quantity is None or quantity <= 0:
            return

        batch_columns = self.db._table_columns(
            "material_batches"
        )

        has_remaining = (
            "remaining_quantity" in batch_columns
        )

        if has_remaining:
            self.cursor.execute("""
            SELECT remaining_quantity
            FROM material_batches
            WHERE id = ?
            AND is_deleted = 0
            """, (batch_id,))

            row = self.cursor.fetchone()

            if not row:
                raise ValueError(tr("error.material.batch_not_found"))

            available = row[0] or 0

            if quantity > available:
                raise ValueError(
                    tr(
                        "error.material.insufficient_batch",
                        available=f"{available:g}",
                    )
                )

            self.cursor.execute("""
            UPDATE material_batches
            SET
                remaining_quantity =
                    remaining_quantity - ?,
                updated_at = datetime('now', 'localtime'),
                updated_by = ?
            WHERE id = ?
            """, (
                quantity,
                updated_by,
                batch_id,
            ))
        else:
            self.consume_batch_quantity(
                batch_id,
                quantity,
                updated_by=updated_by,
            )
            return

        self.cursor.execute("""
        SELECT id, quantity
        FROM storage_items
        WHERE source_type = 'SESSION'
        AND source_id = ?
        AND is_deleted = 0
        ORDER BY id DESC
        LIMIT 1
        """, (batch_id,))

        storage_row = self.cursor.fetchone()

        if storage_row:
            storage_id, storage_qty = storage_row

            self.cursor.execute("""
            UPDATE storage_items
            SET
                quantity = ?,
                updated_at = datetime('now', 'localtime'),
                updated_by = ?
            WHERE id = ?
            """, (
                max(0, storage_qty - quantity),
                updated_by,
                storage_id,
            ))

    def release_batch_from_refinery(
        self,
        batch_id,
        quantity,
        updated_by=None,
    ):
        if quantity is None or quantity <= 0:
            return

        batch_columns = self.db._table_columns(
            "material_batches"
        )
        has_remaining = (
            "remaining_quantity" in batch_columns
        )

        if has_remaining:
            self.cursor.execute("""
            UPDATE material_batches
            SET
                remaining_quantity =
                    remaining_quantity + ?,
                updated_at = datetime('now', 'localtime'),
                updated_by = ?
            WHERE id = ?
            AND is_deleted = 0
            """, (
                quantity,
                updated_by,
                batch_id,
            ))
        else:
            self.cursor.execute("""
            UPDATE material_batches
            SET
                quantity = quantity + ?,
                updated_at = datetime('now', 'localtime'),
                updated_by = ?
            WHERE id = ?
            AND is_deleted = 0
            """, (
                quantity,
                updated_by,
                batch_id,
            ))

        self.cursor.execute("""
        SELECT id, quantity
        FROM storage_items
        WHERE source_type = 'SESSION'
        AND source_id = ?
        AND is_deleted = 0
        ORDER BY id DESC
        LIMIT 1
        """, (batch_id,))

        storage_row = self.cursor.fetchone()

        if storage_row:
            storage_id, storage_qty = storage_row

            self.cursor.execute("""
            UPDATE storage_items
            SET
                quantity = ?,
                updated_at = datetime('now', 'localtime'),
                updated_by = ?
            WHERE id = ?
            """, (
                storage_qty + quantity,
                updated_by,
                storage_id,
            ))

    def allocate_batches_fifo(
        self,
        material_code: str,
        quantity_scu: float,
        *,
        ship_id: int | None = None,
    ) -> list[dict]:
        """Verteilt Menge FIFO auf offene Batches (Raffinerie-Buchführung)."""
        if quantity_scu <= 0:
            return []

        batch_columns = self.db._table_columns("material_batches")
        has_remaining = "remaining_quantity" in batch_columns
        available_sql = (
            "material_batches.remaining_quantity"
            if has_remaining
            else "material_batches.quantity"
        )

        self.cursor.execute(f"""
        SELECT
            material_batches.id,
            material_batches.session_id,
            {available_sql}
        FROM material_batches
        INNER JOIN material_types
            ON material_types.id =
                material_batches.material_type_id
        WHERE material_batches.is_deleted = 0
        AND material_types.material_code = ?
        AND {available_sql} > 0
        ORDER BY material_batches.id ASC
        """, (material_code,))

        rows = self.cursor.fetchall()
        if ship_id is not None:
            filtered = []
            for batch_id, session_id, available in rows:
                ship = self.db.get_session_ship(session_id)
                if ship and ship.get("ship_id") == ship_id:
                    filtered.append((batch_id, session_id, available))
            rows = filtered

        remaining = float(quantity_scu)
        lines: list[dict] = []
        for batch_id, _session_id, available in rows:
            if remaining <= 1e-9:
                break
            take = min(remaining, float(available or 0))
            if take <= 0:
                continue
            lines.append({
                "batch_id": int(batch_id),
                "input_quantity": take,
                "input_material": material_code,
            })
            remaining -= take

        if remaining > 1e-9:
            label = material_label(material_code)
            raise ValueError(
                tr(
                    "error.material.insufficient_batches",
                    material=label,
                    available=f"{quantity_scu - remaining:g}",
                    requested=f"{quantity_scu:g}",
                )
            )

        return lines

    def reduce_session_capture(
        self,
        batch_id: int,
        quantity_scu: float,
        updated_by=None,
    ) -> None:
        """Salvage-Erfassung rückgängig: Batch-Menge reduzieren."""
        if quantity_scu <= 0:
            return

        batch_columns = self.db._table_columns(
            "material_batches"
        )
        has_remaining = (
            "remaining_quantity" in batch_columns
        )

        remaining_sql = (
            ", remaining_quantity"
            if has_remaining
            else ""
        )

        self.cursor.execute(f"""
        SELECT
            quantity
            {remaining_sql}
        FROM material_batches
        WHERE id = ?
        AND is_deleted = 0
        """, (batch_id,))

        row = self.cursor.fetchone()
        if not row:
            raise ValueError(tr("error.material.batch_not_found"))

        total_qty = float(row[0] or 0)
        remaining_qty = (
            float(row[1] or 0)
            if has_remaining
            else total_qty
        )

        if (
            total_qty + 1e-9 < quantity_scu
            or remaining_qty + 1e-9 < quantity_scu
        ):
            raise ValueError(
                tr("error.material.capture_in_use")
            )

        if self.db._table_exists("refinery_job_items"):
            job_deleted = ""
            if "is_deleted" in self.db._table_columns(
                "refinery_jobs"
            ):
                job_deleted = (
                    "AND COALESCE(rj.is_deleted, 0) = 0"
                )

            self.cursor.execute(f"""
            SELECT COALESCE(SUM(rji.input_quantity), 0)
            FROM refinery_job_items rji
            INNER JOIN refinery_jobs rj
                ON rj.id = rji.job_id
            WHERE rji.batch_id = ?
            AND rj.status IN ('RUNNING', 'READY')
            {job_deleted}
            """, (batch_id,))

            active_reserved = float(
                self.cursor.fetchone()[0] or 0
            )
            if active_reserved > 1e-9:
                raise ValueError(
                    tr("error.material.capture_in_refinery")
                )

        new_total = total_qty - quantity_scu
        new_remaining = remaining_qty - quantity_scu

        if new_total <= 1e-9:
            if "is_deleted" in batch_columns:
                if has_remaining:
                    self.cursor.execute("""
                    UPDATE material_batches
                    SET
                        quantity = 0,
                        remaining_quantity = 0,
                        is_deleted = 1,
                        updated_at = datetime('now', 'localtime'),
                        updated_by = ?
                    WHERE id = ?
                    """, (updated_by, batch_id))
                else:
                    self.cursor.execute("""
                    UPDATE material_batches
                    SET
                        quantity = 0,
                        is_deleted = 1,
                        updated_at = datetime('now', 'localtime'),
                        updated_by = ?
                    WHERE id = ?
                    """, (updated_by, batch_id))
            elif has_remaining:
                self.cursor.execute("""
                UPDATE material_batches
                SET
                    quantity = 0,
                    remaining_quantity = 0,
                    updated_at = datetime('now', 'localtime'),
                    updated_by = ?
                WHERE id = ?
                AND is_deleted = 0
                """, (updated_by, batch_id))
            else:
                self.cursor.execute("""
                UPDATE material_batches
                SET
                    quantity = 0,
                    updated_at = datetime('now', 'localtime'),
                    updated_by = ?
                WHERE id = ?
                AND is_deleted = 0
                """, (updated_by, batch_id))
        elif has_remaining:
            self.cursor.execute("""
            UPDATE material_batches
            SET
                quantity = ?,
                remaining_quantity = ?,
                updated_at = datetime('now', 'localtime'),
                updated_by = ?
            WHERE id = ?
            AND is_deleted = 0
            """, (
                new_total,
                new_remaining,
                updated_by,
                batch_id,
            ))
        else:
            self.cursor.execute("""
            UPDATE material_batches
            SET
                quantity = ?,
                updated_at = datetime('now', 'localtime'),
                updated_by = ?
            WHERE id = ?
            AND is_deleted = 0
            """, (
                new_total,
                updated_by,
                batch_id,
            ))

    def session_ids_for_ship_material(
        self,
        material_code: str,
        ship_id: int,
    ) -> list[int]:
        """Session-IDs mit offenem Batch-Material auf dem Schiff."""
        batch_columns = self.db._table_columns("material_batches")
        has_remaining = "remaining_quantity" in batch_columns
        available_sql = (
            "material_batches.remaining_quantity"
            if has_remaining
            else "material_batches.quantity"
        )

        self.cursor.execute(f"""
        SELECT DISTINCT material_batches.session_id
        FROM material_batches
        INNER JOIN material_types
            ON material_types.id =
                material_batches.material_type_id
        WHERE material_batches.is_deleted = 0
        AND material_types.material_code = ?
        AND material_batches.session_id IS NOT NULL
        AND {available_sql} > 0
        ORDER BY material_batches.session_id
        """, (material_code,))

        session_ids: list[int] = []
        for row in self.cursor.fetchall():
            session_id = row[0]
            if not session_id:
                continue
            ship = self.db.get_session_ship(session_id)
            if ship and ship.get("ship_id") == ship_id:
                session_ids.append(int(session_id))
        return session_ids

    def restore_storage_quantity(
        self,
        storage_item_id,
        quantity,
        updated_by=None,
    ):
        if quantity is None or quantity <= 0:
            return

        self.cursor.execute("""
        UPDATE storage_items
        SET
            quantity = quantity + ?,
            updated_at = datetime('now', 'localtime'),
            updated_by = ?
        WHERE id = ?
        AND is_deleted = 0
        """, (
            quantity,
            updated_by,
            storage_item_id,
        ))

    def consume_batch_quantity(
        self,
        batch_id,
        quantity,
        updated_by=None,
    ):
        if quantity is None or quantity <= 0:
            return

        self.cursor.execute("""
        SELECT quantity
        FROM material_batches
        WHERE id = ?
        AND is_deleted = 0
        """, (batch_id,))

        row = self.cursor.fetchone()

        if not row:
            raise ValueError(tr("error.material.batch_not_found"))

        available = row[0]

        if quantity > available:
            raise ValueError(
                tr(
                    "error.material.insufficient_batch",
                    available=f"{available:g}",
                )
            )

        self.cursor.execute("""
        UPDATE material_batches
        SET
            quantity = quantity - ?,
            updated_at = datetime('now', 'localtime'),
            updated_by = ?
        WHERE id = ?
        """, (
            quantity,
            updated_by,
            batch_id,
        ))

        self.cursor.execute("""
        SELECT id, quantity
        FROM storage_items
        WHERE source_type = 'SESSION'
        AND source_id = ?
        AND is_deleted = 0
        ORDER BY id DESC
        LIMIT 1
        """, (batch_id,))

        storage_row = self.cursor.fetchone()

        if storage_row:
            storage_id, storage_qty = storage_row

            self.cursor.execute("""
            UPDATE storage_items
            SET
                quantity = ?,
                updated_at = datetime('now', 'localtime'),
                updated_by = ?
            WHERE id = ?
            """, (
                max(0, storage_qty - quantity),
                updated_by,
                storage_id,
            ))

    def add_to_storage(
        self,
        material_type_id,
        quantity,
        source_type,
        source_id,
        created_by=None,
        notes=None,
    ):
        self.cursor.execute("""
        INSERT INTO storage_items (
            material_type_id,
            quantity,
            source_type,
            source_id,
            notes,
            created_at,
            created_by
        )
        VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'), ?)
        """, (
            material_type_id,
            quantity,
            source_type,
            source_id,
            notes,
            created_by,
        ))

        return self.cursor.lastrowid

    def get_storage_by_source(
        self,
        source_type,
        source_id,
    ):
        self.cursor.execute("""
        SELECT
            storage_items.id,
            material_types.material_code,
            storage_items.quantity,
            storage_items.source_type,
            storage_items.source_id,
            storage_items.created_at
        FROM storage_items
        INNER JOIN material_types
            ON material_types.id =
                storage_items.material_type_id
        WHERE storage_items.source_type = ?
        AND storage_items.source_id = ?
        AND storage_items.is_deleted = 0
        ORDER BY storage_items.id
        """, (source_type, source_id))

        return self.cursor.fetchall()

    def get_batch_trace(self, batch_id):
        self.cursor.execute("""
        SELECT
            material_batches.id,
            material_batches.session_id,
            material_types.material_code,
            material_batches.quantity,
            material_batches.created_at,
            sessions.session_name,
            sessions.status
        FROM material_batches
        INNER JOIN material_types
            ON material_types.id =
                material_batches.material_type_id
        INNER JOIN sessions
            ON sessions.id =
                material_batches.session_id
        WHERE material_batches.id = ?
        """, (batch_id,))

        batch = self.cursor.fetchone()

        if not batch:
            return None

        storage = self.get_storage_by_source(
            "SESSION",
            batch_id,
        )

        self.cursor.execute("""
        SELECT
            refinery_job_items.id,
            refinery_job_items.job_id,
            refinery_job_items.input_quantity,
            refinery_job_items.output_quantity,
            refinery_jobs.status,
            refinery_jobs.station
        FROM refinery_job_items
        INNER JOIN refinery_jobs
            ON refinery_jobs.id =
                refinery_job_items.job_id
        WHERE refinery_job_items.batch_id = ?
        """, (batch_id,))

        refinery = self.cursor.fetchall()

        return {
            "batch": batch,
            "storage": storage,
            "refinery": refinery,
        }

    def get_storage_balance(self, material_code=None):
        if material_code:
            self.cursor.execute("""
            SELECT
                material_types.material_code,
                COALESCE(SUM(storage_items.quantity), 0)
            FROM storage_items
            INNER JOIN material_types
                ON material_types.id =
                    storage_items.material_type_id
            WHERE storage_items.is_deleted = 0
            AND material_types.material_code = ?
            GROUP BY material_types.material_code
            """, (material_code,))

            row = self.cursor.fetchone()

            if not row:
                return 0

            return row[1]

        self.cursor.execute("""
        SELECT
            material_types.material_code,
            COALESCE(SUM(storage_items.quantity), 0)
        FROM storage_items
        INNER JOIN material_types
            ON material_types.id =
                storage_items.material_type_id
        WHERE storage_items.is_deleted = 0
        GROUP BY material_types.material_code
        ORDER BY material_types.material_code
        """)

        return self.cursor.fetchall()

    def get_available_inventory(
        self,
        *,
        exclude_refinery_source: bool = False,
        global_pool_only: bool = False,
    ):
        placeholders = ",".join(
            "?" * len(REFINED_SELLABLE_CODES)
        )
        refinery_filter = ""
        if exclude_refinery_source:
            refinery_filter = """
            AND (
                storage_items.source_type IS NULL
                OR storage_items.source_type != 'REFINERY'
            )
            """
        global_filter = ""
        if global_pool_only:
            if self.db._table_exists("material_stockpiles"):
                global_filter = """
                AND storage_items.id NOT IN (
                    SELECT material_stockpiles.storage_item_id
                    FROM material_stockpiles
                    WHERE material_stockpiles.storage_item_id IS NOT NULL
                    AND material_stockpiles.is_deleted = 0
                )
                AND NOT (
                    storage_items.source_type = 'SESSION'
                    AND EXISTS (
                        SELECT 1
                        FROM material_batches mb
                        INNER JOIN material_stockpiles sp
                            ON sp.session_id = mb.session_id
                        INNER JOIN material_types mt_sp
                            ON mt_sp.id = sp.material_type_id
                        WHERE mb.id = storage_items.source_id
                        AND mt_sp.id = mb.material_type_id
                        AND sp.is_deleted = 0
                        AND sp.location_kind = 'SHIP'
                        AND sp.status = 'IN_SHIP'
                    )
                )
                """
            else:
                global_filter = """
                AND (
                    storage_items.source_type IS NULL
                    OR storage_items.source_type != 'STOCKPILE'
                )
                """

        self.cursor.execute(f"""
        SELECT
            material_types.material_code,
            material_types.material_name,
            COALESCE(SUM(storage_items.quantity), 0)
        FROM storage_items
        INNER JOIN material_types
            ON material_types.id =
                storage_items.material_type_id
        WHERE storage_items.is_deleted = 0
        AND storage_items.quantity > 0
        AND material_types.material_code IN ({placeholders})
        {refinery_filter}
        {global_filter}
        GROUP BY
            material_types.material_code,
            material_types.material_name
        HAVING SUM(storage_items.quantity) > 0
        ORDER BY material_types.material_code
        """, list(REFINED_SELLABLE_CODES))

        return [
            {
                "material_code": row[0],
                "material_name": row[1],
                "quantity": row[2],
            }
            for row in self.cursor.fetchall()
        ]

    def _storage_rows_for_material(
        self,
        material_code,
        *,
        global_pool_only: bool = False,
    ):
        global_filter = ""
        if global_pool_only:
            if self.db._table_exists("material_stockpiles"):
                global_filter = """
                AND storage_items.id NOT IN (
                    SELECT material_stockpiles.storage_item_id
                    FROM material_stockpiles
                    WHERE material_stockpiles.storage_item_id IS NOT NULL
                    AND material_stockpiles.is_deleted = 0
                )
                AND NOT (
                    storage_items.source_type = 'SESSION'
                    AND EXISTS (
                        SELECT 1
                        FROM material_batches mb
                        INNER JOIN material_stockpiles sp
                            ON sp.session_id = mb.session_id
                        INNER JOIN material_types mt_sp
                            ON mt_sp.id = sp.material_type_id
                        WHERE mb.id = storage_items.source_id
                        AND mt_sp.id = mb.material_type_id
                        AND sp.is_deleted = 0
                        AND sp.location_kind = 'SHIP'
                        AND sp.status = 'IN_SHIP'
                    )
                )
                """
            else:
                global_filter = """
                AND (
                    storage_items.source_type IS NULL
                    OR storage_items.source_type != 'STOCKPILE'
                )
                """

        self.cursor.execute(f"""
        SELECT
            storage_items.id,
            storage_items.quantity
        FROM storage_items
        INNER JOIN material_types
            ON material_types.id =
                storage_items.material_type_id
        WHERE material_types.material_code = ?
        AND storage_items.is_deleted = 0
        AND storage_items.quantity > 0
        {global_filter}
        ORDER BY storage_items.id ASC
        """, (material_code,))

        return self.cursor.fetchall()

    def global_pool_quantity(
        self,
        material_code: str,
    ) -> float:
        return sum(
            qty
            for _, qty in self._storage_rows_for_material(
                material_code,
                global_pool_only=True,
            )
        )

    def transfer_global_to_stockpile(
        self,
        material_code: str,
        quantity_scu: float,
        created_by=None,
    ) -> tuple[str, int | None]:
        if quantity_scu <= 0:
            return ("SESSION", None)

        remaining = float(quantity_scu)
        rows = self._storage_rows_for_material(
            material_code,
            global_pool_only=True,
        )
        available = sum(qty for _, qty in rows)

        if available + 1e-9 < remaining:
            raise ValueError(
                tr(
                    "error.storage.insufficient_global",
                    available=f"{available:g}",
                    material=material_label(material_code),
                )
            )

        primary_source_type = "SESSION"
        primary_source_id = None

        for storage_id, available_qty in rows:
            if remaining <= 0:
                break

            if primary_source_id is None:
                self.cursor.execute("""
                SELECT source_type, source_id
                FROM storage_items
                WHERE id = ?
                """, (storage_id,))
                source_row = self.cursor.fetchone()
                if source_row:
                    primary_source_type = source_row[0] or "SESSION"
                    primary_source_id = source_row[1]

            take = min(remaining, float(available_qty))
            self._deduct_storage_row(
                storage_id,
                take,
                created_by,
            )
            remaining -= take

        return (primary_source_type, primary_source_id)

    def create_stockpile_storage_item(
        self,
        material_type_id: int,
        quantity_scu: float,
        *,
        source_type: str,
        source_id: int | None,
        created_by=None,
    ) -> int:
        self.cursor.execute("""
        INSERT INTO storage_items (
            material_type_id,
            quantity,
            source_type,
            source_id,
            created_at,
            created_by
        )
        VALUES (?, ?, ?, ?, datetime('now', 'localtime'), ?)
        """, (
            material_type_id,
            quantity_scu,
            source_type,
            source_id,
            created_by,
        ))

        return self.cursor.lastrowid

    def increase_stockpile_storage_item(
        self,
        storage_item_id: int,
        quantity_scu: float,
        updated_by=None,
    ) -> None:
        self.cursor.execute("""
        SELECT quantity
        FROM storage_items
        WHERE id = ?
        AND is_deleted = 0
        """, (storage_item_id,))

        row = self.cursor.fetchone()
        if not row:
            raise ValueError(tr("error.material.storage_changed"))

        self.cursor.execute("""
        UPDATE storage_items
        SET
            quantity = quantity + ?,
            updated_at = datetime('now', 'localtime'),
            updated_by = ?
        WHERE id = ?
        """, (
            quantity_scu,
            updated_by,
            storage_item_id,
        ))

    def _deduct_storage_row(
        self,
        storage_item_id,
        quantity,
        updated_by=None,
    ):
        self.cursor.execute("""
        SELECT quantity
        FROM storage_items
        WHERE id = ?
        AND is_deleted = 0
        """, (storage_item_id,))

        row = self.cursor.fetchone()

        if not row or row[0] < quantity:
            raise ValueError(tr("error.material.storage_changed"))

        self.cursor.execute("""
        UPDATE storage_items
        SET
            quantity = quantity - ?,
            updated_at = datetime('now', 'localtime'),
            updated_by = ?
        WHERE id = ?
        """, (
            quantity,
            updated_by,
            storage_item_id,
        ))

    def create_sale_with_storage(
        self,
        location,
        sale_date,
        lines,
        created_by=None,
        notes=None,
    ):
        if not lines:
            raise ValueError(tr("error.sale.line_required"))

        sale_item_records = []

        try:
            self.connection.execute(
                "BEGIN IMMEDIATE"
            )

            for line in lines:
                material_code = line["material_code"]
                quantity = float(line["quantity"])
                unit_price = float(line["unit_price"])

                if quantity <= 0:
                    raise ValueError(
                        tr("error.sale.quantity_must_be_positive")
                    )

                if unit_price < 0:
                    raise ValueError(
                        tr("error.sale.price_not_negative")
                    )

                if material_code not in REFINED_SELLABLE_CODES:
                    raise ValueError(
                        tr(
                            "error.sale.material_not_sellable",
                            material_code=material_code,
                        )
                    )

                remaining = quantity

                for (
                    storage_id,
                    available,
                ) in self._storage_rows_for_material(
                    material_code
                ):
                    if remaining <= 0:
                        break

                    take = min(
                        remaining,
                        available,
                    )

                    self._deduct_storage_row(
                        storage_id,
                        take,
                        created_by,
                    )

                    sale_item_records.append({
                        "storage_item_id": storage_id,
                        "quantity": take,
                        "unit_price": unit_price,
                        "total_price": (
                            take * unit_price
                        ),
                    })

                    remaining -= take

                if remaining > 0:
                    raise ValueError(
                        tr(
                            "error.sale.insufficient_stock",
                            material_code=material_code,
                            remaining=f"{remaining:g}",
                        )
                    )

            total_amount = sum(
                item["total_price"]
                for item in sale_item_records
            )

            self.cursor.execute("""
            INSERT INTO sales (
                location,
                sale_date,
                total_amount,
                notes,
                created_at,
                created_by
            )
            VALUES (?, ?, ?, ?, datetime('now', 'localtime'), ?)
            """, (
                location,
                sale_date,
                total_amount,
                notes,
                created_by,
            ))

            sale_id = self.cursor.lastrowid

            for item in sale_item_records:
                self.cursor.execute("""
                INSERT INTO sale_items (
                    sale_id,
                    storage_item_id,
                    quantity,
                    unit_price,
                    total_price,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))
                """, (
                    sale_id,
                    item["storage_item_id"],
                    item["quantity"],
                    item["unit_price"],
                    item["total_price"],
                ))

            self.connection.commit()

            return sale_id

        except Exception:
            self.connection.rollback()
            raise

    def complete_refinery_job(
        self,
        job_id,
        output_quantity,
        output_material_code,
        updated_by=None,
    ):
        self.cursor.execute("""
        UPDATE refinery_jobs
        SET
            status = 'READY',
            end_time = datetime('now', 'localtime'),
            updated_at = datetime('now', 'localtime'),
            updated_by = ?
        WHERE id = ?
        """, (updated_by, job_id))

        self.cursor.execute("""
        UPDATE refinery_job_items
        SET
            output_quantity = ?,
            updated_at = datetime('now', 'localtime')
        WHERE job_id = ?
        """, (output_quantity, job_id))

        material_type_id = self.get_material_type_id(
            output_material_code
        )

        storage_id = self.add_to_storage(
            material_type_id,
            output_quantity,
            source_type="REFINERY",
            source_id=job_id,
            created_by=updated_by,
        )

        self.connection.commit()

        return storage_id

    def create_payout(
        self,
        sale_id,
        items,
        created_by=None,
        notes=None,
        approved_by=None,
    ):
        columns = self.db._table_columns("payouts")

        if approved_by is not None and "approved_by" in columns:
            self.cursor.execute("""
            INSERT INTO payouts (
                sale_id,
                notes,
                created_at,
                created_by,
                approved_by
            )
            VALUES (?, ?, datetime('now', 'localtime'), ?, ?)
            """, (sale_id, notes, created_by, approved_by))
        else:
            self.cursor.execute("""
            INSERT INTO payouts (
                sale_id,
                notes,
                created_at,
                created_by
            )
            VALUES (?, ?, datetime('now', 'localtime'), ?)
            """, (sale_id, notes, created_by))

        payout_id = self.cursor.lastrowid

        for item in items:
            self.cursor.execute("""
            INSERT INTO payout_items (
                payout_id,
                crew_member,
                amount,
                created_at
            )
            VALUES (?, ?, ?, datetime('now', 'localtime'))
            """, (
                payout_id,
                item["crew_member"],
                item["amount"],
            ))

        self.connection.commit()

        return payout_id
