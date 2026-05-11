# SCIP Batch 9 — Notification and Escalation Automation

## Status

Batch 9 is implemented as an evidence-driven notification layer on top of Batch 8 workflow assignment and closure tracking.

Contract: `notifications.v1.batch9`  
Status: `ready_notifications_guarded`

## Preserved platform decisions

- Locked hierarchy remains unchanged:
  - Group
    - Sobha
      - Sobha Dubai
      - Sobha AUH
    - UAQ
      - Siniya
      - Downtown UAQ
- General reconciliation tolerance remains `0.05%`.
- No silent fallback remains enforced.
- Reporting-basis labels remain mandatory.
- Role model remains:
  - Board/CXO
  - CCO/GM/AGM
  - Finance
  - MIS/QCG/Admin
  - Collector/RM
- Entity Head remains removed.
- Notifications inherit the Batch 7 account-action gate and Batch 8 immutable workflow event lineage.
- Notifications remain a Liquid Glass L5 output inside Live Pulse / Risk & Action, not a third Arrival door or separate dashboard.

## New backend module

`notifications.py` adds:

- `GET /notifications`
- `GET /notifications/digests`
- deterministic notification generation from workflow records and event logs
- rule evaluation with explicit evidence payloads
- suppression and deduplication keys
- notification-level validation
- daily and weekly digest payloads

## Escalation rules implemented

| Rule | Purpose | Default recipient roles |
|---|---|---|
| `overdue_due_date` | Due date missed while workflow is active | Collector/RM, CCO/GM/AGM |
| `stale_workflow` | Workflow stale or inactive beyond threshold | CCO/GM/AGM, MIS/QCG/Admin |
| `broken_ptp_promise` | PTP date passed while still open/pending | Collector/RM, CCO/GM/AGM |
| `termination_risk` | Legal/termination escalation status present | CCO/GM/AGM, MIS/QCG/Admin |
| `pr_tat_ageing` | PR/SOA/TAT process follow-up required | Finance, MIS/QCG/Admin |
| `unassigned_high_risk` | High-value queued action lacks owner | CCO/GM/AGM, MIS/QCG/Admin |

## Notification types implemented

- `collector_rm_reminder`
- `manager_escalation`
- `finance_exception_nudge`
- `mis_qcg_governance_alert`

## Digest payloads implemented

- `daily_live_pulse_risk_action`
- `weekly_management_review`

Both digests carry:

- evidence notification IDs
- aggregate counts by rule, role, and severity
- suppression/deduplication keys
- lineage hashes from underlying notifications

## Guardrails enforced

No notification is emitted unless it has:

- source action lineage
- workflow event lineage
- role visibility
- due/stale/PTP/process/escalation rule evidence
- reporting basis
- confidence state
- suppression and deduplication key

A deliberately bad unlineaged action was inserted in smoke testing. It triggered rule conditions but was blocked from notification emission.

## Frontend additions

`App.jsx` now fetches `/notifications` and renders:

- `NotificationEscalationPanel`
- `DigestCard`
- role-filtered notification rows
- lineage buttons for notification source evidence
- notification status and digest evidence count

The panel appears under Live Pulse / Risk & Action. Outside Risk & Action, the UI shows a gated L5 capsule explaining that notifications are not a separate dashboard.

## Files changed or added

- `notifications.py` — new backend notification engine and router
- `main.py` — patched to include notifications router
- `App.jsx` — patched with notification/digest UI
- `liquidGlassTokens.css` — patched with notification panel styles
- `frontend_contracts_batch9.ts` — new TypeScript contracts
- `notifications_sample_payload_batch9.json` — generated sample payload
- `smoke_batch9_notifications_results.json` — validation results
- `smoke_batch9_notifications.py` — reproducible smoke harness

## Validation result

Smoke checks passed: `34 / 34`.

Notification summary from sample workflow state:

- Total notifications: `138`
- Blocked candidates: `1`
- Collector/RM reminders: `6`
- Manager escalations: `62`
- Finance nudges: `25`
- MIS/QCG alerts: `45`

Rule coverage:

- Overdue due-date notifications: `2`
- Stale workflow notifications: `1`
- Broken PTP notifications: `10`
- Termination-risk notifications: `74`
- PR/TAT ageing notifications: `50`
- Unassigned high-risk notifications: `1`

## Production notes

This patch pack emits notification contracts only. It does not send external email, Teams, SMS, or WhatsApp messages. Production delivery should be added as a separate worker after RBAC, suppression windows, and approved channel policy are confirmed.

Recommended production delivery design:

1. Persist workflow records and event logs in a durable database.
2. Run notification generation on a schedule or workflow-event trigger.
3. Store emitted notifications with dedupe keys.
4. Deliver through approved channels.
5. Log delivery status separately from notification eligibility.
6. Keep source lineage immutable.
