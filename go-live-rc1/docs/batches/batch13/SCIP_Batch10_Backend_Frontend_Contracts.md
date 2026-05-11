# SCIP Batch 10 — Backend and Frontend Contracts

## Contract version

```text
persistence_audit.v1.batch10
```

## Backend routes

### POST /persistence/seed

Seeds durable tables from the current Batch 8 workflow runtime and Batch 9 notifications.

Query/body behaviour in this patch pack:

```text
reset: boolean = true
as_of_date: string = 2026-05-09
```

Returns table counts and runtime counts.

### GET /persistence/summary

Returns persistence status, table counts, validation checks, and available audit routes.

Response shape:

```json
{
  "contract_version": "persistence_audit.v1.batch10",
  "status": "ready_persistence_audit_guarded",
  "generated_at": "...",
  "db_path": "...",
  "table_counts": {
    "source_actions": 100,
    "workflow_records": 100,
    "workflow_events": 105,
    "notification_eligibility": 137,
    "notification_emissions": 137,
    "suppression_state": 137,
    "delivery_status": 137,
    "audit_exports": 2
  },
  "validations": {
    "passed": true,
    "checks": {}
  },
  "routes": [
    "POST /persistence/seed",
    "GET /persistence/summary",
    "GET /audit/export?format=json",
    "GET /audit/export?format=csv"
  ]
}
```

### GET /audit/export?format=json

Returns a JSON audit pack.

### GET /audit/export?format=csv

Returns a CSV audit pack.

## Durable schema contract

Required tables:

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

Required immutable fields:

```text
source_actions.source_lineage_hash
workflow_records.lineage_hash
workflow_events.lineage_hash
notification_emissions.dedupe_key
notification_emissions.source_lineage_hash
notification_emissions.workflow_lineage_hash
```

## Frontend contract

The frontend may display:

- persistence status,
- workflow record count,
- notification emission count,
- suppression key count,
- lineage immutability status,
- closed workflow auditability status,
- export links.

The frontend must not compute:

- eligibility,
- dedupe,
- lineage hash,
- escalation rules,
- persistence validation,
- workflow state transitions.

## Liquid Glass placement

Audit export is an L5 output under Risk & Action. It is not a new Arrival door and not a top-level dashboard. Audit/evidence details should be rendered on solid surfaces.
