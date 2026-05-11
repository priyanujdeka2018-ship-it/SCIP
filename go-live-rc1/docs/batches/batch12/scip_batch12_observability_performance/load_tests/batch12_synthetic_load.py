"""Synthetic Batch 12 load harness for telemetry ingestion.
Run from the batch folder: python load_tests/batch12_synthetic_load.py
"""
from __future__ import annotations
import sys
import time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import observability

start = time.perf_counter()
for i in range(1000):
    observability.STORE.timing(
        "api_request_latency_ms",
        10 + (i % 41),
        component="api",
        status="ok",
        endpoint="/action-queues" if i % 2 else "/forecast/month-end",
        method="GET",
        correlation_id=f"synthetic-load-{i//10}",
    )
elapsed_ms = (time.perf_counter() - start) * 1000
summary = observability.STORE.summary()
print({
    "events": summary["event_count"],
    "elapsed_ms": round(elapsed_ms, 2),
    "api_p95_ms": summary["timings"]["api_request_latency_ms"]["p95_ms"],
    "passed": summary["timings"]["api_request_latency_ms"]["p95_ms"] < observability.ALERT_THRESHOLDS["slow_endpoint_p95_ms"],
})
