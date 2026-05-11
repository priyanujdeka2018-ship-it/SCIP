# SCIP Batch 4 Governance and Smoke Checkpoints

## Governance checkpoints

### G1 - Critical metric lineage gate

For every Quickball critical metric, the following fields are mandatory:

```text
source_file
sheet
cell_or_range
validation_status
confidence_state
```

Failure action: Quickball must return `blocked_untrusted_metric`.

### G2 - No silent fallback

Quickball cannot explain a critical metric if its value exists but lineage is missing.

Failure action: blocked answer.

### G3 - Reporting basis visibility

Every explanation and command-centre card must carry a reporting basis:

```text
R18 overdue
Finance
MDO
R08 advance summary
R36 milestone cohort
```

Failure action: UI card must show data-confidence warning.

### G4 - Role model control

Allowed role modes:

```text
Board/CXO
CCO/GM/AGM
Finance
MIS/QCG/Admin
Collector/RM
```

Entity Head remains removed.

### G5 - Collector/RM scope control

Collector/RM mode may show portfolio-level OD and progress signals only. It must not fabricate account-level tasks until account-level reports are onboarded with lineage.

## Smoke checkpoints

Run:

```bash
python smoke_quickball_batch4.py
```

Expected result:

```json
{
  "overall_passed": true,
  "critical_sources_loaded": {
    "R18": "ok",
    "R04": "ok",
    "R02": "ok",
    "R08": "ok",
    "R36": "ok"
  }
}
```

## Checks performed

1. Quickball explains OD, daily collections, MDO targets, advance, rebate, and pipeline metrics.
2. Every explained critical metric has source file, sheet, cell/range, validation status, and confidence state.
3. Every critical answer carries `no_silent_fallback = true`.
4. Every role command centre builds with cards and a trust bar.
5. Every card with metric refs has lineaged metric refs.
6. Negative gate test removes `OD_TODAY` lineage and verifies Quickball blocks the answer.

## Passed Batch 4 result

```json
{
  "overall_passed": true,
  "payload_status": "partial",
  "critical_sources_loaded": {
    "R18": "ok",
    "R04": "ok",
    "R02": "ok",
    "R08": "ok",
    "R36": "ok"
  },
  "negative_lineage_gate_test": {
    "status": "blocked_untrusted_metric",
    "passed": true,
    "reason": "Missing or incomplete lineage for OD_LINEAGE.OD_TODAY"
  }
}
```

`payload_status` is partial because non-critical reports beyond Batch 1-3 are not all onboarded yet. The five critical Batch 4 sources passed.
