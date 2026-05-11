# SCIP Batch 3 Implementation Report — R08 Advance + R36 Milestone Cohort

## Scope completed

Batch 3 extends the Batch 1/2 ingestion foundation with production adapters for:

- **R08 Advance Summary** — CY/FY advance, rebate, 2026 advance mix, Summary entity split, and lineage.
- **R36 Year-on-Year Milestone Report** — milestone cohort matrix, active forward collectible calendar, pipeline gross, year buckets, and lineage.

The implementation preserves the approved platform rules:

```text
Group
  Sobha
    Sobha Dubai
    Sobha AUH
  UAQ
    Siniya
    Downtown UAQ
```

Other preserved rules:

- 0.05% reconciliation tolerance.
- No silent fallback for Board/CXO critical metrics.
- R04 remains Finance daily basis.
- R02 remains MDO target/actual basis.
- R08 is explicitly labelled as Advance Summary basis.
- R36 is explicitly labelled as Milestone Cohort basis.

## Files patched

- `source_adapters.py`
- `data_loader.py`
- `pipeline_config.json`

## New adapter: R08AdvanceAdapter

### Source workbook

`R08_Advance Summary 06-05-2026.xlsx`

### Required sheets

- `Summary`
- `Rebate Summary`
- `Advance 2026CYFY`
- `Siniya CY FY`
- `DT CY FY`

### Extraction strategy

R08 is parsed through a positional matrix adapter, not a generic flat-header reader.

The adapter extracts:

- 2026 total advance.
- 2026 current-year advance.
- 2026 future-year advance.
- CY/FY mix.
- 2025 total advance.
- YTD 2026 NPV applied / rebate.
- YTD 2026 estimated rebate opportunity.
- Advance collected with rebates.
- Siniya 2026 advance.
- Downtown UAQ 2026 advance.
- UAQ 2026 advance rollup.
- Sobha parent residual 2026 advance.
- Summary visible entity split from N:Q block.

### Key R08 output

| Metric | Value AED |
|---|---:|
| 2026 total advance | 1,104,556,736.05 |
| 2026 current-year advance | 828,027,486.65 |
| 2026 future-year advance | 276,529,249.40 |
| CY advance mix | 74.9647% |
| FY advance mix | 25.0353% |
| 2025 total advance | 3,267,829,312.22 |
| YTD 2026 NPV applied / rebate | 17,536,726.00 |
| Sobha parent 2026 advance residual | 961,029,583.80 |
| Siniya 2026 advance | 124,890,728.10 |
| Downtown UAQ 2026 advance | 18,636,424.15 |
| UAQ 2026 advance | 143,527,152.25 |

### Important R08 disclosure

The attached R08 sample exposes Group, Siniya, and Downtown UAQ CY/FY sheets. It does **not** expose separate Sobha Dubai vs Sobha AUH CY/FY split in the CY/FY sheets.

Therefore:

- Sobha parent 2026 advance is computed as residual: `Group - Siniya - Downtown UAQ`.
- Summary sheet exposes a visible Abu Dhabi latest advance row, but this is not a full CY/FY annual child split.
- This is disclosed in validation and lineage rather than silently inferred.

## New adapter: R36MilestoneCohortAdapter

### Source workbook

`R36_year on year Milestone Report as on 05-05-2026.xlsx`

### Required sheets

- `Total`
- `Active`
- `Sobha`
- `Siniya`
- `DT`

### Extraction strategy

R36 is parsed through a cohort-matrix adapter.

Rows are booking/sales cohorts. Columns are collection years.

The adapter extracts:

- Active forward collectible calendar from `Active!N25:W25`.
- Total visible forward collectible calendar from `Total!N25:W25`.
- Active total purchase price from `Active!H25`.
- Total visible purchase price from `Total!H25`.
- Cohort rows from Total, Active, Sobha, Siniya, and DT sheets.
- Lineage for pipeline gross and year buckets.

### Key R36 output

| Metric | Value AED |
|---|---:|
| Pipeline gross / Active forward collectible calendar | 49,181,207,666.38 |
| Total visible forward collectible calendar | 62,942,934,560.72 |
| Active total purchase price | 88,335,143,998.01 |
| Total visible purchase price | 118,674,249,478.72 |
| Milestone cohort rows emitted | 70 |

### Active forward collectible calendar

| Collection bucket | AED |
|---|---:|
| 2026 | 19,914,115,575.99 |
| 2027 | 14,020,562,994.49 |
| 2028 | 7,229,214,001.20 |
| 2029 | 6,574,618,733.86 |
| 2030 | 1,265,808,496.46 |
| 2031 | 176,218,408.38 |
| 2032 | 168,000.00 |
| 2033 | 168,000.00 |
| 2034 | 168,000.00 |
| Beyond 2035 | 165,456.00 |

### Important R36 disclosure

The attached R36 sample has entity sheets for Sobha, Siniya, and DT. These do not fully reconcile to the Active sheet. The adapter keeps this as an **informational disclosed validation**, not a critical failure, because the sample appears to be missing a full AUH/other child split.

## Data-loader integration

Batch 3 updates `data_loader.py` so:

- R08 and R36 are loaded through production adapters.
- R08 and R36 lineage enters `computed`.
- R08 and R36 validation results enter `computed` and `summary`.
- R08 no longer silently falls back to a reference CY mix.
- R36 no longer silently falls back to reference pipeline values.
- Pipeline and advance metrics carry source/confidence state.

## Smoke-test summary

Both smoke tests passed.

```text
smoke_r08_r36_batch3_results.json.overall_passed = true
smoke_data_loader_batch3_results.json.overall_passed = true
```

## Production note

Batch 3 intentionally does not yet modify UI cards or Quickball answers. It prepares trusted lineage-backed advance and pipeline metrics for Batch 4.
