"""SCIP Batch 2 smoke tests for R04 Finance daily and R02 MDO adapters."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import source_adapters

ROOT = Path(__file__).resolve().parent
DATA = ROOT.parent
R04_PATH = DATA / "R04_Total Daily Collection Report 07-05-2026.xlsx"
R02_PATH = DATA / "R02_MDO report 06-05-2026.xlsx"
TOL = 0.0005


def passed(validations: Dict[str, Dict[str, Any]]) -> bool:
    return all(v.get("passed", False) for v in validations.values())


def approx(a: float, b: float, pct: float = TOL) -> Dict[str, Any]:
    diff = abs(float(a) - float(b))
    tolerance = abs(float(b)) * pct
    return {"passed": diff <= tolerance, "left": a, "right": b, "diff": diff, "tolerance_aed": tolerance, "tolerance_pct": pct}


def main() -> Dict[str, Any]:
    r04 = source_adapters.run_adapter("R04", R04_PATH).to_dict()
    r02 = source_adapters.run_adapter("R02", R02_PATH).to_dict()

    r04m = r04["metrics"]
    r02m = r02["metrics"]

    batch_checks = {
        "R04_adapter_status_ok": {"passed": r04["status"] == "ok", "status": r04["status"]},
        "R04_all_native_validations_passed": {"passed": passed(r04["validations"]), "failed": [k for k, v in r04["validations"].items() if not v.get("passed")]},
        "R04_MTD_DA_PLUS_NS_EQUALS_TOTAL": approx((r04m["mtd_da_total"] or 0) + (r04m["mtd_ns_total"] or 0), r04m["mtd_total_collections"]),
        "R04_lineage_present_for_mtd_da": {"passed": "mtd_da_total" in r04["lineage"], "lineage": r04["lineage"].get("mtd_da_total")},
        "R04_advance_split_explicitly_unavailable": {"passed": r04m.get("mtd_advance_total") is None and r04m.get("mtd_advance_status") == "unavailable_in_R04_no_advance_split", "status": r04m.get("mtd_advance_status")},
        "R02_adapter_status_ok": {"passed": r02["status"] == "ok", "status": r02["status"]},
        "R02_all_native_validations_passed": {"passed": passed(r02["validations"]), "failed": [k for k, v in r02["validations"].items() if not v.get("passed")]},
        "R02_may_dues_target_has_lineage": {"passed": "may_dues_target_group" in r02["lineage"], "lineage": r02["lineage"].get("may_dues_target_group")},
        "R02_fy_dues_target_has_lineage": {"passed": "fy_dues_target_group" in r02["lineage"], "lineage": r02["lineage"].get("fy_dues_target_group")},
        "R02_may_fy_values_nonzero": {"passed": all((r02m.get(k) or 0) > 0 for k in ["may_dues_target_group", "may_advance_target_group", "may_da_target_group", "fy_dues_target_group", "fy_advance_target_group", "fy_da_target_group"]), "values": {k: r02m.get(k) for k in ["may_dues_target_group", "may_advance_target_group", "may_da_target_group", "fy_dues_target_group", "fy_advance_target_group", "fy_da_target_group"]}},
    }

    out = {
        "batch": "SCIP Batch 2",
        "tolerance_pct": TOL,
        "overall_passed": all(v.get("passed", False) for v in batch_checks.values()),
        "r04_summary": {
            "snapshot_date": r04m.get("SNAPSHOT_DATE"),
            "reporting_basis": "Finance",
            "mtd_da_total": r04m.get("mtd_da_total"),
            "mtd_ns_total": r04m.get("mtd_ns_total"),
            "mtd_total_collections": r04m.get("mtd_total_collections"),
            "daily_rows_loaded": len(r04.get("rows", [])),
            "lineage_count": len(r04.get("lineage", {})),
        },
        "r02_summary": {
            "snapshot_date": r02m.get("SNAPSHOT_DATE"),
            "reporting_basis": "MDO",
            "may_dues_target_group": r02m.get("may_dues_target_group"),
            "may_advance_target_group": r02m.get("may_advance_target_group"),
            "may_da_target_group": r02m.get("may_da_target_group"),
            "may_new_sales_target_group": r02m.get("may_new_sales_target_group"),
            "may_total_collections_target_group": r02m.get("may_total_collections_target_group"),
            "fy_dues_target_group": r02m.get("fy_dues_target_group"),
            "fy_advance_target_group": r02m.get("fy_advance_target_group"),
            "fy_da_target_group": r02m.get("fy_da_target_group"),
            "fy_total_collections_target_group": r02m.get("fy_total_collections_target_group"),
            "fact_rows_loaded": len(r02.get("rows", [])),
            "lineage_count": len(r02.get("lineage", {})),
        },
        "checks": batch_checks,
        "native_validations": {
            "R04": r04.get("validations", {}),
            "R02": r02.get("validations", {}),
        },
    }
    return out


if __name__ == "__main__":
    results = main()
    out_path = ROOT / "smoke_r04_r02_batch2_results.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
