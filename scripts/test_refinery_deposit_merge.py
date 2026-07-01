"""Prüft: Raffinerie-Abholung merged mit bestehendem CITY-Pool (kein STATION-Duplikat)."""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config.paths as paths

_test_data = Path(tempfile.mkdtemp(prefix="sst_refinery_merge_"))
paths.data_dir = lambda: _test_data

from config.materials import REFINERY_OUTPUT_CODE
from database.database import Database


def main() -> None:
    db = Database()
    db.cursor.execute("""
    INSERT INTO refinery_jobs (
        station,
        start_time,
        status,
        created_at
    )
    VALUES (
        'Orison',
        datetime('now', 'localtime'),
        'COMPLETED',
        datetime('now', 'localtime')
    )
    """)
    job_id = db.cursor.lastrowid

    db.stockpiles._credit_stockpile_at_location(
        material_code="CM",
        quantity_scu=300,
        location_kind="CITY",
        location_label="Orison",
        location_key="ORISON",
        ship_id=None,
        status="STORED",
        from_label="Test",
        source_type="SESSION",
        source_id=1,
        transfer_source="TEST",
    )
    db.stockpiles.deposit_refinery_pickup(
        material_code=REFINERY_OUTPUT_CODE,
        quantity_scu=300,
        station_label="Orison",
        refinery_job_id=job_id,
    )
    db.connection.commit()

    rows = [
        row
        for row in db.list_material_stockpiles()
        if row["material_code"] == "CM"
    ]
    total = sum(float(row["quantity_scu"]) for row in rows)

    if len(rows) != 1:
        raise SystemExit(
            f"FAIL: expected 1 CM row, got {len(rows)}: {rows}"
        )
    if abs(total - 600) > 1e-6:
        raise SystemExit(f"FAIL: expected 600 SCU total, got {total}")
    if rows[0]["location_kind"] != "CITY":
        raise SystemExit(
            f"FAIL: expected CITY kind, got {rows[0]['location_kind']}"
        )

    print("OK: refinery deposit merged into existing CITY pool")

    # Legacy-Bug: alte STATION-Zeile ohne location_key
    db2_dir = Path(tempfile.mkdtemp(prefix="sst_refinery_legacy_"))
    paths.data_dir = lambda: db2_dir
    db2 = Database()
    db2.cursor.execute("""
    INSERT INTO refinery_jobs (
        station, start_time, status, created_at
    )
    VALUES (
        'Orison',
        datetime('now', 'localtime'),
        'COMPLETED',
        datetime('now', 'localtime')
    )
    """)
    job_id2 = db2.cursor.lastrowid
    material_type_id = db2.materials.get_material_type_id("CM")
    db2.cursor.execute("""
    INSERT INTO material_stockpiles (
        material_type_id,
        quantity_scu,
        location_kind,
        location_key,
        location_label,
        status,
        last_activity_at,
        created_at
    )
    VALUES (?, 300, 'STATION', NULL, 'Orison', 'STORED',
        datetime('now', 'localtime'), datetime('now', 'localtime'))
    """, (material_type_id,))
    db2.stockpiles.deposit_refinery_pickup(
        material_code=REFINERY_OUTPUT_CODE,
        quantity_scu=300,
        station_label="Orison",
        refinery_job_id=job_id2,
    )
    db2.connection.commit()
    legacy_rows = [
        row
        for row in db2.list_material_stockpiles()
        if row["material_code"] == "CM"
    ]
    legacy_total = sum(
        float(row["quantity_scu"]) for row in legacy_rows
    )
    if len(legacy_rows) != 1 or abs(legacy_total - 600) > 1e-6:
        raise SystemExit(
            f"FAIL legacy merge: {len(legacy_rows)} rows, {legacy_total} SCU"
        )
    print("OK: legacy STATION row merged on refinery pickup")


if __name__ == "__main__":
    main()
