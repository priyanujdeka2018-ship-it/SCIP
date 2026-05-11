from __future__ import annotations

import importlib
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import observability

RESULTS = {
    "contract_version": observability.OBSERVABILITY_CONTRACT_VERSION,
    "status": "running",
    "checks": [],
    "failures": [],
}


def check(name: str, condition: bool, details=None):
    item = {"name": name, "passed": bool(condition), "details": details or {}}
    RESULTS["checks"].append(item)
    if not condition:
        RESULTS["failures"].append(item)


def main():
    observability.STORE.events.clear()
    observability.STORE.counters.clear()
    observability.STORE.timings.clear()
    observability.STORE.cache.clear()
    observability.STORE.alerts.clear()

    cid = "batch12-correlation-test"
    event = observability.STORE.log(
        event_type="request_completed",
        component="api",
        status="ok",
        endpoint="/forecast/month-end",
        method="GET",
        duration_ms=42.0,
        metric_name="api_request_latency_ms",
        metric_value=42.0,
        correlation_id=cid,
        metadata={"authorization": "Bearer secret-token", "safe": "ok", "customer_name": "Do Not Log"},
    )
    check("observability event has correlation id", event.correlation_id == cid)
    check("authorization token redacted", event.metadata.get("authorization") == "[REDACTED]", event.metadata)
    check("customer field redacted", event.metadata.get("customer_name") == "[REDACTED]", event.metadata)

    observability.log_ingestion_latency("R18", "2026-05-01", 120.5)
    observability.log_adapter_result("R18", "R18OverdueAdapter", True, "2026-05-01")
    observability.log_lineage_coverage("lineage", 100.0, {"critical_metric_count": 17})
    observability.log_quickball_blocked("OD_TODAY", "lineage_missing")
    observability.log_database_query("audit_export", 18.0, row_count=168)
    observability.log_frontend_render("risk_action", 24.0, "/pulse?focus=risk_action", {"device": "desktop"})

    required_metrics = {
        "ingestion_latency_ms",
        "adapter_success_total",
        "adapter_failure_total",
        "lineage_coverage_pct",
        "forecast_generation_ms",
        "quickball_blocked_answers_total",
        "action_queue_generation_ms",
        "workflow_state_transitions_total",
        "notification_emissions_total",
        "notification_suppressions_total",
        "rbac_denials_total",
        "audit_export_rows_total",
        "database_query_ms",
        "frontend_render_ms",
        "api_error_rate_pct",
        "cache_invalidations_total",
    }
    check("required metric catalog present", required_metrics.issubset(set(observability.METRIC_CATALOG)))

    calls = {"count": 0}
    def compute():
        calls["count"] += 1
        return {"value": calls["count"]}

    first = observability.STORE.cache_get_or_compute("forecast", "month_end", "2026-05-07", "R04:2026-05-07|R02:2026-05-06", compute)
    second = observability.STORE.cache_get_or_compute("forecast", "month_end", "2026-05-07", "R04:2026-05-07|R02:2026-05-06", compute)
    third = observability.STORE.cache_get_or_compute("forecast", "month_end", "2026-05-08", "R04:2026-05-08|R02:2026-05-06", compute)
    check("cache returns same value for same snapshot token", first == second and calls["count"] == 2, {"first": first, "second": second, "third": third, "calls": calls["count"]})
    check("cache invalidates when source snapshot date changes", third != second and observability.STORE.counters.get("cache_invalidations_total", 0) >= 1, observability.STORE.counters)

    for i in range(30):
        observability.STORE.increment("rbac_denials_total", component="auth", status="blocked", metadata={"path": "/audit/export"})
    summary = observability.STORE.summary()
    alerts = observability.evaluate_alerts(summary)
    check("high denial alert generated", any(a["alert_key"] == "high_rbac_denials" for a in alerts), alerts)
    check("summary has api timing p95", summary["timings"].get("api_request_latency_ms", {}).get("p95_ms") is not None, summary["timings"].get("api_request_latency_ms"))

    dashboard = observability.dashboard_spec()
    check("dashboard spec keeps observability as L5 governance output", dashboard["liquid_glass_placement"]["observability_visibility"].startswith("L5"), dashboard["liquid_glass_placement"])
    check("dashboard spec contains alert thresholds", "slow_endpoint_p95_ms" in dashboard["alert_thresholds"], dashboard["alert_thresholds"])

    conn = sqlite3.connect(":memory:")
    observability.ensure_observability_tables(conn)
    observability.persist_event(conn, event)
    row = conn.execute("SELECT correlation_id, metadata_json FROM observability_events WHERE event_id=?", (event.event_id,)).fetchone()
    check("observability event persists with correlation id", row is not None and row[0] == cid)
    check("persisted metadata remains redacted", row is not None and "secret-token" not in row[1] and "Do Not Log" not in row[1], row[1] if row else None)

    app_path = HERE / "App.jsx"
    app_text = app_path.read_text(encoding="utf-8")
    check("frontend posts render timing only", "/observability/frontend-timing" in app_text and "duration_ms" in app_text)
    check("frontend contains no new observability dashboard door", "Observability" not in app_text.split("function ArrivalScreen", 1)[0], {"note": "No new L0 door added by Batch 12."})
    check("frontend states no business computation moved", "No business computation moved into the frontend" in app_text)

    # Synthetic load test: 200 timings should keep p95 under alert threshold in this local harness.
    start = time.perf_counter()
    for i in range(200):
        observability.STORE.timing("api_request_latency_ms", 5 + (i % 17), component="api", status="ok", endpoint="/observability/summary", method="GET")
    load_elapsed_ms = (time.perf_counter() - start) * 1000
    load_summary = observability.STORE.summary()
    p95 = load_summary["timings"]["api_request_latency_ms"]["p95_ms"]
    check("synthetic telemetry load accepted", len(observability.STORE.events) >= 200, {"elapsed_ms": load_elapsed_ms})
    check("local telemetry p95 remains below slow endpoint threshold", p95 < observability.ALERT_THRESHOLDS["slow_endpoint_p95_ms"], {"p95_ms": p95})

    (HERE / "observability_summary_sample_batch12.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    (HERE / "observability_dashboard_alert_spec_batch12.json").write_text(json.dumps(dashboard, indent=2, default=str), encoding="utf-8")
    (HERE / "observability_alerts_sample_batch12.json").write_text(json.dumps({"alerts": alerts, "thresholds": observability.ALERT_THRESHOLDS}, indent=2, default=str), encoding="utf-8")

    RESULTS["overall_passed"] = not RESULTS["failures"]
    RESULTS["passed_checks"] = sum(1 for c in RESULTS["checks"] if c["passed"])
    RESULTS["total_checks"] = len(RESULTS["checks"])
    RESULTS["status"] = "passed" if RESULTS["overall_passed"] else "failed"
    (HERE / "smoke_batch12_observability_performance_results.json").write_text(json.dumps(RESULTS, indent=2, default=str), encoding="utf-8")
    return 0 if RESULTS["overall_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
