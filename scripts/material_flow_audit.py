"""
Vollständiger Materialfluss-Audit:
Session (3 Runs) -> Raffinerie -> Verkauf -> Auszahlung

Prüft an jedem Schritt mehrere Zähler gegeneinander und sammelt Abweichungen.
"""
from __future__ import annotations

import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config.paths as paths

_test_data = Path(tempfile.mkdtemp(prefix="sst_material_audit_"))
_redirect = lambda _td=_test_data: _td  # noqa: E731
paths.data_dir = _redirect
import database.database as _db_mod

_db_mod.data_dir = _redirect

from config.materials import (  # noqa: E402
    RAW_CM_MATERIAL_CODES,
    REFINED_SELLABLE_CODES,
    REFINERY_OUTPUT_CODE,
)
from database.dashboard_operations_repository import (  # noqa: E402
    DashboardOperationsRepository,
)
from database.database import Database  # noqa: E402


TOL = 0.01


@dataclass
class MaterialSnapshot:
    step: str
    stockpile_rows: list[dict] = field(default_factory=list)
    stockpile_totals: dict[str, float] = field(default_factory=dict)
    batch_global: dict[str, float] = field(default_factory=dict)
    storage_items: dict[str, float] = field(default_factory=dict)
    sellable_inventory: dict[str, float] = field(default_factory=dict)
    dashboard_materials: dict[str, float] = field(default_factory=dict)
    orphan_storage: dict[str, float] = field(default_factory=dict)
    duplicate_locations: list[str] = field(default_factory=list)
    session_id: int | None = None
    session_status: str | None = None

    def fmt(self) -> str:
        lines = [f"\n=== {self.step} ==="]
        if self.session_id:
            lines.append(
                f"  Session #{self.session_id} status={self.session_status}"
            )
        lines.append(f"  Stockpile-Totals: {self._fmt_map(self.stockpile_totals)}")
        lines.append(f"  Batches (global): {self._fmt_map(self.batch_global)}")
        lines.append(f"  storage_items:    {self._fmt_map(self.storage_items)}")
        lines.append(
            f"  Verkauf-Inventar: {self._fmt_map(self.sellable_inventory)}"
        )
        lines.append(
            f"  Dashboard-Mat.:   {self._fmt_map(self.dashboard_materials)}"
        )
        if self.orphan_storage:
            lines.append(
                f"  ⚠ Waisen storage_items: {self._fmt_map(self.orphan_storage)}"
            )
        if self.duplicate_locations:
            lines.append(
                f"  ⚠ Duplikat-Standorte: {self.duplicate_locations}"
            )
        if self.stockpile_rows:
            lines.append("  Lager-Zeilen:")
            for row in self.stockpile_rows:
                loc = row.get("location_label") or row.get("ship_name") or "?"
                lines.append(
                    f"    #{row['id']} {row['material_code']} "
                    f"{row['quantity_scu']:g} SCU "
                    f"[{row['location_kind']}/{row.get('location_key')}] "
                    f"status={row['status']} @ {loc}"
                )
        return "\n".join(lines)

    @staticmethod
    def _fmt_map(data: dict[str, float]) -> str:
        if not data:
            return "—"
        return ", ".join(f"{k}={v:g}" for k, v in sorted(data.items()))


@dataclass
class Issue:
    step: str
    severity: str  # BUG, WARN, INFO
    message: str


