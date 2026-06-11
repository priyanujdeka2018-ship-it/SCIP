"""
SCIP W0 smoke — instrumentation baseline.

Verifies the W0 timing instrumentation is present and log/status-only:
  1. get_cache_status() exposes last_load_duration_seconds + last_load_timings.
  2. After a load, timings are populated (total, stages, per-source ms).
  3. The loader payload shape is unchanged (no new top-level keys).
  4. Cache hit/miss/invalidate behave as restored (reconciliation check).

Run from Backend/ with SCIP_SOURCE_ROOT pointing at real R-series sources:
    SCIP_SOURCE_ROOT=/tmp/scip/r-series python smoke_w0_instrumentation.py
Read-only against sources; no figures asserted, no data fabricated.
"""
from __future__ import annotations

import json
import sys

import data_loader


def main() -> int:
    failures = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
        if not ok:
            failures.append(name)

    status_cold = data_loader.get_cache_status()
    check(
        "cache status exposes W0 keys before load",
        "last_load_duration_seconds" in status_cold and "last_load_timings" in status_cold,
        f"keys={sorted(status_cold.keys())}",
    )

    payload = data_loader.get_cached_payload(force_refresh=True)
    check(
        "payload top-level shape unchanged",
        set(payload.keys()) == {"dataframes", "computed", "summary", "status", "missing_sources"},
        f"keys={sorted(payload.keys())}",
    )

    status_warm = data_loader.get_cache_status()
    duration = status_warm.get("last_load_duration_seconds")
    timings = status_warm.get("last_load_timings") or {}
    check("last_load_duration_seconds populated", isinstance(duration, (int, float)) and duration > 0, f"value={duration}")
    check("last_load_timings has total_ms", isinstance(timings.get("total_ms"), (int, float)) and timings["total_ms"] > 0)
    check(
        "last_load_timings has stage timings",
        all(isinstance(timings.get(k), (int, float)) for k in ("resolve_r_series_ms", "build_computed_ms", "build_summary_ms")),
        f"timings={json.dumps({k: v for k, v in timings.items() if k != 'slowest_sources'})}",
    )
    slowest = timings.get("slowest_sources") or []
    check("slowest_sources populated", len(slowest) > 0, f"top={slowest[:3]}")

    hits_before = status_warm.get("hits", 0)
    cached_again = data_loader.get_cached_payload()
    hits_after = data_loader.get_cache_status().get("hits", 0)
    check("cache hit served on second call", cached_again is not None and hits_after == hits_before + 1, f"hits {hits_before} -> {hits_after}")

    data_loader.invalidate_cache()
    check("invalidate_cache returns status to cold", data_loader.get_cache_status().get("status") == "cold")

    print()
    if failures:
        print(f"W0 SMOKE FAILED: {len(failures)} failure(s): {failures}")
        return 1
    print("W0 SMOKE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
