# SCIP Batch 5.1 — Liquid Glass UI System Alignment

## Purpose

Batch 5.1 upgrades the Batch 5 frontend from a role-dashboard layout into the locked Liquid Glass interaction model while preserving the Batch 1–5 backend contracts, ingestion trust layer, Quickball lineage gate, forecasting contract, and role model without Entity Head.

## Source of truth applied

`SCIP_Liquid_Glass_UI_Strategy_Final_Unified.docx` was treated as the locked visual/product execution source. The implementation follows the strategy that SCIP should feel like an intelligent briefing rather than a dashboard, with two doors, progressive depth, evidence on demand, and Liquid Glass used only for movement/context/reveal/command.

## Files changed

| File | Status | Purpose |
|---|---|---|
| `App.jsx` | Patched | Refactored Batch 5 frontend into Liquid Glass arrival, world homes, focus screens, trust bar, forecast panel, lineage drawer, and Quickball capsule. |
| `liquidGlassTokens.css` | New | Sobha Liquid Slate token layer: foundations, glass opacity, blur, gold accents, solid truth surfaces, motion/accessibility rules. |
| `forecast.py` | Preserved from Batch 5 | No backend forecast contract change. |
| `command_centres.py` | Preserved from Batch 5 | No backend command-centre contract change. |
| `main.py` | Preserved from Batch 5 | Existing endpoints preserved. |
| `frontend_contracts_batch5_1.ts` | Preserved from Batch 5 | Contract remains compatible. |
| `smoke_batch5_1_liquid_glass.py` | New | Static smoke checks for strategy, lineage, forecast assumptions, and no frontend financial computation. |
| `smoke_batch5_1_liquid_glass_results.json` | New | Validation results. |

## Experience changes

### L0 Arrival

Implemented the locked two-door arrival:

- Live Pulse — What needs attention now?
- Narratives — The story behind the numbers.

Arrival has no role tabs, no sidebar, no KPI grid, no chart, no section tree, no entity filter, and no Ops/Board language.

### Live Pulse

Implemented three L1 choices only:

- Current Signal
- Month Movement
- Risk & Action

Target Track/YTD is kept as a deep-link curiosity from Month Movement, not as a fourth first-level card.

### Narratives

Implemented the guided rail:

- Story
- Portfolio
- Dues
- Advance
- Roadmap

Narratives now behave like an executive journey rather than a menu of equal dashboards.

### Progressive depth

The UI now separates:

- world: Live Pulse / Narratives
- focus: current signal, month movement, risk/action, story, portfolio, dues, advance, roadmap
- depth: Summary / Detailed / Executive
- evidence: lineage drawer opened only after request
- action: Quickball / evidence / detailed lens / future Present/export/action paths

### Role model

Entity Head remains removed. The role model is preserved as an internal audience lens after entry:

- Board/CXO
- CCO/GM/AGM
- Finance
- MIS/QCG/Admin
- Collector/RM

This keeps role-specific payloads while avoiding role/mode clutter on Arrival.

## Visual changes

Implemented Sobha Liquid Slate tokens:

- foundation: `#080D14`, `#0F1623`, `#172232`
- glass: `rgba(255,255,255,0.055)`, `0.085`, `0.12`, blur `26px`
- gold: `#C9A84C`, `#E2C76C`, `#8F7434`
- text: `#F4EFE5`, `#C8C0B3`, `#8F98A6`
- status: `#22C55E`, `#F59E0B`, `#EF4444`

Glass is applied to:

- arrival shell and doors
- context island
- world homes
- rails/chips
- Quickball command capsule
- lineage drawer shell

Solid truth surfaces are applied to:

- KPI cards
- forecast metric boxes
- primary financial visual
- lineage/evidence blocks
- error states

## Preserved contracts and guardrails

- `/command-centres` preserved
- `/forecast/month-end` preserved
- `/quickball/explain?metric=<metric>&role=<role>` preserved
- no-silent-fallback preserved
- forecast assumptions visible
- reporting basis visible on cards
- lineage drawer still displays source, sheet, cell/range, validation, confidence, and basis
- Quickball answers remain backend-driven
- Quickball follow-up actions capped to two
- no business computation moved into the frontend

## Validation result

`smoke_batch5_1_liquid_glass_results.json` and `jsx_transpile_check_batch5_1.json`

Static strategy checks:

```json
{
  "overall_passed": true,
  "checks_total": 22,
  "checks_passed": 22,
  "checks_failed": 0
}
```

TypeScript JSX transpile check also passed with zero diagnostics.

## Build note

This package includes static validation and JSX transpile validation. Full Vite build should still be run in the deployment repo after copying `App.jsx` and `liquidGlassTokens.css` into the frontend source directory:

```bash
npm install
npm run build
npm run dev
```

No backend code needs to be replaced for Batch 5.1 unless you want a single deploy bundle with the copied Batch 5 backend files included here.
