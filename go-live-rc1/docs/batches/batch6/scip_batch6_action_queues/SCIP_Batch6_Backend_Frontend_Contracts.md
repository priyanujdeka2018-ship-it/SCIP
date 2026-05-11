# SCIP Batch 6 Backend / Frontend Contracts

## New endpoint: GET `/action-queues`

Returns lineaged action-queue payloads for:

- `collector_rm`
- `cco_gm_agm`
- `finance`
- `mis_qcg_admin`

### Status values

- `ready`: true account-level queue is available.
- `partial_project_grain_account_source_required`: project-level risk cohorts are available, but true account actions are blocked.
- `blocked_missing_r18`: R18 source is missing.

### Top-level shape

```json
{
  "contract_version": "action_queues.v1.batch6",
  "status": "partial_project_grain_account_source_required",
  "snapshot_date": "2026-05-01",
  "source_availability": {
    "R18": "loaded_project_ageing_grain",
    "account_collector_report": "missing_not_attached"
  },
  "data_grain_disclosure": {
    "current_grain": "project_ageing_bucket",
    "true_account_level_available": false,
    "reason": "Current attached R18 sample lacks account ID, customer ID, collector/RM owner, promise-to-pay, and escalation fields."
  },
  "roles": {
    "collector_rm": {},
    "cco_gm_agm": {},
    "finance": {},
    "mis_qcg_admin": {}
  }
}
```

## Role payload shape

```json
{
  "role": "cco_gm_agm",
  "status": "account_source_required",
  "headline": "Project risk cohorts are ready; account owner drilldown is awaiting source onboarding.",
  "disclosure": "No account-level action is shown without account ID, owner mapping, entity mapping, amount/ageing validation, and source lineage.",
  "account_actions": [],
  "project_risk_cohorts": [],
  "blocked_actions": [],
  "required_source_fields": [
    "account_id",
    "customer_id",
    "collector_rm_owner",
    "project",
    "entity",
    "ageing_bucket",
    "overdue_amount",
    "source_lineage"
  ],
  "reporting_basis": "R18 project ageing evidence; true account queues blocked until account/collector source onboarded"
}
```

## Project-risk cohort action shape

```json
{
  "action_id": "cco_gm_agm-R18-Overdue-1-R40-180plus",
  "action_type": "project_risk_cohort",
  "grain": "project_ageing_bucket",
  "status": "available_project_grain",
  "title": "The S · 180+ ageing",
  "summary": "AED 68.9M overdue in Sobha Dubai from R18 project-ageing evidence.",
  "recommended_action": "Review project-level overdue concentration and request account-owner drilldown.",
  "severity": "risk",
  "amount_aed": 68855057.57,
  "ageing_bucket": "180+",
  "project": "The S",
  "entity_code": "sobha_dubai",
  "collector_rm_owner": null,
  "owner_mapping_status": "missing_account_collector_source",
  "lineage_refs": []
}
```

## New endpoint: GET `/action-queues/collector-drilldown`

Returns the Collector/RM drilldown view. In the current sample set this endpoint is intentionally blocked because owner/account source fields are unavailable.

## Frontend rules

- `App.jsx` fetches `/action-queues` only for display.
- No account/action calculations are performed in frontend.
- The action queue panel appears under Live Pulse > Risk & Action.
- Detailed project-risk table appears only when depth is `detailed`.
- Collector tables and risk evidence use solid surfaces.
- Lineage drawer opens from action queue cards.
