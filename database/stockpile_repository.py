"""Ortsbezogener Materialbestand (Lager / Standorte)."""

from __future__ import annotations

import json
from datetime import datetime

import auth.session as user_session

from config.i18n import tr
from config.materials import material_label, ship_sort_key
from config.storage_idle import (
    DEFAULT_RESERVE_TAG,
    IDLE_WARNING_DAYS,
    should_show_idle_warning,
)


class StockpileRepository:
    LOCATION_KINDS = (
        "STATION",
        "CITY",
        "SHIP",
        "REFINERY",
        "BASE",
        "UNKNOWN",
    )

    STATUSES = (
        "IN_SHIP",
        "STORED",
        "IN_REFINERY",
        "READY_PICKUP",
        "RESERVED",
    )

    SORT_LOCATION = "location"
    SORT_MATERIAL = "material"
    SORT_AGE = "age"

    def __init__(self, db):
        self.db = db
        self.cursor = db.cursor
        self.connection = db.connection
        self.materials = db.materials

    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _current_user_id(self):
        user = user_session.get_user()
        if not user:
            return None
        return user.get("id")

    def _table_exists(self) -> bool:
        return self.db._table_exists("material_stockpiles")

    def list_ships(self) -> list[dict]:
        if not self.db._table_exists("ships"):
            return []

        self.cursor.execute("""
        SELECT id, ship_name, ship_type
        FROM ships
        WHERE is_deleted = 0
        """)

        ships = [
            {
                "id": row[0],
                "ship_name": row[1],
                "ship_type": row[2],
            }
            for row in self.cursor.fetchall()
        ]
        ships.sort(key=lambda ship: ship_sort_key(ship["ship_name"]))
        return ships

    def _row_to_stockpile(self, row) -> dict:
        return {
            "id": row[0],
            "material_code": row[1],
            "material_name": row[2],
            "quantity_scu": row[3],
            "location_kind": row[4],
            "location_key": row[5],
            "location_label": row[6],
            "status": row[7],
            "ship_id": row[8],
            "ship_name": row[9],
            "session_id": row[10],
            "refinery_job_id": row[11],
            "reserve_tag": row[12],
            "notes": row[13],
            "last_activity_at": row[14],
            "idle_reminded_at": row[15],
            "created_at": row[16],
        }

    def _idle_warning_sql(self) -> str:
        return f"""
        material_stockpiles.status = 'STORED'
        AND material_stockpiles.quantity_scu > 0
        AND (
            material_stockpiles.reserve_tag IS NULL
            OR TRIM(material_stockpiles.reserve_tag) = ''
        )
        AND julianday('now', 'localtime')
            - julianday(material_stockpiles.last_activity_at)
            >= {IDLE_WARNING_DAYS}
        AND (
            material_stockpiles.idle_reminded_at IS NULL
            OR TRIM(material_stockpiles.idle_reminded_at) = ''
            OR julianday('now', 'localtime')
                - julianday(material_stockpiles.idle_reminded_at)
                >= {IDLE_WARNING_DAYS}
        )
        """

    def _select_stockpile_columns(self) -> str:
        return """
            material_stockpiles.id,
            material_types.material_code,
            material_types.material_name,
            material_stockpiles.quantity_scu,
            material_stockpiles.location_kind,
            material_stockpiles.location_key,
            material_stockpiles.location_label,
            material_stockpiles.status,
            material_stockpiles.ship_id,
            ships.ship_name,
            material_stockpiles.session_id,
            material_stockpiles.refinery_job_id,
            material_stockpiles.reserve_tag,
            material_stockpiles.notes,
            material_stockpiles.last_activity_at,
            material_stockpiles.idle_reminded_at,
            material_stockpiles.created_at
        """

    def list_stockpiles(
        self,
        *,
        sort_by: str = SORT_LOCATION,
        material_code: str | None = None,
        include_zero: bool = False,
        warnings_only: bool = False,
    ) -> list[dict]:
        if not self._table_exists():
            return []

        order_sql = {
            self.SORT_LOCATION: (
                "material_stockpiles.location_label COLLATE NOCASE, "
                "material_types.material_code"
            ),
            self.SORT_MATERIAL: (
                "material_types.material_code, "
                "material_stockpiles.location_label COLLATE NOCASE"
            ),
            self.SORT_AGE: "material_stockpiles.last_activity_at ASC",
        }.get(sort_by, "material_stockpiles.location_label")

        filters = ["material_stockpiles.is_deleted = 0"]
        params: list = []

        if not include_zero:
            filters.append("material_stockpiles.quantity_scu > 0")

        if material_code:
            filters.append("material_types.material_code = ?")
            params.append(material_code)

        if warnings_only:
            filters.append(f"({self._idle_warning_sql()})")

        where_sql = " AND ".join(filters)

        self.cursor.execute(f"""
        SELECT
            {self._select_stockpile_columns()}
        FROM material_stockpiles
        INNER JOIN material_types
            ON material_types.id =
                material_stockpiles.material_type_id
        LEFT JOIN ships
            ON ships.id = material_stockpiles.ship_id
        WHERE {where_sql}
        ORDER BY {order_sql}
        """, params)

        rows = [
            self._row_to_stockpile(row)
            for row in self.cursor.fetchall()
        ]
        for row in rows:
            row["idle_warning"] = should_show_idle_warning(row)
        return rows

    def count_idle_warnings(self) -> int:
        if not self._table_exists():
            return 0

        self.cursor.execute(f"""
        SELECT COUNT(*)
        FROM material_stockpiles
        WHERE material_stockpiles.is_deleted = 0
        AND {self._idle_warning_sql()}
        """)

        row = self.cursor.fetchone()
        return int(row[0] if row else 0)

    def get_stockpile(self, stockpile_id: int) -> dict | None:
        if not self._table_exists():
            return None

        self.cursor.execute(f"""
        SELECT
            {self._select_stockpile_columns()}
        FROM material_stockpiles
        INNER JOIN material_types
            ON material_types.id =
                material_stockpiles.material_type_id
        LEFT JOIN ships
            ON ships.id = material_stockpiles.ship_id
        WHERE material_stockpiles.id = ?
        AND material_stockpiles.is_deleted = 0
        """, (stockpile_id,))

        row = self.cursor.fetchone()
        if not row:
            return None

        entry = self._row_to_stockpile(row)
        entry["idle_warning"] = should_show_idle_warning(entry)
        return entry

    def _add_event(
        self,
        *,
        stockpile_id: int | None,
        event_type: str,
        quantity_delta: float | None = None,
        from_label: str | None = None,
        to_label: str | None = None,
        notes: str | None = None,
        payload: dict | None = None,
    ) -> int:
        payload_json = (
            json.dumps(payload, ensure_ascii=False)
            if payload
            else None
        )

        self.cursor.execute("""
        INSERT INTO material_stockpile_events (
            stockpile_id,
            event_type,
            quantity_delta,
            from_label,
            to_label,
            payload_json,
            notes,
            created_at,
            created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), ?)
        """, (
            stockpile_id,
            event_type,
            quantity_delta,
            from_label,
            to_label,
            payload_json,
            notes,
            self._current_user_id(),
        ))

        return self.cursor.lastrowid

    def _ensure_stockpile_storage_item(
        self,
        stockpile_id: int,
        material_type_id: int,
        quantity_scu: float,
        user_id,
        *,
        source_type: str,
        source_id: int | None,
    ) -> None:
        if "storage_item_id" not in self.db._table_columns(
            "material_stockpiles"
        ):
            return

        self.cursor.execute("""
        SELECT
            material_stockpiles.storage_item_id,
            storage_items.source_type,
            storage_items.source_id
        FROM material_stockpiles
        LEFT JOIN storage_items
            ON storage_items.id =
                material_stockpiles.storage_item_id
        WHERE material_stockpiles.id = ?
        AND material_stockpiles.is_deleted = 0
        """, (stockpile_id,))

        row = self.cursor.fetchone()
        storage_item_id = row[0] if row else None
        linked_source_type = row[1] if row else None
        linked_source_id = row[2] if row else None

        if (
            storage_item_id
            and linked_source_type == source_type
            and linked_source_id == source_id
        ):
            self.materials.increase_stockpile_storage_item(
                storage_item_id,
                quantity_scu,
                updated_by=user_id,
            )
            return

        storage_item_id = self.materials.create_stockpile_storage_item(
            material_type_id,
            quantity_scu,
            source_type=source_type,
            source_id=source_id,
            created_by=user_id,
        )

        if not row or row[0] is None:
            self.cursor.execute("""
            UPDATE material_stockpiles
            SET storage_item_id = ?
            WHERE id = ?
            AND is_deleted = 0
            """, (storage_item_id, stockpile_id))

    def _find_ship_stockpile(
        self,
        *,
        material_code: str,
        ship_id: int,
    ) -> tuple[int, float] | None:
        self.cursor.execute("""
        SELECT
            material_stockpiles.id,
            material_stockpiles.quantity_scu
        FROM material_stockpiles
        INNER JOIN material_types
            ON material_types.id =
                material_stockpiles.material_type_id
        WHERE material_stockpiles.is_deleted = 0
        AND material_types.material_code = ?
        AND material_stockpiles.location_kind = 'SHIP'
        AND material_stockpiles.ship_id = ?
        AND material_stockpiles.status = 'IN_SHIP'
        AND material_stockpiles.quantity_scu > 0
        ORDER BY material_stockpiles.last_activity_at ASC
        LIMIT 1
        """, (material_code, ship_id))

        row = self.cursor.fetchone()
        if not row:
            return None
        return int(row[0]), float(row[1])

    def _reduce_stockpile_quantity(
        self,
        stockpile_id: int,
        quantity_scu: float,
        user_id,
        *,
        to_label: str | None = None,
        payload: dict | None = None,
    ) -> None:
        self.cursor.execute("""
        SELECT quantity_scu, location_label
        FROM material_stockpiles
        WHERE id = ?
        AND is_deleted = 0
        """, (stockpile_id,))

        row = self.cursor.fetchone()
        if not row:
            raise ValueError(tr("error.storage.not_found"))

        current_qty = float(row[0])
        if current_qty + 1e-9 < quantity_scu:
            raise ValueError(tr("error.material.storage_changed"))

        location_label = row[1]
        new_qty = current_qty - quantity_scu
        now = self._now()

        if new_qty <= 1e-9:
            self.cursor.execute("""
            UPDATE material_stockpiles
            SET
                quantity_scu = 0,
                last_activity_at = ?,
                updated_at = datetime('now', 'localtime'),
                updated_by = ?
            WHERE id = ?
            AND is_deleted = 0
            """, (now, user_id, stockpile_id))
        else:
            self.cursor.execute("""
            UPDATE material_stockpiles
            SET
                quantity_scu = ?,
                last_activity_at = ?,
                updated_at = datetime('now', 'localtime'),
                updated_by = ?
            WHERE id = ?
            AND is_deleted = 0
            """, (new_qty, now, user_id, stockpile_id))

        self._add_event(
            stockpile_id=stockpile_id,
            event_type="WITHDRAW",
            quantity_delta=-quantity_scu,
            from_label=location_label,
            to_label=to_label,
            payload={
                "reason": "transfer_out",
                **(payload or {}),
            },
        )

    def reserve_ship_stockpile_for_refinery(
        self,
        *,
        material_code: str,
        quantity_scu: float,
        refinery_job_id: int,
        station_label: str,
        created_by=None,
    ) -> None:
        """Rohmaterial vom Schiff für Raffinerie-Job abziehen (ohne commit)."""
        if not self._table_exists() or quantity_scu <= 0:
            return

        remaining = float(quantity_scu)
        user_id = created_by or self._current_user_id()
        station_label = (station_label or "").strip() or "—"
        to_label = tr(
            "storage.event.to_refinery",
            station=station_label,
        )

        while remaining > 1e-9:
            self.cursor.execute("""
            SELECT
                material_stockpiles.id,
                material_stockpiles.quantity_scu
            FROM material_stockpiles
            INNER JOIN material_types
                ON material_types.id =
                    material_stockpiles.material_type_id
            WHERE material_stockpiles.is_deleted = 0
            AND material_types.material_code = ?
            AND material_stockpiles.location_kind = 'SHIP'
            AND material_stockpiles.status = 'IN_SHIP'
            AND material_stockpiles.quantity_scu > 0
            ORDER BY material_stockpiles.last_activity_at ASC
            LIMIT 1
            """, (material_code,))

            row = self.cursor.fetchone()
            if not row:
                break

            stockpile_id = int(row[0])
            available = float(row[1])
            take = min(remaining, available)

            self._reduce_stockpile_quantity(
                stockpile_id,
                take,
                user_id,
                to_label=to_label,
                payload={
                    "reason": "refinery_reserve",
                    "refinery_job_id": refinery_job_id,
                    "material_code": material_code,
                },
            )
            remaining -= take

    def restore_ship_stockpile_from_refinery_cancel(
        self,
        *,
        material_code: str,
        quantity_scu: float,
        batch_id: int,
        created_by=None,
    ) -> None:
        """Rohmaterial nach Job-Storno zurück auf Session-Schiff (ohne commit)."""
        if not self._table_exists() or quantity_scu <= 0:
            return

        self.cursor.execute("""
        SELECT session_id
        FROM material_batches
        WHERE id = ?
        AND is_deleted = 0
        """, (batch_id,))

        row = self.cursor.fetchone()
        if not row or not row[0]:
            return

        session_id = row[0]
        ship = self.db.get_session_ship(session_id)
        if not ship:
            return

        ship_id = ship["ship_id"]
        ship_name = ship["ship_name"]
        material_type_id = self.materials.get_material_type_id(
            material_code
        )
        now = self._now()
        user_id = created_by or self._current_user_id()

        existing = self._find_ship_stockpile(
            material_code=material_code,
            ship_id=ship_id,
        )
        if existing:
            stockpile_id, current_qty = existing
            new_qty = current_qty + quantity_scu
            self.cursor.execute("""
            UPDATE material_stockpiles
            SET
                quantity_scu = ?,
                session_id = ?,
                last_activity_at = ?,
                idle_reminded_at = NULL,
                updated_at = datetime('now', 'localtime'),
                updated_by = ?
            WHERE id = ?
            AND is_deleted = 0
            """, (
                new_qty,
                session_id,
                now,
                user_id,
                stockpile_id,
            ))
        else:
            self.cursor.execute("""
            INSERT INTO material_stockpiles (
                material_type_id,
                quantity_scu,
                location_kind,
                location_key,
                location_label,
                status,
                ship_id,
                session_id,
                reserve_tag,
                notes,
                last_activity_at,
                created_at,
                created_by
            )
            VALUES (?, ?, 'SHIP', ?, ?, 'IN_SHIP', ?, ?, NULL, NULL, ?, datetime('now', 'localtime'), ?)
            """, (
                material_type_id,
                quantity_scu,
                str(ship_id),
                ship_name,
                ship_id,
                session_id,
                now,
                user_id,
            ))
            stockpile_id = self.cursor.lastrowid

        self._add_event(
            stockpile_id=stockpile_id,
            event_type="DEPOSIT",
            quantity_delta=quantity_scu,
            from_label=tr("storage.event.refinery_cancelled"),
            to_label=tr(
                "storage.location.ship",
                ship=ship_name,
            ),
            payload={
                "material_code": material_code,
                "batch_id": batch_id,
                "source": "REFINERY_CANCEL",
            },
        )

    def _transfer_from_ship_stockpiles(
        self,
        material_code: str,
        quantity_scu: float,
        created_by=None,
    ) -> tuple[str, int | None]:
        remaining = float(quantity_scu)
        primary_source_type = "SESSION"
        primary_source_id = None
        user_id = created_by or self._current_user_id()

        while remaining > 1e-9:
            self.cursor.execute("""
            SELECT
                material_stockpiles.id,
                material_stockpiles.quantity_scu,
                material_stockpiles.storage_item_id
            FROM material_stockpiles
            INNER JOIN material_types
                ON material_types.id =
                    material_stockpiles.material_type_id
            WHERE material_stockpiles.is_deleted = 0
            AND material_types.material_code = ?
            AND material_stockpiles.location_kind = 'SHIP'
            AND material_stockpiles.status = 'IN_SHIP'
            AND material_stockpiles.quantity_scu > 0
            ORDER BY material_stockpiles.last_activity_at ASC
            LIMIT 1
            """, (material_code,))

            row = self.cursor.fetchone()
            if not row:
                break

            stockpile_id = int(row[0])
            available = float(row[1])
            storage_item_id = row[2]
            take = min(remaining, available)

            if primary_source_id is None and storage_item_id:
                self.cursor.execute("""
                SELECT source_type, source_id
                FROM storage_items
                WHERE id = ?
                """, (storage_item_id,))
                source_row = self.cursor.fetchone()
                if source_row:
                    primary_source_type = source_row[0] or "SESSION"
                    primary_source_id = source_row[1]

            self._reduce_stockpile_quantity(
                stockpile_id,
                take,
                user_id,
            )
            remaining -= take

        if remaining > 1e-9:
            self.cursor.execute("""
            SELECT COALESCE(SUM(material_stockpiles.quantity_scu), 0)
            FROM material_stockpiles
            INNER JOIN material_types
                ON material_types.id =
                    material_stockpiles.material_type_id
            WHERE material_stockpiles.is_deleted = 0
            AND material_types.material_code = ?
            AND material_stockpiles.location_kind = 'SHIP'
            AND material_stockpiles.status = 'IN_SHIP'
            AND material_stockpiles.quantity_scu > 0
            """, (material_code,))

            available_row = self.cursor.fetchone()
            available = float(available_row[0] if available_row else 0)
            raise ValueError(
                tr(
                    "error.storage.insufficient_on_ship",
                    available=f"{available:g}",
                    material=material_label(material_code),
                )
            )

        return (primary_source_type, primary_source_id)

    def deposit_session_capture(
        self,
        *,
        material_code: str,
        quantity_scu: float,
        session_id: int,
        batch_id: int,
        ship_id: int,
        ship_name: str,
        created_by=None,
    ) -> int:
        """Salvage-Erfassung → Stockpile auf Session-Schiff (ohne commit)."""
        if not self._table_exists():
            raise ValueError(tr("error.storage.not_available"))

        if quantity_scu <= 0:
            raise ValueError(tr("error.storage.quantity_positive"))

        ship_name = (ship_name or "").strip()
        if not ship_name:
            raise ValueError(tr("error.storage.ship_required"))

        material_type_id = self.materials.get_material_type_id(
            material_code
        )
        now = self._now()
        user_id = created_by or self._current_user_id()

        existing = self._find_ship_stockpile(
            material_code=material_code,
            ship_id=ship_id,
        )
        if existing:
            stockpile_id, current_qty = existing
            new_qty = current_qty + quantity_scu
            self.cursor.execute("""
            UPDATE material_stockpiles
            SET
                quantity_scu = ?,
                session_id = ?,
                last_activity_at = ?,
                idle_reminded_at = NULL,
                updated_at = datetime('now', 'localtime'),
                updated_by = ?
            WHERE id = ?
            AND is_deleted = 0
            """, (
                new_qty,
                session_id,
                now,
                user_id,
                stockpile_id,
            ))
        else:
            self.cursor.execute("""
            INSERT INTO material_stockpiles (
                material_type_id,
                quantity_scu,
                location_kind,
                location_key,
                location_label,
                status,
                ship_id,
                session_id,
                reserve_tag,
                notes,
                last_activity_at,
                created_at,
                created_by
            )
            VALUES (?, ?, 'SHIP', ?, ?, 'IN_SHIP', ?, ?, NULL, NULL, ?, datetime('now', 'localtime'), ?)
            """, (
                material_type_id,
                quantity_scu,
                str(ship_id),
                ship_name,
                ship_id,
                session_id,
                now,
                user_id,
            ))
            stockpile_id = self.cursor.lastrowid

        self._ensure_stockpile_storage_item(
            stockpile_id,
            material_type_id,
            quantity_scu,
            user_id,
            source_type="SESSION",
            source_id=batch_id,
        )

        self._add_event(
            stockpile_id=stockpile_id,
            event_type="DEPOSIT",
            quantity_delta=quantity_scu,
            from_label=tr("storage.event.session_salvage"),
            to_label=tr(
                "storage.location.ship",
                ship=ship_name,
            ),
            payload={
                "material_code": material_code,
                "session_id": session_id,
                "batch_id": batch_id,
                "source": "SESSION_CAPTURE",
            },
        )

        linked = self.cursor.execute("""
        SELECT storage_item_id
        FROM material_stockpiles
        WHERE id = ?
        """, (stockpile_id,)).fetchone()

        return linked[0] if linked and linked[0] else 0

    def create_stockpile(
        self,
        *,
        material_code: str,
        quantity_scu: float,
        location_kind: str,
        location_label: str,
        location_key: str | None = None,
        status: str = "STORED",
        ship_id: int | None = None,
        session_id: int | None = None,
        reserve_tag: str | None = None,
        notes: str | None = None,
    ) -> int:
        if not self._table_exists():
            raise ValueError(tr("error.storage.not_available"))

        if quantity_scu <= 0:
            raise ValueError(tr("error.storage.quantity_positive"))

        location_label = (location_label or "").strip()
        if not location_label:
            raise ValueError(tr("error.storage.location_required"))

        if location_kind == "SHIP":
            status = "IN_SHIP"
            if ship_id is None:
                raise ValueError(tr("error.storage.ship_required"))

        material_type_id = self.materials.get_material_type_id(
            material_code
        )
        now = self._now()
        user_id = self._current_user_id()
        from_label = tr("dashboard.action.legacy_storage")
        transfer_source = "GLOBAL_TRANSFER"

        try:
            self.connection.execute("BEGIN IMMEDIATE")

            if location_kind == "SHIP":
                source_type, source_id = (
                    self.materials.transfer_global_to_stockpile(
                        material_code,
                        quantity_scu,
                        created_by=user_id,
                    )
                )
                from_label = tr("dashboard.action.legacy_storage")
            else:
                try:
                    source_type, source_id = (
                        self._transfer_from_ship_stockpiles(
                            material_code,
                            quantity_scu,
                            created_by=user_id,
                        )
                    )
                    from_label = tr("storage.event.from_ship")
                    transfer_source = "SHIP_TRANSFER"
                except ValueError as ship_error:
                    try:
                        source_type, source_id = (
                            self.materials.transfer_global_to_stockpile(
                                material_code,
                                quantity_scu,
                                created_by=user_id,
                            )
                        )
                        from_label = tr(
                            "dashboard.action.legacy_storage"
                        )
                    except ValueError:
                        raise ship_error

            stockpile_columns = self.db._table_columns(
                "material_stockpiles"
            )
            has_storage_link = (
                "storage_item_id" in stockpile_columns
            )

            self.cursor.execute("""
            INSERT INTO material_stockpiles (
                material_type_id,
                quantity_scu,
                location_kind,
                location_key,
                location_label,
                status,
                ship_id,
                session_id,
                reserve_tag,
                notes,
                last_activity_at,
                created_at,
                created_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), ?)
            """, (
                material_type_id,
                quantity_scu,
                location_kind,
                location_key,
                location_label,
                status,
                ship_id,
                session_id,
                reserve_tag,
                notes,
                now,
                user_id,
            ))

            stockpile_id = self.cursor.lastrowid

            if has_storage_link:
                self._ensure_stockpile_storage_item(
                    stockpile_id,
                    material_type_id,
                    quantity_scu,
                    user_id,
                    source_type=source_type,
                    source_id=source_id,
                )

            self._add_event(
                stockpile_id=stockpile_id,
                event_type="DEPOSIT",
                quantity_delta=quantity_scu,
                from_label=from_label,
                to_label=location_label,
                notes=notes,
                payload={
                    "material_code": material_code,
                    "location_kind": location_kind,
                    "status": status,
                    "source": transfer_source,
                },
            )

            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

        return stockpile_id

    def deposit_refinery_pickup(
        self,
        *,
        material_code: str,
        quantity_scu: float,
        station_label: str,
        refinery_job_id: int,
        session_id: int | None = None,
    ) -> int | None:
        """DEPOSIT nach Raffinerie-Abholung (ohne commit — für Transaktionen)."""
        if not self._table_exists():
            return None

        if quantity_scu <= 0:
            return None

        station_label = (station_label or "").strip() or "—"
        material_type_id = self.materials.get_material_type_id(
            material_code
        )
        now = self._now()
        user_id = self._current_user_id()

        self.cursor.execute("""
        SELECT
            material_stockpiles.id,
            material_stockpiles.quantity_scu
        FROM material_stockpiles
        INNER JOIN material_types
            ON material_types.id =
                material_stockpiles.material_type_id
        WHERE material_stockpiles.is_deleted = 0
        AND material_types.material_code = ?
        AND material_stockpiles.location_kind = 'STATION'
        AND material_stockpiles.location_label = ?
        AND material_stockpiles.status = 'STORED'
        AND material_stockpiles.quantity_scu > 0
        LIMIT 1
        """, (material_code, station_label))

        existing = self.cursor.fetchone()
        if existing:
            stockpile_id = existing[0]
            new_qty = float(existing[1]) + quantity_scu
            self.cursor.execute("""
            UPDATE material_stockpiles
            SET
                quantity_scu = ?,
                last_activity_at = ?,
                idle_reminded_at = NULL,
                updated_at = datetime('now', 'localtime'),
                updated_by = ?
            WHERE id = ?
            AND is_deleted = 0
            """, (new_qty, now, user_id, stockpile_id))
        else:
            stockpile_columns = self.db._table_columns(
                "material_stockpiles"
            )
            if "refinery_job_id" in stockpile_columns:
                self.cursor.execute("""
                INSERT INTO material_stockpiles (
                    material_type_id,
                    quantity_scu,
                    location_kind,
                    location_key,
                    location_label,
                    status,
                    ship_id,
                    session_id,
                    refinery_job_id,
                    reserve_tag,
                    notes,
                    last_activity_at,
                    created_at,
                    created_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), ?)
                """, (
                    material_type_id,
                    quantity_scu,
                    "STATION",
                    None,
                    station_label,
                    "STORED",
                    None,
                    session_id,
                    refinery_job_id,
                    None,
                    None,
                    now,
                    user_id,
                ))
            else:
                self.cursor.execute("""
                INSERT INTO material_stockpiles (
                    material_type_id,
                    quantity_scu,
                    location_kind,
                    location_key,
                    location_label,
                    status,
                    ship_id,
                    session_id,
                    reserve_tag,
                    notes,
                    last_activity_at,
                    created_at,
                    created_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), ?)
                """, (
                    material_type_id,
                    quantity_scu,
                    "STATION",
                    None,
                    station_label,
                    "STORED",
                    None,
                    session_id,
                    None,
                    None,
                    now,
                    user_id,
                ))

            stockpile_id = self.cursor.lastrowid

        self._add_event(
            stockpile_id=stockpile_id,
            event_type="DEPOSIT",
            quantity_delta=quantity_scu,
            from_label=station_label,
            to_label=station_label,
            payload={
                "material_code": material_code,
                "refinery_job_id": refinery_job_id,
                "source": "REFINERY",
            },
        )

        self._ensure_stockpile_storage_item(
            stockpile_id,
            material_type_id,
            quantity_scu,
            user_id,
            source_type="REFINERY",
            source_id=refinery_job_id,
        )

        return stockpile_id

    def update_stockpile(
        self,
        stockpile_id: int,
        *,
        quantity_scu: float | None = None,
        location_kind: str | None = None,
        location_label: str | None = None,
        location_key: str | None = None,
        status: str | None = None,
        ship_id: int | None = None,
        reserve_tag: str | None = None,
        notes: str | None = None,
        touch_activity: bool = True,
    ) -> None:
        if not self._table_exists():
            raise ValueError(tr("error.storage.not_available"))

        existing = self.get_stockpile(stockpile_id)
        if not existing:
            raise ValueError(tr("error.storage.not_found"))

        updates = []
        params: list = []

        if quantity_scu is not None:
            if quantity_scu < 0:
                raise ValueError(tr("error.storage.quantity_positive"))
            updates.append("quantity_scu = ?")
            params.append(quantity_scu)

        if location_kind is not None:
            updates.append("location_kind = ?")
            params.append(location_kind)

        if location_key is not None:
            updates.append("location_key = ?")
            params.append(location_key)

        if location_label is not None:
            label = location_label.strip()
            if not label:
                raise ValueError(tr("error.storage.location_required"))
            updates.append("location_label = ?")
            params.append(label)

        if status is not None:
            updates.append("status = ?")
            params.append(status)

        if ship_id is not None:
            updates.append("ship_id = ?")
            params.append(ship_id)

        if reserve_tag is not None:
            updates.append("reserve_tag = ?")
            params.append(reserve_tag or None)

        if notes is not None:
            updates.append("notes = ?")
            params.append(notes or None)

        if touch_activity:
            updates.append("last_activity_at = ?")
            params.append(self._now())

        if not updates:
            return

        updates.append("updated_at = datetime('now', 'localtime')")
        updates.append("updated_by = ?")
        params.append(self._current_user_id())
        params.append(stockpile_id)

        self.cursor.execute(f"""
        UPDATE material_stockpiles
        SET {", ".join(updates)}
        WHERE id = ?
        AND is_deleted = 0
        """, params)

        delta = None
        if quantity_scu is not None:
            delta = quantity_scu - existing["quantity_scu"]

        self._add_event(
            stockpile_id=stockpile_id,
            event_type="UPDATE",
            quantity_delta=delta,
            from_label=existing["location_label"],
            to_label=location_label or existing["location_label"],
            payload={
                "material_code": existing["material_code"],
            },
        )

        self.connection.commit()

    def acknowledge_idle_reminder(self, stockpile_id: int) -> None:
        if not self._table_exists():
            raise ValueError(tr("error.storage.not_available"))

        existing = self.get_stockpile(stockpile_id)
        if not existing:
            raise ValueError(tr("error.storage.not_found"))

        now = self._now()
        self.cursor.execute("""
        UPDATE material_stockpiles
        SET
            idle_reminded_at = ?,
            updated_at = datetime('now', 'localtime'),
            updated_by = ?
        WHERE id = ?
        AND is_deleted = 0
        """, (now, self._current_user_id(), stockpile_id))

        self._add_event(
            stockpile_id=stockpile_id,
            event_type="IDLE_REMINDED",
            from_label=existing["location_label"],
            payload={
                "material_code": existing["material_code"],
            },
        )

        self.connection.commit()

    def set_reserve_tag(
        self,
        stockpile_id: int,
        reserve_tag: str | None = None,
    ) -> None:
        if not self._table_exists():
            raise ValueError(tr("error.storage.not_available"))

        existing = self.get_stockpile(stockpile_id)
        if not existing:
            raise ValueError(tr("error.storage.not_found"))

        tag = (reserve_tag or DEFAULT_RESERVE_TAG).strip()
        if not tag:
            raise ValueError(tr("error.storage.reserve_required"))

        self.cursor.execute("""
        UPDATE material_stockpiles
        SET
            reserve_tag = ?,
            idle_reminded_at = NULL,
            updated_at = datetime('now', 'localtime'),
            updated_by = ?
        WHERE id = ?
        AND is_deleted = 0
        """, (tag, self._current_user_id(), stockpile_id))

        self._add_event(
            stockpile_id=stockpile_id,
            event_type="TAG_SET",
            from_label=existing["location_label"],
            notes=tag,
            payload={
                "material_code": existing["material_code"],
                "reserve_tag": tag,
            },
        )

        self.connection.commit()

    def mark_moved_or_withdrawn(self, stockpile_id: int) -> None:
        if not self._table_exists():
            raise ValueError(tr("error.storage.not_available"))

        existing = self.get_stockpile(stockpile_id)
        if not existing:
            raise ValueError(tr("error.storage.not_found"))

        now = self._now()
        self.cursor.execute("""
        UPDATE material_stockpiles
        SET
            last_activity_at = ?,
            idle_reminded_at = NULL,
            updated_at = datetime('now', 'localtime'),
            updated_by = ?
        WHERE id = ?
        AND is_deleted = 0
        """, (now, self._current_user_id(), stockpile_id))

        self._add_event(
            stockpile_id=stockpile_id,
            event_type="ACTIVITY",
            from_label=existing["location_label"],
            payload={
                "material_code": existing["material_code"],
                "reason": "moved_or_withdrawn",
            },
        )

        self.connection.commit()

    def delete_stockpile(self, stockpile_id: int) -> None:
        if not self._table_exists():
            raise ValueError(tr("error.storage.not_available"))

        existing = self.get_stockpile(stockpile_id)
        if not existing:
            raise ValueError(tr("error.storage.not_found"))

        self.cursor.execute("""
        UPDATE material_stockpiles
        SET
            is_deleted = 1,
            deleted_at = datetime('now', 'localtime'),
            updated_at = datetime('now', 'localtime'),
            updated_by = ?
        WHERE id = ?
        """, (self._current_user_id(), stockpile_id))

        self._add_event(
            stockpile_id=stockpile_id,
            event_type="DELETE",
            quantity_delta=-existing["quantity_scu"],
            from_label=existing["location_label"],
            payload={
                "material_code": existing["material_code"],
            },
        )

        self.connection.commit()

    def list_events(
        self,
        *,
        stockpile_id: int | None = None,
        limit: int = 200,
    ) -> list[dict]:
        if not self.db._table_exists("material_stockpile_events"):
            return []

        filters = ["material_stockpile_events.is_deleted = 0"]
        params: list = []

        if stockpile_id is not None:
            filters.append(
                "material_stockpile_events.stockpile_id = ?"
            )
            params.append(stockpile_id)

        where_sql = " AND ".join(filters)
        params.append(limit)

        self.cursor.execute(f"""
        SELECT
            material_stockpile_events.id,
            material_stockpile_events.stockpile_id,
            material_stockpile_events.event_type,
            material_stockpile_events.quantity_delta,
            material_stockpile_events.from_label,
            material_stockpile_events.to_label,
            material_stockpile_events.notes,
            material_stockpile_events.created_at,
            material_types.material_code,
            material_stockpiles.location_label
        FROM material_stockpile_events
        LEFT JOIN material_stockpiles
            ON material_stockpiles.id =
                material_stockpile_events.stockpile_id
        LEFT JOIN material_types
            ON material_types.id =
                material_stockpiles.material_type_id
        WHERE {where_sql}
        ORDER BY material_stockpile_events.created_at DESC
        LIMIT ?
        """, params)

        return [
            {
                "id": row[0],
                "stockpile_id": row[1],
                "event_type": row[2],
                "quantity_delta": row[3],
                "from_label": row[4],
                "to_label": row[5],
                "notes": row[6],
                "created_at": row[7],
                "material_code": row[8],
                "location_label": row[9],
            }
            for row in self.cursor.fetchall()
        ]

    def delete_event(self, event_id: int) -> None:
        if not self.db._table_exists("material_stockpile_events"):
            raise ValueError(tr("error.storage.not_available"))

        self.cursor.execute("""
        UPDATE material_stockpile_events
        SET
            is_deleted = 1,
            deleted_at = datetime('now', 'localtime')
        WHERE id = ?
        AND is_deleted = 0
        """, (event_id,))

        if self.cursor.rowcount == 0:
            raise ValueError(tr("error.storage.event_not_found"))

        self.connection.commit()

    def totals_by_material(self) -> list[dict]:
        if not self._table_exists():
            return []

        self.cursor.execute("""
        SELECT
            material_types.material_code,
            COALESCE(SUM(material_stockpiles.quantity_scu), 0)
        FROM material_stockpiles
        INNER JOIN material_types
            ON material_types.id =
                material_stockpiles.material_type_id
        WHERE material_stockpiles.is_deleted = 0
        AND material_stockpiles.quantity_scu > 0
        GROUP BY material_types.material_code
        ORDER BY material_types.material_code
        """)

        return [
            {
                "material_code": row[0],
                "quantity_scu": row[1],
            }
            for row in self.cursor.fetchall()
        ]

    def format_location(self, entry: dict) -> str:
        if entry.get("ship_name"):
            return tr(
                "storage.location.ship",
                ship=entry["ship_name"],
            )
        return entry.get("location_label") or "—"

    def material_display(self, material_code: str) -> str:
        return material_label(material_code)
