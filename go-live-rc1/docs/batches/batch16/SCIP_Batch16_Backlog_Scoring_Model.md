# SCIP Batch 16 Backlog Scoring Model

Formula:

```text
((reach * impact * confidence) / effort) + trust_risk_reduction + adoption_lift + operational_value
```

Priority bands:

- P0: >= 30
- P1: >= 20
- P2: >= 12
- P3: < 12

Hard blocks override score: missing evidence, missing owner, missing rollback criteria, silent fallback, missing lineage, Entity Head role, third Arrival door, or frontend business computation.
