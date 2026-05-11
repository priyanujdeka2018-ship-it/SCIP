"""
SCIP Batch 12 - production observability, safe performance instrumentation,
and cache freshness controls.

Design guardrails preserved:
- No financial/business computation in frontend.
- No silent fallback: cache entries are keyed by source snapshot/freshness token.
- No sensitive data in structured logs.
- Every observability event has a correlation_id.
- Dashboards/alerts are L5 governance outputs, not new navigation worlds.
"""

from __future__ import annotations

import contextvars
import hashlib
import json
import os
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

try:
    from fastapi import APIRouter, Depends, HTTPException, Request, Response
    from fastapi.responses import JSONResponse
except Exception:  # pragma: no cover - keeps module importable in smoke harness
    APIRouter = None
    Depends = None
    HTTPException = Exception
    Request = Any
    Response = Any
    JSONResponse = None

try:
    import auth
except Exception:  # pragma: no cover
    auth = None

OBSERVABILITY_CONTRACT_VERSION = "observability_performance.v1.batch12"
HERE = Path(__file__).resolve().parent
DEFAULT_DB_PATH = Path(os.environ.get("SCIP_AUDIT_DB", str(HERE / "scip_batch12_observability.sqlite")))
TELEMETRY_RETENTION_EVENTS = int(os.environ.get("SCIP_TELEMETRY_EVENT_LIMIT", "5000"))
TELEMETRY_CACHE_TTL_SECONDS = int(os.environ.get("SCIP_CACHE_TTL_SECONDS", "300"))

CORRELATION_ID_CTX: contextvars.ContextVar[str] = contextvars.ContextVar("scip_correlation_id", default="")

SENSITIVE_KEYS = {
    "password", "passwd", "pwd", "secret", "token", "authorization", "auth",
    "cookie", "set-cookie", "api_key", "apikey", "access_token", "refresh_token",
    "jwt", "bearer", "mobile", "phone", "email", "customer_name", "customer",
    "passport", "emirates_id", "national_id", "card", "iban", "account_number",
}

METRIC_CATALOG = [
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
    "audit_export_generation_ms",
    "database_query_ms",
    "frontend_render_ms",
    "api_error_rate_pct",
    "api_request_latency_ms",
    "cache_hits_total",
    "cache_misses_total",
    "cache_invalidations_total",
]

