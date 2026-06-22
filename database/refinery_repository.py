"""
Raffinerie — batch-basiert (keine Session-IDs im Workflow).

Session → material_batches → refinery_jobs → refinery_job_items → storage_items
"""

import auth.session as user_session

from config.materials import (
    RAW_CM_MATERIAL_CODES,
    REFINERY_OUTPUT_CODE,
    material_label,
)
from config.refinery_methods import calc_refinery_efficiency


class RefineryRepository:
    ACTIVE_STATUSES = (
        "RUNNING",
        "READY",
    )

    def __init__(self, db):
        self.db = db
        self.cursor = db.cursor
        self.connection = db.connection
        self.materials = db.materials

    def _batch_has_remaining_column(self):
        return "remaining_quantity" in self.db._table_columns(
            "material_batches"
        )

    def _available_batch_sql(self):
        if self._batch_has_remaining_column():
            return "COALESCE(material_batches.remaining_quantity, 0)"

        return "COALESCE(material_batches.quantity, 0)"

    def _get_batch_available(self, batch_id):
        available_sql = self._available_batch_sql()

        self.cursor.execute(f"""
        SELECT {available_sql}
        FROM material_batches
        WHERE id = ?
        AND is_deleted = 0
        """, (batch_id,))

        row = self.cursor.fetchone()

        if not row:
            return 0

        return row[0]

    def _get_batch_material_code(self, batch_id):
        self.cursor.execute("""
        SELECT material_types.material_code
        FROM material_batches
        INNER JOIN material_types
            ON material_types.id =
                material_batches.material_type_id
        WHERE material_batches.id = ?
        """, (batch_id,))

        row = self.cursor.fetchone()

        if not row:
            return None

        return row[0]

    def get_available_batches(self):
        available_sql = self._available_batch_sql()
        name_column = self.db._session_name_column()
        placeholders = ",".join(
            "?" * len(RAW_CM_MATERIAL_CODES)
        )

        self.cursor.execute(f"""
        SELECT
            material_batches.id,
            material_batches.session_id,
            material_types.material_code,
            material_types.material_name,
            material_batches.quantity,
            {available_sql},
            sessions.{name_column},
            sessions.start_time
        FROM material_batches
        INNER JOIN material_types
            ON material_types.id =
                material_batches.material_type_id
        INNER JOIN sessions
            ON sessions.id =
                material_batches.session_id
        WHERE material_batches.is_deleted = 0
        AND material_types.material_code IN ({placeholders})
        AND {available_sql} > 0
        ORDER BY material_batches.id DESC
        """, list(RAW_CM_MATERIAL_CODES))

        return [
            {
                "batch_id": row[0],
                "session_id": row[1],
                "material_code": row[2],
                "material_name": row[3],
                "original_quantity": row[4],
                "remaining_quantity": row[5],
                "session_name": row[6],
                "session_start": row[7],
            }
            for row in self.cursor.fetchall()
        ]

    def create_job(
        self,
        refinery_name,
        end_time,
        batch_lines,
        created_by=None,
        notes=None,
        refinery_method="",
        cost=0.0,
        cost_paid_by="",
    ):
        if created_by is None:
            created_by = user_session.get_user_id()

        if not batch_lines:
            raise ValueError(
                "Mindestens ein Material-Batch "
                "ist erforderlich."
            )

        try:
            self.connection.execute(
                "BEGIN IMMEDIATE"
            )

            validated_lines = []

            for line in batch_lines:
                batch_id = line["batch_id"]
                input_quantity = float(
                    line["input_quantity"]
                )

                if input_quantity <= 0:
                    raise ValueError(
                        "Eingabemenge muss größer "
                        "als 0 sein."
                    )

                material_code = (
                    self._get_batch_material_code(
                        batch_id
                    )
                )

                if (
                    material_code
                    not in RAW_CM_MATERIAL_CODES
                ):
                    raise ValueError(
                        f"Batch #{batch_id} ist kein "
                        f"Rohmaterial für die Raffinerie."
                    )

                available = self._get_batch_available(
                    batch_id
                )

                if input_quantity > available:
                    label = material_label(
                        material_code
                    )
                    raise ValueError(
                        f"Nicht genug Material in Batch "
                        f"#{batch_id} ({label}). "
                        f"Verfügbar: {available:g} SCU, "
                        f"angefordert: {input_quantity:g} SCU."
                    )

                validated_lines.append({
                    "batch_id": batch_id,
                    "input_quantity": input_quantity,
                    "input_material": material_code,
                })

            method = (refinery_method or "").strip()
            job_cost = float(cost or 0)
            payer = (cost_paid_by or "").strip()

            if job_cost > 0 and not payer:
                raise ValueError(
                    "Bitte angeben, wer die "
                    "Raffinerie-Kosten bezahlt hat."
                )

            if job_cost <= 0:
                payer = ""

            job_columns = self.db._table_columns(
                "refinery_jobs"
            )

            if (
                "refinery_method" in job_columns
                and "cost_paid_by" in job_columns
            ):
                self.cursor.execute("""
                INSERT INTO refinery_jobs (
                    station,
                    start_time,
                    end_time,
                    status,
                    cost,
                    refinery_method,
                    cost_paid_by,
                    notes,
                    created_at,
                    created_by
                )
                VALUES (
                    ?,
                    datetime('now', 'localtime'),
                    ?,
                    'RUNNING',
                    ?,
                    ?,
                    ?,
                    ?,
                    datetime('now', 'localtime'),
                    ?
                )
                """, (
                    refinery_name,
                    end_time,
                    job_cost,
                    method,
                    payer,
                    notes,
                    created_by,
                ))
            elif "refinery_method" in job_columns:
                self.cursor.execute("""
                INSERT INTO refinery_jobs (
                    station,
                    start_time,
                    end_time,
                    status,
                    cost,
                    refinery_method,
                    notes,
                    created_at,
                    created_by
                )
                VALUES (
                    ?,
                    datetime('now', 'localtime'),
                    ?,
                    'RUNNING',
                    ?,
                    ?,
                    ?,
                    datetime('now', 'localtime'),
                    ?
                )
                """, (
                    refinery_name,
                    end_time,
                    job_cost,
                    method,
                    notes,
                    created_by,
                ))
            else:
                self.cursor.execute("""
                INSERT INTO refinery_jobs (
                    station,
                    start_time,
                    end_time,
                    status,
                    cost,
                    notes,
                    created_at,
                    created_by
                )
                VALUES (
                    ?,
                    datetime('now', 'localtime'),
                    ?,
                    'RUNNING',
                    ?,
                    ?,
                    datetime('now', 'localtime'),
                    ?
                )
                """, (
                    refinery_name,
                    end_time,
                    job_cost,
                    notes,
                    created_by,
                ))

            job_id = self.cursor.lastrowid

            item_columns = self.db._table_columns(
                "refinery_job_items"
            )

            for line in validated_lines:
                self.materials.reserve_batch_for_refinery(
                    line["batch_id"],
                    line["input_quantity"],
                    updated_by=created_by,
                )

                if (
                    "input_material" in item_columns
                    and "output_material" in item_columns
                ):
                    self.cursor.execute("""
                    INSERT INTO refinery_job_items (
                        job_id,
                        batch_id,
                        input_material,
                        input_quantity,
                        output_material,
                        output_quantity,
                        yield_percent,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, 0, 0, datetime('now', 'localtime'))
                    """, (
                        job_id,
                        line["batch_id"],
                        line["input_material"],
                        line["input_quantity"],
                        REFINERY_OUTPUT_CODE,
                    ))
                else:
                    self.cursor.execute("""
                    INSERT INTO refinery_job_items (
                        job_id,
                        batch_id,
                        input_quantity,
                        output_quantity,
                        created_at
                    )
                    VALUES (?, ?, ?, 0, datetime('now', 'localtime'))
                    """, (
                        job_id,
                        line["batch_id"],
                        line["input_quantity"],
                    ))

            self.connection.commit()

            return job_id

        except Exception:
            self.connection.rollback()
            raise

    def get_active_jobs(self):
        deleted_filter = ""

        if "is_deleted" in self.db._table_columns(
            "refinery_jobs"
        ):
            deleted_filter = "AND rj.is_deleted = 0"

        self.cursor.execute(f"""
        SELECT
            rj.id,
            rj.station,
            rj.status,
            rj.start_time,
            rj.end_time,
            rj.notes,
            rj.created_at,
            COALESCE(u.username, '—'),
            COALESCE(rj.cost, 0),
            COALESCE(rj.refinery_method, ''),
            COALESCE(rj.cm_raf_output, 0),
            COALESCE(rj.cost_paid_by, '')
        FROM refinery_jobs rj
        LEFT JOIN users u
            ON u.id = rj.created_by
        WHERE rj.status IN ('RUNNING', 'READY')
        {deleted_filter}
        ORDER BY rj.id DESC
        """)

        jobs = []

        for row in self.cursor.fetchall():
            job_id = row[0]

            self.cursor.execute("""
            SELECT
                refinery_job_items.id,
                refinery_job_items.batch_id,
                COALESCE(
                    refinery_job_items.input_material,
                    material_types.material_code
                ),
                refinery_job_items.input_quantity,
                COALESCE(
                    refinery_job_items.output_material,
                    ?
                ),
                refinery_job_items.output_quantity,
                COALESCE(
                    refinery_job_items.yield_percent,
                    0
                )
            FROM refinery_job_items
            INNER JOIN material_batches
                ON material_batches.id =
                    refinery_job_items.batch_id
            LEFT JOIN material_types
                ON material_types.id =
                    material_batches.material_type_id
            WHERE refinery_job_items.job_id = ?
            ORDER BY refinery_job_items.id
            """, (REFINERY_OUTPUT_CODE, job_id))

            items = [
                {
                    "item_id": item[0],
                    "batch_id": item[1],
                    "input_material": item[2],
                    "input_quantity": item[3],
                    "output_material": item[4],
                    "output_quantity": item[5],
                    "yield_percent": item[6],
                }
                for item in self.cursor.fetchall()
            ]

            jobs.append({
                "id": job_id,
                "refinery_name": row[1],
                "status": row[2],
                "start_time": row[3],
                "end_time": row[4],
                "notes": row[5],
                "created_at": row[6],
                "created_by": row[7],
                "cost": row[8],
                "refinery_method": row[9],
                "cm_raf_output": row[10],
                "cost_paid_by": row[11],
                "items": items,
            })

        return jobs

    def complete_job(
        self,
        job_id,
        output_quantity,
        updated_by=None,
    ):
        if updated_by is None:
            updated_by = user_session.get_user_id()

        output_quantity = float(output_quantity)

        if output_quantity <= 0:
            raise ValueError(
                "Ausgabemenge muss größer als 0 sein."
            )

        self.cursor.execute("""
        SELECT status
        FROM refinery_jobs
        WHERE id = ?
        """, (job_id,))

        job_row = self.cursor.fetchone()

        if not job_row:
            raise ValueError(
                "Raffinerieauftrag nicht gefunden."
            )

        if job_row[0] == "COMPLETED":
            raise ValueError(
                "Auftrag ist bereits abgeschlossen."
            )

        self.cursor.execute("""
        SELECT
            id,
            input_quantity
        FROM refinery_job_items
        WHERE job_id = ?
        ORDER BY id
        """, (job_id,))

        items = self.cursor.fetchall()

        if not items:
            raise ValueError(
                "Auftrag enthält keine Positionen."
            )

        total_input = sum(
            row[1] for row in items
        )

        if total_input <= 0:
            raise ValueError(
                "Ungültige Eingabemenge im Auftrag."
            )

        yield_percent = calc_refinery_efficiency(
            output_quantity,
            total_input,
        )

        try:
            self.connection.execute(
                "BEGIN IMMEDIATE"
            )

            item_columns = self.db._table_columns(
                "refinery_job_items"
            )

            for item_id, input_qty in items:
                item_output = (
                    output_quantity
                    * (input_qty / total_input)
                )

                if (
                    "output_material" in item_columns
                ):
                    self.cursor.execute("""
                    UPDATE refinery_job_items
                    SET
                        output_material = ?,
                        output_quantity = ?,
                        updated_at = datetime('now', 'localtime')
                    WHERE id = ?
                    """, (
                        REFINERY_OUTPUT_CODE,
                        item_output,
                        item_id,
                    ))
                else:
                    self.cursor.execute("""
                    UPDATE refinery_job_items
                    SET
                        output_quantity = ?,
                        updated_at = datetime('now', 'localtime')
                    WHERE id = ?
                    """, (
                        item_output,
                        item_id,
                    ))

            job_columns = self.db._table_columns(
                "refinery_jobs"
            )
            job_update = """
            UPDATE refinery_jobs
            SET
                status = 'COMPLETED',
                end_time = datetime('now', 'localtime'),
                updated_at = datetime('now', 'localtime'),
                updated_by = ?
            """
            job_params = [updated_by]

            if "cm_raf_output" in job_columns:
                job_update = """
                UPDATE refinery_jobs
                SET
                    status = 'COMPLETED',
                    cm_raf_output = ?,
                    end_time = datetime('now', 'localtime'),
                    updated_at = datetime('now', 'localtime'),
                    updated_by = ?
                """
                job_params = [output_quantity, updated_by]

            job_params.append(job_id)
            self.cursor.execute(
                job_update + " WHERE id = ?",
                job_params,
            )

            material_type_id = (
                self.materials.get_material_type_id(
                    REFINERY_OUTPUT_CODE
                )
            )

            self.materials.add_to_storage(
                material_type_id,
                output_quantity,
                source_type="REFINERY",
                source_id=job_id,
                created_by=updated_by,
            )

            for session_id in self._session_ids_for_job(job_id):
                self._refresh_session_status_after_refinery(
                    session_id
                )

            self.connection.commit()

            return {
                "job_id": job_id,
                "output_quantity": output_quantity,
                "cm_raf_output": output_quantity,
                "yield_percent": yield_percent or 0.0,
            }

        except Exception:
            self.connection.rollback()
            raise

    def get_history(self, limit=100):
        deleted_filter = ""

        if "is_deleted" in self.db._table_columns(
            "refinery_jobs"
        ):
            deleted_filter = "WHERE rj.is_deleted = 0"

        self.cursor.execute(f"""
        SELECT
            rj.id,
            rj.station,
            rj.status,
            rj.start_time,
            rj.end_time,
            rj.created_at,
            COALESCE(u.username, '—'),
            COALESCE(rj.cost, 0),
            COALESCE(rj.refinery_method, ''),
            COALESCE(rj.cm_raf_output, 0),
            COALESCE(rj.cost_paid_by, '')
        FROM refinery_jobs rj
        LEFT JOIN users u
            ON u.id = rj.created_by
        {deleted_filter}
        ORDER BY rj.id DESC
        LIMIT ?
        """, (limit,))

        history = []

        for row in self.cursor.fetchall():
            job_id = row[0]

            self.cursor.execute("""
            SELECT
                refinery_job_items.batch_id,
                COALESCE(
                    refinery_job_items.input_material,
                    material_types.material_code
                ),
                refinery_job_items.input_quantity,
                COALESCE(
                    refinery_job_items.output_material,
                    ?
                ),
                refinery_job_items.output_quantity,
                COALESCE(
                    refinery_job_items.yield_percent,
                    0
                )
            FROM refinery_job_items
            INNER JOIN material_batches
                ON material_batches.id =
                    refinery_job_items.batch_id
            LEFT JOIN material_types
                ON material_types.id =
                    material_batches.material_type_id
            WHERE refinery_job_items.job_id = ?
            ORDER BY refinery_job_items.id
            """, (REFINERY_OUTPUT_CODE, job_id))

            items = [
                {
                    "batch_id": item[0],
                    "input_material": item[1],
                    "input_quantity": item[2],
                    "output_material": item[3],
                    "output_quantity": item[4],
                    "yield_percent": item[5],
                }
                for item in self.cursor.fetchall()
            ]

            total_input = sum(
                i["input_quantity"] for i in items
            )
            total_output = row[9] if row[9] > 0 else sum(
                i["output_quantity"] for i in items
            )

            history.append({
                "id": job_id,
                "refinery_name": row[1],
                "status": row[2],
                "start_time": row[3],
                "end_time": row[4],
                "created_at": row[5],
                "created_by": row[6],
                "cost": row[7],
                "refinery_method": row[8],
                "cm_raf_output": row[9],
                "cost_paid_by": row[10],
                "items": items,
                "total_input": total_input,
                "total_output": total_output,
            })

        return history

    def _completed_jobs_sql_filter(self, alias="rj"):
        parts = [f"{alias}.status = 'COMPLETED'"]
        if "is_deleted" in self.db._table_columns(
            "refinery_jobs"
        ):
            parts.append(f"{alias}.is_deleted = 0")
        return " AND ".join(parts)

    def get_efficiency_hint(self, material_code: str) -> dict | None:
        """Durchschnittliche Ausbeute für ein Rohmaterial (eigene Messdaten)."""
        if not material_code:
            return None

        filter_sql = self._completed_jobs_sql_filter("rj")
        self.cursor.execute(f"""
        SELECT
            COALESCE(SUM(rji.input_quantity), 0),
            COALESCE(SUM(rji.output_quantity), 0),
            COUNT(DISTINCT rj.id)
        FROM refinery_job_items rji
        INNER JOIN refinery_jobs rj
            ON rj.id = rji.job_id
        WHERE {filter_sql}
        AND COALESCE(rji.input_material, '') = ?
        AND rji.input_quantity > 0
        AND rji.output_quantity > 0
        """, (material_code,))

        row = self.cursor.fetchone()
        if not row or row[2] == 0:
            return None

        total_input, total_output, job_count = row
        efficiency = calc_refinery_efficiency(
            total_output,
            total_input,
        )
        if efficiency is None:
            return None

        return {
            "material_code": material_code,
            "job_count": job_count,
            "total_input": total_input,
            "total_output": total_output,
            "efficiency_percent": efficiency,
        }

    def get_statistics(self) -> dict:
        filter_sql = self._completed_jobs_sql_filter("rj")

        self.cursor.execute(f"""
        SELECT COUNT(*)
        FROM refinery_jobs rj
        WHERE {filter_sql}
        AND COALESCE(rj.cm_raf_output, 0) > 0
        """)
        job_count = self.cursor.fetchone()[0]

        self.cursor.execute(f"""
        SELECT COALESCE(SUM(rji.input_quantity), 0)
        FROM refinery_job_items rji
        INNER JOIN refinery_jobs rj
            ON rj.id = rji.job_id
        WHERE {filter_sql}
        AND rji.input_quantity > 0
        """)
        total_input = self.cursor.fetchone()[0]

        self.cursor.execute(f"""
        SELECT COALESCE(SUM(rj.cm_raf_output), 0)
        FROM refinery_jobs rj
        WHERE {filter_sql}
        AND COALESCE(rj.cm_raf_output, 0) > 0
        """)
        total_output = self.cursor.fetchone()[0]

        avg_efficiency = calc_refinery_efficiency(
            total_output,
            total_input,
        )

        self.cursor.execute(f"""
        SELECT
            COALESCE(rji.input_material, '—'),
            COALESCE(SUM(rji.input_quantity), 0),
            COALESCE(SUM(rji.output_quantity), 0),
            COUNT(DISTINCT rj.id)
        FROM refinery_job_items rji
        INNER JOIN refinery_jobs rj
            ON rj.id = rji.job_id
        WHERE {filter_sql}
        AND rji.input_quantity > 0
        AND rji.output_quantity > 0
        GROUP BY COALESCE(rji.input_material, '—')
        ORDER BY 1
        """)

        by_material = []
        for material_code, inp, out, count in self.cursor.fetchall():
            by_material.append({
                "material_code": material_code,
                "job_count": count,
                "total_input": inp,
                "total_output": out,
                "efficiency_percent": calc_refinery_efficiency(
                    out,
                    inp,
                ),
            })

        self.cursor.execute(f"""
        SELECT
            COALESCE(NULLIF(TRIM(rj.refinery_method), ''), '—'),
            COALESCE(SUM(rji.input_quantity), 0),
            COALESCE(SUM(rji.output_quantity), 0),
            COUNT(DISTINCT rj.id)
        FROM refinery_job_items rji
        INNER JOIN refinery_jobs rj
            ON rj.id = rji.job_id
        WHERE {filter_sql}
        AND rji.input_quantity > 0
        AND rji.output_quantity > 0
        GROUP BY COALESCE(NULLIF(TRIM(rj.refinery_method), ''), '—')
        ORDER BY 1
        """)

        by_method = []
        for method, inp, out, count in self.cursor.fetchall():
            by_method.append({
                "refinery_method": method,
                "job_count": count,
                "total_input": inp,
                "total_output": out,
                "efficiency_percent": calc_refinery_efficiency(
                    out,
                    inp,
                ),
            })

        return {
            "job_count": job_count,
            "total_input": total_input,
            "total_output": total_output,
            "avg_efficiency_percent": avg_efficiency,
            "by_material": by_material,
            "by_method": by_method,
        }

    def _session_ids_for_job(self, job_id):
        self.cursor.execute("""
        SELECT DISTINCT material_batches.session_id
        FROM refinery_job_items
        INNER JOIN material_batches
            ON material_batches.id =
                refinery_job_items.batch_id
        WHERE refinery_job_items.job_id = ?
        AND material_batches.session_id IS NOT NULL
        """, (job_id,))

        return [
            row[0]
            for row in self.cursor.fetchall()
        ]

    def session_has_pending_refinery(self, session_id):
        deleted_filter = ""

        if "is_deleted" in self.db._table_columns(
            "refinery_jobs"
        ):
            deleted_filter = "AND rj.is_deleted = 0"

        self.cursor.execute(f"""
        SELECT COUNT(*)
        FROM refinery_jobs rj
        INNER JOIN refinery_job_items rji
            ON rji.job_id = rj.id
        INNER JOIN material_batches mb
            ON mb.id = rji.batch_id
        WHERE mb.session_id = ?
        AND rj.status IN ('RUNNING', 'READY')
        {deleted_filter}
        """, (session_id,))

        if self.cursor.fetchone()[0] > 0:
            return True

        available_sql = self._available_batch_sql()
        placeholders = ", ".join(
            "?" for _ in RAW_CM_MATERIAL_CODES
        )

        self.cursor.execute(f"""
        SELECT COALESCE(SUM({available_sql}), 0)
        FROM material_batches
        INNER JOIN material_types
            ON material_types.id =
                material_batches.material_type_id
        WHERE material_batches.session_id = ?
        AND material_batches.is_deleted = 0
        AND material_types.material_code IN (
            {placeholders}
        )
        """, (
            session_id,
            *RAW_CM_MATERIAL_CODES,
        ))

        return self.cursor.fetchone()[0] > 0

    def _refresh_session_status_after_refinery(
        self,
        session_id,
    ):
        self.cursor.execute("""
        SELECT status
        FROM sessions
        WHERE id = ?
        """, (session_id,))

        row = self.cursor.fetchone()

        if not row or row[0] != "WAITING_FOR_REFINERY":
            return

        if self.session_has_pending_refinery(session_id):
            return

        self.cursor.execute("""
        UPDATE sessions
        SET
            status = 'WAITING_FOR_SALE',
            updated_at = datetime('now', 'localtime')
        WHERE id = ?
        """, (session_id,))

    def count_open_jobs(self):
        deleted_filter = ""

        if "is_deleted" in self.db._table_columns(
            "refinery_jobs"
        ):
            deleted_filter = "AND is_deleted = 0"

        self.cursor.execute(f"""
        SELECT COUNT(*)
        FROM refinery_jobs
        WHERE status IN ('RUNNING', 'READY')
        {deleted_filter}
        """)

        return self.cursor.fetchone()[0]
