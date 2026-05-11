# SCIP Batch 7 Backend / Frontend Contracts

## Endpoint

```http
GET /action-queues
GET /action-queues?role=collector_rm
GET /action-queues/collector-drilldown?collector=Farheen
```

## Contract version

```json
{
  "contract_version": "action_queues.v2.batch7",
  "status": "ready_account_level_guarded"
}
```

## Roles

```text
collector_rm
cco_gm_agm
finance
mis_qcg_admin
```

Entity Head remains removed.

## Role payload shape

```ts
{
  role: string,
  status: string,
  headline: string,
  disclosure: string,
  account_actions: AccountAction[],
  process_actions: AccountAction[],
  management_actions: AccountAction[],
  required_source_fields: string[],
  reporting_basis: string
}
```

## AccountAction minimum fields

Every visible account action must include:

```text
action_id
action_type
grain
role_visibility
status
title
summary
recommended_action
severity
account_id
unit
collector_rm_owner
entity_code
amount_aed or process count
ageing_bucket or process status
reporting_basis
confidence_state
lineage_refs[]
```

## LineageRef minimum fields

```text
source_code
source_file
sheet
cell_or_range
validation_status
confidence_state
reporting_basis
```

## Frontend placement

Action queues render only when:

```text
route = live_pulse
focus = risk_action
```

They are an L5 action output / L4 evidence path, not a new dashboard.
