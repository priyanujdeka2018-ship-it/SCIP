# SCIP Batch 4 Implementation Report

## Batch 4 purpose

Batch 4 builds the trusted user-facing intelligence layer on top of the Batch 1-3 ingestion foundation.

It does **not** change the R-series extraction logic. Instead, it introduces:

1. Quickball lineage-first explanations.
2. Role-specific command-centre payloads.
3. Backend/frontend API contracts.
4. Smoke tests proving no critical Quickball answer uses an unlineaged metric.

## Locked decisions preserved

| Decision | Batch 4 status |
|---|---|
| Entity hierarchy | Preserved: Group > Sobha/UAQ; Sobha > Sobha Dubai/Sobha AUH; UAQ > Siniya/Downtown UAQ |
| General reconciliation tolerance | Preserved at 0.05% |
| Board/CXO no-silent-fallback | Preserved and enforced by Quickball lineage gate |
| Critical ingestion layer | R18, R04, R02, R08, R36 |
| Role model | Board/CXO, CCO/GM/AGM, Finance, MIS/QCG/Admin, Collector/RM |
| Entity Head role | Removed |
| Finance-vs-MDO labels | Preserved: R04 actuals = Finance; R02 targets/actuals = MDO |
| R08/R36 labels | Preserved: R08 advance summary; R36 milestone cohort |

## Files added or patched

| File | Purpose |
|---|---|
| `quickball.py` | New lineage-first Quickball router and explanation engine |
| `command_centres.py` | New role-specific command-centre payload builder |
| `main.py` | Patched FastAPI entrypoint to include Quickball router safely |
| `pipeline_config.json` | Metadata updated for Batch 4 contract and role model |
| `constants.py` | Platform version updated to `v8.4 Batch 4` |
| `frontend_contracts_batch4.ts` | Frontend TypeScript contract for Quickball and command-centre payloads |
| `SCIP_Batch4_Backend_Frontend_Contracts.md` | Human-readable endpoint and payload contract |
| `smoke_quickball_batch4.py` | Smoke test for Quickball lineage gate and command centres |
| `smoke_quickball_batch4_results.json` | Smoke-test result |
| `quickball_sample_answers_batch4.json` | Sample Quickball answer payloads |
| `command_centres_sample_payload_batch4.json` | Sample command-centre payload |
| `quickball_metric_catalog_batch4.json` | Full metric catalogue used by Quickball |

## Quickball design

Quickball now answers “explain this number” using a metric catalogue.

A critical metric answer requires:

- metric value,
- source file,
- source sheet,
- cell/range,
- validation status,
- confidence state,
- reporting basis,
- role-specific interpretation.

If any required lineage field is missing, the answer is blocked with:

```text
status = blocked_untrusted_metric
```

This means Quickball cannot silently explain a fallback or untraceable number.

## Quickball supported critical metric families

| Family | Source | Examples |
|---|---|---|
| OD | R18 | `OD_TODAY`, `OD_SOBHA`, `OD_UAQ`, `OD_SOBHA_DUBAI`, `OD_SOBHA_AUH` |
| Daily collections | R04 | `MTD_TOTAL_COLLECTIONS`, `MTD_DA_TOTAL`, `MTD_NS_TOTAL` |
| MDO targets | R02 | `MAY_DA_TARGET`, `MAY_TOTAL_COLLECTIONS_TARGET`, `FY_TOTAL_COLLECTIONS_TARGET` |
| Advance | R08 | `ADVANCE_2026_TOTAL`, `ADVANCE_2026_CY`, `ADVANCE_2026_FY`, `CY_ADV_MIX_YTD`, `YTD_2026_REBATE` |
| Milestone pipeline | R36 | `PIPELINE_GROSS`, `PIPELINE_FORWARD_2026`, `PIPELINE_FORWARD_2027`, `PIPELINE_FORWARD_2028` |

## Role modes implemented

### Board/CXO

Purpose: decision clarity, source trust, cash risk, and strategic forward visibility.

Cards:

- Current OD exposure.
- MTD total collections.
- 2026 advance mix.
- Forward collectible calendar.

### CCO/GM/AGM

Purpose: daily operating review, intervention queue, and month-end pacing.

Cards:

- MTD collections vs May MDO target.
- Sobha OD.
- UAQ OD.
- MTD new-sales collections.

### Finance

Purpose: reconciliation, reporting-basis control, and audit traceability.

Cards:

- Finance actual vs MDO target basis.
- YTD 2026 rebate / NPV applied.
- Pipeline gross source control.

### MIS/QCG/Admin

Purpose: source freshness, validation, smoke gates, and release governance.

Cards:

- Critical lineage coverage.
- Missing sources.

### Collector/RM

Purpose: frontline action focus without unverified account-level claims.

Cards:

- OD follow-up pool.
- MTD collection progress signal.

Account-level tasking remains intentionally blocked until lineaged account-level reports are onboarded.

## Smoke result

`smoke_quickball_batch4_results.json` passed.

Key result:

```json
{
  "overall_passed": true,
  "critical_sources_loaded": {
    "R18": "ok",
    "R04": "ok",
    "R02": "ok",
    "R08": "ok",
    "R36": "ok"
  },
  "negative_lineage_gate_test": {
    "status": "blocked_untrusted_metric",
    "passed": true
  }
}
```

The negative gate test deliberately removed `OD_TODAY` lineage. Quickball correctly refused to answer.

## Sample Quickball answers

### OD_TODAY

Group overdue today is AED 1.894B. Reporting basis: R18 overdue. Source: R18_Consolidated and Overdue 01-05-26.xlsx / sheet Overdue-1 / cell or range O204. Validation: passed; confidence: live_validated.

### MTD_TOTAL_COLLECTIONS

MTD total collections is AED 330.9M. Reporting basis: Finance. Source: R04_Total Daily Collection Report 07-05-2026.xlsx / sheet daily / cell or range E40. Validation: passed; confidence: live_validated.

### MAY_DA_TARGET

May MDO D+A target is AED 855.4M. Reporting basis: MDO. Source: R02_MDO report 06-05-2026.xlsx / sheet MDO Dynamic / cell or range H11. Validation: passed; confidence: live_validated.

### ADVANCE_2026_TOTAL

2026 total advance is AED 1.105B. Reporting basis: R08 advance summary. Source: R08_Advance Summary 06-05-2026.xlsx / sheet Advance 2026CYFY / cell or range B18. Validation: passed; confidence: live_validated.

### PIPELINE_GROSS

Pipeline gross / active forward collectible calendar is AED 49.181B. Reporting basis: R36 milestone cohort. Source: R36_year on year Milestone Report as on 05-05-2026.xlsx / sheet Active / cell or range N25:W25. Validation: passed; confidence: live_validated.

## Known constraints after Batch 4

1. Collector/RM mode is still portfolio-level because account-level lineaged reports are not yet onboarded.
2. Quickball is deterministic and local-data based. It does not yet use an LLM prompt layer.
3. Command-centre cards are payload contracts, not final UI cards.
4. Forecasting is intentionally deferred to Batch 5.

## Deployment guidance

1. Replace backend `quickball.py` with this Batch 4 file.
2. Add `command_centres.py` beside backend modules.
3. Replace `main.py` if the current deployment still has an unguarded Quickball import.
4. Replace `pipeline_config.json` and `constants.py` with the Batch 4 versions if using the Batch 3 folder as the active backend.
5. Run:

```bash
python smoke_quickball_batch4.py
```

6. Only release the role command-centre UI after smoke output shows:

```text
overall_passed = true
```