ALERT_THRESHOLDS = {
    "stale_critical_source_hours": 24,
    "missing_critical_lineage_count": 0,
    "migration_failure_count": 0,
    "backup_failure_count": 0,
    "rbac_denials_per_15m_high": 25,
    "slow_endpoint_p95_ms": 1500,
    "failed_export_count": 0,
    "api_error_rate_pct_high": 3.0,
    "adapter_failure_count_high": 1,
    "quickball_blocked_answers_per_hour_high": 20,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except Exception:
        return None


def _canonical_key(key: str) -> str:
    return key.strip().lower().replace("-", "_").replace(" ", "_")


def _looks_sensitive(key: str) -> bool:
    lower = _canonical_key(key)
    return any(s in lower for s in SENSITIVE_KEYS)


def redact(value: Any, parent_key: str = "") -> Any:
    """Recursively redact sensitive fields while preserving event shape."""
    if _looks_sensitive(parent_key):
        return "[REDACTED]"
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for k, v in value.items():
            out[str(k)] = redact(v, str(k))
        return out
    if isinstance(value, list):
        return [redact(v, parent_key) for v in value]
    if isinstance(value, tuple):
        return tuple(redact(v, parent_key) for v in value)
    if isinstance(value, str) and ("Bearer " in value or "eyJ" in value[:8]):
        return "[REDACTED]"
    return value


def stable_hash(value: Any) -> str:
    payload = json.dumps(redact(value), sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def get_or_create_correlation_id(request: Optional[Any] = None) -> str:
    if request is not None:
        try:
            inbound = request.headers.get("x-scip-correlation-id") or request.headers.get("x-request-id")
            if inbound:
                cid = inbound.strip()[:96]
                CORRELATION_ID_CTX.set(cid)
                return cid
        except Exception:
            pass
    existing = CORRELATION_ID_CTX.get()
    if existing:
        return existing
    cid = f"scip-{uuid.uuid4().hex}"
    CORRELATION_ID_CTX.set(cid)
    return cid


@dataclass
class TelemetryEvent:
    event_id: str
    timestamp: str
    correlation_id: str
    event_type: str
    component: str
    status: str
    actor_role: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    duration_ms: Optional[float] = None
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    source_code: Optional[str] = None
    snapshot_date: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheEntry:
    cache_name: str
    key: str
    snapshot_date: str
    freshness_token: str
    created_at: float
    expires_at: float
    value: Any


class TelemetryStore:
    def __init__(self, max_events: int = TELEMETRY_RETENTION_EVENTS) -> None:
        self.max_events = max_events
        self.events: List[TelemetryEvent] = []
        self.counters: Dict[str, float] = {}
        self.timings: Dict[str, List[float]] = {}
        self.cache: Dict[Tuple[str, str], CacheEntry] = {}
        self.alerts: List[Dict[str, Any]] = []

    def emit(self, event: TelemetryEvent) -> TelemetryEvent:
        event.metadata = redact(event.metadata)
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
        if event.metric_name:
            if event.metric_name.endswith("_ms") and event.metric_value is not None:
                self.timings.setdefault(event.metric_name, []).append(float(event.metric_value))
                self.timings[event.metric_name] = self.timings[event.metric_name][-1000:]
            else:
                self.counters[event.metric_name] = self.counters.get(event.metric_name, 0.0) + float(event.metric_value or 1.0)
        return event

    def log(
        self,
        event_type: str,
        component: str,
        status: str = "ok",
        metadata: Optional[Dict[str, Any]] = None,
        *,
        duration_ms: Optional[float] = None,
        metric_name: Optional[str] = None,
        metric_value: Optional[float] = None,
        actor_role: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        source_code: Optional[str] = None,
        snapshot_date: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> TelemetryEvent:
        cid = correlation_id or get_or_create_correlation_id()
        event = TelemetryEvent(
            event_id=f"evt_{uuid.uuid4().hex[:18]}",
            timestamp=_now(),
            correlation_id=cid,
            event_type=event_type,
            component=component,
            status=status,
            actor_role=actor_role,
            endpoint=endpoint,
            method=method,
            duration_ms=duration_ms,
            metric_name=metric_name,
            metric_value=metric_value,
            source_code=source_code,
            snapshot_date=snapshot_date,
            metadata=metadata or {},
        )
        return self.emit(event)

    def timing(self, metric_name: str, duration_ms: float, **kwargs: Any) -> TelemetryEvent:
        return self.log(
            event_type="metric_timing",
            component=kwargs.pop("component", "platform"),
            status=kwargs.pop("status", "ok"),
            metric_name=metric_name,
            metric_value=duration_ms,
            duration_ms=duration_ms,
            **kwargs,
        )

    def increment(self, metric_name: str, value: float = 1.0, **kwargs: Any) -> TelemetryEvent:
        return self.log(
            event_type="metric_counter",
            component=kwargs.pop("component", "platform"),
            status=kwargs.pop("status", "ok"),
            metric_name=metric_name,
            metric_value=value,
            **kwargs,
        )

    def percentile(self, values: Iterable[float], pct: float) -> Optional[float]:
        arr = sorted(float(x) for x in values)
        if not arr:
            return None
        idx = min(len(arr) - 1, max(0, int(round((pct / 100.0) * (len(arr) - 1)))))
        return arr[idx]

    def summary(self) -> Dict[str, Any]:
        timing_summary = {}
        for name, values in self.timings.items():
            timing_summary[name] = {
                "count": len(values),
                "p50_ms": self.percentile(values, 50),
                "p95_ms": self.percentile(values, 95),
                "max_ms": max(values) if values else None,
            }
        api_errors = sum(1 for e in self.events if e.component == "api" and e.status == "error")
        api_total = sum(1 for e in self.events if e.component == "api" and e.event_type in {"request_completed", "request_failed"})
        error_rate = (api_errors / api_total * 100.0) if api_total else 0.0
        return {
            "contract_version": OBSERVABILITY_CONTRACT_VERSION,
            "generated_at": _now(),
            "event_count": len(self.events),
            "metrics_catalog": METRIC_CATALOG,
            "counters": dict(sorted(self.counters.items())),
            "timings": timing_summary,
            "api_error_rate_pct": round(error_rate, 4),
            "cache_entries": len(self.cache),
            "active_alerts": self.alerts[-50:],
        }

    def cache_get(self, cache_name: str, key: str, snapshot_date: str, freshness_token: str) -> Optional[Any]:
        now = time.time()
        entry = self.cache.get((cache_name, key))
        if entry is None:
            self.increment("cache_misses_total", component="cache", metadata={"cache_name": cache_name})
            return None
        if entry.snapshot_date != snapshot_date or entry.freshness_token != freshness_token:
            self.cache.pop((cache_name, key), None)
            self.increment(
                "cache_invalidations_total",
                component="cache",
                metadata={
                    "cache_name": cache_name,
                    "reason": "snapshot_or_freshness_changed",
                    "old_snapshot_date": entry.snapshot_date,
                    "new_snapshot_date": snapshot_date,
                },
            )
            return None
        if entry.expires_at < now:
            self.cache.pop((cache_name, key), None)
            self.increment("cache_invalidations_total", component="cache", metadata={"cache_name": cache_name, "reason": "ttl_expired"})
            return None
        self.increment("cache_hits_total", component="cache", metadata={"cache_name": cache_name})
        return entry.value

    def cache_set(self, cache_name: str, key: str, snapshot_date: str, freshness_token: str, value: Any, ttl_seconds: int = TELEMETRY_CACHE_TTL_SECONDS) -> Any:
        now = time.time()
        self.cache[(cache_name, key)] = CacheEntry(
            cache_name=cache_name,
            key=key,
            snapshot_date=snapshot_date,
            freshness_token=freshness_token,
            created_at=now,
            expires_at=now + max(1, ttl_seconds),
            value=value,
        )
        return value

    def cache_get_or_compute(
        self,
        cache_name: str,
        key: str,
        snapshot_date: str,
        freshness_token: str,
        compute_fn: Callable[[], Any],
        ttl_seconds: int = TELEMETRY_CACHE_TTL_SECONDS,
    ) -> Any:
        cached = self.cache_get(cache_name, key, snapshot_date, freshness_token)
        if cached is not None:
            return cached
        value = compute_fn()
        return self.cache_set(cache_name, key, snapshot_date, freshness_token, value, ttl_seconds=ttl_seconds)


STORE = TelemetryStore()


def log_ingestion_latency(source_code: str, snapshot_date: str, duration_ms: float, status: str = "ok", metadata: Optional[Dict[str, Any]] = None) -> TelemetryEvent:
    return STORE.timing(
        "ingestion_latency_ms",
        duration_ms,
        component="ingestion",
        status=status,
        source_code=source_code,
        snapshot_date=snapshot_date,
        metadata=metadata or {},
    )


def log_adapter_result(source_code: str, adapter_name: str, success: bool, snapshot_date: str, metadata: Optional[Dict[str, Any]] = None) -> TelemetryEvent:
    return STORE.increment(
        "adapter_success_total" if success else "adapter_failure_total",
        component="adapter",
        status="ok" if success else "error",
        source_code=source_code,
        snapshot_date=snapshot_date,
        metadata={"adapter_name": adapter_name, **(metadata or {})},
    )


def log_lineage_coverage(component: str, coverage_pct: float, metadata: Optional[Dict[str, Any]] = None) -> TelemetryEvent:
    return STORE.log(
        event_type="metric_gauge",
        component=component,
        status="ok" if coverage_pct >= 100.0 else "attention",
        metric_name="lineage_coverage_pct",
        metric_value=coverage_pct,
        metadata=metadata or {},
    )


def log_quickball_blocked(metric_key: str, reason: str, metadata: Optional[Dict[str, Any]] = None) -> TelemetryEvent:
    return STORE.increment(
        "quickball_blocked_answers_total",
        component="quickball",
        status="blocked",
        metadata={"metric_key": metric_key, "reason": reason, **(metadata or {})},
    )


def log_database_query(query_name: str, duration_ms: float, row_count: Optional[int] = None, status: str = "ok") -> TelemetryEvent:
    return STORE.timing(
        "database_query_ms",
        duration_ms,
        component="database",
        status=status,
        metadata={"query_name": query_name, "row_count": row_count},
    )


def log_frontend_render(view: str, duration_ms: float, route: str, metadata: Optional[Dict[str, Any]] = None) -> TelemetryEvent:
    return STORE.timing(
        "frontend_render_ms",
        duration_ms,
        component="frontend",
        status="ok",
        metadata={"view": view, "route": route, **(metadata or {})},
    )


def evaluate_alerts(summary: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    summary = summary or STORE.summary()
    alerts: List[Dict[str, Any]] = []
    counters = summary.get("counters", {})
    timings = summary.get("timings", {})
    api_error_rate = float(summary.get("api_error_rate_pct") or 0.0)
    if counters.get("adapter_failure_total", 0) > ALERT_THRESHOLDS["adapter_failure_count_high"]:
        alerts.append({"alert_key": "adapter_failures", "severity": "high", "threshold": ALERT_THRESHOLDS["adapter_failure_count_high"], "actual": counters.get("adapter_failure_total", 0)})
    if counters.get("rbac_denials_total", 0) > ALERT_THRESHOLDS["rbac_denials_per_15m_high"]:
        alerts.append({"alert_key": "high_rbac_denials", "severity": "medium", "threshold": ALERT_THRESHOLDS["rbac_denials_per_15m_high"], "actual": counters.get("rbac_denials_total", 0)})
    if api_error_rate > ALERT_THRESHOLDS["api_error_rate_pct_high"]:
        alerts.append({"alert_key": "api_error_rate_high", "severity": "high", "threshold": ALERT_THRESHOLDS["api_error_rate_pct_high"], "actual": api_error_rate})
    slow_p95 = timings.get("api_request_latency_ms", {}).get("p95_ms")
    if slow_p95 and slow_p95 > ALERT_THRESHOLDS["slow_endpoint_p95_ms"]:
        alerts.append({"alert_key": "slow_endpoint_p95", "severity": "medium", "threshold": ALERT_THRESHOLDS["slow_endpoint_p95_ms"], "actual": slow_p95})
    failed_exports = counters.get("failed_export_count", 0)
    if failed_exports > ALERT_THRESHOLDS["failed_export_count"]:
        alerts.append({"alert_key": "failed_exports", "severity": "high", "threshold": ALERT_THRESHOLDS["failed_export_count"], "actual": failed_exports})
    STORE.alerts = alerts
    return alerts


def dashboard_spec() -> Dict[str, Any]:
    return {
        "contract_version": OBSERVABILITY_CONTRACT_VERSION,
        "generated_at": _now(),
        "dashboards": [
            {
                "dashboard_id": "executive_reliability_overview",
                "title": "SCIP Reliability Overview",
                "surface": "L5 governance output",
                "panels": [
                    "API p95 latency and error rate",
                    "Critical source freshness and lineage coverage",
                    "Quickball blocked answer trend",
                    "Notification emission/suppression trend",
                    "RBAC denial trend",
                ],
            },
            {
                "dashboard_id": "data_pipeline_health",
                "title": "Data Pipeline Health",
                "surface": "solid evidence",
                "panels": [
                    "Ingestion latency by R-code",
                    "Adapter success/failure by source",
                    "Lineage coverage by metric group",
                    "Cache hit/miss/invalidation by snapshot date",
                ],
            },
            {
                "dashboard_id": "workflow_automation_health",
                "title": "Workflow & Notification Automation",
                "surface": "solid evidence",
                "panels": [
                    "Workflow transition volume",
                    "Escalation rule coverage",
                    "Suppression/deduplication counts",
                    "Audit export volume and failures",
                ],
            },
            {
                "dashboard_id": "security_and_deployment",
                "title": "Security & Deployment Hardening",
                "surface": "solid evidence",
                "panels": [
                    "RBAC denied attempts by role/path",
                    "Migration status",
                    "Backup/restore status",
                    "CORS/auth mode/secrets status",
                ],
            },
        ],
        "alert_thresholds": ALERT_THRESHOLDS,
        "liquid_glass_placement": {
            "entry_model": "unchanged: Live Pulse and Narratives only",
            "observability_visibility": "L5 governance output and MIS/QCG/Admin evidence",
            "financial_truth_surfaces": "solid; no blur over audit/log tables",
        },
    }


def ensure_observability_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS observability_events (
            event_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            correlation_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            component TEXT NOT NULL,
            status TEXT NOT NULL,
            actor_role TEXT,
            endpoint TEXT,
            method TEXT,
            duration_ms REAL,
            metric_name TEXT,
            metric_value REAL,
            source_code TEXT,
            snapshot_date TEXT,
            metadata_json TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_observability_events_correlation ON observability_events(correlation_id);
        CREATE INDEX IF NOT EXISTS idx_observability_events_metric ON observability_events(metric_name);
        CREATE TABLE IF NOT EXISTS performance_cache_index (
            cache_name TEXT NOT NULL,
            cache_key TEXT NOT NULL,
            snapshot_date TEXT NOT NULL,
            freshness_token TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            PRIMARY KEY(cache_name, cache_key)
        );
        CREATE TABLE IF NOT EXISTS alert_evaluations (
            evaluation_id TEXT PRIMARY KEY,
            evaluated_at TEXT NOT NULL,
            alerts_json TEXT NOT NULL,
            summary_json TEXT NOT NULL
        );
        """
    )


def persist_event(conn: sqlite3.Connection, event: TelemetryEvent) -> None:
    ensure_observability_tables(conn)
    conn.execute(
        """
        INSERT OR REPLACE INTO observability_events(
            event_id, timestamp, correlation_id, event_type, component, status,
            actor_role, endpoint, method, duration_ms, metric_name, metric_value,
            source_code, snapshot_date, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.event_id,
            event.timestamp,
            event.correlation_id,
            event.event_type,
            event.component,
            event.status,
            event.actor_role,
            event.endpoint,
            event.method,
            event.duration_ms,
            event.metric_name,
            event.metric_value,
            event.source_code,
            event.snapshot_date,
            json.dumps(event.metadata, sort_keys=True, default=str),
        ),
    )


async def correlation_middleware(request: Request, call_next: Callable) -> Response:
    correlation_id = get_or_create_correlation_id(request)
    start = time.perf_counter()
    path = getattr(request.url, "path", "")
    method = getattr(request, "method", "")
    try:
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000.0
        status_code = getattr(response, "status_code", 200)
        STORE.timing(
            "api_request_latency_ms",
            duration_ms,
            component="api",
            status="ok" if status_code < 500 else "error",
            endpoint=path,
            method=method,
            metadata={"status_code": status_code},
            correlation_id=correlation_id,
        )
        response.headers["x-scip-correlation-id"] = correlation_id
        return response
    except Exception as exc:
        duration_ms = (time.perf_counter() - start) * 1000.0
        STORE.timing(
            "api_request_latency_ms",
            duration_ms,
            component="api",
            status="error",
            endpoint=path,
            method=method,
            metadata={"error_type": exc.__class__.__name__},
            correlation_id=correlation_id,
        )
        raise


router = APIRouter(prefix="/observability", tags=["observability"]) if APIRouter else None

if router is not None:
    def _require_observability_actor(request: Request):
        if auth is None:
            return None
        actor = auth.get_actor(request)
        if actor.role not in {"mis_qcg_admin", "cco_gm_agm"}:
            auth.log_denied_attempt(actor, "read:observability", "role_not_permitted", path=getattr(getattr(request, "url", None), "path", "/observability"), method=getattr(request, "method", "GET"))
            raise HTTPException(status_code=403, detail="observability_not_permitted")
        return actor

    @router.get("/summary")
    async def get_observability_summary(request: Request) -> Dict[str, Any]:
        actor = _require_observability_actor(request)
        summary = STORE.summary()
        summary["actor_role"] = getattr(actor, "role", None)
        return summary

    @router.get("/events")
    async def get_observability_events(request: Request, limit: int = 100) -> Dict[str, Any]:
        actor = _require_observability_actor(request)
        rows = [asdict(e) for e in STORE.events[-max(1, min(limit, 500)):]]
        return {"contract_version": OBSERVABILITY_CONTRACT_VERSION, "actor_role": getattr(actor, "role", None), "events": rows}

    @router.get("/dashboards")
    async def get_dashboard_spec(request: Request) -> Dict[str, Any]:
        _require_observability_actor(request)
        return dashboard_spec()

    @router.get("/alerts")
    async def get_alerts(request: Request) -> Dict[str, Any]:
        _require_observability_actor(request)
        summary = STORE.summary()
        alerts = evaluate_alerts(summary)
        return {"contract_version": OBSERVABILITY_CONTRACT_VERSION, "generated_at": _now(), "alerts": alerts, "thresholds": ALERT_THRESHOLDS}

    @router.post("/frontend-timing")
    async def post_frontend_timing(request: Request, payload: Dict[str, Any]) -> Dict[str, Any]:
        actor = auth.get_actor(request) if auth is not None else None
        view = str(payload.get("view", "unknown"))[:80]
        route = str(payload.get("route", "unknown"))[:120]
        duration_ms = _safe_float(payload.get("duration_ms")) or 0.0
        # This endpoint accepts render timings only; it rejects business metrics so computation stays backend-side.
        forbidden_keys = {"amount", "target", "forecast", "od", "collection", "revenue"}
        if any(k in _canonical_key(str(payload.keys())) for k in forbidden_keys):
            raise HTTPException(status_code=400, detail="frontend_business_metric_logging_rejected")
        event = log_frontend_render(view=view, duration_ms=duration_ms, route=route, metadata={"browser": payload.get("browser"), "device": payload.get("device")})
        return {"status": "accepted", "event_id": event.event_id, "correlation_id": event.correlation_id, "actor_role": getattr(actor, "role", None)}

    @router.post("/emit-test-event")
    async def emit_test_event(request: Request, payload: Dict[str, Any]) -> Dict[str, Any]:
        _require_observability_actor(request)
        event = STORE.log(
            event_type=str(payload.get("event_type", "manual_test")),
            component=str(payload.get("component", "manual")),
            status=str(payload.get("status", "ok")),
            metadata=payload.get("metadata") or {},
            metric_name=payload.get("metric_name"),
            metric_value=_safe_float(payload.get("metric_value")),
            correlation_id=get_or_create_correlation_id(request),
        )
        return {"status": "accepted", "event": asdict(event)}
