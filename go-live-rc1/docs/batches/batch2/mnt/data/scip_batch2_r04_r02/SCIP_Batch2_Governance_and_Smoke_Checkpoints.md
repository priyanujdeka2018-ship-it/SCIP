# SCIP Batch 2 Governance and Smoke Checkpoints

## Governance rules added

### 1. Finance-vs-MDO disambiguation

Every R04 metric must carry:

```text
reporting_basis = Finance
```

Every R02 metric must carry:

```text
reporting_basis = MDO
```

Dashboard cards and Quickball answers must never call an R04 number an MDO number, or vice versa.

### 2. R04 advance split rule

R04 does not expose pure advance split.

Allowed state:

```text
mtd_advance_total = null
mtd_advance_status = unavailable_in_R04_no_advance_split
```

Not allowed:

```text
mtd_advance_total = 0
mtd_advance_total = inferred silently
mtd_advance_total = fallback without label
```

### 3. Tolerance rule

All reconciliation checks use the approved general rule:

```text
0.05% of reference value
```

### 4. Source lineage rule

Each high-level extracted metric must include:

```text
metric_key
metric_label
value
unit
source_code
source_file
sheet
cell_or_range
snapshot_date
extraction_method
entity_scope
business_definition
validation_status
confidence_state
reporting_basis
```

### 5. User hierarchy rule

The active user roles remain:

```text
Board/CXO
CCO/GM/AGM
Finance
MIS/QCG/Admin
Collector/RM
```

Entity Head remains removed.

## Batch 2 smoke checkpoints

### R04

| Rule | Severity |
|---|---|
| R04_REQUIRED_SHEETS_PRESENT | Critical |
| R04_DAILY_SUM_EQUALS_TOTAL_MTD_DA | Critical |
| R04_DAILY_SUM_EQUALS_TOTAL_MTD_NEW_SALES | Critical |
| R04_DAILY_SUM_EQUALS_TOTAL_MTD_TOTAL_COLLECTIONS | Critical |
| R04_MTD_DA_PLUS_NS_EQUALS_TOTAL | Critical |
| R04_DAILY_DA_PLUS_NS_EQUALS_TOTAL_BY_DAY | Warning |
| R04_FINANCE_TARGET_LABEL_PRESENT | Critical |
| R04 advance split explicitly unavailable | Critical |

### R02

| Rule | Severity |
|---|---|
| R02_REQUIRED_SECTIONS_PRESENT | Critical |
| R02_MAY_DUES_TARGET_GROUP_EQUALS_LEAF_ROLLUP | Critical |
| R02_MAY_ADVANCE_TARGET_GROUP_EQUALS_LEAF_ROLLUP | Critical |
| R02_MAY_DA_TARGET_GROUP_EQUALS_LEAF_ROLLUP | Critical |
| R02_MAY_TOTAL_COLLECTIONS_TARGET_GROUP_EQUALS_LEAF_ROLLUP | Critical |
| R02_FY_DUES_TARGET_GROUP_EQUALS_LEAF_ROLLUP | Critical |
| R02_FY_ADVANCE_TARGET_GROUP_EQUALS_LEAF_ROLLUP | Critical |
| R02_FY_DA_TARGET_GROUP_EQUALS_LEAF_ROLLUP | Critical |
| R02_FY_TOTAL_COLLECTIONS_TARGET_GROUP_EQUALS_LEAF_ROLLUP | Critical |
| May/FY target lineage present | Critical |

## Release gate

Batch 2 is safe to merge into the ingestion branch only if:

```text
smoke_r04_r02_batch2_results.json.overall_passed = true
smoke_data_loader_batch2_results.json.overall_passed = true
```

Current result:

```text
passed
```
