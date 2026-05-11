# SCIP Batch 3 Governance and Smoke Checkpoints

## Governance rules applied

1. **Critical source files**
   - R08 and R36 are critical reports.
   - Missing or invalid source data must show as unavailable or warning.
   - Board/CXO views must not receive silent fallback values.

2. **Tolerance**
   - General reconciliation tolerance: **0.05%**.
   - Tolerance is calculated as `abs(reference_value) * 0.0005`.

3. **Lineage requirement**
   Every critical R08/R36 aggregate must carry:
   - source code,
   - source filename,
   - sheet,
   - cell/range,
   - snapshot date where available,
   - extraction method,
   - entity scope,
   - validation status,
   - confidence state.

4. **Hierarchy rule**

```text
Group
  Sobha
    Sobha Dubai
    Sobha AUH
  UAQ
    Siniya
    Downtown UAQ
```

5. **Disclosure rule**
   If a workbook does not expose a requested child split, the adapter must disclose this instead of inferring unsupported values.

## R08 smoke gates

| Gate | Severity | Status |
|---|---|---|
| Required sheets present | Critical | Passed |
| CY + FY = 2026 advance total | Critical | Passed |
| CY/FY total = Summary 2026 advance | Critical | Passed |
| Rebate Summary 2026 advance = CY/FY total | Warning | Passed |
| Entity child split disclosure | Info | Passed |

## R36 smoke gates

| Gate | Severity | Status |
|---|---|---|
| Required sheets present | Critical | Passed |
| Active row total = Active purchase price | Critical | Passed |
| Total row total = Total purchase price | Critical | Passed |
| Active forward year buckets = pipeline gross | Critical | Passed |
| Total forward buckets = visible total forward calendar | Critical | Passed |
| Pipeline constants labelled | Critical | Passed |
| Entity sheets roll up to Active | Info | Disclosed; not a failure |

## Data-loader smoke gates

| Gate | Status |
|---|---|
| R08 live source loaded | Passed |
| R36 live source loaded | Passed |
| R08 confidence live_validated | Passed |
| R36 confidence live_validated | Passed |
| R08 lineage present | Passed |
| R36 lineage present | Passed |
| No silent R08 fallback | Passed |
| No silent R36 fallback | Passed |
| R08 CY/FY reconciles | Passed |
| R36 forward calendar reconciles | Passed |

## Known disclosed limitations for next batches

1. R08 does not expose Sobha Dubai vs Sobha AUH full CY/FY child split in the attached CY/FY sheets.
2. R36 entity sheets do not fully reconcile to Active in the sample; likely missing AUH/other breakdown.
3. R08 average advance lead days remains unavailable in Batch 3 adapter scope and should not silently fall back in Board view.
4. Project-level R36 drilldown is not present in the attached R36 sample; current extraction is entity/cohort/year level.