class MaterialFlowAuditor:
    def __init__(self, db: Database):
        self.db = db
        self.issues: list[Issue] = []
        self.snapshots: list[MaterialSnapshot] = []

    def snap(self, step: str, session_id: int | None = None) -> MaterialSnapshot:
        snapshot = self._capture(step, session_id)
        self.snapshots.append(snapshot)
        self._check_invariants(snapshot)
        return snapshot

    def _capture(
        self,
        step: str,
        session_id: int | None,
    ) -> MaterialSnapshot:
        rows = self.db.list_material_stockpiles()
        totals = {
            entry["material_code"]: float(entry["quantity_scu"])
            for entry in self.db.get_stockpile_totals()
        }
        batch_global = {
            code: float(self.db.get_global_batch_available(code) or 0)
            for code in list(RAW_CM_MATERIAL_CODES) + list(REFINED_SELLABLE_CODES)
        }
        storage = {
            row[0]: float(row[1])
            for row in (self.db.materials.get_storage_balance() or [])
        }
        sellable = {
            entry["material_code"]: float(entry["quantity"])
            for entry in self.db.get_available_storage_inventory()
        }
        dash = DashboardOperationsRepository(self.db)._build_materials()

        orphan = self._orphan_storage()
        duplicates = self._duplicate_location_labels(rows)

        status = None
        if session_id:
            self.db.cursor.execute(
                "SELECT status FROM sessions WHERE id = ?",
                (session_id,),
            )
            row = self.db.cursor.fetchone()
            status = row[0] if row else None

        return MaterialSnapshot(
            step=step,
            stockpile_rows=rows,
            stockpile_totals=totals,
            batch_global=batch_global,
            storage_items=storage,
            sellable_inventory=sellable,
            dashboard_materials=dash,
            orphan_storage=orphan,
            duplicate_locations=duplicates,
            session_id=session_id,
            session_status=status,
        )

    def _orphan_storage(self) -> dict[str, float]:
        """storage_items ohne Stockpile-Verknüpfung (Legacy/Waisen)."""
        if not self.db._table_exists("material_stockpiles"):
            return {}
        self.db.cursor.execute("""
        SELECT
            material_types.material_code,
            COALESCE(SUM(storage_items.quantity), 0)
        FROM storage_items
        INNER JOIN material_types
            ON material_types.id = storage_items.material_type_id
        WHERE storage_items.is_deleted = 0
        AND storage_items.quantity > 0
        AND storage_items.id NOT IN (
            SELECT material_stockpiles.storage_item_id
            FROM material_stockpiles
            WHERE material_stockpiles.storage_item_id IS NOT NULL
            AND material_stockpiles.is_deleted = 0
        )
        GROUP BY material_types.material_code
        """)
        return {row[0]: float(row[1]) for row in self.db.cursor.fetchall()}

    def _duplicate_location_labels(self, rows: list[dict]) -> list[str]:
        """Gleicher Anzeigename + Material, unterschiedlicher kind/key."""
        seen: dict[tuple, set] = {}
        for row in rows:
            if row.get("status") not in {"STORED", "IN_SHIP"}:
                continue
            label = (
                row.get("location_label")
                or row.get("ship_name")
                or ""
            ).strip()
            material = row.get("material_code")
            key = (
                row.get("location_kind"),
                row.get("location_key"),
                label,
                material,
            )
            pool = (label.casefold(), material)
            seen.setdefault(pool, set()).add(key)

        dups = []
        for (label, material), keys in seen.items():
            if len(keys) > 1:
                dups.append(f"{material}@{label} ({len(keys)} Zeilen)")
        return dups

    def _check_invariants(self, s: MaterialSnapshot) -> None:
        # Stockpile-Totals = Summe der Zeilen
        summed: dict[str, float] = {}
        for row in s.stockpile_rows:
            code = row["material_code"]
            summed[code] = summed.get(code, 0) + float(row["quantity_scu"])
        for code, total in s.stockpile_totals.items():
            if abs(total - summed.get(code, 0)) > TOL:
                self._bug(
                    s.step,
                    f"Stockpile-Totals {code}: DB={total:g}, "
                    f"Zeilen-Summe={summed.get(code, 0):g}",
                )

        # Verkauf-Inventar = physische sellable Stockpiles
        for code in REFINED_SELLABLE_CODES:
            sellable = self.db.stockpiles.sellable_quantity(code)
            inv = s.sellable_inventory.get(code, 0)
            if abs(inv - sellable) > TOL:
                self._bug(
                    s.step,
                    f"Verkauf-Inventar {code}: angezeigt={inv:g}, "
                    f"sellable={sellable:g}",
                )

        # Dashboard RMC/CM vs Verkauf-Inventar
        for code in ("RMC", "CM"):
            dash = s.dashboard_materials.get(code, 0)
            inv = s.sellable_inventory.get(code, 0)
            if abs(dash - inv) > TOL:
                self._warn(
                    s.step,
                    f"Dashboard {code}={dash:g} ≠ Verkauf-Inventar {code}={inv:g}",
                )

        # Waisen storage_items
        for code, qty in s.orphan_storage.items():
            if qty > TOL:
                self._warn(
                    s.step,
                    f"Waisen storage_items {code}={qty:g} SCU "
                    f"(nicht mit Lagerzeile verknüpft)",
                )

        # Duplikat-Standorte
        for dup in s.duplicate_locations:
            self._bug(s.step, f"Doppelter Lager-Pool: {dup}")

        # storage_items Gesamt vs verknüpft — grobe Prüfung
        linked_mismatch = self._linked_storage_mismatch()
        for msg in linked_mismatch:
            self._warn(s.step, msg)

    def _linked_storage_mismatch(self) -> list[str]:
        msgs = []
        if not self.db._table_exists("material_stockpiles"):
            return msgs
        self.db.cursor.execute("""
        SELECT
            material_stockpiles.id,
            material_types.material_code,
            material_stockpiles.quantity_scu,
            storage_items.quantity,
            material_stockpiles.location_label,
            material_stockpiles.status
        FROM material_stockpiles
        INNER JOIN material_types
            ON material_types.id = material_stockpiles.material_type_id
        INNER JOIN storage_items
            ON storage_items.id = material_stockpiles.storage_item_id
        WHERE material_stockpiles.is_deleted = 0
        AND storage_items.is_deleted = 0
        AND material_stockpiles.quantity_scu > 0
        AND ABS(material_stockpiles.quantity_scu - storage_items.quantity) > 0.01
        """)
        for row in self.db.cursor.fetchall():
            msgs.append(
                f"Stockpile #{row[0]} {row[1]} Lager={row[2]:g} SCU "
                f"≠ storage_item={row[3]:g} @ {row[4]} ({row[5]})"
            )
        return msgs

    def _bug(self, step: str, message: str) -> None:
        self.issues.append(Issue(step, "BUG", message))

    def _warn(self, step: str, message: str) -> None:
        self.issues.append(Issue(step, "WARN", message))

    def _info(self, step: str, message: str) -> None:
        self.issues.append(Issue(step, "INFO", message))

    def check_session_ship_parity(
        self,
        step: str,
        session_id: int,
        materials: dict[str, float],
    ) -> None:
        """Batch-Summe auf Schiff = Stockpile auf Schiff."""
        for code, expected in materials.items():
            batch_qty = float(
                self.db.get_session_batch_available(session_id, code) or 0
            )
            ship_qty = sum(
                float(r["quantity_scu"])
                for r in self.db.list_material_stockpiles(material_code=code)
                if r.get("status") == "IN_SHIP"
                and r.get("session_id") == session_id
            )
            if abs(batch_qty - expected) > TOL:
                self._warn(
                    step,
                    f"Session-Batch {code}: erwartet {expected:g}, "
                    f"batch_available={batch_qty:g}",
                )
            if abs(ship_qty - expected) > TOL:
                self._bug(
                    step,
                    f"Schiff-Stockpile {code}: erwartet {expected:g}, "
                    f"auf Schiff={ship_qty:g}, batch={batch_qty:g}",
                )


