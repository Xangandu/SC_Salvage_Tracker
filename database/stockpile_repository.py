"""Ortsbezogener Materialbestand (Lager / Standorte)."""

from __future__ import annotations

import json
from datetime import datetime

import auth.session as user_session

from config.i18n import tr
from config.locations.catalog import lookup_location_by_label
from config.materials import REFINED_SELLABLE_CODES, material_label, ship_sort_key
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

        if storage_item_id:
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

    def _deduct_linked_storage_item(
        self,
        stockpile_id: int,
        quantity_scu: float,
        *,
        updated_by=None,
    ) -> None:
        if "storage_item_id" not in self.db._table_columns(
            "material_stockpiles"
        ):
            return

        self.cursor.execute("""
        SELECT storage_item_id
        FROM material_stockpiles
        WHERE id = ?
        AND is_deleted = 0
        """, (stockpile_id,))
        row = self.cursor.fetchone()
        storage_item_id = row[0] if row else None
        if storage_item_id:
            self.materials._deduct_storage_row(
                storage_item_id,
                quantity_scu,
                updated_by=updated_by,
            )

    def _ensure_storage_quantity_for_sale(
        self,
        storage_item_id: int,
        quantity_scu: float,
        *,
        updated_by=None,
    ) -> None:
        """Verknüpftes storage_item auf Verkaufsmenge synchronisieren."""
        self.cursor.execute("""
        SELECT quantity
        FROM storage_items
        WHERE id = ?
        AND is_deleted = 0
        """, (storage_item_id,))

        row = self.cursor.fetchone()
        if not row:
            raise ValueError(tr("error.material.storage_changed"))

        available = float(row[0])
        if available + 1e-9 < quantity_scu:
            self.materials.increase_stockpile_storage_item(
                storage_item_id,
                quantity_scu - available,
                updated_by=updated_by,
            )

    def _sellable_stockpile_filter_sql(self) -> str:
        return """
        AND (
            (
                material_stockpiles.status = 'STORED'
                AND material_stockpiles.location_kind IN (
                    'STATION', 'CITY'
                )
            )
            OR (
                material_stockpiles.status = 'IN_SHIP'
                AND material_stockpiles.location_kind = 'SHIP'
            )
        )
        """

    def sellable_quantity(self, material_code: str) -> float:
        """Verkaufbare SCU aus physischen Lager-Pools (Schiff + Station)."""
        if (
            not self._table_exists()
            or material_code not in REFINED_SELLABLE_CODES
        ):
            return 0.0

        sellable_filter = self._sellable_stockpile_filter_sql()
        self.cursor.execute(f"""
        SELECT COALESCE(SUM(material_stockpiles.quantity_scu), 0)
        FROM material_stockpiles
        INNER JOIN material_types
            ON material_types.id =
                material_stockpiles.material_type_id
        WHERE material_stockpiles.is_deleted = 0
        AND material_stockpiles.quantity_scu > 0
        AND material_types.material_code = ?
        {sellable_filter}
        """, (material_code,))

        row = self.cursor.fetchone()
        return float(row[0] if row else 0)

    def withdraw_material_for_sale(
        self,
        material_code: str,
        quantity_scu: float,
        *,
        sale_location: str,
        created_by=None,
    ) -> tuple[list[dict], float]:
        """
        Entnimmt verkaufbare SCU FIFO aus material_stockpiles.
        Gibt (sale_item-Zeilen, Restmenge) zurück.
        """
        if not self._table_exists():
            return [], float(quantity_scu)

        if material_code not in REFINED_SELLABLE_CODES:
            return [], float(quantity_scu)

        remaining = float(quantity_scu)
        if remaining <= 0:
            return [], 0.0

        user_id = created_by or self._current_user_id()
        sale_item_records: list[dict] = []
        sellable_filter = self._sellable_stockpile_filter_sql()

        while remaining > 1e-9:
            self.cursor.execute(f"""
            SELECT
                material_stockpiles.id,
                material_stockpiles.quantity_scu,
                material_stockpiles.storage_item_id,
                material_stockpiles.location_label
            FROM material_stockpiles
            INNER JOIN material_types
                ON material_types.id =
                    material_stockpiles.material_type_id
            WHERE material_stockpiles.is_deleted = 0
            AND material_stockpiles.quantity_scu > 0
            AND material_types.material_code = ?
            {sellable_filter}
            ORDER BY material_stockpiles.last_activity_at ASC
            LIMIT 1
            """, (material_code,))

            row = self.cursor.fetchone()
            if not row:
                break

            stockpile_id = int(row[0])
            take = min(remaining, float(row[1]))
            storage_item_id = row[2]

            if not storage_item_id:
                material_type_id = self.materials.get_material_type_id(
                    material_code
                )
                storage_item_id = (
                    self.materials.create_stockpile_storage_item(
                        material_type_id,
                        take,
                        source_type="STOCKPILE",
                        source_id=stockpile_id,
                        created_by=user_id,
                    )
                )
                self.cursor.execute("""
                UPDATE material_stockpiles
                SET storage_item_id = ?
                WHERE id = ?
                AND is_deleted = 0
                """, (storage_item_id, stockpile_id))
            else:
                self._ensure_storage_quantity_for_sale(
                    int(storage_item_id),
                    take,
                    updated_by=user_id,
                )

            self._reduce_stockpile_quantity(
                stockpile_id,
                take,
                user_id,
                to_label=sale_location,
                payload={
                    "reason": "sale",
                    "material_code": material_code,
                    "sale_location": sale_location,
                },
            )
            self._deduct_linked_storage_item(
                stockpile_id,
                take,
                updated_by=user_id,
            )

            sale_item_records.append({
                "storage_item_id": int(storage_item_id),
                "quantity": take,
            })
            remaining -= take

        return sale_item_records, remaining

    def session_sellable_quantity(self, session_id: int) -> float:
        """Verkaufbare SCU einer Session (physische Stockpiles)."""
        if not self._table_exists():
            return 0.0

        placeholders = ", ".join(
            "?" for _ in REFINED_SELLABLE_CODES
        )
        sellable_filter = self._sellable_stockpile_filter_sql()

        self.cursor.execute(f"""
        SELECT COALESCE(SUM(material_stockpiles.quantity_scu), 0)
        FROM material_stockpiles
        INNER JOIN material_types
            ON material_types.id =
                material_stockpiles.material_type_id
        WHERE material_stockpiles.is_deleted = 0
        AND material_stockpiles.quantity_scu > 0
        AND material_types.material_code IN ({placeholders})
        {sellable_filter}
        AND (
            material_stockpiles.session_id = ?
            OR material_stockpiles.refinery_job_id IN (
                SELECT DISTINCT refinery_job_items.job_id
                FROM refinery_job_items
                INNER JOIN material_batches
                    ON material_batches.id =
                        refinery_job_items.batch_id
                WHERE material_batches.session_id = ?
                AND material_batches.is_deleted = 0
            )
        )
        """, [*REFINED_SELLABLE_CODES, session_id, session_id])

        row = self.cursor.fetchone()
        return float(row[0] if row else 0)

    def restore_stockpile_for_storage_item(
        self,
        storage_item_id: int,
        quantity_scu: float,
        *,
        updated_by=None,
    ) -> None:
        """Stellt physischen Lagerbestand nach Verkaufs-Storno wieder her."""
        if (
            not self._table_exists()
            or quantity_scu <= 0
            or "storage_item_id" not in self.db._table_columns(
                "material_stockpiles"
            )
        ):
            return

        self.cursor.execute("""
        SELECT
            material_stockpiles.id,
            material_stockpiles.quantity_scu,
            material_stockpiles.location_label,
            material_types.material_code
        FROM material_stockpiles
        INNER JOIN material_types
            ON material_types.id =
                material_stockpiles.material_type_id
        WHERE material_stockpiles.storage_item_id = ?
        AND material_stockpiles.is_deleted = 0
        ORDER BY material_stockpiles.id ASC
        LIMIT 1
        """, (storage_item_id,))

        row = self.cursor.fetchone()
        if not row:
            return

        stockpile_id = int(row[0])
        new_qty = float(row[1]) + quantity_scu
        location_label = row[2] or "—"
        material_code = row[3]
        user_id = updated_by or self._current_user_id()
        now = self._now()

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
            event_type="DEPOSIT",
            quantity_delta=quantity_scu,
            from_label=location_label,
            to_label=location_label,
            payload={
                "reason": "sale_void",
                "material_code": material_code,
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
        ship_id: int | None = None,
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

        ship_filter = ""
        params: list = [material_code]
        if ship_id is not None:
            ship_filter = "AND material_stockpiles.ship_id = ?"
            params.append(ship_id)

        while remaining > 1e-9:
            self.cursor.execute(f"""
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
            {ship_filter}
            ORDER BY material_stockpiles.last_activity_at ASC
            LIMIT 1
            """, params)

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

        if remaining > 1e-9:
            label = material_label(material_code)
            raise ValueError(
                tr(
                    "error.storage.insufficient_ship_pool",
                    material=label,
                    available=f"{quantity_scu - remaining:g}",
                    requested=f"{quantity_scu:g}",
                )
            )

    def reserve_stored_stockpile_for_refinery(
        self,
        *,
        material_code: str,
        quantity_scu: float,
        refinery_job_id: int,
        station_label: str,
        location_kind: str,
        location_key: str,
        created_by=None,
    ) -> None:
        """Rohmaterial vom Lager (Station/Stadt) für Raffinerie abziehen."""
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
            AND material_stockpiles.location_kind = ?
            AND material_stockpiles.status = 'STORED'
            AND material_stockpiles.location_key = ?
            AND material_stockpiles.quantity_scu > 0
            ORDER BY material_stockpiles.last_activity_at ASC
            LIMIT 1
            """, (material_code, location_kind, location_key))

            row = self.cursor.fetchone()
            if not row:
                break

            stockpile_id = int(row[0])
            take = min(remaining, float(row[1]))
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

        if remaining > 1e-9:
            label = material_label(material_code)
            raise ValueError(
                tr(
                    "error.storage.insufficient_stored_pool",
                    material=label,
                    available=f"{quantity_scu - remaining:g}",
                    requested=f"{quantity_scu:g}",
                )
            )

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

    def _transfer_from_stored_stockpiles(
        self,
        material_code: str,
        quantity_scu: float,
        created_by=None,
        *,
        stockpile_id: int | None = None,
        to_label: str | None = None,
    ) -> tuple[str, int | None]:
        """Station/Stadt → Ziel; optional nur von einer Bestandszeile."""
        remaining = float(quantity_scu)
        user_id = created_by or self._current_user_id()
        primary_source_type = "STOCKPILE"
        primary_source_id = None

        if stockpile_id is not None:
            existing = self.get_stockpile(stockpile_id)
            if not existing:
                raise ValueError(tr("error.storage.not_found"))
            if existing["material_code"] != material_code:
                raise ValueError(tr("error.storage.transfer_material_mismatch"))
            if existing["location_kind"] not in {"STATION", "CITY"}:
                raise ValueError(tr("error.storage.transfer_invalid_source"))
            if existing["status"] != "STORED":
                raise ValueError(tr("error.storage.transfer_invalid_source"))
            available = float(existing["quantity_scu"])
            if available + 1e-9 < remaining:
                raise ValueError(
                    tr(
                        "error.storage.insufficient_at_source",
                        available=f"{available:g}",
                        material=material_label(material_code),
                    )
                )
            self._reduce_stockpile_quantity(
                stockpile_id,
                remaining,
                user_id,
                to_label=to_label,
                payload={
                    "reason": "location_transfer",
                    "material_code": material_code,
                },
            )
            return ("STOCKPILE", stockpile_id)

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
            AND material_stockpiles.location_kind IN ('STATION', 'CITY')
            AND material_stockpiles.status = 'STORED'
            AND material_stockpiles.quantity_scu > 0
            ORDER BY material_stockpiles.last_activity_at ASC
            LIMIT 1
            """, (material_code,))

            row = self.cursor.fetchone()
            if not row:
                break

            source_id = int(row[0])
            available = float(row[1])
            take = min(remaining, available)

            if primary_source_id is None:
                primary_source_id = source_id

            self._reduce_stockpile_quantity(
                source_id,
                take,
                user_id,
                to_label=to_label,
                payload={
                    "reason": "location_transfer",
                    "material_code": material_code,
                },
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
            AND material_stockpiles.location_kind IN ('STATION', 'CITY')
            AND material_stockpiles.status = 'STORED'
            AND material_stockpiles.quantity_scu > 0
            """, (material_code,))

            available_row = self.cursor.fetchone()
            available = float(available_row[0] if available_row else 0)
            raise ValueError(
                tr(
                    "error.storage.insufficient_at_location",
                    available=f"{available:g}",
                    material=material_label(material_code),
                )
            )

        return (primary_source_type, primary_source_id)

    def _resolve_inbound_transfer(
        self,
        material_code: str,
        quantity_scu: float,
        *,
        target_location_kind: str,
        created_by=None,
    ) -> tuple[str, str, int | None, str]:
        user_id = created_by or self._current_user_id()
        to_label = tr("storage.event.inbound_transfer")

        if target_location_kind == "SHIP":
            attempts = (
                (
                    lambda: self._transfer_from_stored_stockpiles(
                        material_code,
                        quantity_scu,
                        user_id,
                        to_label=to_label,
                    ),
                    tr("storage.event.from_location"),
                    "LOCATION_TRANSFER",
                ),
            )
        else:
            attempts = (
                (
                    lambda: self._transfer_from_ship_stockpiles(
                        material_code,
                        quantity_scu,
                        created_by=user_id,
                    ),
                    tr("storage.event.from_ship"),
                    "SHIP_TRANSFER",
                ),
                (
                    lambda: self._transfer_from_stored_stockpiles(
                        material_code,
                        quantity_scu,
                        user_id,
                        to_label=to_label,
                    ),
                    tr("storage.event.from_location"),
                    "LOCATION_TRANSFER",
                ),
            )

        last_error: ValueError | None = None
        for resolver, from_label, transfer_key in attempts:
            try:
                source_type, source_id = resolver()
                return from_label, source_type, source_id, transfer_key
            except ValueError as error:
                last_error = error

        if last_error is not None:
            raise last_error
        raise ValueError(tr("error.storage.transfer_failed"))

    def _find_location_stockpile(
        self,
        *,
        material_code: str,
        location_kind: str,
        location_key: str | None,
        location_label: str,
        ship_id: int | None = None,
        status: str,
    ) -> tuple[int, float] | None:
        if location_kind == "SHIP":
            if ship_id is None:
                return None
            return self._find_ship_stockpile(
                material_code=material_code,
                ship_id=ship_id,
            )

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
        AND material_stockpiles.location_kind = ?
        AND material_stockpiles.status = ?
        AND material_stockpiles.quantity_scu > 0
        AND (
            (? IS NOT NULL AND material_stockpiles.location_key = ?)
            OR material_stockpiles.location_label = ?
        )
        ORDER BY material_stockpiles.last_activity_at ASC
        LIMIT 1
        """, (
            material_code,
            location_kind,
            status,
            location_key,
            location_key,
            location_label,
        ))

        row = self.cursor.fetchone()
        if not row:
            return None
        return int(row[0]), float(row[1])

    def _find_stored_stockpile_by_label(
        self,
        *,
        material_code: str,
        location_label: str,
    ) -> tuple[int, float] | None:
        """STORED-Pool an Station/Stadt per Anzeigename (kind-unabhängig)."""
        location_label = (location_label or "").strip()
        if not location_label:
            return None

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
        AND material_stockpiles.location_kind IN ('STATION', 'CITY')
        AND material_stockpiles.status = 'STORED'
        AND material_stockpiles.quantity_scu > 0
        AND material_stockpiles.location_label = ?
        ORDER BY material_stockpiles.last_activity_at ASC
        LIMIT 1
        """, (material_code, location_label))

        row = self.cursor.fetchone()
        if not row:
            return None
        return int(row[0]), float(row[1])

    def _locations_match(
        self,
        source: dict,
        *,
        location_kind: str,
        location_key: str | None,
        location_label: str,
        ship_id: int | None,
    ) -> bool:
        if source["location_kind"] == "SHIP" and location_kind == "SHIP":
            return source.get("ship_id") == ship_id

        if source["location_kind"] in {"STATION", "CITY"} and (
            location_kind in {"STATION", "CITY"}
        ):
            if (
                source.get("location_key")
                and location_key
                and source["location_key"] == location_key
            ):
                return source["location_kind"] == location_kind
            return (
                source["location_kind"] == location_kind
                and (source.get("location_label") or "").casefold()
                == location_label.casefold()
            )

        return False

    def _credit_stockpile_at_location(
        self,
        *,
        material_code: str,
        quantity_scu: float,
        location_kind: str,
        location_label: str,
        location_key: str | None,
        ship_id: int | None,
        status: str,
        from_label: str,
        source_type: str,
        source_id: int | None,
        transfer_source: str,
        event_type: str = "DEPOSIT",
        notes: str | None = None,
        reserve_tag: str | None = None,
        revert_metadata: dict | None = None,
    ) -> int:
        material_type_id = self.materials.get_material_type_id(
            material_code
        )
        now = self._now()
        user_id = self._current_user_id()

        existing = self._find_location_stockpile(
            material_code=material_code,
            location_kind=location_kind,
            location_key=location_key,
            location_label=location_label,
            ship_id=ship_id,
            status=status,
        )

        if existing:
            stockpile_id, current_qty = existing
            new_qty = current_qty + quantity_scu
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
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, datetime('now', 'localtime'), ?)
            """, (
                material_type_id,
                quantity_scu,
                location_kind,
                location_key,
                location_label,
                status,
                ship_id,
                reserve_tag,
                notes,
                now,
                user_id,
            ))
            stockpile_id = self.cursor.lastrowid

        if "storage_item_id" in self.db._table_columns(
            "material_stockpiles"
        ):
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
            event_type=event_type,
            quantity_delta=quantity_scu,
            from_label=from_label,
            to_label=location_label,
            notes=notes,
            payload={
                "material_code": material_code,
                "location_kind": location_kind,
                "status": status,
                "source": transfer_source,
                **(
                    {"revert": revert_metadata}
                    if revert_metadata
                    else {}
                ),
            },
        )

        return stockpile_id

    def transfer_stockpile(
        self,
        *,
        source_stockpile_id: int,
        quantity_scu: float,
        location_kind: str,
        location_label: str,
        location_key: str | None = None,
        ship_id: int | None = None,
    ) -> int:
        """Material von einer Bestandszeile zu Schiff/Station/Stadt verschieben."""
        if not self._table_exists():
            raise ValueError(tr("error.storage.not_available"))

        if quantity_scu <= 0:
            raise ValueError(tr("error.storage.quantity_positive"))

        location_label = (location_label or "").strip()
        if not location_label:
            raise ValueError(tr("error.storage.location_required"))

        source = self.get_stockpile(source_stockpile_id)
        if not source:
            raise ValueError(tr("error.storage.not_found"))

        if source["status"] not in {"STORED", "IN_SHIP"}:
            raise ValueError(tr("error.storage.transfer_invalid_source"))

        available = float(source["quantity_scu"])
        if available + 1e-9 < quantity_scu:
            raise ValueError(
                tr(
                    "error.storage.insufficient_at_source",
                    available=f"{available:g}",
                    material=material_label(source["material_code"]),
                )
            )

        if location_kind == "SHIP":
            status = "IN_SHIP"
            if ship_id is None:
                raise ValueError(tr("error.storage.ship_required"))
        else:
            status = "STORED"
            if location_kind not in {"STATION", "CITY"}:
                raise ValueError(tr("error.storage.location_required"))

        if self._locations_match(
            source,
            location_kind=location_kind,
            location_key=location_key,
            location_label=location_label,
            ship_id=ship_id,
        ):
            raise ValueError(tr("error.storage.transfer_same_location"))

        from_label = self.format_location(source)
        to_label = (
            tr("storage.location.ship", ship=location_label)
            if location_kind == "SHIP"
            else location_label
        )
        user_id = self._current_user_id()

        try:
            self.connection.execute("BEGIN IMMEDIATE")

            self._reduce_stockpile_quantity(
                source_stockpile_id,
                quantity_scu,
                user_id,
                to_label=to_label,
                payload={
                    "reason": "transfer",
                    "material_code": source["material_code"],
                    "target_kind": location_kind,
                },
            )

            dest_id = self._credit_stockpile_at_location(
                material_code=source["material_code"],
                quantity_scu=quantity_scu,
                location_kind=location_kind,
                location_label=location_label,
                location_key=location_key,
                ship_id=ship_id,
                status=status,
                from_label=from_label,
                source_type="STOCKPILE",
                source_id=source_stockpile_id,
                transfer_source="STOCKPILE_TRANSFER",
                event_type="TRANSFER",
            )

            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

        return dest_id

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

        try:
            self.connection.execute("BEGIN IMMEDIATE")

            from_label, source_type, source_id, transfer_source = (
                self._resolve_inbound_transfer(
                    material_code,
                    quantity_scu,
                    target_location_kind=location_kind,
                    created_by=user_id,
                )
            )

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

        resolved = lookup_location_by_label(station_label)
        if resolved:
            location_kind, location_key, location_label = resolved
        else:
            location_kind = "STATION"
            location_key = None
            location_label = station_label

        existing = self._find_location_stockpile(
            material_code=material_code,
            location_kind=location_kind,
            location_key=location_key,
            location_label=location_label,
            status="STORED",
        )
        if not existing:
            existing = self._find_stored_stockpile_by_label(
                material_code=material_code,
                location_label=location_label,
            )

        stockpile_columns = self.db._table_columns(
            "material_stockpiles"
        )

        if existing:
            stockpile_id = existing[0]
            new_qty = float(existing[1]) + quantity_scu
            updates = [
                "quantity_scu = ?",
                "location_kind = ?",
                "location_key = ?",
                "location_label = ?",
                "last_activity_at = ?",
                "idle_reminded_at = NULL",
                "updated_at = datetime('now', 'localtime')",
                "updated_by = ?",
            ]
            params: list = [
                new_qty,
                location_kind,
                location_key,
                location_label,
                now,
                user_id,
            ]
            if "refinery_job_id" in stockpile_columns:
                updates.append("refinery_job_id = ?")
                params.append(refinery_job_id)
            if session_id is not None:
                updates.append("session_id = ?")
                params.append(session_id)
            params.append(stockpile_id)
            self.cursor.execute(f"""
            UPDATE material_stockpiles
            SET {", ".join(updates)}
            WHERE id = ?
            AND is_deleted = 0
            """, params)
        else:
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
                    location_kind,
                    location_key,
                    location_label,
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
                    location_kind,
                    location_key,
                    location_label,
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
            to_label=location_label,
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

    def clear_reserve_tag(self, stockpile_id: int) -> None:
        if not self._table_exists():
            raise ValueError(tr("error.storage.not_available"))

        existing = self.get_stockpile(stockpile_id)
        if not existing:
            raise ValueError(tr("error.storage.not_found"))

        if not (existing.get("reserve_tag") or "").strip():
            raise ValueError(tr("error.storage.reserve_not_set"))

        self.cursor.execute("""
        UPDATE material_stockpiles
        SET
            reserve_tag = NULL,
            updated_at = datetime('now', 'localtime'),
            updated_by = ?
        WHERE id = ?
        AND is_deleted = 0
        """, (self._current_user_id(), stockpile_id))

        self._add_event(
            stockpile_id=stockpile_id,
            event_type="TAG_CLEAR",
            from_label=existing["location_label"],
            notes=existing.get("reserve_tag"),
            payload={
                "material_code": existing["material_code"],
                "reserve_tag": existing.get("reserve_tag"),
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

    def _load_event(self, event_id: int) -> dict | None:
        if not self.db._table_exists("material_stockpile_events"):
            return None

        self.cursor.execute("""
        SELECT
            material_stockpile_events.id,
            material_stockpile_events.stockpile_id,
            material_stockpile_events.event_type,
            material_stockpile_events.quantity_delta,
            material_stockpile_events.from_label,
            material_stockpile_events.to_label,
            material_stockpile_events.payload_json,
            material_stockpile_events.notes,
            material_stockpile_events.created_at,
            material_stockpile_events.is_deleted
        FROM material_stockpile_events
        WHERE material_stockpile_events.id = ?
        """, (event_id,))

        row = self.cursor.fetchone()
        if not row:
            return None

        payload = {}
        if row[6]:
            try:
                payload = json.loads(row[6])
            except json.JSONDecodeError:
                payload = {}

        return {
            "id": row[0],
            "stockpile_id": row[1],
            "event_type": row[2],
            "quantity_delta": row[3],
            "from_label": row[4],
            "to_label": row[5],
            "payload": payload,
            "notes": row[7],
            "created_at": row[8],
            "is_deleted": row[9],
        }

    def list_session_capture_events(
        self,
        session_id: int,
        *,
        limit: int = 50,
    ) -> list[dict]:
        if not self.db._table_exists("material_stockpile_events"):
            return []

        self.cursor.execute("""
        SELECT
            material_stockpile_events.id,
            material_stockpile_events.stockpile_id,
            material_stockpile_events.quantity_delta,
            material_stockpile_events.created_at,
            material_stockpile_events.payload_json,
            material_types.material_code
        FROM material_stockpile_events
        LEFT JOIN material_stockpiles
            ON material_stockpiles.id =
                material_stockpile_events.stockpile_id
        LEFT JOIN material_types
            ON material_types.id =
                material_stockpiles.material_type_id
        WHERE material_stockpile_events.is_deleted = 0
        AND material_stockpile_events.event_type = 'DEPOSIT'
        AND json_extract(
            material_stockpile_events.payload_json,
            '$.source'
        ) = 'SESSION_CAPTURE'
        AND CAST(json_extract(
            material_stockpile_events.payload_json,
            '$.session_id'
        ) AS INTEGER) = ?
        AND COALESCE(json_extract(
            material_stockpile_events.payload_json,
            '$.reverted'
        ), 0) = 0
        ORDER BY material_stockpile_events.id DESC
        LIMIT ?
        """, (session_id, limit))

        results = []
        for row in self.cursor.fetchall():
            payload = {}
            if row[4]:
                try:
                    payload = json.loads(row[4])
                except json.JSONDecodeError:
                    payload = {}

            material_code = (
                payload.get("material_code")
                or row[5]
                or "—"
            )
            results.append({
                "id": row[0],
                "stockpile_id": row[1],
                "quantity_scu": float(row[2] or 0),
                "created_at": row[3],
                "material_code": material_code,
                "batch_id": payload.get("batch_id"),
                "session_id": payload.get("session_id"),
            })

        return results

    def _reduce_ship_stockpile_capture(
        self,
        *,
        stockpile_id: int,
        quantity_scu: float,
        batch_id: int,
        material_code: str,
        user_id,
    ) -> None:
        entry = self.get_stockpile(stockpile_id)
        if not entry:
            raise ValueError(tr("error.storage.not_found"))

        current_qty = float(entry.get("quantity_scu") or 0)
        if current_qty + 1e-9 < quantity_scu:
            raise ValueError(tr("error.material.storage_changed"))

        new_qty = current_qty - quantity_scu
        now = self._now()

        if new_qty <= 1e-9:
            self.cursor.execute("""
            UPDATE material_stockpiles
            SET
                quantity_scu = 0,
                is_deleted = 1,
                deleted_at = datetime('now', 'localtime'),
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

        self.cursor.execute("""
        SELECT storage_item_id
        FROM material_stockpiles
        WHERE id = ?
        """, (stockpile_id,))
        storage_row = self.cursor.fetchone()
        storage_item_id = (
            storage_row[0] if storage_row else None
        )
        if storage_item_id:
            self.materials._deduct_storage_row(
                storage_item_id,
                quantity_scu,
                updated_by=user_id,
            )

    def undo_session_capture_event(
        self,
        event_id: int,
        *,
        updated_by=None,
    ) -> None:
        event = self._load_event(event_id)
        if not event or event.get("is_deleted"):
            raise ValueError(tr("error.storage.event_not_found"))

        payload = event.get("payload") or {}
        if payload.get("source") != "SESSION_CAPTURE":
            raise ValueError(
                tr("error.correction.capture_not_reversible")
            )

        if payload.get("reverted"):
            raise ValueError(
                tr("error.correction.already_reverted")
            )

        batch_id = payload.get("batch_id")
        session_id = payload.get("session_id")
        material_code = payload.get("material_code")
        quantity_scu = float(event.get("quantity_delta") or 0)

        if (
            not batch_id
            or not session_id
            or not material_code
            or quantity_scu <= 0
        ):
            raise ValueError(
                tr("error.correction.capture_not_reversible")
            )

        user_id = updated_by or self._current_user_id()
        stockpile_id = event.get("stockpile_id")

        try:
            self.connection.execute("BEGIN IMMEDIATE")

            self.materials.reduce_session_capture(
                int(batch_id),
                quantity_scu,
                updated_by=user_id,
            )

            if stockpile_id:
                self._reduce_ship_stockpile_capture(
                    stockpile_id=int(stockpile_id),
                    quantity_scu=quantity_scu,
                    batch_id=int(batch_id),
                    material_code=material_code,
                    user_id=user_id,
                )

            payload["reverted"] = True
            self.cursor.execute("""
            UPDATE material_stockpile_events
            SET
                payload_json = ?,
                notes = COALESCE(notes, '') ||
                    CASE
                        WHEN notes IS NULL OR TRIM(notes) = ''
                        THEN ?
                        ELSE char(10) || ?
                    END
            WHERE id = ?
            """, (
                json.dumps(payload, ensure_ascii=False),
                tr("storage.event.reverted_note"),
                tr("storage.event.reverted_note"),
                event_id,
            ))

            self._add_event(
                stockpile_id=stockpile_id,
                event_type="REVERT",
                quantity_delta=-quantity_scu,
                from_label=event.get("to_label"),
                to_label=tr("storage.event.session_salvage"),
                payload={
                    "reverts_event_id": event_id,
                    "source": "SESSION_CAPTURE_UNDO",
                    "material_code": material_code,
                    "session_id": session_id,
                    "batch_id": batch_id,
                },
            )

            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def revert_stockpile_event(
        self,
        event_id: int,
        *,
        updated_by=None,
    ) -> None:
        event = self._load_event(event_id)
        if not event or event.get("is_deleted"):
            raise ValueError(tr("error.storage.event_not_found"))

        payload = event.get("payload") or {}
        if payload.get("reverted"):
            raise ValueError(
                tr("error.correction.already_reverted")
            )

        event_type = event.get("event_type")
        user_id = updated_by or self._current_user_id()

        if event_type == "DEPOSIT" and (
            payload.get("source") == "SESSION_CAPTURE"
        ):
            self.undo_session_capture_event(
                event_id,
                updated_by=user_id,
            )
            return

        revert_info = payload.get("revert")
        if not revert_info:
            raise ValueError(
                tr("error.correction.event_not_reversible")
            )

        quantity_scu = abs(
            float(
                revert_info.get("quantity_scu")
                or event.get("quantity_delta")
                or 0
            )
        )
        if quantity_scu <= 0:
            raise ValueError(
                tr("error.correction.event_not_reversible")
            )

        try:
            self.connection.execute("BEGIN IMMEDIATE")

            if event_type == "TRANSFER":
                dest_id = event.get("stockpile_id")
                if not dest_id:
                    raise ValueError(
                        tr("error.correction.event_not_reversible")
                    )

                source_pool = revert_info.get("source_pool")
                if not isinstance(source_pool, dict):
                    raise ValueError(
                        tr("error.correction.event_not_reversible")
                    )

                self._reduce_stockpile_quantity(
                    int(dest_id),
                    quantity_scu,
                    user_id,
                    to_label=event.get("from_label") or "—",
                    payload={
                        "reason": "transfer_revert",
                        "reverts_event_id": event_id,
                    },
                )

                if source_pool.get("pool_kind") == "SHIP":
                    ship_id = source_pool.get("ship_id")
                    ship_name = source_pool.get("ship_name") or "—"
                    self._credit_stockpile_at_location(
                        material_code=source_pool["material_code"],
                        quantity_scu=quantity_scu,
                        location_kind="SHIP",
                        location_key=str(ship_id) if ship_id else None,
                        location_label=ship_name,
                        ship_id=ship_id,
                        status="IN_SHIP",
                        from_label=event.get("to_label") or "—",
                        source_type="STOCKPILE",
                        source_id=dest_id,
                        transfer_source="TRANSFER_REVERT",
                        event_type="REVERT",
                    )
                else:
                    self._credit_stockpile_at_location(
                        material_code=source_pool["material_code"],
                        quantity_scu=quantity_scu,
                        location_kind=source_pool.get(
                            "location_kind"
                        ),
                        location_key=source_pool.get(
                            "location_key"
                        ),
                        location_label=source_pool.get(
                            "location_label"
                        )
                        or "—",
                        ship_id=None,
                        status="STORED",
                        from_label=event.get("to_label") or "—",
                        source_type="STOCKPILE",
                        source_id=dest_id,
                        transfer_source="TRANSFER_REVERT",
                        event_type="REVERT",
                    )

            elif event_type == "WITHDRAW":
                source_pool = revert_info.get("source_pool")
                if not isinstance(source_pool, dict):
                    raise ValueError(
                        tr("error.correction.event_not_reversible")
                    )

                if source_pool.get("pool_kind") == "SHIP":
                    ship_id = source_pool.get("ship_id")
                    ship_name = source_pool.get("ship_name") or "—"
                    self._credit_stockpile_at_location(
                        material_code=source_pool["material_code"],
                        quantity_scu=quantity_scu,
                        location_kind="SHIP",
                        location_key=str(ship_id) if ship_id else None,
                        location_label=ship_name,
                        ship_id=ship_id,
                        status="IN_SHIP",
                        from_label=event.get("to_label") or "—",
                        source_type="STOCKPILE",
                        source_id=None,
                        transfer_source="WITHDRAW_REVERT",
                        event_type="REVERT",
                    )
                else:
                    self._credit_stockpile_at_location(
                        material_code=source_pool["material_code"],
                        quantity_scu=quantity_scu,
                        location_kind=source_pool.get(
                            "location_kind"
                        ),
                        location_key=source_pool.get(
                            "location_key"
                        ),
                        location_label=source_pool.get(
                            "location_label"
                        )
                        or "—",
                        ship_id=None,
                        status="STORED",
                        from_label=event.get("to_label") or "—",
                        source_type="STOCKPILE",
                        source_id=None,
                        transfer_source="WITHDRAW_REVERT",
                        event_type="REVERT",
                    )
            else:
                raise ValueError(
                    tr("error.correction.event_not_reversible")
                )

            payload["reverted"] = True
            self.cursor.execute("""
            UPDATE material_stockpile_events
            SET payload_json = ?
            WHERE id = ?
            """, (
                json.dumps(payload, ensure_ascii=False),
                event_id,
            ))

            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

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

    def list_material_pools(
        self,
        *,
        raw_cm_only: bool = False,
    ) -> list[dict]:
        """Aggregierte Material-Pools (Schiff oder Lager) für Raffinerie/Transfer."""
        if not self._table_exists():
            return []

        from config.materials import RAW_CM_MATERIAL_CODES

        material_filter = ""
        params: list = []
        if raw_cm_only:
            placeholders = ", ".join("?" * len(RAW_CM_MATERIAL_CODES))
            material_filter = (
                f"AND material_types.material_code IN ({placeholders})"
            )
            params.extend(RAW_CM_MATERIAL_CODES)

        pools: list[dict] = []

        self.cursor.execute(f"""
        SELECT
            material_types.material_code,
            material_stockpiles.ship_id,
            COALESCE(ships.ship_name, material_stockpiles.location_label),
            COALESCE(SUM(material_stockpiles.quantity_scu), 0)
        FROM material_stockpiles
        INNER JOIN material_types
            ON material_types.id =
                material_stockpiles.material_type_id
        LEFT JOIN ships
            ON ships.id = material_stockpiles.ship_id
        WHERE material_stockpiles.is_deleted = 0
        AND material_stockpiles.quantity_scu > 0
        AND material_stockpiles.location_kind = 'SHIP'
        AND material_stockpiles.status = 'IN_SHIP'
        {material_filter}
        GROUP BY
            material_types.material_code,
            material_stockpiles.ship_id,
            ships.ship_name,
            material_stockpiles.location_label
        ORDER BY ships.ship_name, material_types.material_code
        """, params)

        for code, ship_id, ship_name, qty in self.cursor.fetchall():
            if float(qty or 0) <= 0:
                continue
            pools.append({
                "pool_kind": "SHIP",
                "material_code": code,
                "quantity_scu": float(qty),
                "ship_id": ship_id,
                "ship_name": ship_name or "—",
                "location_kind": "SHIP",
                "location_key": str(ship_id) if ship_id else None,
                "location_label": ship_name or "—",
            })

        self.cursor.execute(f"""
        SELECT
            material_types.material_code,
            material_stockpiles.location_kind,
            material_stockpiles.location_key,
            material_stockpiles.location_label,
            COALESCE(SUM(material_stockpiles.quantity_scu), 0)
        FROM material_stockpiles
        INNER JOIN material_types
            ON material_types.id =
                material_stockpiles.material_type_id
        WHERE material_stockpiles.is_deleted = 0
        AND material_stockpiles.quantity_scu > 0
        AND material_stockpiles.location_kind IN ('STATION', 'CITY')
        AND material_stockpiles.status = 'STORED'
        {material_filter}
        GROUP BY
            material_types.material_code,
            material_stockpiles.location_kind,
            material_stockpiles.location_key,
            material_stockpiles.location_label
        ORDER BY material_stockpiles.location_label, material_types.material_code
        """, params)

        for (
            code,
            loc_kind,
            loc_key,
            loc_label,
            qty,
        ) in self.cursor.fetchall():
            if float(qty or 0) <= 0:
                continue
            pools.append({
                "pool_kind": "STORED",
                "material_code": code,
                "quantity_scu": float(qty),
                "ship_id": None,
                "ship_name": None,
                "location_kind": loc_kind,
                "location_key": loc_key,
                "location_label": loc_label or "—",
            })

        return pools

    def session_ids_for_pool(self, pool: dict) -> list[int]:
        """Session-IDs, die Material in diesem Pool liefern (auch nach Sitzungsende)."""
        if not pool or not self._table_exists():
            return []

        material_code = pool.get("material_code")
        if not material_code:
            return []

        session_ids: set[int] = set()
        pool_kind = pool.get("pool_kind")

        if pool_kind == "SHIP" and pool.get("ship_id"):
            ship_id = int(pool["ship_id"])
            if hasattr(self.db, "materials"):
                for session_id in (
                    self.db.materials.session_ids_for_ship_material(
                        material_code,
                        ship_id,
                    )
                ):
                    session_ids.add(session_id)

            self.cursor.execute("""
            SELECT DISTINCT ms.session_id
            FROM material_stockpiles ms
            INNER JOIN material_types mt
                ON mt.id = ms.material_type_id
            WHERE ms.is_deleted = 0
            AND ms.ship_id = ?
            AND ms.session_id IS NOT NULL
            AND ms.quantity_scu > 0
            AND mt.material_code = ?
            """, (ship_id, material_code))
            for row in self.cursor.fetchall():
                if row[0]:
                    session_ids.add(int(row[0]))

        elif pool_kind == "STORED":
            loc_kind = pool.get("location_kind")
            loc_key = pool.get("location_key")
            if loc_kind and loc_key is not None:
                self.cursor.execute("""
                SELECT DISTINCT ms.session_id
                FROM material_stockpiles ms
                INNER JOIN material_types mt
                    ON mt.id = ms.material_type_id
                WHERE ms.is_deleted = 0
                AND ms.location_kind = ?
                AND ms.location_key = ?
                AND ms.session_id IS NOT NULL
                AND ms.quantity_scu > 0
                AND mt.material_code = ?
                """, (
                    loc_kind,
                    str(loc_key),
                    material_code,
                ))
                for row in self.cursor.fetchall():
                    if row[0]:
                        session_ids.add(int(row[0]))

        return sorted(session_ids)

    def _pool_quantity(self, pool: dict) -> float:
        if not self._table_exists():
            return 0.0

        material_code = pool.get("material_code")
        if not material_code:
            return 0.0

        if pool.get("pool_kind") == "SHIP":
            ship_id = pool.get("ship_id")
            if ship_id is None:
                return 0.0
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
            AND material_stockpiles.ship_id = ?
            """, (material_code, ship_id))
        else:
            self.cursor.execute("""
            SELECT COALESCE(SUM(material_stockpiles.quantity_scu), 0)
            FROM material_stockpiles
            INNER JOIN material_types
                ON material_types.id =
                    material_stockpiles.material_type_id
            WHERE material_stockpiles.is_deleted = 0
            AND material_types.material_code = ?
            AND material_stockpiles.location_kind = ?
            AND material_stockpiles.status = 'STORED'
            AND material_stockpiles.location_key = ?
            """, (
                material_code,
                pool.get("location_kind"),
                pool.get("location_key"),
            ))

        row = self.cursor.fetchone()
        return float(row[0] if row else 0)

    def _withdraw_from_pool(
        self,
        pool: dict,
        quantity_scu: float,
        *,
        to_label: str,
        payload: dict | None = None,
        created_by=None,
    ) -> None:
        if quantity_scu <= 0:
            raise ValueError(tr("error.storage.quantity_positive"))

        material_code = pool["material_code"]
        remaining = float(quantity_scu)
        user_id = created_by or self._current_user_id()

        if pool.get("pool_kind") == "SHIP":
            ship_id = pool.get("ship_id")
            ship_filter = ""
            params: list = [material_code]
            if ship_id is not None:
                ship_filter = "AND material_stockpiles.ship_id = ?"
                params.append(ship_id)

            while remaining > 1e-9:
                self.cursor.execute(f"""
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
                {ship_filter}
                ORDER BY material_stockpiles.last_activity_at ASC
                LIMIT 1
                """, params)
                row = self.cursor.fetchone()
                if not row:
                    break
                stockpile_id = int(row[0])
                take = min(remaining, float(row[1]))
                event_payload = {
                    **(payload or {}),
                    "revert": {
                        "source_pool": dict(pool),
                        "quantity_scu": take,
                    },
                }
                self._reduce_stockpile_quantity(
                    stockpile_id,
                    take,
                    user_id,
                    to_label=to_label,
                    payload=event_payload,
                )
                remaining -= take
        else:
            loc_kind = pool.get("location_kind")
            loc_key = pool.get("location_key")
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
                AND material_stockpiles.location_kind = ?
                AND material_stockpiles.status = 'STORED'
                AND material_stockpiles.location_key = ?
                AND material_stockpiles.quantity_scu > 0
                ORDER BY material_stockpiles.last_activity_at ASC
                LIMIT 1
                """, (material_code, loc_kind, loc_key))
                row = self.cursor.fetchone()
                if not row:
                    break
                stockpile_id = int(row[0])
                take = min(remaining, float(row[1]))
                event_payload = {
                    **(payload or {}),
                    "revert": {
                        "source_pool": dict(pool),
                        "quantity_scu": take,
                    },
                }
                self._reduce_stockpile_quantity(
                    stockpile_id,
                    take,
                    user_id,
                    to_label=to_label,
                    payload=event_payload,
                )
                remaining -= take

        if remaining > 1e-9:
            label = material_label(material_code)
            raise ValueError(
                tr(
                    "error.storage.insufficient_pool",
                    material=label,
                    available=f"{quantity_scu - remaining:g}",
                    requested=f"{quantity_scu:g}",
                )
            )

    def withdraw_from_material_pool(
        self,
        pool: dict,
        quantity_scu: float,
        *,
        created_by=None,
    ) -> None:
        """Material aus Pool entnehmen (FIFO über zugrundeliegende Zeilen)."""
        if not self._table_exists():
            raise ValueError(tr("error.storage.not_available"))

        try:
            self.connection.execute("BEGIN IMMEDIATE")
            available = self._pool_quantity(pool)
            if quantity_scu > available + 1e-9:
                label = material_label(pool.get("material_code", ""))
                raise ValueError(
                    tr(
                        "error.storage.insufficient_pool",
                        material=label,
                        available=f"{available:g}",
                        requested=f"{quantity_scu:g}",
                    )
                )

            location = pool.get("location_label") or "—"
            if pool.get("ship_name"):
                location = tr(
                    "storage.location.ship",
                    ship=pool["ship_name"],
                )

            self._withdraw_from_pool(
                pool,
                quantity_scu,
                to_label=tr("storage.event.withdrawn"),
                payload={
                    "reason": "pool_withdraw",
                    "material_code": pool.get("material_code"),
                },
                created_by=created_by,
            )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def transfer_from_material_pool(
        self,
        pool: dict,
        quantity_scu: float,
        *,
        location_kind: str,
        location_key: str | None,
        location_label: str,
        ship_id: int | None = None,
        created_by=None,
    ) -> int:
        """Material aus Pool an Ziel verschieben (FIFO)."""
        if not self._table_exists():
            raise ValueError(tr("error.storage.not_available"))

        material_code = pool.get("material_code")
        if not material_code:
            raise ValueError(tr("error.storage.not_found"))

        try:
            self.connection.execute("BEGIN IMMEDIATE")
            available = self._pool_quantity(pool)
            if quantity_scu > available + 1e-9:
                label = material_label(material_code)
                raise ValueError(
                    tr(
                        "error.storage.insufficient_pool",
                        material=label,
                        available=f"{available:g}",
                        requested=f"{quantity_scu:g}",
                    )
                )

            source_label = pool.get("location_label") or "—"
            if pool.get("ship_name"):
                source_label = tr(
                    "storage.location.ship",
                    ship=pool["ship_name"],
                )

            self._withdraw_from_pool(
                pool,
                quantity_scu,
                to_label=location_label,
                payload={
                    "reason": "pool_transfer",
                    "material_code": material_code,
                    "destination": location_label,
                },
                created_by=created_by,
            )

            dest_id = self._credit_stockpile_at_location(
                material_code=material_code,
                quantity_scu=quantity_scu,
                location_kind=location_kind,
                location_key=location_key,
                location_label=location_label,
                ship_id=ship_id,
                status="IN_SHIP" if location_kind == "SHIP" else "STORED",
                from_label=source_label,
                source_type="STOCKPILE",
                source_id=None,
                transfer_source="POOL_TRANSFER",
                event_type="TRANSFER",
                revert_metadata={
                    "quantity_scu": quantity_scu,
                    "source_pool": dict(pool),
                },
            )
            self.connection.commit()
            return dest_id
        except Exception:
            self.connection.rollback()
            raise

    def migrate_orphan_storage_into_stockpiles(self) -> int:
        """
        Verwaiste storage_items (ohne Stockpile-Verknüpfung) bereinigen:
        - Phantome (Stockpile existiert bereits) → storage auf 0
        - Echte Waisen → Stockpile-Zeile mit Verknüpfung anlegen
        """
        if not self._table_exists():
            return 0

        if "storage_item_id" not in self.db._table_columns(
            "material_stockpiles"
        ):
            return 0

        self.cursor.execute("""
        SELECT
            storage_items.id,
            storage_items.material_type_id,
            material_types.material_code,
            storage_items.quantity,
            storage_items.source_type,
            storage_items.source_id
        FROM storage_items
        INNER JOIN material_types
            ON material_types.id =
                storage_items.material_type_id
        WHERE storage_items.is_deleted = 0
        AND storage_items.quantity > 0
        AND storage_items.id NOT IN (
            SELECT material_stockpiles.storage_item_id
            FROM material_stockpiles
            WHERE material_stockpiles.storage_item_id IS NOT NULL
            AND material_stockpiles.is_deleted = 0
        )
        ORDER BY storage_items.id ASC
        """)

        orphans = self.cursor.fetchall()
        if not orphans:
            return 0

        migrated = 0
        now = self._now()

        for (
            storage_id,
            material_type_id,
            material_code,
            quantity,
            source_type,
            source_id,
        ) in orphans:
            qty = float(quantity or 0)
            if qty <= 0:
                continue

            self.cursor.execute("""
            SELECT COALESCE(SUM(material_stockpiles.quantity_scu), 0)
            FROM material_stockpiles
            INNER JOIN material_types
                ON material_types.id =
                    material_stockpiles.material_type_id
            WHERE material_stockpiles.is_deleted = 0
            AND material_stockpiles.quantity_scu > 0
            AND material_types.material_code = ?
            """, (material_code,))

            stockpile_total = float(self.cursor.fetchone()[0] or 0)

            if stockpile_total > 1e-9:
                self.materials._deduct_storage_row(
                    storage_id,
                    qty,
                )
                migrated += 1
                continue

            location_kind = "STATION"
            location_key = None
            location_label = "Legacy Import"
            status = "STORED"
            ship_id = None
            session_id = None

            if source_type == "SESSION" and source_id:
                self.cursor.execute("""
                SELECT session_id
                FROM material_batches
                WHERE id = ?
                AND is_deleted = 0
                """, (source_id,))
                batch_row = self.cursor.fetchone()
                if batch_row and batch_row[0]:
                    session_id = batch_row[0]
                    ship = self.db.get_session_ship(session_id)
                    if ship:
                        location_kind = "SHIP"
                        location_key = str(ship["ship_id"])
                        location_label = ship["ship_name"]
                        status = "IN_SHIP"
                        ship_id = ship["ship_id"]

            elif source_type == "REFINERY" and source_id:
                self.cursor.execute("""
                SELECT station
                FROM refinery_jobs
                WHERE id = ?
                """, (source_id,))
                job_row = self.cursor.fetchone()
                if job_row and job_row[0]:
                    location_label = (job_row[0] or "").strip() or location_label
                    resolved = lookup_location_by_label(location_label)
                    if resolved:
                        location_kind, location_key, location_label = resolved

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
                storage_item_id,
                last_activity_at,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
            """, (
                material_type_id,
                qty,
                location_kind,
                location_key,
                location_label,
                status,
                ship_id,
                session_id,
                storage_id,
                now,
            ))
            migrated += 1

        if migrated:
            self.connection.commit()

        return migrated

    def sync_unlinked_stockpile_storage_ledgers(self) -> int:
        """Stockpile-Zeilen ohne storage_item_id an verknüpftes Ledger anbinden."""
        if not self._table_exists():
            return 0

        if "storage_item_id" not in self.db._table_columns(
            "material_stockpiles"
        ):
            return 0

        self.cursor.execute("""
        SELECT
            material_stockpiles.id,
            material_stockpiles.material_type_id,
            material_stockpiles.quantity_scu
        FROM material_stockpiles
        WHERE material_stockpiles.is_deleted = 0
        AND material_stockpiles.quantity_scu > 0
        AND (
            material_stockpiles.storage_item_id IS NULL
            OR material_stockpiles.storage_item_id = 0
        )
        """)

        rows = self.cursor.fetchall()
        if not rows:
            return 0

        user_id = self._current_user_id()
        synced = 0

        for stockpile_id, material_type_id, quantity_scu in rows:
            self._ensure_stockpile_storage_item(
                int(stockpile_id),
                int(material_type_id),
                float(quantity_scu),
                user_id,
                source_type="STOCKPILE",
                source_id=int(stockpile_id),
            )
            synced += 1

        if synced:
            self.connection.commit()

        return synced

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
