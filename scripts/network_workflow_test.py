"""
Host-Client Workflow-Test (RPC-Schicht, ohne GUI).

Simuliert den Materialfluss über execute_rpc mit Gast-Benutzer,
wie er vom Client aus ausgeführt wird.
"""
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config.paths as paths

_test_data = Path(tempfile.mkdtemp(prefix="sst_net_flow_"))
paths.data_dir = lambda: _test_data

from database.database import Database
from network.rpc_executor import execute_rpc
from network.rpc_registry import build_guest_user
from config.materials import REFINERY_OUTPUT_CODE


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


def rpc(db, guest, path, *args, **kwargs):
    return execute_rpc(db, guest, path, list(args), kwargs)


def main():
    db = Database()
    guest = build_guest_user("Crew-Tester")

    # --- Host: Session (admin-Kontext simuliert lokal) ---
    session_id = db.create_session(
        None,
        "Vulture",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        created_by=1,
    )
    db.add_crew_member(session_id, "Pilot-A")
    db.add_crew_member(session_id, "Gast-Client")
    db.end_session(session_id)

    session_id2 = db.create_session(
        None,
        "Reclaimer",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        created_by=1,
    )
    db.add_crew_member(session_id2, "Pilot-A")

    # --- Client (Gast): Material zur aktiven Sitzung ---
    active = rpc(db, guest, "get_active_session")
    assert active is not None, "Gast sieht aktive Host-Sitzung"
    assert_eq("active session ship", active[1], "Reclaimer")

    rpc(db, guest, "add_material", session_id2, "RMC", 50)
    rpc(db, guest, "add_material", session_id2, "CM_RUBBLE", 40)

    rpc(db, guest, "end_session", session_id2)

    batches = rpc(db, guest, "get_available_refinery_batches")
    assert_eq("refinery batches", len(batches), 1)
    batch_id = batches[0]["batch_id"]

    # --- Client: Raffinerie ---
    end_time = (
        datetime.now() - timedelta(minutes=1)
    ).strftime("%Y-%m-%d %H:%M:%S")
    job_id = rpc(
        db,
        guest,
        "create_refinery_job_from_batches",
        "Orison",
        end_time,
        [{"batch_id": batch_id, "input_quantity": 30}],
    )
    result = rpc(db, guest, "complete_refinery_job", job_id, 25)
    assert_close("refinery output", result["output_quantity"], 25)

    # --- Client: Verkauf ---
    sale_id = rpc(
        db,
        guest,
        "record_storage_sale",
        "Area18",
        datetime.now().strftime("%Y-%m-%d"),
        "RMC",
        30,
        1000,
    )
    assert sale_id > 0

    sale_id2 = rpc(
        db,
        guest,
        "record_storage_sale",
        "Area18",
        datetime.now().strftime("%Y-%m-%d"),
        REFINERY_OUTPUT_CODE,
        25,
        800,
    )
    assert sale_id2 > 0

    # --- Client: Auszahlung ---
    proposal = rpc(db, guest, "calculate_payout_proposal", sale_id)
    assert_close("payout revenue", proposal["revenue"], 30000)

    payout_id = rpc(
        db,
        guest,
        "create_payout",
        sale_id,
        proposal["items"],
    )
    assert payout_id > 0

    print("=" * 60)
    print("NETWORK WORKFLOW TEST: OK")
    print(f"  Session #{session_id2} (Material vom Gast)")
    print(f"  Refinery job #{job_id} -> 25 SCU CM")
    print(f"  Sales #{sale_id}, #{sale_id2}")
    print(f"  Payout #{payout_id}")
    print(f"  Test DB: {_test_data}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        raise
