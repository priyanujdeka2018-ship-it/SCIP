# SCIP Batch 5 Implementation Report

## Scope

Batch 5 builds the UI-card and month-end forecasting layer on top of the trusted Batch 1-4 ingestion, lineage, Quickball and command-centre contracts.

Preserved guardrails:

- Locked hierarchy: Group > Sobha > Sobha Dubai + Sobha AUH; Group > UAQ > Siniya + Downtown UAQ.
- General reconciliation tolerance: 0.05%.
- No silent fallback for critical metrics.
- Reporting basis labels: R18 overdue, R04 Finance, R02 MDO, R08 advance summary, R36 milestone cohort.
- Role model without Entity Head: Board/CXO, CCO/GM/AGM, Finance, MIS/QCG/Admin, Collector/RM.

## Backend changes

### New `forecast.py`

Adds `GET /forecast/month-end` and `build_month_end_forecast(payload)`.

Forecast logic:

```text
current_daily_run_rate = R04 MTD total collections / elapsed working days
projected_month_end_landing = current_daily_run_rate * total working days
required_daily_run_rate_remaining = max(R02 May MDO target - R04 MTD actual, 0) / remaining working days
gap_to_may_mdo_target = projected_month_end_landing - R02 May MDO target
```

Critical input lineage required:

- `MTD_TOTAL_COLLECTIONS` from R04 `daily!E40`
- `MAY_TOTAL_COLLECTIONS_TARGET` from R02 `MDO Dynamic!H15`

Working-day inference:

- Reads R04 month target total and R04 MTD pro-rata total target.
- Infers elapsed/total working days by matching the pro-rata ratio.
- Latest sample resolves to `5 / 17` working days, with 12 remaining.

### Patched `command_centres.py`

Adds Batch 5 contract extension:

- `contract_version = command_centres.v2.batch5`
- Adds month-end forecast cards for Board/CXO, CCO/GM/AGM and Finance.
- Enforces every card has:
  - `reporting_basis`
  - `lineage_refs`
  - `lineage_display`
  - trust state

Governance cards now carry a platform trust lineage reference so the UI always has a source drawer to open.

### Patched `main.py`

Adds forecast router import and exposes:

- `/forecast/month-end`
- `/command-centres`
- `/quickball/explain`

Version updated to `v8.5 Batch 5`.

## Frontend changes

### New Batch 5 `App.jsx`

Implements:

- Role tabs for the approved role model.
- `/command-centres` fetch and card rendering.
- `/forecast/month-end` fetch and forecast panel rendering.
- Data-confidence trust bar.
- Lineage drawer.
- Blocked-answer warning state.
- Quickball explain box using `/quickball/explain`.
- Forecast assumption disclosure.
- Reporting-basis display on every card.

### New `frontend_contracts_batch5.ts`

Defines TypeScript contracts for:

- Command centres response.
- Role command centre.
- Command-centre card.
- Lineage reference.
- Month-end forecast.
- Quickball explain response.

## Forecast result from latest samples

| Forecast field | Result |
|---|---:|
| R04 MTD total collections | AED 330.9M |
| R02 May MDO total collections target | AED 1.005B |
| Elapsed working days | 5 |
| Total working days | 17 |
| Remaining working days | 12 |
| Current daily run-rate | AED 66.2M |
| Required daily run-rate remaining | AED 56.2M |
| Projected month-end landing | AED 1.125B |
| Gap to May MDO target | AED 119.7M |
| Projected achievement | 111.9% |

Important basis disclosure:

> Actuals are R04 Finance daily collections; targets are R02 MDO targets. This is allowed only with visible basis labelling.

## Validation result

`smoke_batch5_ui_forecast_results.json.overall_passed = true`

Smoke checks prove:

- Critical sources R18/R04/R02/R08/R36 loaded.
- Every command-centre card has reporting basis and lineage display.
- Forecast contains assumptions.
- Forecast critical inputs are lineaged.
- Frontend contains trust bar, lineage drawer, blocked-answer state and forecast panel.
- Frontend role model excludes Entity Head.

## Files changed / added

- `forecast.py` added.
- `command_centres.py` patched.
- `main.py` patched.
- `App.jsx` replaced with Batch 5 command-centre frontend.
- `frontend_contracts_batch5.ts` added.
- `smoke_batch5_ui_forecast.py` added.
- `smoke_batch5_ui_forecast_results.json` added.
- `forecast_month_end_sample_batch5.json` added.
- `command_centres_sample_payload_batch5.json` added.
- `SCIP_Batch6_Next_Prompt.md` added.
