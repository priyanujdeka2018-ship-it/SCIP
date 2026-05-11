# SCIP Batch 16 Backend / Frontend Contracts

## Backend routes

```text
GET  /governance/continuous-improvement
POST /governance/continuous-improvement/seed
GET  /governance/monthly-review-pack
POST /governance/improvement-items
GET  /governance/backlog-scoring-model
GET  /governance/templates
```

## Improvement item contract

```json
{
  "title": "Improve Quickball metric synonym mapping",
  "theme": "quickball_trust",
  "evidence_refs": [{"source":"adoption", "metric":"quickball_blocked_rate"}],
  "owner": "quickball_owner",
  "decision": "proposed",
  "expected_impact": "Improve answer success without weakening lineage.",
  "rollout_gate": "pilot",
  "rollback_criteria": "Rollback if any critical answer renders without lineage."
}
```

## Frontend contract
The frontend may display server-provided governance evidence in an L5 governance/evidence panel. It must not compute backlog scoring, adoption conversion, workflow closure, or notification effectiveness locally.

## Forbidden changes
- No third Arrival door.
- No Entity Head role.
- No financial computation in frontend.
- No unlineaged improvement item in monthly review.
