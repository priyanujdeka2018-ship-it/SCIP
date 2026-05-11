# SCIP Source File Refresh and Cutover

## Required production source files

### Critical platform intelligence

| R-code | Purpose | Required before go-live |
|---|---|---|
| R02 | MDO targets | Yes |
| R04 | Finance daily collections | Yes |
| R08 | Advance summary / CY-FY / rebate | Yes |
| R18 | OD and ageing | Yes |
| R36 | Milestone pipeline / forward calendar | Yes |

### Account actions and workflow

| R-code | Purpose | Required before account queues go live |
|---|---|---|
| R09 | Project collections | Yes |
| R10 | Dues coverage / PTP / allocation | Yes |
| R17 | SPA / pre-registration legal split | Yes |
| R20 | PR-to-SOA TAT | Yes |
| R30 | Collector feedback/performance | Yes |
| R31 | PR unit update / finance issues | Yes |
| R32 | RM collectors / PR receipts | Yes |
| R34 | Termination status | Yes |
| R38 | Risk analysis | Yes |

## Source refresh checklist

- [ ] Latest file received from source owner.
- [ ] File date matches current operating cycle.
- [ ] File name mapped to correct R-code.
- [ ] Snapshot date extracted.
- [ ] Adapter smoke passed.
- [ ] Lineage coverage is 100% for critical metrics.
- [ ] No silent fallback active.
- [ ] Source owner signs off.

## Source folder convention

```text
/data/scip/r-series/current/R02_*.xlsx
/data/scip/r-series/current/R04_*.xlsx
/data/scip/r-series/current/R08_*.xlsx
/data/scip/r-series/current/R18_*.xlsx
/data/scip/r-series/current/R36_*.xlsx
/data/scip/r-series/current/R09_*.xlsx
...
```

Archive after successful ingestion:

```text
/data/scip/r-series/archive/YYYY-MM-DD/Rxx_filename.xlsx
```
