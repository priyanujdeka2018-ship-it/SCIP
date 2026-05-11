# SCIP Batch 15 Backend / Frontend Contracts

## Contract

`adoption_optimization.v1.batch15`

## POST /adoption/record

Records one redacted adoption event.

Required fields:

```json
{
  "world": "live_pulse",
  "focus": "risk_action",
  "depth": "action",
  "event_type": "action_queue_open",
  "session_id": "browser-session-id",
  "properties": {}
}
```

The server derives actor identity from JWT/SSO or local-dev actor context and hashes actor/session identifiers before persistence.

## GET /adoption/summary

Returns aggregate metrics:

- `world_focus_depth_usage`
- `quickball_explanation_usage`
- `evidence_path_opens`
- `action_queue_conversion_rate`
- `workflow_closure_rate`
- `notification_effectiveness`
- `forecast_review_frequency`
- `role_level_engagement`
- `stale_source_impact`
- `uat_to_production_defect_trends`

## GET /adoption/dashboards

Returns three governance briefs:

1. Adoption Experience Brief
2. Operational Conversion Brief
3. Rollout Quality Brief

All are L5 governance outputs and explicitly marked `not_arrival_door: true`.

## GET /adoption/backlog

Returns optimization recommendations with evidence and guardrails. Recommendations must preserve the two-door Liquid Glass model and cannot propose dashboard-first navigation or a third Arrival door.

## Frontend rule

The frontend renders adoption metrics only. It must not compute conversion rates, defect trends, workflow closure, notification effectiveness, or any financial/business metric.
