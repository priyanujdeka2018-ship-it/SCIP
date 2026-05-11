"""
SCIP Batch 1 R18 smoke test.

Validates that the R18 adapter extracts OD metrics using the locked hierarchy:
Group -> Sobha(Sobha Dubai, Sobha AUH) + UAQ(Siniya, Downtown UAQ).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from source_adapters import TOLERANCE_PCT, run_adapter


def find_r18(data_dir: Path) -> Path:
    exact = data_dir / "R18_Consolidated and Overdue 01-05-26.xlsx"
    if exact.exists():
        return exact
    matches = sorted(data_dir.glob("R18*.xlsx"))
    if not matches:
        raise FileNotFoundError("No R18*.xlsx file found")
    return matches[-1]


def pct_check(left, right, reference):
    diff = abs((left or 0) - (right or 0))
    tolerance = abs(reference or 0) * TOLERANCE_PCT
    return {"passed": diff <= tolerance, "left": left, "right": right, "diff": diff, "tolerance_aed": tolerance, "tolerance_pct": TOLERANCE_PCT}


def main() -> int:
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/mnt/data")
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("smoke_r18_batch1_results.json")
    r18_path = find_r18(data_dir)
    result = run_adapter("R18", r18_path).to_dict()
    metrics = result.get("metrics", {})

    checks = {
        "adapter_status_ok_or_warning": result.get("status") in {"ok", "warning"},
        "snapshot_date_found": bool(metrics.get("SNAPSHOT_DATE")),
        "sobha_auh_extracted": (metrics.get("OD_SOBHA_AUH") or 0) > 0,
        "lineage_for_every_od_metric": all(k in result.get("lineage", {}) for k in [
            "OD_SOBHA_DUBAI", "OD_SOBHA_AUH", "OD_SOBHA", "OD_SINIYA",
            "OD_DOWNTOWN_UAQ", "OD_DT", "OD_UAQ", "OD_GROUP", "OD_TODAY"
        ]),
        "OD_SOBHA_equals_Dubai_plus_AUH": pct_check(
            metrics.get("OD_SOBHA"),
            (metrics.get("OD_SOBHA_DUBAI") or 0) + (metrics.get("OD_SOBHA_AUH") or 0),
            metrics.get("OD_SOBHA"),
        ),
        "OD_UAQ_equals_Siniya_plus_Downtown_UAQ": pct_check(
            metrics.get("OD_UAQ"),
            (metrics.get("OD_SINIYA") or 0) + (metrics.get("OD_DOWNTOWN_UAQ") or 0),
            metrics.get("OD_UAQ"),
        ),
        "OD_SOBHA_plus_OD_UAQ_equals_OD_TODAY": pct_check(
            (metrics.get("OD_SOBHA") or 0) + (metrics.get("OD_UAQ") or 0),
            metrics.get("OD_TODAY"),
            metrics.get("OD_TODAY"),
        ),
    }

    failures = []
    for key, value in checks.items():
        passed = value.get("passed") if isinstance(value, dict) else bool(value)
        if not passed:
            failures.append(key)

    report = {
        "source_file": str(r18_path),
        "tolerance_pct": TOLERANCE_PCT,
        "metrics": {k: v for k, v in metrics.items() if not k.startswith("_")},
        "validations_from_adapter": result.get("validations", {}),
        "checks": checks,
        "lineage_keys": sorted(result.get("lineage", {}).keys()),
        "overall_status": "passed" if not failures else "failed",
        "failures": failures,
    }
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"overall_status": report["overall_status"], "failures": failures}, indent=2))
    print(f"Wrote: {out_path}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
