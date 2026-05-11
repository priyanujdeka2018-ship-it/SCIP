"""Standalone smoke test for SCIP Batch 18 Analytics Transformation Engine."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PATCH_ROOT = Path(__file__).resolve().parents[1]
BACKEND = PATCH_ROOT / "Backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
# Optional: point SCIP_BATCH13_BACKEND to a folder containing Batch 13 source_adapters.py.
B13 = os.environ.get("SCIP_BATCH13_BACKEND")
if B13 and B13 not in sys.path:
    sys.path.append(B13)

from analytics_engine import AnalyticsTransformationEngine, build_default_report_file_map


def main() -> int:
    data_dir = Path(os.environ.get("SCIP_BATCH18_DATA_DIR", "/mnt/data"))
    role = os.environ.get("SCIP_BATCH18_ROLE", "Board/CXO")
    files = build_default_report_file_map(data_dir)
    scope = os.environ.get("SCIP_BATCH18_SMOKE_SCOPE", "core").lower()
    if scope != "full":
        core_codes = {"R02", "R04", "R08", "R09", "R10", "R17", "R18", "R20", "R30", "R31", "R32", "R34", "R36"}
        files = {code: path for code, path in files.items() if code in core_codes}
    engine = AnalyticsTransformationEngine(PATCH_ROOT / "config" / "metric_registry_v1.json")
    result = engine.run(files, role=role)
    payload = result.to_dict()
    out_path = Path(os.environ.get("SCIP_BATCH18_SMOKE_OUT", str(PATCH_ROOT / "smoke" / "smoke_batch18_analytics_engine_runtime_results.json")))
    out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    summary = {
        "scope": scope,
        "reports_seen": sorted(files.keys()),
        "profile_count": len(result.profiles),
        "fact_count": len(result.facts),
        "metric_count": len(result.metrics),
        "link_count": len(result.links),
        "candidate_count": len(result.candidates),
        "chart_count": len(result.charts),
        "validation_count": len(result.validations),
        "errors": result.errors,
        "warnings": result.warnings,
        "output": str(out_path),
    }
    print(json.dumps(summary, indent=2, default=str))
    if result.errors:
        return 1
    if len(result.facts) < 25:
        print("Expected at least 25 facts from uploaded R-series set")
        return 2
    if len(result.metrics) < 5:
        print("Expected at least 5 compiled metrics")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
