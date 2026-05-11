# SCIP Batch 4 Backend and Frontend Contracts

## Contract version

```text
quickball.v1.batch4
command_centres.v1.batch4
```

## Backend endpoints

### GET `/quickball`

Returns Quickball status, role model, metric catalogue count, and guardrails.

Minimum response:

```json
{
  "status": "ok",
  "mode": "lineage_first",
  "roles": {},
  "metric_catalog_count": 29,
  "guardrails": {
    "no_silent_fallback": true,
    "critical_metrics_require_lineage": true,
    "reporting_basis_required": true
  }
}
```

### GET `/quickball/explain?metric=<metric>&role=<role>`

Explains a trusted metric.

Supported roles:

```text
board_cxo
cco_gm_agm
finance
mis_qcg_admin
collector_rm
```

Supported metric examples:

```text
OD_TODAY
MTD_TOTAL_COLLECTIONS
MAY_DA_TARGET
ADVANCE_2026_TOTAL
CY_ADV_MIX_YTD
YTD_2026_REBATE
PIPELINE_GROSS
PIPELINE_FORWARD_2026
```

Successful response:

```json
{
  "status": "answered",
  "metric_key": "OD_TODAY",
  "metric_label": "Group overdue today",
  "display_value": "AED 1.894B",
  "reporting_basis": "R18 overdue",
  "source_code": "R18",
  "answer": "...",
  "lineage": {
    "source_file": "R18_Consolidated and Overdue 01-05-26.xlsx",
    "sheet": "Overdue-1",
    "cell_or_range": "O204",
    "validation_status": "passed",
    "confidence_state": "live_validated"
  },
  "guardrail": {
    "critical_metric": true,
    "no_silent_fallback": true,
    "requires_lineage": true,
    "lineage_gate_passed": true
  }
}
```

Blocked response:

```json
{
  "status": "blocked_untrusted_metric",
  "metric_key": "OD_TODAY",
  "reason": "Missing or incomplete lineage for OD_LINEAGE.OD_TODAY",
  "guardrail": {
    "critical_metric": true,
    "no_silent_fallback": true,
    "requires_lineage": true
  }
}
```

Frontend rule: render blocked responses as a trust warning, not as a normal answer.

### GET `/quickball/sample-answers`

Returns representative sample answers for smoke/demo use.

### GET `/command-centres`

Returns all role-specific command-centre payloads.

### GET `/command-centres/{role}`

Returns one command centre.

## Command-centre response shape

```json
{
  "status": "ok",
  "contract_version": "command_centres.v1.batch4",
  "role_order": ["board_cxo", "cco_gm_agm", "finance", "mis_qcg_admin", "collector_rm"],
  "roles": {
    "board_cxo": {
      "role_label": "Board/CXO",
      "purpose": "Decision clarity, source trust, cash risk, and strategic forward visibility.",
      "trust_bar": {},
      "cards": []
    }
  },
  "guardrails": {
    "no_silent_fallback": true,
    "critical_cards_require_lineage_refs": true,
    "finance_vs_mdo_label_required": true,
    "entity_head_removed": true
  }
}
```

## Command-centre card shape

```json
{
  "card_id": "board_od_exposure",
  "title": "Current OD exposure",
  "value": 1893779883.21,
  "display_value": "AED 1.894B",
  "reporting_basis": "R18 overdue",
  "action": "Review Sobha/UAQ split before executive action review.",
  "severity": "risk",
  "lineage_refs": [
    {
      "metric_key": "OD_TODAY",
      "lineage_bucket": "OD_LINEAGE",
      "lineage_key": "OD_TODAY",
      "has_lineage": true,
      "source_file": "R18_Consolidated and Overdue 01-05-26.xlsx",
      "sheet": "Overdue-1",
      "cell_or_range": "O204",
      "validation_status": "passed",
      "confidence_state": "live_validated"
    }
  ],
  "trust_state": "lineaged"
}
```

Frontend rule: every card with `trust_state != "lineaged"` must show a data-confidence warning.

## Trust bar shape

```json
{
  "snapshot_date": "2026-05-01",
  "load_timestamp": "...",
  "platform_version": "v8.4 Batch 4",
  "sources_loaded": ["R18", "R04", "R02", "R08", "R36"],
  "sources_missing": [],
  "critical_sources": ["R18", "R04", "R02", "R08", "R36"],
  "critical_lineage_counts": {
    "R18": 15,
    "R04": 12,
    "R02": 17,
    "R08": 19,
    "R36": 14
  },
  "no_silent_fallback": true,
  "tolerance_pct": 0.05
}
```

## UI rendering requirements

1. Always show reporting basis beside the value.
2. Always expose source lineage in hover/detail drawer.
3. Do not show blocked Quickball responses as normal answers.
4. Do not compare R04 Finance actuals and R02 MDO targets without displaying both labels.
5. Keep `Entity Head` removed from role tabs.
6. Collector/RM cards must not claim account-level action lists until account-level lineage exists.

## Frontend role tabs

Display order:

```text
Board/CXO
CCO/GM/AGM
Finance
MIS/QCG/Admin
Collector/RM
```

Do not include Entity Head.
