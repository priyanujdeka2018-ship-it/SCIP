# SCIP Batch 5.1 — Liquid Glass Visual System Notes

## Design intent

SCIP should feel like an intelligent boardroom instrument: calm on arrival, fluid in navigation, precise in evidence, and powerful only when the user asks for depth.

## Applied rules

### Two doors only

Arrival now exposes only:

1. Live Pulse
2. Narratives

No role selector, section tree, KPI grid, chart preview, filters, MTD/YTD, or Ops/Board toggle appears at L0.

### Three choices only in Live Pulse

Live Pulse L1 exposes:

1. Current Signal
2. Month Movement
3. Risk & Action

Target Track/YTD is available as a Month Movement curiosity path.

### Glass means movement

Glass is used for:

- arrival cards
- world cards
- context island
- rails and chips
- Quickball capsule
- drawer shell

### Solid means trust

Solid surfaces are used for:

- KPIs
- forecast metric boxes
- primary financial visual
- lineage blocks
- error/fallback states

### Quickball

Quickball is now a bottom command capsule. It remains backend-driven and caps visible follow-up actions to two.

### Evidence

Evidence is not shown by default. Lineage opens in a drawer only after the user clicks Show evidence/View lineage.

### Motion and accessibility

- soft 240–320ms motion tokens
- no bounce/overshoot/sparkle rules
- reduced motion supported
- keyboard focus visible
- aria labels added for arrival, trust bar, drawer, and Quickball capsule

## Tokens

| Token group | Values |
|---|---|
| Foundation | `#080D14`, `#0F1623`, `#172232` |
| Glass | `rgba(255,255,255,0.055)`, `0.085`, `0.12`, blur `26px` |
| Gold | `#C9A84C`, `#E2C76C`, `#8F7434` |
| Text | `#F4EFE5`, `#C8C0B3`, `#8F98A6` |
| Status | `#22C55E`, `#F59E0B`, `#EF4444` |

## What deliberately did not change

- Backend data computations
- Forecast formula ownership
- R04/R02/R08/R18/R36 ingestion layer
- Quickball backend lineage gate
- command-centre API shape
- no-silent-fallback rule
- entity hierarchy
- role model excluding Entity Head
