# SCIP Batch 17 — Executive Steering Committee Pack

## Frequency
Quarterly, with monthly optimization pre-read

## Standing agenda
- 1. Executive signal: what changed since last review?
- 2. Benefits realization: what value has SCIP delivered?
- 3. Trust review: source freshness, lineage, no-silent-fallback, audit exceptions.
- 4. Operating adoption: action conversion, closure rates, notification effectiveness.
- 5. Roadmap decisions: approve/hold/rollback/retire items.
- 6. Risk and dependency decisions: data warehouse, identity, source owners, process blockers.
- 7. Release train signoff and next-quarter gates.

## Required decision record fields
- decision_id
- decision
- owner
- due_date
- evidence_refs
- expected_impact
- rollout_gate
- rollback_criteria

## Sample decision log
| Decision | Owner | Due date | Evidence | Gate | Rollback |
|---|---|---|---|---|---|
| Approve DW parallel-run scope | Data Engineering + MIS/QCG/Admin | Month 3 review | RM-04 evidence pack | Architecture review + reconciliation harness | Keep workbook adapters as source of truth |
| Approve collector scale-up cohort | CCO/GM/AGM | Month 4 review | RM-05 pilot metrics | RBAC + training + action accuracy | Disable noisy rules and revert to pilot group |
