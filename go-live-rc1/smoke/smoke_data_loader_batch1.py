"""SCIP Batch 1 data_loader integration smoke test."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import data_loader


def main() -> int:
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/mnt/data")
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("smoke_data_loader_batch1_results.json")
    payload = data_loader.load_all(data_dir=data_dir)
    computed = payload.get("computed", {})
    portfolio = payload.get("summary", {}).get("portfolio", {})
    r18_source = payload.get("dataframes", {}).get("R18", {})

    checks = {
        "r18_loaded": r18_source.get("status") == "ok",
        "od_today_available": computed.get("OD_TODAY") is not None,
        "od_sobha_plus_uaq_equals_od_today": abs(((computed.get("OD_SOBHA") or 0) + (computed.get("OD_UAQ") or 0)) - (computed.get("OD_TODAY") or 0)) <= ((computed.get("OD_TODAY") or 0) * 0.0005),
        "od_lineage_present": bool(computed.get("OD_LINEAGE")) and "OD_TODAY" in computed.get("OD_LINEAGE", {}),
        "summary_contains_new_hierarchy": all(k in portfolio for k in ["od_sobha_dubai", "od_sobha_auh", "od_uaq", "od_downtown_uaq"]),
        "no_silent_fallback": computed.get("OD_SOURCE") == "R18_live" and computed.get("OD_FALLBACK_POLICY") == "live_or_labelled_unavailable",
    }
    failures = [k for k, v in checks.items() if not v]
    report = {
        "payload_status": payload.get("status"),
        "missing_sources": payload.get("missing_sources"),
        "checks": checks,
        "computed_od": {k: computed.get(k) for k in [
            "SNAPSHOT_DATE", "OD_SOURCE", "OD_CONFIDENCE", "OD_FALLBACK_POLICY", "OD_TODAY", "OD_GROUP",
            "OD_SOBHA", "OD_SOBHA_DUBAI", "OD_SOBHA_AUH", "OD_UAQ", "OD_SINIYA", "OD_DOWNTOWN_UAQ", "OD_DT"
        ]},
        "r18_validations": computed.get("OD_VALIDATIONS"),
        "r18_lineage_sample": {k: computed.get("OD_LINEAGE", {}).get(k) for k in ["OD_TODAY", "OD_SOBHA", "OD_UAQ"]},
        "overall_status": "passed" if not failures else "failed",
        "failures": failures,
    }
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"overall_status": report["overall_status"], "failures": failures}, indent=2))
    print(f"Wrote: {out_path}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
