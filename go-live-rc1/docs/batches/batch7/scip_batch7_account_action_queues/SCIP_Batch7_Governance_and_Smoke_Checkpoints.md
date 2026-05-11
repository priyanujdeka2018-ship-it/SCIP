# SCIP Batch 7 Governance and Smoke Checkpoints

## Governance rules

1. No account-level action without source lineage.
2. No collector/RM action without owner mapping.
3. No account action without entity mapping.
4. No account action without amount/status and ageing/process validation.
5. No role leakage: Finance does not receive collector PTP call tasks; Collector/RM does not receive finance PR-processing tasks.
6. Entity Head remains removed.
7. Liquid Glass remains progressive-depth: action queues are Live Pulse -> Risk & Action -> L5 output.
8. Dense action rows use solid evidence surfaces.
9. No silent fallback. If a source is missing, the source status must say missing.
10. Frontend does not calculate account action eligibility.

## Smoke checks executed

The smoke suite validates:

- Contract version is `action_queues.v2.batch7`.
- R10/R17/R20/R30/R31/R32/R34/R38/R09 are loaded.
- Collector account actions are unlocked from lineaged R10 + R34 joins.
- Finance PR exception actions are unlocked from R31.
- TAT / process actions are unlocked from R20 and R10 coverage.
- Every visible action has lineage and reporting basis.
- Collector/RM role has no finance PR action.
- Finance role has no collector PTP call action.
- Frontend renders account action cards only inside Risk & Action.
- Entity Head role key is absent.

Result: see `smoke_batch7_action_queues_results.json`.
