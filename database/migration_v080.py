from config.debug import debug_log


class MigrationV080:
    VERSION = "0.8.2"

    def __init__(self, db):
        self.db = db
        self.cursor = db.cursor
        self.connection = db.connection

    def is_applied(self):
        self.cursor.execute("""
        SELECT 1
        FROM database_version
        WHERE version = ?
        LIMIT 1
        """, (self.VERSION,))

        return self.cursor.fetchone() is not None

    def mark_applied(self):
        self.cursor.execute("""
        INSERT OR IGNORE INTO database_version (
            version,
            applied_at
        )
        VALUES (?, datetime('now', 'localtime'))
        """, (self.VERSION,))

        self.connection.commit()

    def run(self):
        if self.is_applied():
            debug_log(
                f"Migration {self.VERSION} bereits angewendet"
            )
            return

        debug_log(
            f"Migration {self.VERSION} wird ausgeführt"
        )

        self._ensure_legacy_archive()
        self._add_audit_columns()
        self._upgrade_refinery_schema()
        self._upgrade_sales_schema()
        self._upgrade_payout_schema()
        self._migrate_session_materials()
        self._ensure_indexes()

        self.mark_applied()

    def _ensure_indexes(self):
        if self._table_exists("refinery_jobs"):
            columns = self._table_columns("refinery_jobs")

            if "station" in columns:
                self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_refinery_jobs_station
                ON refinery_jobs(station)
                """)

        if self._table_exists("sales"):
            columns = self._table_columns("sales")

            if "location" in columns:
                self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_sales_location
                ON sales(location)
                """)

        if self._table_exists("payout_items"):
            columns = self._table_columns("payout_items")

            if "crew_member" in columns:
                self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_payout_items_crew_member
                ON payout_items(crew_member)
                """)

        self.connection.commit()

    def _table_exists(self, name):
        self.cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = ?
        """, (name,))

        return self.cursor.fetchone() is not None

    def _table_columns(self, table_name):
        self.cursor.execute(
            f"PRAGMA table_info({table_name})"
        )
        return {
            row[1]
            for row in self.cursor.fetchall()
        }

    def _add_column_if_missing(
        self,
        table_name,
        column_name,
        column_definition,
    ):
        if not self._table_exists(table_name):
            return

        columns = self._table_columns(table_name)

        if column_name in columns:
            return

        self.cursor.execute(
            f"ALTER TABLE {table_name} "
            f"ADD COLUMN {column_name} {column_definition}"
        )

    def _ensure_legacy_archive(self):
        if not self._table_exists("session_materials"):
            return

        if self._table_exists("session_materials_legacy"):
            return

        self.cursor.execute("""
        ALTER TABLE session_materials
        RENAME TO session_materials_legacy
        """)

        self.connection.commit()

    def _add_audit_columns(self):
        audit_tables = [
            "sessions",
            "material_batches",
            "refinery_jobs",
            "storage_items",
            "sales",
            "payouts",
            "costs",
        ]

        for table in audit_tables:
            self._add_column_if_missing(
                table,
                "created_by",
                "INTEGER",
            )
            self._add_column_if_missing(
                table,
                "updated_by",
                "INTEGER",
            )

        self.connection.commit()

    def _upgrade_refinery_schema(self):
        if not self._table_exists("refinery_jobs"):
            return

        columns = self._table_columns("refinery_jobs")

        if "session_id" in columns and "station" not in columns:
            self.cursor.execute("""
            ALTER TABLE refinery_jobs
            RENAME TO refinery_jobs_legacy
            """)

            self.connection.commit()
            return

        self._add_column_if_missing(
            "refinery_jobs",
            "station",
            "TEXT",
        )
        self._add_column_if_missing(
            "refinery_jobs",
            "cost",
            "REAL DEFAULT 0",
        )

        self.connection.commit()

    def _upgrade_sales_schema(self):
        if not self._table_exists("sales"):
            return

        columns = self._table_columns("sales")

        if "location" not in columns:
            self._add_column_if_missing(
                "sales",
                "location",
                "TEXT",
            )

            if "buyer_name" in columns:
                self.cursor.execute("""
                UPDATE sales
                SET location = buyer_name
                WHERE location IS NULL
                AND buyer_name IS NOT NULL
                """)

        self.connection.commit()

    def _upgrade_payout_schema(self):
        if not self._table_exists("payout_items"):
            return

        columns = self._table_columns("payout_items")

        self._add_column_if_missing(
            "payout_items",
            "crew_member",
            "TEXT",
        )

        if (
            "crew_member_id" in columns
            and "crew_member" in self._table_columns(
                "payout_items"
            )
        ):
            self.cursor.execute("""
            UPDATE payout_items
            SET crew_member = (
                SELECT player_name
                FROM crew_members
                WHERE crew_members.id =
                    payout_items.crew_member_id
            )
            WHERE crew_member IS NULL
            AND crew_member_id IS NOT NULL
            """)

        self.connection.commit()

    def _get_material_type_id(self, material_code):
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

    def _migrate_session_materials(self):
        if not self._table_exists(
            "session_materials_legacy"
        ):
            return

        self.cursor.execute("""
        SELECT
            session_id,
            material_type,
            amount
        FROM session_materials_legacy
        """)

        rows = self.cursor.fetchall()

        for session_id, material_type, amount in rows:
            if not amount:
                continue

            material_type_id = (
                self._get_material_type_id(
                    material_type
                )
            )

            self.cursor.execute("""
            SELECT id
            FROM material_batches
            WHERE session_id = ?
            AND material_type_id = ?
            AND quantity = ?
            LIMIT 1
            """, (
                session_id,
                material_type_id,
                amount,
            ))

            if self.cursor.fetchone():
                continue

            self.cursor.execute("""
            INSERT INTO material_batches (
                session_id,
                material_type_id,
                quantity,
                created_at
            )
            VALUES (?, ?, ?, datetime('now', 'localtime'))
            """, (
                session_id,
                material_type_id,
                amount,
            ))

            batch_id = self.cursor.lastrowid

            self.cursor.execute("""
            INSERT INTO storage_items (
                material_type_id,
                quantity,
                source_type,
                source_id,
                created_at
            )
            VALUES (?, ?, 'SESSION', ?, datetime('now', 'localtime'))
            """, (
                material_type_id,
                amount,
                batch_id,
            ))

        self.connection.commit()

        debug_log(
            "session_materials_legacy nach "
            "material_batches + storage migriert"
        )
