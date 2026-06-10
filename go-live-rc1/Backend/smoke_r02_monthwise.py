"""
smoke_r02_monthwise.py — runs r02_monthwise_extension against the REAL R02
workbook. Gates:
  1. POSITIVE  — planned targets + Q1 achievement emitted with full lineage;
                 NS ~52%, Dues ~100%, Advance ~98% vs planned; composite =
                 worst category (NS).
  2. NEGATIVE  — workbook copy with 'Monthwise MDO' removed: every extension
                 key is None/unavailable; validation fails; no exception;
                 no fabricated number.
  3. ADDITIVE  — pre-existing metrics/lineage keys are never touched.
  4. CONTRACT  — every lineage record carries the full required field set.

Usage: python smoke_r02_monthwise.py /path/to/R02_*.xlsx
"""
import shutil
import sys
import tempfile
from pathlib import Path

from openpyxl import load_workbook

from r02_monthwise_extension import extend_r02_with_monthwise

REQUIRED_LINEAGE_FIELDS = [
    "metric_key", "metric_label", "value", "unit", "source_code", "source_file",
    "sheet", "cell_or_range", "snapshot_date", "extraction_method",
    "entity_scope", "business_definition", "validation_status",
    "confidence_state", "last_loaded_at", "reporting_basis",
]


class StubResult:
    """Duck-typed AdapterResult stand-in with pre-existing keys."""
    def __init__(self):
        self.metrics = {"may_total_collections_target_group": 1.0,
                        "_sections_detected": {"group": {}}}
        self.lineage = {"may_total_collections_target_group": {"value": 1.0}}
        self.validations = {"R02_REQUIRED_SECTIONS_PRESENT": {"passed": True}}
        self.warnings = []
        self.errors = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    return bool(cond)


