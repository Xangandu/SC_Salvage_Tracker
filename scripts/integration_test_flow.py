"""
End-to-end workflow test:
Session -> material_batches/storage -> refinery -> storage(CM) -> sale -> profit
"""
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config.paths as paths

_test_data = Path(tempfile.mkdtemp(prefix="sst_flow_test_"))
paths.data_dir = lambda: _test_data

from database.database import Database
from config.materials import (
    REFINED_SELLABLE_CODES,
    RAW_CM_MATERIAL_CODES,
    REFINERY_OUTPUT_CODE,
)


def assert_eq(label, got, expected):
    if got != expected:
        raise AssertionError(
            f"{label}: expected {expected!r}, got {got!r}"
        )


def assert_close(label, got, expected, tol=0.01):
    if abs(got - expected) > tol:
        raise AssertionError(
            f"{label}: expected ~{expected}, got {got}"
        )


def main():
    db = Database()

    # --- Session ---
    session_id = db.create_session(
        None,
        "Drake Vulture",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        created_by=1,
    )
    db.add_crew_member(session_id, "Pilot-A")
    db.add_crew_member(session_id, "Gunner-B")
    db.add_cost(session_id, "Mission", 5000, "Pilot-A")

    db.add_material(session_id, "RMC", 100)
    db.add_material(session_id, "CM_RUBBLE", 80)
    db.end_session(session_id)

    batches = db.get_available_refinery_batches()
    assert_eq("refinery batches count", len(batches), 1)
    batch_id = batches[0]["batch_id"]
    assert_close(
        "batch remaining",
        batches[0]["remaining_quantity"],
        80,
    )

    inv = db.get_available_storage_inventory()
    inv_map = {i["material_code"]: i["quantity"] for i in inv}
    assert_close("sales inventory RMC", inv_map.get("RMC", 0), 100)
    assert_eq(
        "raw not in sales inventory",
        "CM_RUBBLE" in inv_map,
        False,
    )
    assert_close(
        "storage CM_RUBBLE (warehouse)",
        db.materials.get_storage_balance("CM_RUBBLE"),
        80,
    )

    # --- Refinery job ---
    end_time = (
        datetime.now() - timedelta(minutes=1)
    ).strftime("%Y-%m-%d %H:%M:%S")

    job_id = db.create_refinery_job_from_batches(
        "Orison",
        end_time,
        [{"batch_id": batch_id, "input_quantity": 50}],
        cost=500,
        cost_paid_by="Gunner-B",
    )

    batches_after = db.get_available_refinery_batches()
    assert_close(
        "batch remaining after reserve",
        batches_after[0]["remaining_quantity"],
        30,
    )

    inv_after_ref = db.materials.get_storage_balance(
        "CM_RUBBLE"
    )
    assert_close(
        "storage CM_RUBBLE after reserve",
        inv_after_ref,
        30,
    )

    result = db.complete_refinery_job(job_id, 35)
    assert_close("refinery output", result["output_quantity"], 35)

    inv_after_complete = {
        i["material_code"]: i["quantity"]
        for i in db.get_available_storage_inventory()
    }
    assert_close(
        "storage CM after refinery",
        inv_after_complete.get("CM", 0),
        35,
    )
    assert_close(
        "storage RMC unchanged",
        inv_after_complete.get("RMC", 0),
        100,
    )

    # --- Sales ---
    sale_id = db.record_storage_sale(
        "Area18",
        datetime.now().strftime("%Y-%m-%d"),
        "RMC",
        40,
        1000,
    )
    assert sale_id > 0

    inv_after_sale = {
        i["material_code"]: i["quantity"]
        for i in db.get_available_storage_inventory()
    }
    assert_close(
        "storage RMC after sale",
        inv_after_sale.get("RMC", 0),
        60,
    )

    sale_id2 = db.record_storage_sale(
        "Area18",
        datetime.now().strftime("%Y-%m-%d"),
        REFINERY_OUTPUT_CODE,
        35,
        800,
    )
    assert sale_id2 > 0

    # --- Payout (sale 1: RMC only from session) ---
    proposal = db.calculate_payout_proposal(sale_id)
    assert proposal["session_ids"] == [session_id]
    assert_close("payout revenue", proposal["revenue"], 40000)
    assert_close("payout costs", proposal["total_costs"], 5000)
    assert_close(
        "payout distributed",
        proposal["distributed_total"],
        40000,
    )

    payout_id = db.create_payout(
        sale_id,
        proposal["items"],
    )
    assert payout_id > 0
    assert_eq(
        "sale marked paid",
        db.payouts.sale_has_payout(sale_id),
        True,
    )

    proposal2 = db.calculate_payout_proposal(sale_id2)
    assert_close("payout2 revenue", proposal2["revenue"], 28000)
    assert_close(
        "payout2 costs (refinery)",
        proposal2["total_costs"],
        500,
    )
    assert_close(
        "payout2 distributed",
        proposal2["distributed_total"],
        28000,
    )

    payout_id2 = db.create_payout(
        sale_id2,
        proposal2["items"],
    )
    assert payout_id2 > 0

    paid_total = db.get_total_payouts_value()
    assert_close("total payouts", paid_total, 68000)

    # --- Financials ---
    revenue = db.get_total_sales_value()
    costs = db.get_global_total_costs()
    profit = db.get_total_profit()

    assert_close("revenue", revenue, 40 * 1000 + 35 * 800)
    assert_close("costs", costs, 5500)
    assert_close("profit", profit, revenue - costs)

    # --- Dashboard CM (potential bug check) ---
    global_cm = db.get_global_refined_cm_total()
    session_cm = db.get_refined_cm_total(session_id)

    # --- Sales inventory sellable filter check ---
    sellable_in_inv = {
        i["material_code"]
        for i in db.get_available_storage_inventory()
    }
    raw_in_sales = sellable_in_inv & set(RAW_CM_MATERIAL_CODES)

    print("=" * 60)
    print("INTEGRATION TEST: CORE FLOW OK")
    print(f"  Session #{session_id}")
    print(f"  Refinery job #{job_id} -> 35 SCU CM")
    print(f"  Sales #{sale_id}, #{sale_id2}")
    print(f"  Revenue: {revenue:,.0f} aUEC")
    print(f"  Costs:   {costs:,.0f} aUEC")
    print(f"  Profit:  {profit:,.0f} aUEC")
    print("-" * 60)
    print("POTENTIAL ISSUES:")
    print(
        f"  Dashboard global CM (material_batches): {global_cm} "
        f"(storage CM: {inv_after_sale.get('CM', 0)})"
    )
    print(
        f"  Dashboard session CM (material_batches): {session_cm}"
    )
    assert_close("global CM total", global_cm, 35)
    assert_close("session CM total", session_cm, 35)
    assert_eq("raw in sales inventory", raw_in_sales, set())

    refunds = db.get_cost_refunds(session_id)
    print(f"  get_cost_refunds rows: {len(refunds)}")

    ready_count = db.get_ready_for_sale_count()
    print(
        f"  sellable storage SCU (dashboard LAGER): "
        f"{ready_count:g}"
    )

    print("=" * 60)
    print(f"Test DB: {_test_data}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        raise
