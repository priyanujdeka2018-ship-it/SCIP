# SCIP Batch 2 Implementation Report

## Scope

Batch 2 implements production-grade adapters for:

- **R04 Total Daily Collection Report** — Finance daily collection source.
- **R02 MDO Report** — MDO monthly target and actual source.

It preserves Batch 1 decisions:

```text
Group
  Sobha
    Sobha Dubai
    Sobha AUH
  UAQ
    Siniya
    Downtown UAQ
```

It also preserves the approved **0.05% general reconciliation tolerance** and **no silent fallback** rule.

## Important reporting-basis decision now enforced

### R04 = Finance basis

R04 daily sheet exposes:

- `Collection Due` in column C
- `New sales` in column D
- `Total` in column E
- `DLD/Oqood` in column F

SCIP Batch 2 treats R04 column C as **Finance D+A / collection-due** and labels it as Finance. R04 does **not** expose a pure advance split, so `mtd_advance_total` is explicitly marked:

```text
unavailable_in_R04_no_advance_split
```

This is intentional. The platform must not silently infer a pure advance amount from R04.

### R02 = MDO basis

R02 `MDO Dynamic` exposes:

- Dues Target
- Dues actual
- Advance Target
- Current Year Advance actual
- Future Year Advance actual
- Dues + Advance Target
- Dues + Advance actual
- New Sales Target
- New Sales actual
- Total Collections Target
- MTD Total Collections

Batch 2 labels these as **MDO** metrics and keeps them separate from R04 Finance daily metrics.

## Files changed

- `source_adapters.py`
  - Added `R04FinanceDailyAdapter`.
  - Added `R02MDOAdapter`.
  - Kept `R18OverdueAdapter` from Batch 1.
  - Kept R08/R36 as validation scaffolds for Batch 3.

- `data_loader.py`
  - Routes R02/R04 through source-specific adapters.
  - Adds R04 Finance daily series and MTD metrics into computed payload.
  - Adds R02 May/FY MDO target and actual metrics into computed payload.
  - Adds R02/R04 lineage and validations to frontend summary.

- `pipeline_config.json`
  - Updated to v8.2 Batch 2.
  - Added Finance-vs-MDO governance rule.
  - Added adapter classes, validation rules, and metric disambiguation notes.

## R04 extracted values

Source: `R04_Total Daily Collection Report 07-05-2026.xlsx`  
Sheet: `daily`  
Snapshot date: `2026-05-07`

| Metric | Cell | AED |
|---|---:|---:|
| MTD Finance D+A / Collection Due | C40 | 285,457,068.02 |
| MTD New Sales | D40 | 45,459,445.28 |
| MTD Total Collections | E40 | 330,916,513.30 |
| MTD DLD/Oqood | F40 | 4,773,809.64 |
| Monthly Finance D+A Target | C5 | 860,429,189.91 |
| Monthly New Sales Target | D5 | 563,625,000.00 |
| Monthly Total Target | E5 | 1,424,054,189.91 |
| MTD Pro-rata Finance D+A Target | C6 | 253,067,408.80 |
| MTD Pro-rata New Sales Target | D6 | 165,772,058.82 |
| MTD Pro-rata Total Target | E6 | 418,839,467.62 |

R04 loaded 7 actual daily rows through the snapshot date.

## R02 extracted values

Source: `R02_MDO report 06-05-2026.xlsx`  
Sheet: `MDO Dynamic`  
Snapshot date: `2026-05-06`

| Metric | Cell | AED |
|---|---:|---:|
| May MDO Dues Target | H6 | 639,116,739.08 |
| May MDO Advance Target | H8 | 216,273,365.16 |
| May MDO D+A Target | H11 | 855,390,104.25 |
| May MDO New Sales Target | H13 | 150,000,000.00 |
| May MDO Total Collections Target | H15 | 1,005,390,104.25 |
| FY MDO Dues Target | S6 | 10,334,860,910.81 |
| FY MDO Advance Target | S8 | 2,761,187,578.26 |
| FY MDO D+A Target | S11 | 13,096,048,489.07 |
| FY MDO Total Collections Target | S15 | 15,065,628,459.21 |

R02 loaded 918 fact rows across entity, period, and metric combinations.

## Validation results

All Batch 2 smoke tests passed.

### R04 native checks

- Required sheets present.
- Daily sum equals Total MTD for Finance D+A / Collection Due.
- Daily sum equals Total MTD for New Sales.
- Daily sum equals Total MTD for Total Collections.
- MTD D+A plus New Sales equals Total Collections.
- Daily D+A plus New Sales equals Total Collections by day.
- Finance labels are present.

### R02 native checks

- Required sections present.
- Group May dues target equals leaf roll-up.
- Group May advance target equals leaf roll-up.
- Group May D+A target equals leaf roll-up.
- Group May total collections target equals leaf roll-up.
- Group FY dues target equals leaf roll-up.
- Group FY advance target equals leaf roll-up.
- Group FY D+A target equals leaf roll-up.
- Group FY total collections target equals leaf roll-up.

## Known intentional limitation

R04 does not expose pure advance collections. Batch 2 therefore does not invent an R04 advance value. It marks R04 advance as unavailable and expects advance analysis to come from R02/R08.

## Next direction

Batch 3 should implement R08 and R36:

- R08 for advance CY/FY, rebate, entity advance mix, and advance opportunity.
- R36 for milestone cohorts, pipeline gross, forward collectible calendar, and year-wise obligation logic.
