# SCIP Batch 10 — Governance and Smoke Checkpoints

## Governance checkpoints

### Persistence gate

No source action, workflow event, or notification emission may be persisted unless it has source lineage and lineage hash.

### Immutability gate

Lineage hashes are immutable. Updates that attempt to mutate lineage hashes are blocked by database triggers.

### Notification dedupe gate

Notification emissions use durable `dedupe_key` and `suppression_scope`. Re-running notification generation must not create duplicates.

### Auditability gate

Closed workflows are not deleted. They remain visible in audit export with event history and closure reason.

### Role gate

Entity Head remains removed. Audit records may include only the approved role model:

```text
Board/CXO
CCO/GM/AGM
Finance
MIS/QCG/Admin
Collector/RM
```

### Frontend governance

The frontend renders persistence state and export actions only. It does not compute lineage, workflow state, notification eligibility, dedupe, or escalation rules.

## Smoke checkpoints passed

```text
30 / 30 checks passed
```

Smoke file:

```text
smoke_batch10_persistence_audit_results.json
```

Key checks:

- source actions persisted,
- workflow records persisted,
- workflow events persisted,
- notification emissions persisted,
- suppression state persisted,
- delivery status persisted,
- notification dedupe survives restart,
- second pass emits zero duplicate notifications,
- lineage tampering blocked by DB trigger,
- closed workflows remain auditable,
- JSON audit export created,
- CSV audit export created,
- audit export includes source lineage,
- audit export includes workflow event lineage,
- audit export includes notification lineage,
- audit export includes actor/timestamp/role/state,
- audit export includes closure and escalation evidence,
- Entity Head absent,
- frontend fetches persistence summary,
- frontend links audit exports,
- no business computation in frontend.
