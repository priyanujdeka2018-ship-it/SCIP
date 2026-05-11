# SCIP Batch 9 — Backend / Frontend Contracts

## Backend routes

```text
GET /notifications
GET /notifications?role=collector_rm&as_of_date=2026-05-09
GET /notifications/digests
GET /notifications/digests?role=finance&as_of_date=2026-05-09
```

## Notification payload

```json
{
  "contract_version": "notifications.v1.batch9",
  "status": "ready_notifications_guarded",
  "as_of_date": "2026-05-09",
  "summary": {
    "notification_count": 138,
    "blocked_candidate_count": 1,
    "by_role": {},
    "by_rule": {},
    "by_severity": {}
  },
  "notifications": [],
  "digests": {},
  "validations": {}
}
```

## Notification object

Required fields:

```text
notification_id
notification_type
rule_id
severity
recipient_role
recipient_role_label
recipient_owner
title
message
recommended_action
world = live_pulse
focus = risk_action
output_layer = L5_notification_output
source_action_id
workflow_id
workflow_state
reporting_basis
confidence_state
lineage.source_action_lineage_refs
lineage.source_lineage_hash
lineage.workflow_event_lineage.latest_event_id
lineage.workflow_event_lineage.workflow_lineage_hash
rule_evidence.rule_id
rule_evidence.as_of_date
suppression.dedupe_key
suppression.suppression_scope
```

## Digest object

Required fields:

```text
digest_id
title
world = live_pulse
focus = risk_action
output_layer = L5_digest_output
as_of_date
notification_count
evidence_notification_ids
aggregate_counts.by_severity
aggregate_counts.by_role
aggregate_counts.by_rule
suppression.dedupe_key
lineage_hashes
```

## Frontend rendering rules

- Fetch `/notifications` alongside `/command-centres`, `/forecast/month-end`, `/action-queues`, and `/workflows`.
- Render notifications only under Live Pulse / Risk & Action.
- Keep dense notification/evidence rows on solid surfaces.
- Use glass surfaces only for L5 notification panel shell and movement/context.
- Show reporting basis, rule evidence, and dedupe key.
- Provide a lineage button for every notification.
- Do not compute escalation rules in frontend.
- Do not add notifications as a third Arrival door.

## Frontend contract file

See `frontend_contracts_batch9.ts`.
