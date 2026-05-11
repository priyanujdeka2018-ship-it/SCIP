# SCIP Batch 1 Governance and Smoke Checkpoints

## Required checkpoints before promoting Batch 1

| Gate | Checkpoint | Pass condition | Owner role |
|---|---|---|---|
| Source presence | R18 file detected by resolver | `R18*.xlsx` found and sheet `Overdue-1` exists | MIS/QCG/Admin |
| Structural extraction | Sub Total A-H found | No missing subtotal labels | MIS/QCG/Admin |
| Hierarchy rollup | Sobha = Sobha Dubai + Sobha AUH | Difference <= 0.05% | MIS/QCG/Admin |
| Hierarchy rollup | UAQ = Siniya + Downtown UAQ | Difference <= 0.05% | MIS/QCG/Admin |
| Group rollup | Sobha + UAQ = OD_TODAY | Difference <= 0.05% | MIS/QCG/Admin |
| Grand total | OD_GROUP = Grand Total | Difference <= 0.05% | MIS/QCG/Admin |
| Ageing | Ageing buckets sum to OD_TODAY | Difference <= 0.05%; warning if failed | MIS/QCG/Admin |
| Lineage | OD metric lineage exists | OD_TODAY, OD_GROUP, OD_SOBHA, OD_UAQ and children have lineage | MIS/QCG/Admin |
| Board trust | No silent fallback | Missing R18 sets OD unavailable/live_warning, not hardcoded reference | Board/CXO trust gate |

## Promotion rule

Batch 1 can be promoted only if the adapter smoke and data-loader smoke pass. If non-R18 sources are missing in the sample folder, that is acceptable for Batch 1 as long as R18 hierarchy checks pass.

## Failure handling

- Missing subtotal: block Board/CXO OD display and show source validation error.
- Rollup mismatch above 0.05%: show live_warning and expose diff/tolerance.
- Missing lineage: block Quickball explain-this-number for the affected metric.
- Missing R18: show unavailable state; do not use fallback values without visible fallback label.
