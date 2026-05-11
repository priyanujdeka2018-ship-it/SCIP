"""SCIP Batch 2 data_loader smoke test."""
from __future__ import annotations

import json
from pathlib import Path

import data_loader

ROOT = Path(__file__).resolve().parent
DATA = ROOT.parent


def main():
    loaded = data_loader.load_all(data_dir=DATA)
    computed = loaded["computed"]
    checks = {
        "load_all_returns_payload": {"passed": isinstance(loaded, dict) and "computed" in loaded and "summary" in loaded},
        "R04_loaded_with_finance_basis": {"passed": loaded["dataframes"].get("R04", {}).get("status") == "ok" and computed.get("R04_REPORTING_BASIS") == "Finance"},
        "R02_loaded_with_mdo_basis": {"passed": loaded["dataframes"].get("R02", {}).get("status") == "ok" and computed.get("R02_REPORTING_BASIS") == "MDO"},
        "R04_computed_mtd_values_present": {"passed": all(computed.get(k) is not None for k in ["MTD_DA_TOTAL", "MTD_NS_TOTAL", "MTD_TOTAL_COLLECTIONS"]), "values": {k: computed.get(k) for k in ["MTD_DA_TOTAL", "MTD_NS_TOTAL", "MTD_TOTAL_COLLECTIONS"]}},
        "R02_computed_may_fy_targets_present": {"passed": all(computed.get(k) is not None for k in ["MAY_DUES_TARGET", "MAY_ADV_TARGET", "MAY_DA_TARGET", "FY_DUES_TARGET", "FY_ADV_TARGET", "FY_DA_TARGET"]), "values": {k: computed.get(k) for k in ["MAY_DUES_TARGET", "MAY_ADV_TARGET", "MAY_DA_TARGET", "FY_DUES_TARGET", "FY_ADV_TARGET", "FY_DA_TARGET"]}},
        "lineage_available_in_summary": {"passed": bool(loaded["summary"]["daily"].get("lineage")) and bool(loaded["summary"]["targets"].get("lineage"))},
        "native_validations_pass": {"passed": not [k for k, v in computed.get("R04_VALIDATIONS", {}).items() if not v.get("passed")] and not [k for k, v in computed.get("R02_VALIDATIONS", {}).items() if not v.get("passed")]},
    }
    out = {
        "batch": "SCIP Batch 2",
        "overall_passed": all(v.get("passed", False) for v in checks.values()),
        "platform_status": loaded.get("status"),
        "source_statuses": {k: v.get("status") for k, v in loaded.get("dataframes", {}).items() if k in ["R18", "R04", "R02", "R08", "R36"]},
        "checks": checks,
        "computed_sample": {
            "MTD_DA_TOTAL": computed.get("MTD_DA_TOTAL"),
            "MTD_NS_TOTAL": computed.get("MTD_NS_TOTAL"),
            "MTD_TOTAL_COLLECTIONS": computed.get("MTD_TOTAL_COLLECTIONS"),
            "MAY_DUES_TARGET": computed.get("MAY_DUES_TARGET"),
            "MAY_ADV_TARGET": computed.get("MAY_ADV_TARGET"),
            "MAY_DA_TARGET": computed.get("MAY_DA_TARGET"),
            "FY_DUES_TARGET": computed.get("FY_DUES_TARGET"),
            "FY_ADV_TARGET": computed.get("FY_ADV_TARGET"),
            "FY_DA_TARGET": computed.get("FY_DA_TARGET"),
        },
    }
    return out


if __name__ == "__main__":
    results = main()
    out_path = ROOT / "smoke_data_loader_batch2_results.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
