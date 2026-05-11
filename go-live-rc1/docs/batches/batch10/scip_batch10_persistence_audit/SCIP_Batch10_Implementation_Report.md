# SCIP Batch 10 — Durable Database Persistence and Audit Export

## Status

Batch 10 is implemented as a persistence/audit layer on top of Batch 8 workflow tracking and Batch 9 notifications.

It preserves the existing SCIP macro rules:

- Batch 5.1 Liquid Glass model remains unchanged.
- Audit/export stays as an L5 output, not a third Arrival door.
- Dense audit evidence remains on solid surfaces.
- Locked hierarchy remains unchanged: Group > Sobha > Sobha Dubai/Sobha AUH and Group > UAQ > Siniya/Downtown UAQ.
- 0.05% tolerance and no-silent-fallback rules remain untouched.
- Role model excludes Entity Head.
- Batch 7 account-action gate remains the source of truth.
- Batch 8 immutable workflow event lineage is preserved.
- Batch 9 notification dedupe/suppression rules are persisted.

## What changed

### New durable backend module

`persistence.py` adds an SQLite-backed repository and FastAPI router.

New routes:

```text
POST /persistence/seed
GET  /persistence/summary
GET  /audit/export?format=json
GET  /audit/export?format=csv
```

### New migration-ready schema

`migrations/001_batch10_persistence.sql` defines:

```text
source_actions
workflow_records
workflow_events
notification_eligibility
notification_emissions
suppression_state
delivery_status
audit_exports
```

The schema includes immutability triggers for:

```text
source_actions.source_lineage_hash
workflow_records.lineage_hash
workflow_events.lineage_hash
notification_emissions.dedupe_key / lineage hashes
```

### New audit exports

Batch 10 creates both JSON and CSV audit packs:

```text
audit_exports/scip_batch10_audit_export.json
audit_exports/scip_batch10_audit_export.csv
```

Each export includes:

- source action lineage,
- workflow event lineage,
- notification lineage,
- actor,
- timestamp,
- role,
- workflow state,
- closure reason,
- escalation rule evidence,
- dedupe/suppression key,
- delivery state.

### Frontend patch

`App.jsx` now fetches:

```text
/persistence/summary
```

and exposes L5 audit export links:

```text
/audit/export?format=json
/audit/export?format=csv
```

The frontend does not compute business logic. It renders persistence status, table counts, lineage immutability state, and export links only.

## Smoke validation result

```text
30 / 30 checks passed
```

Persisted sample counts from the Batch 10 smoke run:

| Table | Count |
|---|---:|
| source_actions | 100 |
| workflow_records | 100 |
| workflow_events | 105 |
| notification_eligibility | 137 |
| notification_emissions | 137 |
| suppression_state | 137 |
| delivery_status | 137 |
| audit_exports | 2 |

Audit export rows:

```text
JSON export rows: 168
CSV export rows: 168
```

## Key validations

- Lineage hashes remain immutable across persistence round-trips.
- DB triggers block lineage tampering.
- Notification dedupe survives a simulated restart.
- Duplicate notification re-emission is suppressed.
- Closed workflows remain auditable.
- Audit exports include source action lineage, workflow event lineage, notification lineage, actor, timestamp, role, state, and closure/escalation evidence.
- Entity Head remains removed.
- No business computation moved into frontend.

## Production note

SQLite is used for the patch pack because it is dependency-light and migration-ready. Production can port the schema to Postgres or implement it through SQLAlchemy/Alembic with the same table contract.
