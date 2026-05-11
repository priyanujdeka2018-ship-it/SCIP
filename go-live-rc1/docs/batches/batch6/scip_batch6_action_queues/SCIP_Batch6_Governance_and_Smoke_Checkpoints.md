# SCIP Batch 6 Governance and Smoke Checkpoints

## Governance decisions preserved

- No Entity Head role.
- No silent fallback.
- Account-level actions cannot be fabricated from project-level facts.
- Collector/RM queue requires owner/account lineage.
- Dense action/evidence views are not shown on Arrival or L1.
- Liquid Glass strategy remains progressive depth; solid surfaces are used for financial proof and action tables.

## Required account action fields

A queue item may become a true account action only when all of the following exist:

1. account ID
2. collector/RM owner
3. entity mapping
4. project
5. overdue amount
6. ageing bucket
7. source lineage
8. validation status
9. confidence state

Optional but recommended for prioritisation:

- customer ID / customer name
- promised amount
- promised date
- escalation status
- last contact date
- legal/termination status

## Batch 6 smoke checkpoints

The smoke test validates:

- `/action-queues` contract version.
- R18 source is loaded.
- Account/collector source is disclosed as missing.
- Project-ageing facts are extracted.
- Top project-risk cohorts exist.
- Eligible account actions are zero when owner/account fields are missing.
- Collector/RM actions are blocked without owner source.
- All project-risk cohorts carry lineage.
- All actions carry reporting basis.
- Frontend fetches `/action-queues`.
- Frontend action queue panel is gated to Risk & Action.
- Frontend uses solid evidence table for dense queue proof.
- Frontend does not perform action-queue calculations.

## Smoke output

`smoke_batch6_action_queues_results.json`

Current result:

```text
38 / 38 passed
```
