# SCIP Batch 6 Implementation Report

## Scope

Batch 6 builds account-level action queues and collector drilldowns on top of the Batch 5.1 Liquid Glass UI model and Batch 5 backend contracts.

Preserved guardrails:

- Locked hierarchy: Group > Sobha > Sobha Dubai / Sobha AUH and Group > UAQ > Siniya / Downtown UAQ.
- 0.05% reconciliation tolerance.
- No silent fallback.
- Finance-vs-MDO-vs-R08-vs-R36 reporting labels remain untouched.
- Role model remains without Entity Head.
- Liquid Glass remains a progressive-depth system: action queues are L5 outputs and dense collector evidence is solid, not blurred glass.

## Key finding from the available attached sources

The available R18 workbook exposes project/category/ageing overdue facts in `Overdue-1`, but it does not expose true account ID, customer ID, collector/RM owner, promise-to-pay date, promised amount, or escalation status.

Therefore Batch 6 does **not** invent account-level or owner-level actions. It creates:

1. Lineaged `project_ageing_bucket` facts from R18.
2. Project-risk cohorts for CCO/GM/AGM, Finance, and MIS/QCG/Admin.
3. A blocked Collector/RM queue state that explains the missing account/owner source requirement.
4. A future-ready action-queue contract that will unlock account actions only when account ID + owner + entity + amount + ageing + lineage are present.

## Backend files

- `account_action_queues.py`
  - New FastAPI router for `/action-queues` and `/action-queues/collector-drilldown`.
  - New `R18ProjectAgeingFactAdapter`.
  - Generates lineaged project-ageing facts from `R18 / Overdue-1`.
  - Blocks true account actions when owner/account fields are missing.

- `main.py`
  - Patched to include the action-queue router.
  - Root endpoint now advertises `/action-queues` and `/action-queues/collector-drilldown`.

- `data_loader.py`, `source_adapters.py`, `command_centres.py`, `forecast.py`, `quickball.py`
  - Included from prior trusted batches so this package remains deployable as a patch pack.

## Frontend files

- `App.jsx`
  - Fetches `/action-queues` alongside `/command-centres` and `/forecast/month-end`.
  - Adds `ActionQueuePanel` under Live Pulse > Risk & Action.
  - Does not perform action calculations in frontend.
  - Shows project-risk cohorts as solid evidence surfaces.
  - Shows Collector/RM queue as blocked when owner/account source is missing.

- `liquidGlassTokens.css`
  - Adds Batch 6 styles for action queues.
  - Uses solid evidence surfaces for risk tables and action lists.
  - Keeps Liquid Glass for navigation/context layers only.

## Action queue contract result from current samples

Status: `partial_project_grain_account_source_required`

Facts extracted from R18:

- Project-ageing facts: 746
- Top project risk cohorts: 15
- Eligible account actions: 0

The observation amount is marked non-additive because R18 includes parent project rows and child phase/tower rows. Batch 6 uses each row as lineaged action evidence, not as an additive financial total.

## Safety gates

A true account action requires all of the following:

- `account_id`
- `customer_id` where available
- `collector_rm_owner`
- `project`
- `entity_code`
- `ageing_bucket`
- `amount_aed`
- source lineage with source file, sheet, cell/range, validation status, and confidence state

If any field is missing, the account-level action is blocked.

## Smoke result

`smoke_batch6_action_queues_results.json`

- 38 / 38 checks passed.
- No account-level action is shown without owner/account lineage.
- Collector/RM actions are blocked because the attached sources lack owner fields.
- Project-risk cohorts are lineaged and available to management, finance, and MIS/QCG/Admin.
- Frontend fetches `/action-queues` and keeps the panel gated to Risk & Action.
- No business calculation was moved into the frontend.

## What remains for the next batch

Batch 7 should onboard the missing account/collector source report. Once that source is attached, Batch 7 can unlock true Collector/RM queues with owner assignment, promise tracking, escalation status, and closure workflow.
