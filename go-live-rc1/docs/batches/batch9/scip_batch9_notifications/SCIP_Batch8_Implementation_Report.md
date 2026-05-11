# SCIP Batch 8 Implementation Report

## Purpose
Batch 8 adds workflow assignment and closure tracking on top of Batch 7 account-level action queues while preserving the Batch 5.1 Liquid Glass experience model.

Batch 8 does **not** create a new homepage or dashboard. Workflow remains an L5 action/output layer opened from Live Pulse -> Risk & Action, with a glass workflow drawer and solid evidence timeline.

## Preserved rules

- Locked entity hierarchy: Group > Sobha(Sobha Dubai, Sobha AUH) + UAQ(Siniya, Downtown UAQ)
- General reconciliation tolerance: 0.05%
- No silent fallback
- Reporting-basis labels remain visible
- Entity Head remains removed
- Batch 7 account-action gate is inherited
- No frontend financial or workflow computation
- Dense evidence remains solid, not glass

## New backend module

### `workflow.py`

Adds:

- Workflow states: queued, assigned, in_progress, promised, escalated, closed, stale, blocked
- In-memory workflow store for patch pack review
- Immutable event log
- Lineage hash per workflow/action
- Role permission model
- Backend functions for:
  - assignment
  - reassignment
  - due-date update
  - disposition update
  - evidence attachment
  - closure
  - stale marking

Production implementation should replace the in-memory store with durable workflow tables using the same contract.

## New API routes

| Route | Method | Purpose |
|---|---|---|
| `/workflows` | GET | List workflow records and event log |
| `/workflows/{action_id}` | GET | Get one workflow record and its events |
| `/workflows/assign` | POST | Assign an action |
| `/workflows/reassign` | POST | Reassign an action |
| `/workflows/due-date` | POST | Set or update due date |
| `/workflows/disposition` | POST | Update disposition and non-terminal state |
| `/workflows/evidence` | POST | Attach evidence reference |
| `/workflows/close` | POST | Close action with closure reason |
| `/workflows/stale` | POST | Mark action stale |

## Workflow gate

No action can be assigned unless it has:

- source action ID
- account/unit identity
- owner
- entity mapping
- amount/status
- ageing/process status
- reporting basis
- confidence state
- immutable source lineage references
- role visibility

## Event log contract

Every event contains:

- event ID
- workflow ID
- source action ID
- event type
- actor role
- actor
- from state
- to state
- event payload
- immutable source lineage references
- lineage hash
- timestamp

The event log copies lineage references from the original source action. It does not mutate source facts or re-resolve lineage.

## Frontend changes

### `App.jsx`

Adds:

- fetch for `/workflows`
- workflow state summary on the action queue panel
- workflow button on account-action cards
- `WorkflowDrawer`
- solid evidence timeline
- visible workflow contract note that assign/close operations are backend-controlled

### `liquidGlassTokens.css`

Adds:

- workflow drawer glass shell
- workflow summary cards
- workflow action control row
- solid evidence timeline table
- responsive layout

## Validation summary

Smoke checks passed: 25 / 25.

Main checks:

- workflow payload ready
- states present
- records generated
- all records lineaged
- all events lineaged
- assignment succeeds for authorised manager
- collector can update disposition but cannot self-assign
- finance cannot assign collector action
- unlineaged action cannot be assigned
- closure reason is required
- lineage hash remains immutable after workflow lifecycle
- frontend fetches `/workflows`
- frontend has workflow drawer
- frontend does not perform business computation
- `main.py` includes workflow router

## Current sample output

The smoke run generated:

- 101 workflow records
- 105 workflow events
- 82 queued
- 1 closed by smoke lifecycle
- 18 blocked by source gate or role/state protection

The sample payload is included as `workflow_sample_payload_batch8.json`.
