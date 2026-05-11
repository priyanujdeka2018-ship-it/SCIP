# SCIP Batch 5 Governance and Smoke Checkpoints

## Release gates

A Batch 5 release should not be promoted unless all checks below pass.

### Backend gates

- `forecast.py`, `command_centres.py`, `quickball.py`, `data_loader.py`, `main.py`, and `source_adapters.py` compile with `python -m py_compile`.
- `/forecast/month-end` returns `status = ok` only when R04 actuals and R02 May MDO target have lineage.
- `/command-centres` returns `contract_version = command_centres.v2.batch5`.
- Every card has `reporting_basis`.
- Every card has `lineage_refs` and `lineage_display`.
- No critical card may use an unlineaged metric.
- Forecast must include assumptions and basis disclosure.

### Frontend gates

- App renders role tabs for Board/CXO, CCO/GM/AGM, Finance, MIS/QCG/Admin, and Collector/RM only.
- Entity Head must not appear.
- Data-confidence trust bar is visible.
- Forecast panel is visible and shows assumptions.
- Every card displays reporting basis.
- Every card exposes a lineage drawer action.
- Quickball blocked-answer warning is available.

### Forecast gates

- Forecast input actual = R04 MTD total collections.
- Forecast target = R02 May MDO total collections target.
- Working-day inference lineage comes from R04 month target and R04 MTD pro-rata target.
- Forecast discloses mixed Finance-vs-MDO basis.
- Forecast does not infer unavailable R04 pure advance split.

## Latest smoke result

```text
smoke_batch5_ui_forecast_results.json.overall_passed = true
```

## Latest forecast checkpoints

```text
MTD actual: AED 330.9M
May MDO target: AED 1.005B
Elapsed working days: 5
Total working days: 17
Remaining working days: 12
Projected month-end landing: AED 1.125B
Projected achievement: 111.9%
```

## Known limitation

Batch 5 forecasts at aggregate command-centre level. Account-level action queues and collector drilldowns are intentionally deferred to Batch 6 because they require account/collector source onboarding and lineage.