def run_full_scenario() -> MaterialFlowAuditor:
    db = Database()
    audit = MaterialFlowAuditor(db)

    ship = "Aegis Reclaimer"
    runs = [
        {"RMC": 120, "CM_SALVAGE": 100},
        {"RMC": 85, "CM_SALVAGE": 70},
        {"RMC": 95, "CM_SALVAGE": 90},
    ]
    totals = {"RMC": 0.0, "CM_SALVAGE": 0.0}
    for run in runs:
        for code, qty in run.items():
            totals[code] += qty

    audit.snap("00 — Start (leer)")

    session_id = db.create_session(
        None,
        ship,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        created_by=1,
    )
    db.add_crew_member(session_id, "Kapitän")
    db.add_crew_member(session_id, "Salvager-1")
    db.add_crew_member(session_id, "Salvager-2")
    db.add_cost(session_id, "Treibstoff", 8000, "Kapitän")
    db.add_cost(session_id, "Verschleiß", 3500, "Org-Kasse")

    for index, run in enumerate(runs, start=1):
        for code, qty in run.items():
            db.add_material(session_id, code, qty)
        audit.snap(f"0{index} — Run {index} erfasst", session_id)
        audit.check_session_ship_parity(
            f"Run {index}",
            session_id,
            {
                code: sum(
                    runs[i][code]
                    for i in range(index)
                )
                for code in totals
            },
        )

    db.end_session(session_id)
    audit.snap("04 — Session beendet", session_id)

    # --- Raffinerie: gesamtes Roh-CM verarbeiten ---
    batches = db.get_available_refinery_batches()
    raw_batch = next(
        (b for b in batches if b.get("input_material") == "CM_SALVAGE"),
        batches[0] if batches else None,
    )
    if not raw_batch:
        audit._bug("Raffinerie", "Keine Raffinerie-Batches verfügbar")
        return audit

    batch_id = raw_batch["batch_id"]
    input_qty = float(raw_batch["remaining_quantity"])

    end_time = (
        datetime.now() - timedelta(minutes=1)
    ).strftime("%Y-%m-%d %H:%M:%S")

    job_id = db.create_refinery_job_from_batches(
        "Orison",
        end_time,
        [{"batch_id": batch_id, "input_quantity": input_qty}],
        cost=1200,
        cost_paid_by="Kapitän",
        refinery_method="Bulk",
    )
    audit.snap("05 — Raffinerie-Job gestartet", session_id)

    cm_output = round(input_qty * 0.72)
    result = db.complete_refinery_job(job_id, cm_output)
    audit.snap("06 — Raffinerie abgeschlossen", session_id)

    audit._info(
        "Raffinerie",
        f"Input {input_qty:g} CM_SALVAGE -> Output {result['output_quantity']:g} CM",
    )

    # CM sollte an Orison liegen; RMC noch auf Schiff
    cm_at_orison = sum(
        float(r["quantity_scu"])
        for r in db.list_material_stockpiles(material_code="CM")
        if (r.get("location_label") or "").casefold() == "orison"
    )
    if abs(cm_at_orison - cm_output) > TOL:
        audit._bug(
            "Nach Raffinerie",
            f"CM an Orison: erwartet {cm_output:g}, gefunden {cm_at_orison:g} "
            f"(Stockpile-Totals CM={audit.snapshots[-1].stockpile_totals.get('CM', 0):g})",
        )

    # --- Verkauf alles ---
    rmc_qty = totals["RMC"]
    sale_rmc = db.record_storage_sale(
        "Area18",
        datetime.now().strftime("%Y-%m-%d"),
        "RMC",
        rmc_qty,
        950,
    )
    audit.snap("07 — RMC verkauft", session_id)

    sale_cm = db.record_storage_sale(
        "Area18",
        datetime.now().strftime("%Y-%m-%d"),
        REFINERY_OUTPUT_CODE,
        cm_output,
        820,
    )
    audit.snap("08 — CM verkauft", session_id)

    # Nach Verkauf: nichts mehr verkaufbar
    remaining = db.get_available_storage_inventory()
    if remaining:
        audit._bug(
            "Nach Verkauf",
            f"Noch verkaufbar: {remaining}",
        )

    remaining_stock = db.get_stockpile_totals()
    sellable_stock = {
        code: db.stockpiles.sellable_quantity(code)
        for code in REFINED_SELLABLE_CODES
    }
    if any(v > TOL for v in sellable_stock.values()):
        audit._bug(
            "Nach Verkauf",
            f"Sellable Stockpiles noch > 0: {sellable_stock}",
        )
    if remaining_stock:
        audit._warn(
            "Nach Verkauf",
            f"Lager-Totals noch > 0 (nicht verkaufbar?): {remaining_stock}",
        )

    # --- Auszahlungen ---
    for sale_id, label in ((sale_rmc, "RMC"), (sale_cm, "CM")):
        proposal = db.calculate_payout_proposal(sale_id)
        payout_id = db.create_payout(sale_id, proposal["items"])
        audit._info(
            "Auszahlung",
            f"{label} Sale #{sale_id} -> Payout #{payout_id}, "
            f"Revenue {proposal['revenue']:,.0f}, "
            f"Costs {proposal['total_costs']:,.0f}",
        )

    audit.snap("09 — Auszahlungen erstellt", session_id)

    # Session-Status
    db.cursor.execute(
        "SELECT status FROM sessions WHERE id = ?",
        (session_id,),
    )
    final_status = db.cursor.fetchone()[0]
    if final_status != "SOLD":
        audit._warn(
            "Session-Status",
            f"Session #{session_id} Status={final_status} (erwartet SOLD)",
        )

    # Finanzen
    revenue = db.get_total_sales_value()
    costs = db.get_global_total_costs()
    profit = db.get_total_profit()
    expected_revenue = rmc_qty * 950 + cm_output * 820
    expected_costs = 8000 + 3500 + 1200
    audit._info(
        "Finanzen",
        f"Umsatz {revenue:,.0f} (erw. {expected_revenue:,.0f}), "
        f"Kosten {costs:,.0f} (erw. {expected_costs:,.0f}), "
        f"Gewinn {profit:,.0f}",
    )
    if abs(revenue - expected_revenue) > 1:
        audit._bug("Finanzen", f"Umsatz falsch: {revenue} vs {expected_revenue}")
    if abs(costs - expected_costs) > 1:
        audit._bug("Finanzen", f"Kosten falsch: {costs} vs {expected_costs}")

    # Dashboard CM (material_batches-Historie vs Lager)
    global_cm = float(db.get_global_refined_cm_total() or 0)
    if abs(global_cm - cm_output) > TOL:
        audit._warn(
            "Dashboard",
            f"get_global_refined_cm_total={global_cm:g} "
            f"(Raffinerie-Output war {cm_output:g}) — "
            f"Historischer Wert, nicht physisches Lager",
        )

    audit.snap("10 — Ende", session_id)
    return audit


def main() -> int:
    audit = run_full_scenario()

    print("=" * 72)
    print("MATERIALFLUSS-AUDIT — Vollständiger Durchlauf")
    print(f"Test-DB: {_test_data}")
    print("=" * 72)

    for snapshot in audit.snapshots:
        print(snapshot.fmt())

    bugs = [i for i in audit.issues if i.severity == "BUG"]
    warns = [i for i in audit.issues if i.severity == "WARN"]
    infos = [i for i in audit.issues if i.severity == "INFO"]

    print("\n" + "=" * 72)
    print(f"BEFUNDE: {len(bugs)} BUG(s), {len(warns)} WARNUNG(en), {len(infos)} Info")
    print("=" * 72)

    for issue in bugs + warns:
        print(f"  [{issue.severity}] ({issue.step}) {issue.message}")

    if infos:
        print("\n--- Info ---")
        for issue in infos:
            print(f"  ({issue.step}) {issue.message}")

    if bugs:
        print("\n❌ AUDIT FEHLGESCHLAGEN — Bugs gefunden")
        return 1

    if warns:
        print("\n⚠ AUDIT MIT WARNUNGEN — bitte prüfen")
        return 0

    print("\nAUDIT OK - kein Materialfehler im Happy Path")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
