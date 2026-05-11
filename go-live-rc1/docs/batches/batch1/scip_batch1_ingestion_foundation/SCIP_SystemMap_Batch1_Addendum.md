# SCIP SystemMap Batch 1 Addendum

## Macro purpose retained

SCIP remains a role-aware internal collections command centre. Batch 1 strengthens the trust layer before expanding UI, forecasting, or Quickball.

## Batch 1 source-of-truth update

R18 is now handled by `R18OverdueAdapter`, not by generic row/header ingestion. R18 produces:

- `fact_overdue_snapshot`
- `fact_overdue_ageing`
- `dim_source_lineage`

## Entity hierarchy

```text
Group
  Sobha
    Sobha Dubai
    Sobha AUH
  UAQ
    Siniya
    Downtown UAQ
```

## User role model

Entity Head has been removed from the role model for now. The active hierarchy of product views is:

1. Board/CXO
2. CCO/GM/AGM
3. Finance
4. MIS/QCG/Admin
5. Collector/RM

## Trust contract

Every critical OD number must have:

- source code
- source file
- sheet
- cell/range or rollup formula
- snapshot date
- extraction method
- entity scope
- validation status
- confidence state

## No silent fallback rule

If R18 fails, Board/CXO OD cards must not show stale hardcoded reference values as live. They must show unavailable or labelled fallback/live-warning state.
