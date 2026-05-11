# SCIP Batch 1 Implementation Report

## Purpose

Batch 1 implements the ingestion trust foundation for R18 OD. It converts R18 from generic flat-sheet loading into a source-specific positional adapter with metric-level lineage, hierarchy rollups, and smoke-test validations.

## User decisions applied

1. Sobha AUH visibility: under Sobha drilldown first.
2. General reconciliation tolerance: **0.05%** of the relevant reference value.
3. Board/CXO fallback rule: **no silent fallback**. Missing or failed critical metrics must show unavailable/live-warning state.
4. Critical reports: **R18, R04, R02, R08, R36**.
5. Role model: **Board/CXO, CCO/GM/AGM, Finance, MIS/QCG/Admin, Collector/RM**. Entity Head removed.

## Locked hierarchy

```text
Group
  Sobha
    Sobha Dubai = Sub Total A-E
    Sobha AUH   = Sub Total H
  UAQ
    Siniya       = Sub Total F
    Downtown UAQ = Sub Total G
```

## R18 extracted metrics from latest sample

Source: `R18_Consolidated and Overdue 01-05-26.xlsx`  
Sheet: `Overdue-1`  
Snapshot date: `2026-05-01`

| Metric | AED | AED M |
|---|---:|---:|
| OD_SOBHA_DUBAI | 1,582,272,314.75 | 1,582.3M |
| OD_SOBHA_AUH | 80,005,049.23 | 80.0M |
| OD_SOBHA | 1,662,277,363.98 | 1,662.3M |
| OD_SINIYA | 214,282,915.27 | 214.3M |
| OD_DOWNTOWN_UAQ | 17,219,603.96 | 17.2M |
| OD_UAQ | 231,502,519.23 | 231.5M |
| OD_GROUP | 1,893,779,883.21 | 1,893.8M |
| OD_TODAY / Grand Total | 1,893,779,883.21 | 1,893.8M |

## Smoke-test result

`smoke_r18_batch1.py`: **PASSED**  
`smoke_data_loader_batch1.py`: **PASSED**

### Key validation checks

| Check | Result | Difference | Tolerance |
|---|---:|---:|---:|
| OD_SOBHA + OD_UAQ = OD_TODAY | True | 0.000000 | 946,889.94 |
| OD_GROUP = Grand Total | True | 0.000000 | 946,889.94 |
| OD_SOBHA = Sobha Dubai + Sobha AUH | True | 0.000000 | 831,138.68 |
| OD_UAQ = Siniya + Downtown UAQ | True | 0.000000 | 115,751.26 |
| Ageing buckets = OD_TODAY | True | 0.000000 | 946,889.94 |

## Files changed / created

- `source_adapters.py` — new adapter module with `R18OverdueAdapter`.
- `data_loader.py` — patched to call the R18 adapter and expose OD lineage/validations.
- `constants.py` — patched with locked hierarchy, 0.05% tolerance, and `v8-batch1` platform version.
- `file_resolver.py` — patched to include R13/R32 and detect `.xlsb` for future adapters.
- `pipeline_config.json` — upgraded to v8.1 Batch 1 with hierarchy, critical source list, no-silent-fallback rule, and tolerance.
- `smoke_r18_batch1.py` — adapter-level smoke test.
- `smoke_data_loader_batch1.py` — data-loader integration smoke test.

## Integration instruction

Use the files in this folder as a drop-in patch after review. The safest application order is:

1. Copy `source_adapters.py` into the backend module folder.
2. Replace backend `pipeline_config.json`.
3. Replace backend `constants.py`, `file_resolver.py`, and `data_loader.py`.
4. Run `python -m py_compile source_adapters.py data_loader.py constants.py file_resolver.py`.
5. Run `python smoke_r18_batch1.py /path/to/data`.
6. Run `python smoke_data_loader_batch1.py /path/to/data`.
7. Only then start the app.

## Notes

- `OD_DT` remains only as a backward-compatible alias for `OD_DOWNTOWN_UAQ`. Future UI should display `Downtown UAQ`.
- Batch 1 intentionally does not fully implement R02/R04/R08/R36 adapters. It marks them critical in configuration and keeps adapter scaffolds for Batch 2 onward.
- The data-loader smoke status is `partial` overall because many non-attached R-series files are not present in the sample folder. The R18 integration checks passed.
