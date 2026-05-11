# SCIP Batch 8 Governance and Smoke Checkpoints

## Governance gates

### Source-action gate

No workflow action can be assigned unless the source action satisfies the Batch 7 gate:

- account ID
- unit
- owner
- entity mapping
- amount or process status
- ageing bucket or process ageing/status
- reporting basis
- confidence state
- source lineage
- role visibility

### Workflow state gate

Allowed states:

```text
queued -> assigned -> in_progress -> promised -> escalated -> closed
queued -> stale
any non-terminal -> blocked only by source/system gate
```

Terminal states:

```text
closed
blocked
```

### Closure gate

Closed records must have:

- closure reason
- actor role
- source lineage hash
- event log entry

### Event log gate

Events must preserve:

- immutable source lineage refs
- lineage hash
- source action ID
- workflow ID
- actor role
- from state
- to state
- timestamp

### Role gate

- Collector/RM cannot self-assign or reassign.
- Collector/RM can update disposition, due date, evidence, and closure only on visible Collector/RM actions.
- Finance cannot assign Collector/RM PTP actions.
- MIS/QCG/Admin has broad governance visibility.
- Entity Head remains removed.

### Liquid Glass gate

- Workflow drawer is glass because it is an L5 command/reveal layer.
- Evidence timeline is solid because it is audit/financial proof.
- No workflow control appears on L0 Arrival.
- Workflow remains under Live Pulse -> Risk & Action.

## Smoke tests run

File: `smoke_batch8_workflow_tracking.py`

Checks passed: 25 / 25.

Validated:

- workflow payload status
- workflow states present
- records generated
- events generated
- records have immutable lineage
- events have immutable lineage hash
- Entity Head removed
- authorised manager can assign
- due date can be set
- collector can update disposition on visible action
- evidence can be attached
- close requires closure reason
- lineage hash remains immutable
- lifecycle events are recorded
- finance cannot assign collector action
- collector cannot self-assign
- unlineaged action assignment is blocked
- frontend fetches `/workflows`
- frontend contains `WorkflowDrawer`
- frontend has no business computation keywords
- backend includes workflow router
- workflow routes exist

## Local deployment checks still required

Run inside the actual app repo:

```bash
npm install
npm run build
npm run dev
```

Run backend locally:

```bash
uvicorn main:app --reload
```

Then verify:

```text
GET /workflows
POST /workflows/assign
POST /workflows/disposition
POST /workflows/evidence
POST /workflows/close
```
