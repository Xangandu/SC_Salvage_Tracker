"""Randfälle für Materialfluss — ergänzt material_flow_audit.py."""
from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config.paths as paths

from config.materials import REFINERY_OUTPUT_CODE
from database.database import Database


def _fresh_db(prefix: str) -> Database:
    td = Path(tempfile.mkdtemp(prefix=prefix))
    redirect = lambda _td=td: _td  # noqa: E731
    paths.data_dir = redirect
    import database.database as db_mod

    db_mod.data_dir = redirect
    Database.close_all_connections()
    return Database()


def test_orphan_storage_after_refinery_merge() -> list[str]:
    """CM existiert schon — Raffinerie bucht dazu, keine Doppelzählung."""
    issues: list[str] = []
    db = _fresh_db("sst_edge_orphan_")

    db.cursor.execute("""
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
    job_id = db.cursor.lastrowid

    db.stockpiles._credit_stockpile_at_location(
        material_code="CM",
        quantity_scu=300,
        location_kind="CITY",
        location_label="Orison",
        location_key="ORISON",
        ship_id=None,
        status="STORED",
        from_label="Altbestand",
        source_type="SESSION",
        source_id=1,
        transfer_source="TEST",
    )
    db.connection.commit()

    db.stockpiles.deposit_refinery_pickup(
        material_code=REFINERY_OUTPUT_CODE,
        quantity_scu=300,
        station_label="Orison",
        refinery_job_id=job_id,
    )
    db.connection.commit()

    stockpile_cm = sum(
        float(r["quantity_scu"])
        for r in db.list_material_stockpiles(material_code="CM")
    )
    sellable = db.stockpiles.sellable_quantity("CM")
    inventory = sum(
        e["quantity"]
        for e in db.get_available_storage_inventory()
        if e["material_code"] == "CM"
    )
    rows = db.list_material_stockpiles(material_code="CM")

    if len(rows) != 1:
        issues.append(
            f"ORPHAN-MERGE: {len(rows)} CM-Zeilen statt 1 "
            f"(Stockpile-Summe {stockpile_cm:g})"
        )
    if abs(stockpile_cm - 600) > 0.01:
        issues.append(
            f"ORPHAN-MERGE: Stockpile CM={stockpile_cm:g} (erw. 600)"
        )
    if abs(inventory - stockpile_cm) > 0.01:
        issues.append(
            f"ORPHAN-MERGE: Verkauf-Inventar CM={inventory:g} "
            f"!= physisches Lager {stockpile_cm:g} "
            f"(sellable={sellable:g})"
        )

    try:
        db.record_storage_sale(
            "Area18",
            datetime.now().strftime("%Y-%m-%d"),
            "CM",
            600,
            800,
        )
        after = db.get_available_storage_inventory()
        if after:
            issues.append(
                f"ORPHAN-MERGE: Nach Verkauf von 600 SCU noch "
                f"verkaufbar: {after}"
            )
    except Exception as exc:
        issues.append(f"ORPHAN-MERGE: Verkauf 600 SCU fehlgeschlagen: {exc}")

    return issues


def test_station_city_split() -> list[str]:
    issues: list[str] = []
    db = _fresh_db("sst_edge_split_")

    mt = db.materials.get_material_type_id("CM")
    db.cursor.execute("""
    INSERT INTO material_stockpiles (
        material_type_id, quantity_scu, location_kind, location_key,
        location_label, status, last_activity_at, created_at
    )
    VALUES (?, 300, 'STATION', NULL, 'Orison', 'STORED',
        datetime('now', 'localtime'), datetime('now', 'localtime'))
    """, (mt,))

    db.cursor.execute("""
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
    job_id = db.cursor.lastrowid

    db.stockpiles.deposit_refinery_pickup(
        material_code=REFINERY_OUTPUT_CODE,
        quantity_scu=300,
        station_label="Orison",
        refinery_job_id=job_id,
    )
    db.connection.commit()

    rows = db.list_material_stockpiles(material_code="CM")
    total = sum(float(r["quantity_scu"]) for r in rows)

    if len(rows) > 1:
        issues.append(
            f"CITY/SPLIT: {len(rows)} CM-Zeilen an Orison "
            f"(Summe {total:g})"
        )
    if abs(total - 600) > 0.01:
        issues.append(f"CITY/SPLIT: Summe {total:g} (erw. 600)")

    return issues


def test_pool_refinery_vulture() -> list[str]:
    issues: list[str] = []
    db = _fresh_db("sst_edge_pool_")

    sid = db.create_session(
        None,
        "Drake Vulture",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        created_by=1,
    )
    db.add_material(sid, "CM_RUBBLE", 150)
    db.add_material(sid, "RMC", 50)
    db.end_session(sid)

    pools = db.list_material_pools()
    rubble_pool = next(
        p for p in pools
        if p["material_code"] == "CM_RUBBLE"
    )

    end_time = (
        datetime.now() - timedelta(minutes=1)
    ).strftime("%Y-%m-%d %H:%M:%S")
    job_id = db.create_refinery_job_from_pool(
        "Area18",
        end_time,
        pool=rubble_pool,
        input_quantity=150,
    )
    db.complete_refinery_job(job_id, 105)
    db.connection.commit()

    cm_total = sum(
        float(r["quantity_scu"])
        for r in db.list_material_stockpiles(material_code="CM")
    )
    if abs(cm_total - 105) > 0.01:
        issues.append(
            f"POOL: CM nach Raffinerie {cm_total:g} (erw. 105)"
        )

    db.record_storage_sale(
        "Area18",
        datetime.now().strftime("%Y-%m-%d"),
        "RMC",
        50,
        900,
    )
    db.record_storage_sale(
        "Area18",
        datetime.now().strftime("%Y-%m-%d"),
        "CM",
        105,
        800,
    )

    if db.get_available_storage_inventory():
        issues.append("POOL: Nach Verkauf noch inventar")

    if db.get_stockpile_totals():
        issues.append(
            f"POOL: Nach Verkauf Lager-Totals: {db.get_stockpile_totals()}"
        )

    return issues


def main() -> int:
    all_issues: list[tuple[str, list[str]]] = [
        ("Orphan nach Raffinerie-Merge", test_orphan_storage_after_refinery_merge()),
        ("STATION/CITY Split", test_station_city_split()),
        ("Pool-Raffinerie Vulture", test_pool_refinery_vulture()),
    ]

    print("=" * 72)
    print("MATERIALFLUSS — RANDFAELLE (Stockpile-only)")
    print("=" * 72)

    bug_count = 0
    for name, issues in all_issues:
        print(f"\n--- {name} ---")
        if issues:
            bug_count += len(issues)
            for msg in issues:
                print(f"  BUG: {msg}")
        else:
            print("  OK")

    print("\n" + "=" * 72)
    print(f"Gesamt: {bug_count} Problem(e)")
    return 1 if bug_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
