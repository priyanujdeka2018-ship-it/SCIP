# SCIP Batch 12 Dashboard and Alert Specification

## Dashboards

### 1. SCIP Reliability Overview

Purpose: executive reliability posture without becoming a new platform world.

Panels:

- API p95 latency and error rate
- Critical source freshness and lineage coverage
- Quickball blocked answer trend
- Notification emission/suppression trend
- RBAC denial trend

### 2. Data Pipeline Health

Purpose: monitor ingestion, adapter, lineage, and cache health.

Panels:

- Ingestion latency by R-code
- Adapter success/failure by source
- Lineage coverage by metric group
- Cache hit/miss/invalidation by snapshot date

### 3. Workflow and Notification Automation

Purpose: monitor operational automation quality.

Panels:

- Workflow transition volume
- Escalation rule coverage
- Suppression/deduplication counts
- Audit export volume and failures

### 4. Security and Deployment Hardening

Purpose: monitor RBAC and production readiness.

Panels:

- RBAC denied attempts by role/path
- Migration status
- Backup/restore status
- CORS/auth mode/secrets status

## Alert thresholds

```json
{
  "stale_critical_source_hours": 24,
  "missing_critical_lineage_count": 0,
  "migration_failure_count": 0,
  "backup_failure_count": 0,
  "rbac_denials_per_15m_high": 25,
  "slow_endpoint_p95_ms": 1500,
  "failed_export_count": 0,
  "api_error_rate_pct_high": 3.0,
  "adapter_failure_count_high": 1,
  "quickball_blocked_answers_per_hour_high": 20
}
```

## Liquid Glass placement

Observability lives as L5 governance output and MIS/QCG/Admin evidence. It does not add a new Arrival door, product world, sidebar, or dashboard-first flow.
