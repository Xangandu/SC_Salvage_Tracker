import sqlite3
import weakref
from datetime import datetime
from pathlib import Path

from config.debug import debug_log
from config.i18n import tr
from config.paths import data_dir
from database.user_auth import UserAuthMixin
from database.initial_setup import InitialSetupMixin
from database.migration_v080 import MigrationV080
from database.material_repository import MaterialRepository
from database.refinery_repository import RefineryRepository
from database.payout_repository import PayoutRepository
from database.correction_repository import CorrectionRepository
from database.migration_manager import (
    BACKUP_AUTO_BEFORE_RESET_KEY,
    BACKUP_AUTO_BEFORE_RESTORE_KEY,
    BACKUP_MAX_COUNT_KEY,
    DEFAULT_BACKUP_MAX_COUNT,
    MigrationManager,
)
from database.backup_repository import BackupRepository
import auth.session as user_session
from config.permissions import sessions_restrict_to_own


class Database(UserAuthMixin, InitialSetupMixin):

    _instances = weakref.WeakSet()

    @staticmethod
    def database_path():
        return data_dir() / "salvage_tracker.db"

    @staticmethod
    def remember_me_path():
        return data_dir() / "remember_me.json"

    @classmethod
    def delete_database_files(cls, *, clear_remember_me=True):
        """Remove the DB file so the next connect rebuilds schema from scratch."""
        db_path = cls.database_path()
        db_path.parent.mkdir(exist_ok=True)

        if db_path.exists():
            db_path.unlink()

        if clear_remember_me:
            remember_path = cls.remember_me_path()
            if remember_path.exists():
                remember_path.unlink()

    @classmethod
    def close_all_connections(cls):
        for instance in list(cls._instances):
            instance.close_connection()

    @classmethod
    def _get_connected_instance(cls):
        for instance in list(cls._instances):
            if getattr(instance, "connection", None):
                return instance

        return None

    @classmethod
    def create_safety_backup(
        cls,
        reason: str,
        setting_key: str | None = None,
        *,
        default: bool = True,
    ):
        if not cls.database_path().exists():
            return None

        db = cls._get_connected_instance()
        temporary = False

        if db is None:
            db = cls()
            temporary = True

        try:
            if setting_key is not None:
                if not BackupRepository.auto_backup_enabled(
                    db,
                    setting_key,
                    default=default,
                ):
                    return None

            return db.create_database_backup(reason=reason)
        finally:
            if temporary:
                db.close_connection()

    @staticmethod
    def _do_restore_from_backup(filename: str) -> dict:
        backup_path = (
            BackupRepository.backup_directory() / filename
        )

        if not BackupRepository._is_backup_file(backup_path):
            raise ValueError(tr("error.backup.invalid_file"))

        if not backup_path.exists():
            raise FileNotFoundError(tr("error.backup.not_found"))

        pre_restore_backup = Database.create_safety_backup(
            "pre_restore",
            BACKUP_AUTO_BEFORE_RESTORE_KEY,
        )

        Database.close_all_connections()

        target_path = Database.database_path()
        BackupRepository.copy_backup_to_database(
            backup_path,
            target_path,
        )

        from database.access import reset_database_access

        reset_database_access()

        db = Database()
        schema_status = db.get_schema_status()

        return {
            "restored_from": filename,
            "pre_restore_backup": pre_restore_backup,
            "schema_status": schema_status,
        }

    @classmethod
    def reset_database_with_backup(
        cls,
        *,
        clear_remember_me: bool = True,
    ) -> dict:
        pre_reset_backup = cls.create_safety_backup(
            "pre_reset",
            BACKUP_AUTO_BEFORE_RESET_KEY,
        )

        cls.close_all_connections()
        cls.delete_database_files(
            clear_remember_me=clear_remember_me,
        )

        from database.access import reset_database_access

        reset_database_access()

        return {
            "pre_reset_backup": pre_reset_backup,
        }

    def close_connection(self):
        if getattr(self, "connection", None):
            self.connection.close()
            self.connection = None
            self.cursor = None
    
    def get_schema_directory(self):

        return (
            Path(__file__).parent
            / "schema"
        )


    def get_schema_files(self):

        schema_dir = (
            self.get_schema_directory()
        )

        return sorted(
            schema_dir.glob("*.sql")
        )
        
    def run_schema_files(self, progress=None):

        schema_files = list(self.get_schema_files())
        total = len(schema_files)

        for index, schema_file in enumerate(schema_files, start=1):

            if progress is not None:
                progress(index, total, schema_file.name)

            debug_log(
                f"LADE SCHEMA: {schema_file.name}"
            )

            with open(
                schema_file,
                "r",
                encoding="utf-8"
            ) as file:

                sql_script = file.read()

            self.connection.executescript(
                sql_script
            )

        self.connection.commit()

    def __init__(self, schema_progress=None):
        db_path = self.database_path()

        db_path.parent.mkdir(exist_ok=True)

        self.connection = sqlite3.connect(db_path)
        
        debug_log(
            "DB DATEI:",
            self.connection.execute(
                "PRAGMA database_list"
            ).fetchall()
        )
        
        self.cursor = self.connection.cursor()
        
        self.connection.commit()

        self.run_schema_files(progress=schema_progress)

        MigrationV080(self).run()

        self._upgrade_refinery_model()
        self._upgrade_refinery_output_fields()
        self._upgrade_costs_model()
        self.migrate_auth_schema()
        self.seed_system_accounts()

        from database.permission_repository import (
            PermissionRepository,
        )

        self.permissions = PermissionRepository(self)
        self.permissions.migrate_permissions()

        from database.settings_repository import (
            SettingsRepository,
        )

        self.settings = SettingsRepository(self)

        from database.dashboard_layout_repository import (
            DashboardLayoutRepository,
        )

        self.dashboard_layouts = DashboardLayoutRepository(self)

        self.materials = MaterialRepository(self)
        self.refinery = RefineryRepository(self)
        self.payouts = PayoutRepository(self)
        self.corrections = CorrectionRepository(self)
        self.backups = BackupRepository(self)
        self.migrations = MigrationManager(self)
        self.migrations.ensure_backup_defaults()
        self.migrations.finalize_version_metadata()
        self.finalize_initial_setup_state()

        Database._instances.add(self)

    def _session_name_column(self):
        session_columns = self._table_columns("sessions")

        if "session_name" in session_columns:
            return "session_name"

        if "ship" in session_columns:
            return "ship"

        return "session_name"

    def _sum_sales_from_sales_table(self):
        if not self._table_exists("sales"):
            return 0

        sales_columns = self._table_columns("sales")
        deleted_filter = ""

        if "is_deleted" in sales_columns:
            deleted_filter = "WHERE is_deleted = 0"

        self.cursor.execute(f"""
        SELECT COALESCE(
            SUM(total_amount),
            0
        )
        FROM sales
        {deleted_filter}
        """)

        return self.cursor.fetchone()[0]

    def _upgrade_refinery_model(self):
        batch_columns = self._table_columns(
            "material_batches"
        )

        if "remaining_quantity" not in batch_columns:
            self.cursor.execute("""
            ALTER TABLE material_batches
            ADD COLUMN remaining_quantity REAL
            """)

            self.cursor.execute("""
            UPDATE material_batches
            SET remaining_quantity = quantity
            WHERE remaining_quantity IS NULL
            """)

        item_columns = self._table_columns(
            "refinery_job_items"
        )

        for column, col_type in (
            ("input_material", "TEXT"),
            ("output_material", "TEXT"),
            ("yield_percent", "REAL"),
        ):
            if column not in item_columns:
                self.cursor.execute(f"""
                ALTER TABLE refinery_job_items
                ADD COLUMN {column} {col_type}
                """)

        self.connection.commit()

    def _upgrade_refinery_output_fields(self):
        if not self._table_exists("refinery_jobs"):
            return

        columns = self._table_columns("refinery_jobs")

        if "cm_raf_output" not in columns:
            self.cursor.execute("""
            ALTER TABLE refinery_jobs
            ADD COLUMN cm_raf_output REAL NOT NULL DEFAULT 0
            """)

        columns = self._table_columns("refinery_jobs")

        if "refinery_method" not in columns:
            self.cursor.execute("""
            ALTER TABLE refinery_jobs
            ADD COLUMN refinery_method TEXT NOT NULL DEFAULT ''
            """)

        self.cursor.execute("""
        UPDATE refinery_jobs
        SET cm_raf_output = (
            SELECT COALESCE(SUM(output_quantity), 0)
            FROM refinery_job_items
            WHERE job_id = refinery_jobs.id
        )
        WHERE status = 'COMPLETED'
        AND cm_raf_output = 0
        AND EXISTS (
            SELECT 1
            FROM refinery_job_items
            WHERE job_id = refinery_jobs.id
            AND output_quantity > 0
        )
        """)

        self.connection.commit()

        columns = self._table_columns("refinery_jobs")

        if "cost_paid_by" not in columns:
            self.cursor.execute("""
            ALTER TABLE refinery_jobs
            ADD COLUMN cost_paid_by TEXT NOT NULL DEFAULT ''
            """)

        self.connection.commit()

    def _upgrade_costs_model(self):
        cost_columns = self._table_columns("costs")

        if "paid_by" not in cost_columns:
            self.cursor.execute("""
            ALTER TABLE costs
            ADD COLUMN paid_by TEXT
            """)

        self.cursor.execute("""
        SELECT id, description
        FROM costs
        WHERE (
            paid_by IS NULL
            OR TRIM(paid_by) = ''
        )
        AND description LIKE 'Bezahlt von %'
        """)

        for cost_id, description in self.cursor.fetchall():
            payer = description[12:].strip()

            if payer:
                self.cursor.execute("""
                UPDATE costs
                SET paid_by = ?
                WHERE id = ?
                """, (payer, cost_id))

        self.connection.commit()

    def get_available_refinery_batches(self):
        return self.refinery.get_available_batches()

    def create_refinery_job_from_batches(
        self,
        refinery_name,
        end_time,
        batch_lines,
        notes=None,
        created_by=None,
        refinery_method="",
        cost=0.0,
        cost_paid_by="",
    ):
        return self.refinery.create_job(
            refinery_name,
            end_time,
            batch_lines,
            created_by=created_by,
            notes=notes,
            refinery_method=refinery_method,
            cost=cost,
            cost_paid_by=cost_paid_by,
        )

    def get_active_refinery_jobs(self):
        return self.refinery.get_active_jobs()

    def complete_refinery_job(
        self,
        job_id,
        output_quantity,
        updated_by=None,
    ):
        return self.refinery.complete_job(
            job_id,
            output_quantity,
            updated_by=updated_by,
        )

    def get_refinery_history(self, limit=100):
        return self.refinery.get_history(limit)

    def get_refinery_statistics(self):
        return self.refinery.get_statistics()

    def get_refinery_efficiency_hint(self, material_code: str):
        return self.refinery.get_efficiency_hint(material_code)

    def get_schema_status(self):
        return self.migrations.get_status()

    def verify_database(self):
        return self.migrations.verify_database()

    def rerun_migrations(self):
        MigrationV080(self).run()
        self._upgrade_refinery_model()
        self._upgrade_refinery_output_fields()
        self._upgrade_costs_model()
        self.migrate_auth_schema()
        self.permissions.migrate_permissions()
        self.settings.migrate_settings_schema()
        self.migrations.ensure_backup_defaults()
        return self.migrations.finalize_version_metadata()

    def reinitialize_database(self, *, clear_remember_me=True):
        result = type(self).reset_database_with_backup(
            clear_remember_me=clear_remember_me,
        )

        from database.access import reconnect_database

        db = reconnect_database()
        result["schema_status"] = db.get_schema_status()
        return result

    def create_database_backup(self, *, reason="manual"):
        return self.backups.create_backup(reason=reason)

    def list_database_backups(self):
        return self.backups.list_backups()

    def get_database_backup_status(self):
        return self.backups.get_status()

    def delete_database_backup(self, filename):
        return self.backups.delete_backup(filename)

    def save_database_backup_settings(
        self,
        *,
        max_count: int,
        auto_before_reset: bool,
        auto_before_restore: bool,
    ) -> dict:
        limit = max(
            1,
            min(DEFAULT_BACKUP_MAX_COUNT, int(max_count)),
        )

        self.settings.set_app_setting(
            BACKUP_MAX_COUNT_KEY,
            str(limit),
        )
        self.settings.set_app_setting(
            BACKUP_AUTO_BEFORE_RESET_KEY,
            "1" if auto_before_reset else "0",
        )
        self.settings.set_app_setting(
            BACKUP_AUTO_BEFORE_RESTORE_KEY,
            "1" if auto_before_restore else "0",
        )

        removed = self.backups.enforce_retention()

        return {
            "max_backup_count": limit,
            "auto_before_reset": auto_before_reset,
            "auto_before_restore": auto_before_restore,
            "removed_count": removed,
        }

    def restore_from_backup(self, filename: str) -> dict:
        return Database._do_restore_from_backup(filename)

    def _session_user_filter(self):
        user = user_session.get_user()
        if user and user.get("is_network_guest"):
            return None

        if sessions_restrict_to_own():
            return user_session.get_user_id()

        return None

    def create_session(
        self,
        mission_id,
        session_name,
        start_time,
        notes="",
        created_by=None,
    ):

        self.cursor.execute("""
        UPDATE sessions
        SET status = 'WAITING_FOR_REFINERY'
        WHERE status = 'ACTIVE'
        """)

        columns = self._table_columns("sessions")

        if "created_by" in columns:
            self.cursor.execute("""
            INSERT INTO sessions (
                mission_id,
                session_name,
                start_time,
                status,
                notes,
                created_at,
                created_by
            )
            VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'), ?)
            """, (
                mission_id,
                session_name,
                start_time,
                "ACTIVE",
                notes,
                created_by,
            ))
        else:
            self.cursor.execute("""
            INSERT INTO sessions (
                mission_id,
                session_name,
                start_time,
                status,
                notes,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))
            """, (
                mission_id,
                session_name,
                start_time,
                "ACTIVE",
                notes
            ))

        self.connection.commit()

        return self.cursor.lastrowid

    def _table_exists(self, table_name):
        self.cursor.execute("""
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
        AND name = ?
        LIMIT 1
        """, (table_name,))

        return self.cursor.fetchone() is not None

    def _get_or_create_crew_member_id(
        self,
        player_name,
    ):
        columns = self._table_columns("crew_members")

        if "is_deleted" in columns:
            self.cursor.execute("""
            SELECT id
            FROM crew_members
            WHERE player_name = ?
            AND is_deleted = 0
            LIMIT 1
            """, (player_name,))
        else:
            self.cursor.execute("""
            SELECT id
            FROM crew_members
            WHERE player_name = ?
            LIMIT 1
            """, (player_name,))

        row = self.cursor.fetchone()

        if row:
            return row[0]

        if "created_at" in columns:
            self.cursor.execute("""
            INSERT INTO crew_members (
                player_name,
                created_at
            )
            VALUES (?, datetime('now', 'localtime'))
            """, (player_name,))
        else:
            self.cursor.execute("""
            INSERT INTO crew_members (
                player_name
            )
            VALUES (?)
            """, (player_name,))

        return self.cursor.lastrowid

    def add_crew_member(
        self,
        session_id,
        player_name
    ):
        crew_columns = self._table_columns("crew_members")

        if (
            "session_id" in crew_columns
            and not self._table_exists("session_crew")
        ):
            self.cursor.execute("""
            INSERT INTO crew_members(
                session_id,
                player_name
            )
            VALUES(?,?)
            """, (
                session_id,
                player_name,
            ))
            self.connection.commit()
            return

        crew_member_id = self._get_or_create_crew_member_id(
            player_name
        )

        self.cursor.execute("""
        INSERT OR IGNORE INTO session_crew (
            session_id,
            crew_member_id,
            role_name,
            joined_at,
            created_at
        )
        VALUES (?, ?, 'Operator', datetime('now', 'localtime'), datetime('now', 'localtime'))
        """, (
            session_id,
            crew_member_id,
        ))

        self.connection.commit()

    def get_active_session(self):

        name_column = self._session_name_column()
        restrict_user = self._session_user_filter()
        params = []

        query = f"""
        SELECT
            id,
            {name_column},
            status
        FROM sessions
        WHERE status = 'ACTIVE'
        """

        if "is_deleted" in self._table_columns("sessions"):
            query += " AND is_deleted = 0"

        if (
            restrict_user is not None
            and "created_by" in self._table_columns("sessions")
        ):
            query += " AND created_by = ?"
            params.append(restrict_user)

        query += " ORDER BY id DESC LIMIT 1"

        self.cursor.execute(query, params)

        return self.cursor.fetchone()

    def get_session_display_details(
        self,
        session_id,
    ):
        name_column = self._session_name_column()

        self.cursor.execute(f"""
        SELECT
            id,
            {name_column},
            start_time,
            status
        FROM sessions
        WHERE id = ?
        """, (session_id,))

        row = self.cursor.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "name": row[1],
            "start_time": row[2],
            "status": row[3],
            "total_scu": self.get_session_total_scu(
                session_id
            ),
            "crew_count": len(
                self.get_crew_members(session_id)
            ),
        }

    def get_sessions_by_status(
        self,
        status,
    ):
        name_column = self._session_name_column()

        self.cursor.execute(f"""
        SELECT id
        FROM sessions
        WHERE status = ?
        ORDER BY id DESC
        """, (status,))

        session_ids = [
            row[0]
            for row in self.cursor.fetchall()
        ]

        results = []

        for session_id in session_ids:
            details = self.get_session_display_details(
                session_id
            )

            if details:
                results.append(details)

        return results

    def get_latest_session(self):

        name_column = self._session_name_column()

        self.cursor.execute(f"""
        SELECT
            id,
            {name_column},
            status
        FROM sessions
        ORDER BY id DESC
        LIMIT 1
        """)

        return self.cursor.fetchone()

    def get_open_refinery_jobs(self):

        if not self._table_exists("refinery_jobs"):
            return 0

        if hasattr(self, "refinery"):
            return self.refinery.count_open_jobs()

        return 0
    
    def get_crew_members(self, session_id):

        if self._table_exists("session_crew"):
            self.cursor.execute("""
            SELECT cm.player_name
            FROM session_crew sc
            JOIN crew_members cm
                ON cm.id = sc.crew_member_id
            WHERE sc.session_id = ?
            ORDER BY sc.id
            """, (session_id,))

            return self.cursor.fetchall()

        crew_columns = self._table_columns("crew_members")

        if "session_id" in crew_columns:
            self.cursor.execute("""
            SELECT player_name
            FROM crew_members
            WHERE session_id = ?
            """, (session_id,))

            return self.cursor.fetchall()

        return []

    def _get_cost_type_id(self, cost_type):
        self.cursor.execute("""
        SELECT id
        FROM cost_types
        WHERE cost_code = ?
           OR cost_name = ?
        LIMIT 1
        """, (cost_type, cost_type))

        row = self.cursor.fetchone()

        if row:
            return row[0]

        self.cursor.execute("""
        INSERT INTO cost_types (
            cost_code,
            cost_name,
            created_at
        )
        VALUES (?, ?, datetime('now', 'localtime'))
        """, (cost_type, cost_type))

        self.connection.commit()

        return self.cursor.lastrowid

    def _cost_payer_select_sql(self, alias="c"):
        cost_columns = self._table_columns("costs")

        if "paid_by" in cost_columns:
            return f"""
                COALESCE(
                    NULLIF(TRIM({alias}.paid_by), ''),
                    CASE
                        WHEN {alias}.description LIKE 'Bezahlt von %'
                        THEN SUBSTR({alias}.description, 13)
                        ELSE COALESCE({alias}.description, 'Unbekannt')
                    END
                )
            """

        return f"COALESCE({alias}.description, 'Unbekannt')"

    @staticmethod
    def _parse_cost_payer(paid_by, description):
        payer = (paid_by or "").strip()

        if payer:
            return payer

        description = description or ""

        if description.startswith("Bezahlt von "):
            return description[12:].strip() or "Unbekannt"

        return description.strip() or "Unbekannt"

    def reassign_cost_payer(
        self,
        session_ids,
        from_payer,
        to_payer,
    ):
        from_payer = from_payer.strip()
        to_payer = to_payer.strip()

        if not from_payer or not to_payer:
            raise ValueError(tr("error.cost.payers_required"))

        cost_columns = self._table_columns("costs")
        has_paid_by = "paid_by" in cost_columns
        has_description = (
            "description" in cost_columns
        )

        for session_id in session_ids:
            self.cursor.execute("""
            SELECT
                id,
                paid_by,
                description
            FROM costs
            WHERE session_id = ?
            """, (session_id,))

            for cost_id, paid_by, description in (
                self.cursor.fetchall()
            ):
                current_payer = self._parse_cost_payer(
                    paid_by,
                    description,
                )

                if current_payer != from_payer:
                    continue

                updates = []
                values = []

                if has_paid_by:
                    updates.append("paid_by = ?")
                    values.append(to_payer)

                if has_description:
                    updates.append("description = ?")
                    values.append(
                        f"Bezahlt von {to_payer}"
                    )

                if not updates:
                    continue

                values.append(cost_id)

                self.cursor.execute(f"""
                UPDATE costs
                SET {", ".join(updates)}
                WHERE id = ?
                """, values)

        self.connection.commit()

    def add_cost(
        self,
        session_id,
        cost_type,
        amount,
        paid_by
    ):
        cost_columns = self._table_columns("costs")

        if "cost_type_id" in cost_columns:
            cost_type_id = self._get_cost_type_id(
                cost_type
            )

            description = (
                f"Bezahlt von {paid_by}"
                if paid_by
                else None
            )

            insert_columns = [
                "session_id",
                "cost_type_id",
                "amount",
            ]
            values = [
                session_id,
                cost_type_id,
                amount,
            ]

            if "paid_by" in cost_columns:
                insert_columns.append("paid_by")
                values.append(paid_by)

            if "description" in cost_columns:
                insert_columns.append("description")
                values.append(description)

            if "created_at" in cost_columns:
                insert_columns.append("created_at")
                values.append(
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )

            placeholders = ", ".join(
                "?" for _ in values
            )
            column_list = ", ".join(
                insert_columns
            )

            self.cursor.execute(f"""
            INSERT INTO costs (
                {column_list}
            )
            VALUES ({placeholders})
            """, values)
        elif "cost_type" in cost_columns:
            self.cursor.execute("""
            INSERT INTO costs(
                session_id,
                cost_type,
                amount,
                paid_by
            )
            VALUES(?,?,?,?)
            """, (
                session_id,
                cost_type,
                amount,
                paid_by,
            ))
        else:
            raise ValueError(tr("error.cost.unknown_schema"))

        self.connection.commit()

    def reassign_refinery_cost_payer(
        self,
        job_ids,
        from_payer,
        to_payer,
    ):
        from_payer = from_payer.strip()
        to_payer = to_payer.strip()

        if not from_payer or not to_payer:
            raise ValueError(tr("error.cost.payers_required"))

        if not job_ids:
            return

        columns = self._table_columns("refinery_jobs")

        if "cost_paid_by" not in columns:
            return

        placeholders = ", ".join(
            "?" for _ in job_ids
        )

        self.cursor.execute(f"""
        UPDATE refinery_jobs
        SET cost_paid_by = ?
        WHERE id IN ({placeholders})
        AND TRIM(COALESCE(cost_paid_by, '')) = ?
        """, [to_payer, *job_ids, from_payer])

        self.connection.commit()

    def end_session(
        self,
        session_id
    ):

        self.cursor.execute("""
        UPDATE sessions
        SET
            status = 'WAITING_FOR_REFINERY',
            end_time = datetime('now', 'localtime')
        WHERE id = ?
        """, (session_id,))

        self.connection.commit()

    def get_session_costs(
        self,
        session_id
    ):
        cost_columns = self._table_columns("costs")

        if "cost_type_id" in cost_columns:
            deleted_filter = ""

            if "is_deleted" in cost_columns:
                deleted_filter = (
                    "AND c.is_deleted = 0"
                )

            self.cursor.execute(f"""
            SELECT
                ct.cost_name,
                c.amount,
                {self._cost_payer_select_sql("c")}
            FROM costs c
            JOIN cost_types ct
                ON ct.id = c.cost_type_id
            WHERE c.session_id = ?
            {deleted_filter}
            ORDER BY c.id
            """, (session_id,))

            return self.cursor.fetchall()

        self.cursor.execute("""
        SELECT
            cost_type,
            amount,
            paid_by
        FROM costs
        WHERE session_id = ?
        """, (session_id,))

        return self.cursor.fetchall()
    
    def get_total_costs(
        self,
        session_id
    ):

        self.cursor.execute("""
        SELECT COALESCE(
            SUM(amount),
            0
        )
        FROM costs
        WHERE session_id = ?
        """, (session_id,))

        return self.cursor.fetchone()[0]

    def get_cost_refunds(
        self,
        session_id
    ):
        cost_columns = self._table_columns("costs")

        if "cost_type_id" in cost_columns:
            deleted_filter = ""

            if "is_deleted" in cost_columns:
                deleted_filter = "AND is_deleted = 0"

            payer_sql = self._cost_payer_select_sql("c")

            self.cursor.execute(f"""
            SELECT
                {payer_sql},
                SUM(c.amount)
            FROM costs c
            WHERE c.session_id = ?
            {deleted_filter}
            GROUP BY 1
            """, (session_id,))

            return [
                (row[0], row[1])
                for row in self.cursor.fetchall()
            ]

        self.cursor.execute("""
        SELECT
            paid_by,
            SUM(amount)
        FROM costs
        WHERE session_id = ?
        GROUP BY paid_by
        """, (session_id,))

        return self.cursor.fetchall()
    
    def get_ready_for_sale_count(self):
        """Verkaufbares Lager (RMC + CM in SCU)."""
        return self.get_sellable_storage_total_scu()

    def get_sellable_storage_total_scu(self):
        inventory = self.get_available_storage_inventory()

        return sum(
            entry["quantity"]
            for entry in inventory
        )

    def get_storage_balance(self, material_code):
        return self.materials.get_storage_balance(
            material_code
        )

    def get_session_captured_total(
        self,
        session_id,
        material_code,
    ):
        self.cursor.execute("""
        SELECT COALESCE(
            SUM(material_batches.quantity),
            0
        )
        FROM material_batches
        INNER JOIN material_types
            ON material_types.id =
                material_batches.material_type_id
        WHERE material_batches.session_id = ?
        AND material_types.material_code = ?
        AND material_batches.is_deleted = 0
        """, (
            session_id,
            material_code,
        ))

        return self.cursor.fetchone()[0]

    def get_global_batch_available(
        self,
        material_code,
    ):
        batch_columns = self._table_columns(
            "material_batches"
        )

        if "remaining_quantity" in batch_columns:
            quantity_sql = (
                "COALESCE(material_batches.remaining_quantity, 0)"
            )
        else:
            quantity_sql = "material_batches.quantity"

        self.cursor.execute(f"""
        SELECT COALESCE(
            SUM({quantity_sql}),
            0
        )
        FROM material_batches
        INNER JOIN material_types
            ON material_types.id =
                material_batches.material_type_id
        WHERE material_types.material_code = ?
        AND material_batches.is_deleted = 0
        AND {quantity_sql} > 0
        """, (material_code,))

        return self.cursor.fetchone()[0]

    def get_session_batch_available(
        self,
        session_id,
        material_code,
    ):
        return self.get_material_total(
            session_id,
            material_code,
        )

    def get_unpaid_sales(self, limit=50):
        return self.payouts.get_unpaid_sales(limit)

    def calculate_payout_proposal(
        self,
        sale_id,
        cost_payer_overrides=None,
    ):
        return self.payouts.calculate_payout_proposal(
            sale_id,
            cost_payer_overrides=cost_payer_overrides,
        )

    def create_payout(
        self,
        sale_id,
        items,
        notes=None,
        created_by=None,
    ):
        payout_id = self.payouts.create_payout(
            sale_id,
            items,
            created_by=created_by,
            notes=notes,
        )
        return payout_id

    def delete_session(self, session_id):
        return self.corrections.delete_session(session_id)

    def get_correctable_sessions(self, limit=25):
        return self.corrections.get_correctable_sessions(
            limit
        )

    def cancel_refinery_job(self, job_id):
        return self.corrections.cancel_refinery_job(job_id)

    def delete_refinery_job(self, job_id):
        return self.corrections.delete_refinery_job(job_id)

    def void_sale(self, sale_id):
        return self.corrections.void_sale(sale_id)

    def void_payout(self, payout_id):
        return self.corrections.void_payout(payout_id)

    def get_payout_history(self, limit=100):
        restrict_user = None

        from config.permissions import payouts_restrict_to_own

        if payouts_restrict_to_own():
            restrict_user = user_session.get_user_id()

        return self.payouts.get_payout_history(
            limit,
            restrict_to_user_id=restrict_user,
        )

    def get_total_payouts_value(self):
        return self.payouts.get_total_payouts_value()

    def get_crew_payout_totals(self):
        return self.payouts.get_crew_payout_totals()

    def get_total_sales_value(self):

        return self._sum_sales_from_sales_table()

    def get_available_storage_inventory(self):
        return self.materials.get_available_inventory()

    def get_sales_count(self):
        if not self._table_exists("sales"):
            return 0

        deleted_filter = ""

        if "is_deleted" in self._table_columns("sales"):
            deleted_filter = "WHERE is_deleted = 0"

        self.cursor.execute(f"""
        SELECT COUNT(*)
        FROM sales
        {deleted_filter}
        """)

        return self.cursor.fetchone()[0]

    def get_refinery_total_costs(self):
        columns = self._table_columns("refinery_jobs")
        if "cost" not in columns:
            return 0

        deleted_filter = ""
        if "is_deleted" in columns:
            deleted_filter = "AND is_deleted = 0"

        self.cursor.execute(f"""
        SELECT COALESCE(SUM(cost), 0)
        FROM refinery_jobs
        WHERE status = 'COMPLETED'
        {deleted_filter}
        """)

        return self.cursor.fetchone()[0]

    def get_global_total_costs(self):
        cost_columns = self._table_columns("costs")
        deleted_filter = ""

        if "is_deleted" in cost_columns:
            deleted_filter = "WHERE is_deleted = 0"

        self.cursor.execute(f"""
        SELECT COALESCE(SUM(amount), 0)
        FROM costs
        {deleted_filter}
        """)

        session_costs = self.cursor.fetchone()[0]
        return session_costs + self.get_refinery_total_costs()

    def record_storage_sale(
        self,
        location,
        sale_date,
        material_code,
        quantity,
        unit_price,
        notes=None,
        created_by=None,
    ):
        import auth.session as user_session

        if created_by is None:
            created_by = user_session.get_user_id()

        from config.dates import normalize_date_input

        sale_date = normalize_date_input(sale_date)

        sale_id = self.materials.create_sale_with_storage(
            location,
            sale_date,
            [{
                "material_code": material_code,
                "quantity": quantity,
                "unit_price": unit_price,
            }],
            created_by=created_by,
            notes=notes,
        )
        self.payouts.refresh_sessions_for_sale(sale_id)
        return sale_id

    def get_sales_history(self, limit=100):
        if not self._table_exists("sales"):
            return []

        deleted_filter = ""

        if "is_deleted" in self._table_columns("sales"):
            deleted_filter = "WHERE s.is_deleted = 0"

        self.cursor.execute(f"""
        SELECT
            s.id,
            s.location,
            s.sale_date,
            s.total_amount,
            s.created_at,
            COALESCE(u.username, '—')
        FROM sales s
        LEFT JOIN users u
            ON u.id = s.created_by
        {deleted_filter}
        ORDER BY s.id DESC
        LIMIT ?
        """, (limit,))

        sales = []

        for row in self.cursor.fetchall():
            sale_id = row[0]

            self.cursor.execute("""
            SELECT
                material_types.material_code,
                material_types.material_name,
                sale_items.quantity,
                sale_items.unit_price,
                sale_items.total_price
            FROM sale_items
            INNER JOIN storage_items
                ON storage_items.id =
                    sale_items.storage_item_id
            INNER JOIN material_types
                ON material_types.id =
                    storage_items.material_type_id
            WHERE sale_items.sale_id = ?
            ORDER BY sale_items.id
            """, (sale_id,))

            items = [
                {
                    "material_code": item[0],
                    "material_name": item[1],
                    "quantity": item[2],
                    "unit_price": item[3],
                    "total_price": item[4],
                }
                for item in self.cursor.fetchall()
            ]

            sales.append({
                "id": sale_id,
                "location": row[1],
                "sale_date": row[2],
                "total_amount": row[3],
                "created_at": row[4],
                "created_by": row[5],
                "items": items,
            })

        return sales
    
    def get_refined_cm_total(
        self,
        session_id,
    ):
        """Refined CM produced from this session's batches."""
        if not self._table_exists("refinery_job_items"):
            return 0

        self.cursor.execute("""
        SELECT COALESCE(
            SUM(refinery_job_items.output_quantity),
            0
        )
        FROM refinery_job_items
        INNER JOIN material_batches
            ON material_batches.id =
                refinery_job_items.batch_id
        INNER JOIN refinery_jobs
            ON refinery_jobs.id =
                refinery_job_items.job_id
        WHERE material_batches.session_id = ?
        AND refinery_jobs.status = 'COMPLETED'
        AND material_batches.is_deleted = 0
        """, (session_id,))

        return self.cursor.fetchone()[0]

    def get_global_refined_cm_total(self):
        if not self._table_exists("refinery_job_items"):
            return 0

        self.cursor.execute("""
        SELECT COALESCE(
            SUM(refinery_job_items.output_quantity),
            0
        )
        FROM refinery_job_items
        INNER JOIN refinery_jobs
            ON refinery_jobs.id =
                refinery_job_items.job_id
        WHERE refinery_jobs.status = 'COMPLETED'
        """)

        return self.cursor.fetchone()[0]

    def get_dashboard_session(self):
        session = self.get_active_session()

        if session:
            return session

        latest = self.get_latest_session()

        if latest and latest[2] == "SOLD":
            return None

        return latest
    
    def get_total_profit(self):

        total_sales = self._sum_sales_from_sales_table()
        total_costs = self.get_global_total_costs()

        return total_sales - total_costs
    
    def get_active_session_count(self):

        self.cursor.execute("""
        SELECT COUNT(*)
        FROM sessions
        WHERE status = 'ACTIVE'
        """)

        return self.cursor.fetchone()[0]
    
    def get_total_session_count(self):

        self.cursor.execute("""
        SELECT COUNT(*)
        FROM sessions
        """)

        return self.cursor.fetchone()[0]

    def get_material_type_id(
        self,
        material_code
    ):

        self.cursor.execute(
            """
            SELECT id
            FROM material_types
            WHERE material_code = ?
            """,
            (material_code,)
        )

        result = self.cursor.fetchone()

        if result:
            return result[0]

        self.cursor.execute(
            """
            INSERT INTO material_types(
                material_code,
                material_name,
                created_at
            )
            VALUES(
                ?, ?, datetime('now', 'localtime')
            )
            """,
            (
                material_code,
                material_code
            )
        )

        self.connection.commit()

        return self.cursor.lastrowid
    
    def add_material(
        self,
        session_id,
        material_type,
        amount,
        created_by=None,
    ):
        import auth.session as user_session

        if amount is None or amount <= 0:
            return

        if created_by is None:
            created_by = user_session.get_user_id()

        self.materials.create_batch_from_session(
            session_id,
            material_type,
            amount,
            created_by=created_by,
        )

    def get_material_total(
        self,
        session_id,
        material_type
    ):
        batch_columns = self._table_columns(
            "material_batches"
        )

        if "remaining_quantity" in batch_columns:
            quantity_sql = (
                "COALESCE(material_batches.remaining_quantity, "
                "material_batches.quantity)"
            )
        else:
            quantity_sql = "material_batches.quantity"

        self.cursor.execute(f"""
        SELECT COALESCE(
            SUM({quantity_sql}),
            0
        )
        FROM material_batches
        INNER JOIN material_types
            ON material_types.id =
                material_batches.material_type_id
        WHERE material_batches.session_id = ?
        AND material_types.material_code = ?
        AND material_batches.is_deleted = 0
        AND {quantity_sql} > 0
        """, (
            session_id,
            material_type,
        ))

        return self.cursor.fetchone()[0]
    
    def get_session_total_scu(
        self,
        session_id
    ):

        self.cursor.execute("""
        SELECT COALESCE(
            SUM(material_batches.quantity),
            0
        )
        FROM material_batches
        WHERE material_batches.session_id = ?
        AND material_batches.is_deleted = 0
        """, (session_id,))

        return self.cursor.fetchone()[0]
