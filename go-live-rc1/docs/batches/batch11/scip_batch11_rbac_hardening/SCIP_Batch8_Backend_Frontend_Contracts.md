# SCIP Batch 8 Backend / Frontend Contracts

## Contract version

`workflow.v1.batch8`

## GET `/workflows`

### Query params

| Param | Optional | Values |
|---|---|---|
| `role` | Yes | collector_rm, cco_gm_agm, finance, mis_qcg_admin |

### Response shape

```json
{
  "contract_version": "workflow.v1.batch8",
  "status": "ready_workflow_tracking_guarded",
  "generated_at": "2026-05-09T...Z",
  "workflow_states": ["queued", "assigned", "in_progress", "promised", "escalated", "closed", "stale", "blocked"],
  "guardrails": {},
  "permission_model": {},
  "summary": {
    "workflow_count": 101,
    "event_count": 105,
    "state_counts": {},
    "lineaged_event_count": 105
  },
  "records": [],
  "event_log": [],
  "validations": {}
}
```

## Workflow record

```json
{
  "workflow_id": "wf::collector_ptp::...",
  "source_action_id": "collector_ptp::...",
  "action_type": "collector_ptp_follow_up",
  "grain": "account_unit",
  "workflow_state": "queued",
  "assigned_owner": "Collector name",
  "due_date": null,
  "disposition": null,
  "closure_reason": null,
  "evidence_attachments": [],
  "source_snapshot": {},
  "immutable_lineage_refs": [],
  "lineage_hash": "sha256...",
  "source_gate": {
    "assignable": true,
    "failures": []
  }
}
```

## Event log

```json
{
  "event_id": "evt_...",
  "workflow_id": "wf::...",
  "source_action_id": "collector_ptp::...",
  "event_type": "assigned",
  "actor_role": "cco_gm_agm",
  "actor": "Head Collections",
  "from_state": "queued",
  "to_state": "assigned",
  "event_payload": {},
  "immutable_lineage_refs": [],
  "lineage_hash": "sha256...",
  "created_at": "2026-05-09T...Z"
}
```

## POST `/workflows/assign`

```json
{
  "action_id": "collector_ptp::...",
  "assignee": "Collector name",
  "actor": "Manager name",
  "actor_role": "cco_gm_agm",
  "due_date": "2026-05-15",
  "note": "Optional"
}
```

## POST `/workflows/reassign`

```json
{
  "action_id": "collector_ptp::...",
  "assignee": "New owner",
  "actor": "Manager name",
  "actor_role": "cco_gm_agm",
  "note": "Optional"
}
```

## POST `/workflows/due-date`

```json
{
  "action_id": "collector_ptp::...",
  "due_date": "2026-05-15",
  "actor": "User name",
  "actor_role": "collector_rm",
  "note": "Optional"
}
```

## POST `/workflows/disposition`

```json
{
  "action_id": "collector_ptp::...",
  "disposition": "Customer contacted; promised payment",
  "next_state": "promised",
  "actor": "Collector name",
  "actor_role": "collector_rm",
  "note": "Optional"
}
```

Allowed non-terminal `next_state`: assigned, in_progress, promised, escalated, stale.

Terminal updates must use `/workflows/close` or blocked system handling.

## POST `/workflows/evidence`

```json
{
  "action_id": "collector_ptp::...",
  "evidence_type": "call_note",
  "evidence_ref": "CALL-20260509-001",
  "actor": "Collector name",
  "actor_role": "collector_rm",
  "note": "Optional"
}
```

## POST `/workflows/close`

```json
{
  "action_id": "collector_ptp::...",
  "closure_reason": "Payment received / promise captured / issue resolved",
  "evidence_ref": "CALL-20260509-001",
  "actor": "Manager name",
  "actor_role": "cco_gm_agm",
  "note": "Optional"
}
```

Closure reason is mandatory.

## Permissions

| Role | Assign | Reassign | Due date | Disposition | Evidence | Close |
|---|---:|---:|---:|---:|---:|---:|
| Collector/RM | No | No | Yes | Yes | Yes | Yes |
| CCO/GM/AGM | Yes | Yes | Yes | Yes | Yes | Yes |
| Finance | Yes for finance-visible actions | Yes | Yes | Yes | Yes | Yes |
| MIS/QCG/Admin | Yes | Yes | Yes | Yes | Yes | Yes |

Board/CXO is intentionally read-only in this workflow batch.

## Frontend contract

The frontend must:

- fetch `/workflows`
- never calculate workflow eligibility locally
- display workflow state counts from backend
- open workflow details only from Risk & Action / action list context
- show workflow drawer as glass movement surface
- show event/evidence timeline as solid evidence surface
- never display Entity Head role
