# SCIP Batch 12 Governance and Smoke Checkpoints

## Governance rules

1. Observability is a governance/evidence output, not a third product world.
2. Every observability event must include a correlation ID.
3. Middleware must not log request bodies.
4. Sensitive fields must be redacted before persistence or export.
5. Cache keys must include snapshot date and freshness token.
6. Cache invalidation must happen when source snapshot dates change.
7. Frontend render timing may be logged; frontend financial values may not.
8. Alerts must be evidence-based and threshold-driven.
9. Observability visibility must follow Batch 11 RBAC.
10. Liquid Glass surfaces must remain solid for audit/log/evidence tables.

## Smoke checks included

- Correlation ID exists on event.
- Authorization token redacted.
- Customer field redacted.
- Required metric catalog present.
- Cache returns same value for same snapshot.
- Cache invalidates when source snapshot changes.
- High-denial alert generated.
- API timing p95 generated.
- Dashboard spec is L5 governance output.
- Alert thresholds exist.
- Event persists with correlation ID.
- Persisted metadata remains redacted.
- Frontend posts render timing only.
- No new L0 Observability door.
- Frontend states no business computation moved.
- Synthetic telemetry load accepted.
- Synthetic p95 below slow endpoint threshold.

## Local validation command

```bash
python smoke_batch12_observability_performance.py
python load_tests/batch12_synthetic_load.py
```