def main(path: Path) -> int:
    ok = True
    M = 1e6

    # ---------------- 1. POSITIVE ----------------
    res = StubResult()
    pre_metrics = dict(res.metrics)
    pre_lineage = dict(res.lineage)
    extend_r02_with_monthwise(res, path, loaded_at="smoke")

    g = lambda k: res.metrics.get(k)
    print("\n== POSITIVE: extracted values ==")
    for k in sorted(res.metrics):
        if k.startswith("_"):
            continue
        if k in pre_metrics:
            continue
        v = res.metrics[k]
        disp = f"{v/M:,.2f}M" if isinstance(v, float) and abs(v) > 1e4 else v
        print(f"   {k} = {disp}")

    ok &= check("Monthwise sheet present validation",
                res.validations.get("R02_MONTHWISE_SHEET_PRESENT", {}).get("passed") is True)

    pq1_ns = g("planned_ns_target_q1_group")
    ok &= check("planned Q1 NS target ~1,097.1M",
                pq1_ns is not None and abs(pq1_ns - 1_097_104_425) / 1_097_104_425 < 0.01
                if pq1_ns else False,
                f"got {pq1_ns/M:,.1f}M" if pq1_ns else "None")

    ns = g("q1_achievement_planned_ns_pct_group")
    ok &= check("Q1 NS achievement vs planned in [51,54]%",
                ns is not None and 51 <= ns <= 54, f"got {ns}%")
    dues = g("q1_achievement_planned_dues_pct_group")
    ok &= check("Q1 Dues achievement vs planned in [99,101]%",
                dues is not None and 99 <= dues <= 101, f"got {dues}%")
    adv = g("q1_achievement_planned_advance_pct_group")
    ok &= check("Q1 Advance achievement vs planned in [96,100]%",
                adv is not None and 96 <= adv <= 100, f"got {adv}%")

    comp = g("q1_mdo_achievement_by_category")
    ok &= check("composite = worst category (== NS pct)",
                comp is not None and comp == ns, f"composite {comp} vs ns {ns}")

    # cross-check achievement against independent recompute
    act = g("q1_ns_actual_monthwise_group")
    if act and pq1_ns:
        recomputed = round(act / pq1_ns * 100, 1)
        ok &= check("NS pct equals independent recompute", recomputed == ns,
                    f"{recomputed} vs {ns}")

    ok &= check("Q1 internal consistency (Q1 col == Jan+Feb+Mar)",
                res.validations.get("R02_MONTHWISE_Q1_INTERNAL_CONSISTENCY", {}).get("passed") is True)
    parity = res.validations.get("R02_PLANNED_VS_DYNAMIC_FY_PARITY", {})
    pdetail = parity.get("detail", {})
    ok &= check("FY parity ran and dues parity holds",
                pdetail.get("dues", {}).get("passed") is True,
                f"dues planned/dynamic {pdetail.get('dues')}")
    diverged = sorted(k for k, v in pdetail.items() if v.get("passed") is False)
    ok &= check("FY divergence DISCLOSED for revised categories (adv/ns/total)",
                set(diverged) >= {"advance", "ns", "total_collections"},
                f"diverged={diverged} — Dynamic revises future-month targets; "
                "disclosed, never silently reconciled")
    ok &= check("basis-gap disclosure present",
                res.validations.get("R02_PLANNED_BASIS_GAP_DISCLOSED", {}).get("disclosed") is True)

    # ---------------- 4. CONTRACT ----------------
    print("\n== CONTRACT: lineage completeness ==")
    new_lineage = {k: v for k, v in res.lineage.items() if k not in pre_lineage}
    missing_any = []
    for k, rec in new_lineage.items():
        missing = [f for f in REQUIRED_LINEAGE_FIELDS if f not in rec]
        if missing:
            missing_any.append((k, missing))
    ok &= check(f"all {len(new_lineage)} new lineage records carry full contract",
                not missing_any, str(missing_any[:3]))
    valued = [k for k, v in res.metrics.items()
              if not k.startswith("_") and k not in pre_metrics and v is not None]
    unlineaged = [k for k in valued if k not in res.lineage]
    ok &= check("every valued metric has lineage", not unlineaged, str(unlineaged))
    bad_conf = [k for k, v in res.metrics.items()
                if not k.startswith("_") and k not in pre_metrics and v is None
                and res.lineage.get(k, {}).get("confidence_state") != "unavailable"]
    ok &= check("every None metric is marked unavailable (no silent state)",
                not bad_conf, str(bad_conf))

    # ---------------- 3. ADDITIVE ----------------
    print("\n== ADDITIVE: regression ==")
    ok &= check("pre-existing metrics untouched",
                all(res.metrics[k] == v for k, v in pre_metrics.items()))
    ok &= check("pre-existing lineage untouched",
                all(res.lineage[k] == v for k, v in pre_lineage.items()))
    ok &= check("pre-existing validations untouched",
                res.validations.get("R02_REQUIRED_SECTIONS_PRESENT", {}).get("passed") is True)

    # ---------------- 2. NEGATIVE ----------------
    print("\n== NEGATIVE: Monthwise sheet removed ==")
    with tempfile.TemporaryDirectory() as td:
        crippled = Path(td) / "R02_no_monthwise.xlsx"
        shutil.copy(path, crippled)
        wb = load_workbook(crippled)
        del wb["Monthwise MDO"]
        wb.save(crippled)

        nres = StubResult()
        try:
            extend_r02_with_monthwise(nres, crippled, loaded_at="smoke")
            no_raise = True
        except Exception as exc:
            no_raise = False
            print("   raised:", exc)
        ok &= check("no exception on missing sheet", no_raise)
        ok &= check("sheet-present validation FAILED",
                    nres.validations.get("R02_MONTHWISE_SHEET_PRESENT", {}).get("passed") is False)
        new_keys = [k for k in nres.metrics
                    if not k.startswith("_") and k not in ("may_total_collections_target_group",)]
        fabricated = [k for k in new_keys if nres.metrics[k] is not None]
        ok &= check("no fabricated numbers (all extension keys None)",
                    not fabricated, str(fabricated))
        not_unavail = [k for k in new_keys
                       if nres.lineage.get(k, {}).get("confidence_state") != "unavailable"]
        ok &= check("all extension lineage marked unavailable", not not_unavail,
                    str(not_unavail[:5]))

    print("\n" + ("SMOKE: ALL GATES GREEN" if ok else "SMOKE: FAILURES PRESENT"))
    return 0 if ok else 1


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("R02_MDO_report_06-05-2026.xlsx")
    sys.exit(main(src))
