# SCIP Batch 12 Backend / Frontend Contracts

## Contract version

```text
observability_performance.v1.batch12
```

## Backend routes

### GET /observability/summary

Returns event counts, metric catalog, counters, timing percentiles, API error rate, cache count, and active alerts. Requires MIS/QCG/Admin or CCO/GM/AGM visibility.

### GET /observability/events

Returns the latest redacted observability events. Requires observability permission.

### GET /observability/dashboards

Returns production dashboard specifications and alert thresholds.

### GET /observability/alerts

Evaluates thresholds and returns active alerts.

### POST /observability/frontend-timing

Accepts render timing only. Rejects frontend business metrics. This endpoint must not be used for financial computation.

Payload:

```json
{
  "route": "live_pulse",
  "view": "risk_action",
  "duration_ms": 34.8,
  "device": {"reducedMotion": false}
}
```

Response:

```json
{
  "status": "accepted",
  "event_id": "evt_...",
  "correlation_id": "scip-...",
  "actor_role": "mis_qcg_admin"
}
```

## Correlation ID contract

Incoming request header:

```text
X-SCIP-Correlation-ID
```

Fallback generated format:

```text
scip-<uuid4-hex>
```

Outgoing response header:

```text
x-scip-correlation-id
```

## Frontend behavior

The frontend may:

- post render timing,
- display observability summary within Live Pulse / Risk & Action,
- display dashboard names and alert status as governance evidence.

The frontend must not:

- calculate financial metrics,
- generate forecasts,
- determine lineage validity,
- compute action queues,
- calculate notification eligibility,
- create a third Arrival door.

## RBAC

Observability routes are visible to:

- MIS/QCG/Admin,
- CCO/GM/AGM.

Other roles receive a denied attempt audit event through Batch 11 auth logging.
