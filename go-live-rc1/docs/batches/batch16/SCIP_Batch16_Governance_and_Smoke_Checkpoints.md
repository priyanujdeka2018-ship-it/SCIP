# SCIP Batch 16 Governance and Smoke Checkpoints

## Smoke checkpoints
1. Governance router imports successfully.
2. Migration schema contains all required governance tables.
3. Sample monthly review pack includes improvement items.
4. Every improvement item has evidence, owner, decision, expected impact, rollout gate, and rollback criteria.
5. Backlog scoring returns a priority band.
6. Entity Head is not present in role labels or sample governance items.
7. Liquid Glass guardrail is attached to every improvement item.
8. Frontend contains L5 governance panel only; no third Arrival door string is introduced.
9. Main app includes governance router.
10. No governance item may approve changes that weaken no-silent-fallback or lineage gates.

## Manual deployment checkpoints
- Run migration 006 in staging before production.
- Seed governance samples only in non-production or as approved admin operation.
- Review monthly pack in pilot before enabling production review cadence.
