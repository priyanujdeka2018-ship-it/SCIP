-- SCIP Batch 12 - observability and performance persistence
-- Migration-ready SQL for production telemetry metadata. Event payload values are redacted before insert.

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
CREATE INDEX IF NOT EXISTS idx_observability_events_component ON observability_events(component, status);
CREATE INDEX IF NOT EXISTS idx_observability_events_metric ON observability_events(metric_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_observability_events_source_snapshot ON observability_events(source_code, snapshot_date);

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

CREATE TABLE IF NOT EXISTS frontend_performance_events (
    event_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    actor_role TEXT,
    route TEXT NOT NULL,
    view_name TEXT NOT NULL,
    duration_ms REAL NOT NULL,
    device_json TEXT NOT NULL
);
