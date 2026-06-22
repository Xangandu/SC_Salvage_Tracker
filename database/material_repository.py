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
from config.materials import REFINED_SELLABLE_CODES


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

        batch_id = self.cursor.lastrowid

        storage_id = self.add_to_storage(
            material_type_id,
            quantity,
            source_type="SESSION",
            source_id=batch_id,
            created_by=created_by,
        )

        self.connection.commit()

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
                raise ValueError(
                    "Material-Batch nicht gefunden."
                )

            available = row[0] or 0

            if quantity > available:
                raise ValueError(
                    f"Nicht genug Material im Batch "
                    f"({available:g} SCU verfügbar)."
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
            raise ValueError(
                "Material-Batch nicht gefunden."
            )

        available = row[0]

        if quantity > available:
            raise ValueError(
                f"Nicht genug Material im Batch "
                f"({available:g} SCU verfügbar)."
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

    def get_available_inventory(self):
        placeholders = ",".join(
            "?" * len(REFINED_SELLABLE_CODES)
        )

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
    ):
        self.cursor.execute("""
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
        ORDER BY storage_items.id ASC
        """, (material_code,))

        return self.cursor.fetchall()

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
            raise ValueError(
                "Lagerbestand hat sich geändert. "
                "Bitte erneut versuchen."
            )

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
            raise ValueError(
                "Mindestens eine Verkaufsposition "
                "ist erforderlich."
            )

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
                        "Verkaufsmenge muss größer "
                        "als 0 sein."
                    )

                if unit_price < 0:
                    raise ValueError(
                        "Verkaufspreis darf nicht "
                        "negativ sein."
                    )

                if material_code not in REFINED_SELLABLE_CODES:
                    raise ValueError(
                        f"{material_code} ist kein "
                        f"verkaufbares Material. "
                        f"Rohmaterial muss zuerst "
                        f"raffiniert werden."
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
                        f"Nicht genug Lagerbestand für "
                        f"{material_code}. "
                        f"Es fehlen {remaining:g} SCU."
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
