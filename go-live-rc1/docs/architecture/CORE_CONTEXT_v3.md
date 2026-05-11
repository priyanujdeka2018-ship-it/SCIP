# Sobha Collections Intelligence Platform
## CORE_CONTEXT v3.0 — v9.1 Build Reference

**Authority:** v9.1 Master Architecture — March 2026 consolidated decisions
**Supersedes:** CORE_CONTEXT v2.0 (v6 Streamlit build — fully obsolete)
**Tech Stack:** React (frontend) + FastAPI (backend)
**Status:** Approved for Phase 5 engineering build
**Date:** March 2026

---

## Part 0 — Operating Model

| Field | Value |
|---|---|
| Platform | Sobha Collections Intelligence Platform |
| Owner | Priyanuj Deka — AGM Dues, Sobha Realty Dubai |
| Development | Claude AI — sole engineering resource |
| Team role | Source data refresh only — no platform code responsibility |
| Deployment authority | Priyanuj only — GitHub Desktop push = deployment |
| Data governance | Priyanuj reviews all source files before any push to live platform |

**Confirmed reporting lines (S07 must use these — strategy doc org chart is factually wrong):**

| Team | Lead | Dubai | India | Total |
|---|---|---|---|---|
| QCG | Garima | 2 | 10 | 12 |
| MIS | Asjad | 6 | 9 | 15 (India growing) |
| Mathews team | Mathews Babu | 15 | 23 | 38 (India growing) |
| RMs direct to Priyanuj | — | 12 | — | 12 |
| RMs via Rohan → Akkad | — | 12 | — | 12 |

**CCO:** Ashish · **GM Advance:** Manuraj · **AGM Dues Dubai:** Priyanuj · **AGM UAQ:** Karan · **AGM Siniya:** Akkad

---

## Part 1 — Two-Tier Architecture

v9.1 is a production two-tier web application. The prior single-file HTML+JS and Streamlit approaches are fully superseded. One GitHub repository. Two top-level folders. One shared data layer.

```
┌─────────────────────────────────────────────────────────────┐
│           SOBHA COLLECTIONS INTELLIGENCE PLATFORM           │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  FRONTEND — REACT                     │  │
│  │                                                       │  │
│  │   ┌──────────────────┐  ┌──────────────────────────┐  │  │
│  │   │    OPS MODE      │  │      BOARD MODE           │  │  │
│  │   │ Daily collections│  │  C-suite / Board /        │  │  │
│  │   │ Team performance │  │  Investor presentation    │  │  │
│  │   │ Calculator tools │  │  Narrative-first layout   │  │  │
│  │   │ Deep analytics   │  │  Full-screen mode         │  │  │
│  │   └──────────────────┘  └──────────────────────────┘  │  │
│  │                                                       │  │
│  │   ┌───────────────────────────────────────────────┐   │  │
│  │   │         QUICKBALL — PERSISTENT PANEL          │   │  │
│  │   │  Embedded AI assistant. Floats in both modes. │   │  │
│  │   │  Calls backend. No cross-URL jumps.           │   │  │
│  │   └───────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                  │
│                   HTTP API calls                             │
│                           │                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                 BACKEND — FASTAPI                     │  │
│  │  Computation engine. Business logic. Claude API relay.│  │
│  │  Pre-aggregates R-series → ~100KB JSON for frontend.  │  │
│  │  Claude API key held server-side only.                │  │
│  │  SUBMODULE_MANIFEST lives here.                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                  │
│                   reads /data folder                         │
│                           │                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           SHARED DATA LAYER — GitHub /data            │  │
│  │  R-series xlsx files. One push refreshes both tiers.  │  │
│  │  Backend reads via raw GitHub URL on every request.   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Frontend

| Field | Value |
|---|---|
| Hosting | Netlify (free permanent tier) |
| URL | sobha-collections.netlify.app |
| Stack | React + Recharts / Plotly.js |
| Deployment | Auto-deploy on GitHub push via GitHub Desktop |
| Data | Fetches pre-aggregated ~100KB JSON from backend on load. Never reads raw R-series files directly. |
| Offline | Core content cached after initial load. Both modes available offline. Quickball shows graceful offline state. |

### Backend

| Field | Value |
|---|---|
| Prototype hosting | Render (free permanent tier) |
| Production hosting | Google Cloud Run (always-free tier — future migration, zero code change) |
| Stack | Python + FastAPI (~200–300 lines total) |
| API key | ANTHROPIC_API_KEY as Render environment variable only. Never in any file, Drive folder, or repository. |
| State | Stateless. No database. No persistent storage. |
| Warming | Frontend pings /health every 10 min. UptimeRobot secondary 5-min ping backup. |
| R-series reads | openpyxl only. xlsx format only. No xlsb, PDF, or Word. |

---

## Part 2 — Data Pipeline

### Source format rule (non-negotiable)
All R-series files: **xlsx only**. Single file per report. Multi-sheet files (e.g. R08 — 24 sheets) kept intact. Non-xlsx file triggers graceful degradation — never a crash.

### Pipeline flow

```
Team (Asjad / Garima / Mathews)
  → Export from ERP as xlsx
  → Drop into shared Google Drive staging folder

Priyanuj (sole authority)
  → Reviews file in Drive (spot-check key metrics)
  → Downloads → drags into GitHub Desktop /data folder
  → Commit → Push (2–3 min total)

Backend (automated)
  → data_loader.py reads xlsx via openpyxl on next request
  → pipeline_config.json defines column mappings
  → Pre-aggregates to ~100KB JSON for frontend
  → SNAPSHOT_DATE read from file metadata — never hardcoded
  → Missing/malformed file → graceful degradation with
    "data pending refresh" label. Never an error to user.
```

> **Rule:** Google Drive is staging only. GitHub /data is the authoritative platform data source. Backend reads raw GitHub URL — never Drive directly.

---

## Part 3 — Mode Architecture

Mode toggle is a React state variable. Switching re-renders section content. Header, Quickball, and filters persist across mode switches. URL reflects mode: `?mode=ops` (default) or `?mode=board`.

### Ops Mode — Default

| Field | Value |
|---|---|
| Primary users | AGM Dues, RMs, Collectors, Ops leads, MIS |
| Layout | Sidebar navigation + main content area. Dense display. |
| Sections | All Context sections + full Live Pulse section |
| Charts | Plotly interactive — hover, zoom enabled |
| Filters | Entity toggle + Target version toggle |

### Board Mode

| Field | Value |
|---|---|
| Primary users | CCO, GM Advance, Board members, Investors |
| Layout | Full-width narrative panels. Minimal chrome. Large typography. |
| Sections | S01, S02, S04, S05, S08 only (summary variants). S06, S07, Live Pulse hidden. |
| Charts | Recharts static. Clean. Print-friendly. |
| Filters | Entity toggle retained. Target version toggle hidden. |
| Presentation | ?mode=present removes header and Quickball. Font scale 140%. Arrow key navigation. Quickball via keyboard shortcut during Q&A. |

### Section visibility by mode

| Section | Ops Mode | Board Mode |
|---|---|---|
| S01 Strategic Narrative | Full | Summary — curated headline version |
| S02 Portfolio Overview | Full | Summary — KPI strip + headline chart |
| S04 Dues Collections | Full | Summary — OD position, IC flag, trend |
| S05 Advance Collections | Full | Summary — penetration, rebate, mix |
| S06 Operations & QCG | Full | Hidden |
| S07 Team Structure | Full | Hidden |
| S08 Strategic Roadmap | Full | Summary — top 3 initiatives |
| Live Pulse (all layers) | Full | Hidden entirely |

---

## Part 4 — Quickball Architecture

Quickball is a persistent floating panel — an embedded AI assistant, not a navigation router. Operates identically in both modes. Calls backend → backend calls Claude API via `ANTHROPIC_API_KEY`. No key in client.

### Every Quickball response carries all three:

```
[AI Annotation]
2–3 sentence interpretation in context of current data.
References actual metrics from computed dict.

[Summary Panel]
Target submodule rendered in mode="summary" inline.
Answer appears without navigating away from current section.

[Action Buttons — up to 3]
  "See full section →"    Scrolls to section in same mode
  "Run [Tool name] →"     Opens calculator panel inline
  "Switch to Board view"  Toggles mode — same app
```

### SUBMODULE_MANIFEST

- Location: `/backend/manifest.json`
- Claude maintains. Updated when submodules are added.
- Contains every submodule: question it answers, mode(s), audience, calculator flag, related submodules.
- Backend serves to frontend on load. Quickball routing uses this at query time.

### Guided Workflows (pre-written prompt buttons)

**Workflow A — "Prepare for board meeting"**
Step 1 → S01 Strategic Narrative | Step 2 → S02 Portfolio Overview | Step 3 → Live Pulse Snapshot | Step 4 → Stress Test Tool | Step 5 → S08 Roadmap

**Workflow B — "Review collector performance"**
Step 1 → Live Pulse SM5 collectors | Step 2 → Live Pulse SM6 coverage | Step 3 → Run Rate Calculator

**Workflow C — "Morning operations check"**
Step 1 → Live Pulse SM1 MTD | Step 2 → S04 SM1 OD Today | Step 3 → Coverage gaps

### Operational rules

| Rule | Detail |
|---|---|
| Cold start | Eliminated by 10-min frontend health ping + UptimeRobot 5-min backup |
| API cost | Identical queries cached 1 hour in backend. Usage logging active. |
| Offline | Graceful "AI unavailable" state. Navigation and tools still work. |
| Session memory | Conversation in React state for browser session only. Resets on tab close — accepted. |

---

## Part 5 — File Structure

```
/
├── /frontend
│   └── /src
│       ├── App.jsx                  Shell. Mode state. Header. Zero business logic.
│       ├── navigation.jsx           Mode-aware two-level nav. Zero business logic.
│       ├── ModeToggle.jsx           [Ops] [Board] toggle. Updates ?mode= URL param.
│       ├── filters.jsx              Entity + Target version toggles. URL param state.
│       ├── Quickball.jsx            Floating panel. Calls backend. Offline graceful state.
│       └── /components
│           ├── /context
│           │   ├── S01/             Strategic Narrative submodule components
│           │   ├── S02/             Portfolio Overview submodule components
│           │   ├── S04/             Dues Collections submodule components
│           │   ├── S05/             Advance Collections submodule components
│           │   ├── S06/             Operations submodule components
│           │   ├── S07/             Team Structure (confirmed org only)
│           │   └── S08/             Strategic Roadmap submodule components
│           ├── /pulse
│           │   ├── /snapshot/       Current period submodule components
│           │   ├── /insights/       Deep analytical insight components
│           │   ├── ToolRunRate.jsx
│           │   ├── ToolProjection.jsx
│           │   ├── ToolStressTest.jsx
│           │   └── PulseDefinitions.jsx
│           └── /shared
│               ├── KpiStrip.jsx
│               ├── ChartPanel.jsx
│               ├── TrendPanel.jsx
│               ├── InsightBlock.jsx
│               └── DefinitionBlock.jsx
│
├── /backend
│   ├── main.py                      FastAPI entry. Routes only. Zero business logic.
│   ├── constants.py                 Structural constants only. No imports.
│   ├── pipeline_config.json         Column mappings per R-series source.
│   ├── data_loader.py               Reads xlsx via openpyxl. Returns computed dict.
│   ├── utils.py                     Formatting helpers. Imports constants only.
│   ├── quickball.py                 Claude API relay. 1-hr cache. Usage logging.
│   ├── manifest.json                SUBMODULE_MANIFEST. Claude maintains.
│   ├── /endpoints
│   │   ├── context.py               All Context section endpoints
│   │   ├── pulse.py                 All Pulse layer endpoints
│   │   ├── tools.py                 All calculator tool endpoints
│   │   └── health.py                /health ping endpoint
│   └── /pipeline
│       └── schema_core.json         R-series file manifest and schema
│
└── /data
    └── [R-series xlsx files]        Team → Drive staging → Priyanuj reviews → GitHub push
```

---

## Part 6 — Global Submodule Standards

### Six canonical types — no others permitted

| Code | Name | Rule |
|---|---|---|
| `KPI_STRIP` | Headline Metrics Strip | 3–8 numbers. Always top of section. |
| `CHART_PANEL` | Visual Data Panel | One data theme. Current-period only. |
| `TREND_PANEL` | Longitudinal View | Multi-year/period only. Distinct from CHART_PANEL — never combined. |
| `INSIGHT_BLOCK` | Narrative Callouts | Flags, alerts, editorial context. |
| `DEFINITION_BLOCK` | Business Rules | Formulas, governance. Always bottom of section. |
| `JOURNEY_PANEL` | Process Swimlane | Customer or operational flow. Max 1 per section. |

> **Rule:** Each submodule has exactly one responsibility. Mixed responsibility = mandatory split.

### Submodule function signature (non-negotiable)

Every React component accepts:
```
{ data, computed, filters, mode }
```

Every FastAPI endpoint function:
```python
def get_{section}_{submodule}(
    computed: dict,
    filters: dict,
    mode: str = "full"
) -> dict
```

`mode="full"` → complete submodule for section view
`mode="summary"` → compact version for Quickball surfacing
`mode="board"` → board-appropriate version where relevant

No exceptions. No alternative calling conventions in either tier.

---

## Part 7 — Global Constants and Business Logic

### Structural constants — `constants.py` (never refreshed)

| Constant | Value | Notes |
|---|---|---|
| `WORKING_DAYS_MONTH` | 21 | March 2026 calendar. Never hardcode 22. |
| `ENTITY_LIST` | [Sobha, Siniya, DT, Group] | — |
| `TARGET_VERSIONS` | [MDO Dues, Finance Dues] | — |
| `MDO_DUES_FY_2026` | 11,500M | — |
| `MDO_ADV_FY_2026` | 4,000M | — |

### Derived constants — owned by `data_loader.py` via `pipeline_config.json`

| Constant | Value | Source | Label required |
|---|---|---|---|
| `OD_TODAY` | Refreshed on load | R18 | Never hardcode |
| `OD_SOBHA` | 1,472.7M | R18 derived | — |
| `OD_SINIYA` | 166.4M | R18 derived | — |
| `OD_DT` | 11.0M | R18 derived | — |
| `PIPELINE_GROSS` | 43.5B | R36 | "Total Forward Pipeline" |
| `PIPELINE_FORWARD_BOOK` | ~40B | Narrative | "~Opening 2025 Book" |
| `PIPELINE_ADV_DENOM` | 37.8B | R36 derived (43.5B − 5.7B) | "2026 Penetration Denominator" — S05, S08 only |
| `CY_ADV_MIX_YTD` | 81.1% | R08 | Computed once — referenced in S01/S03/S05. Never recompute. |
| `AVG_ADVANCE_LEAD_DAYS` | 248 days | R08 | — |
| `SNAPSHOT_DATE` | From file metadata | pipeline | Never manually entered |
| `DAILY_DAYS[]` | Array | R04 | Single array. No duplicates. |

> **Pipeline disambiguation rule:** `PIPELINE_GROSS` ≠ `PIPELINE_FORWARD_BOOK` ≠ `PIPELINE_ADV_DENOM`. Always display with inline label. Never show an unlabelled pipeline figure.

> **Target disambiguation rule (always labelled on-screen):**
> MDO Dues = 700.5M Jan · Dues only · Dynamic mid-year · R02
> Finance Dues = 909M Jan · D+A combined · Static · R04

> **Units disambiguation rule (always labelled on-screen):**
> `active_excl_pcc` = 30,044 → use for app adoption%, coverage calculations
> `all_qualified_itd` = 34,731 → use for portfolio count, hero card

### Canonical formula rules — never recalculated per submodule

| Metric | Formula | Critical note |
|---|---|---|
| `od_pct` | `od_aed ÷ ms_due_itd_aed × 100` | **NEVER** ÷ `purchase_price_aed` |
| `efficiency_30d` | `dues_collected_aed ÷ booksize_bom_aed × 100` | 2025 avg = 34.8%. Deprecated 18% is wrong. |
| `book_penetration` | `annual_advance_aed ÷ PIPELINE_ADV_DENOM × 100` | Denominator must carry label |
| `achievement_pct` | `actual_aed ÷ target_aed × 100` | Label MDO vs Finance explicitly on every display |
| `channel_share_pct` | `app_txn_count ÷ total_da_txn_count × 100` | COUNT only. Never AED value. |
| `da_cagr` | `(12,966M ÷ 867M)^(1/4) − 1` | = 97% |
| `mdo_daily_avg` | `monthly_dues_target ÷ WORKING_DAYS_MONTH` | WORKING_DAYS_MONTH = 21 |
| NPV figures | 652M / 21M / 31M | Always label **[PROJECTED]**. Never label Actual. |
| `collector_achievement` | `actual ÷ target × 100` | Collector chart always sorted DESC by achievement% |
| Jan 2025 CY% | 70.1% | 30% was FY% — deprecated. Never use 30% as CY. |

---

## Part 8 — Section Map

### S01 — Strategic Narrative (`sec-story`)
**Audience:** C-suite, Board · **Mode:** Full (Ops) / Curated headline (Board)

| Ref | Submodule | Type | Responsibility | Source |
|---|---|---|---|---|
| SM1 | Annual Collections Story | `KPI_STRIP` + `CHART_PANEL` | Entity annual stacked bars + CAGR 97%, 15× growth, entity 2025 totals | R01, R26 |
| SM2 | Collections Composition | `TREND_PANEL` | Mix % trend 2021–2025 (annual + monthly); LP charges; units by year | R01, R08, R26, R03 |
| SM3 | Advance Narrative | `KPI_STRIP` | Advance growth KPIs + c-adv-qtr (quarterly acceleration). NPV KPIs **[PROJECTED]**. No 3yr monthly chart. | R08 |
| SM4 | Portfolio Risk Profile | `CHART_PANEL` | Nationality bar + OD% line (c-nat); CIV band bar + OD% line (c-civ) | R16 |
| SM5 | Narrative Callouts | `INSIGHT_BLOCK` | Growth inflection; LP acceleration; NPV rebate ROI; top-risk nationality flags | Derived |
| SM6 | Metric Definitions | `DEFINITION_BLOCK` | OD% formula; NPV methodology; CAGR formula; [PROJECTED] label rule | Global |

> Advance data in S01 = KPI-only. No charts duplicated from S05. Exception: c-adv-qtr (quarterly acceleration story — not in S05).

---

### S02 — Portfolio Overview (`sec-overview`)
**Audience:** Dept head, Finance, Senior leadership · **Mode:** Full (Ops) / KPI strip + headline chart (Board)

| Ref | Submodule | Type | Responsibility | Source |
|---|---|---|---|---|
| SM1 | Portfolio Snapshot | `KPI_STRIP` + `JOURNEY_PANEL` | 86B / 43.3B (50.3%) / 43.5B pipeline / 1,650.1M OD + 6-node payment journey | R13, R18, R36, R08, R20 |
| SM2 | MDO Target Performance | `CHART_PANEL` + `KPI_STRIP` | 9-month grouped bars; FY targets; Q1 achievement | R02 |
| SM3 | Finance Target Performance | `CHART_PANEL` + `KPI_STRIP` | Finance D+A bars; Finance vs MDO disambiguation | R04 |
| SM4 | Target Achievement Summary | `KPI_STRIP` | FY Dues 11.5B; FY Advance 4.0B; Q1 MDO 91%; Q1 Advance 73%; Q1 NS 31% ⚠ | R02, R04 |
| SM5 | UAE Market Context | `INSIGHT_BLOCK` | 214,912 tx / 682.5B / 65–72% off-plan / Sobha #4 ~10% share | External static |
| SM6 | Target Definitions | `DEFINITION_BLOCK` | MDO Dues vs Finance Dues; entity split logic; NS target basis | R02, R04 |

> Entity-level OD lives here (Sobha/Siniya/DT). Group-level OD analysis lives in S04. c-mdo2 removed — purpose unconfirmed.

---

### S03 — Live Pulse (`sec-pulse`)
**Audience:** Ops lead, AGM, Daily review · **Mode:** Ops only (hidden in Board)

| Ref | Submodule | Type | Responsibility | Source |
|---|---|---|---|---|
| SM1 | MTD Snapshot | `KPI_STRIP` | Dues MTD / Advance MTD / NS MTD ⚠ / daily MDO avg (÷ WORKING_DAYS_MONTH) | R04–R07 |
| SM2 | Daily Bar Charts | `CHART_PANEL` | c-daily + entity panels filtered via entity_toggle | R04–R07 |
| SM3 | YTD Achievement | `KPI_STRIP` | Q1 Dues 91% / Advance 73% / NS 31% ⚠ / CY mix 81.1% | R02, R04, R08 |
| SM4 | YTD Trend Charts | `CHART_PANEL` | Monthly MDO target vs actual (c-ytd-dues); Advance CY/FY entity stacked (c-ytd-adv) | R02, R08 |
| SM5 | Collector Performance | `CHART_PANEL` | Horizontal bars **sorted DESC by achievement%**; top/bottom table; PTP | R30, R32 |
| SM6 | Coverage & Channel | `CHART_PANEL` | 5-bucket coverage bars + current-period channel doughnut (COUNT basis) | R10, R25 |
| SM7 | Performance Flags | `INSIGHT_BLOCK` | NS critical gap; Siniya 86.2% gap (198 units / 319M); collector outlier flags | Derived |
| SM8 | Operational Definitions | `DEFINITION_BLOCK` | MDO daily avg formula; achievement% formula; coverage% formula | Global |

> Collector data always labelled "Snapshot: Mar 2026 MTD". DAILY_DAYS[] centralised — no per-section re-declaration.

---

### S04 — Dues Collections (`sec-dues`)
**Audience:** AGM Dues, Collections ops, Risk function · **Mode:** Full (Ops) / OD position + IC flag (Board)

| Ref | Submodule | Type | Responsibility | Source |
|---|---|---|---|---|
| SM1 | OD Position | `KPI_STRIP` | OD_TODAY / entity split / collectible window / EOM projection / 30d efficiency | R18, R02, R12 |
| SM2 | OD Snapshot | `CHART_PANEL` | Ageing doughnut + project ranking bar + SPA bar + IC risk heatmap | R18, R17, R38 |
| SM3 | OD Progression | `TREND_PANEL` | Monthly OD ageing evolution — distinct from snapshot in SM2 | R12, R18 |
| SM4 | Collection Efficiency | `CHART_PANEL` | 30d efficiency trend; termination pipeline | R12, R34 |
| SM5 | OD Flags & Risk Alerts | `INSIGHT_BLOCK` | IC threshold advisory 907.7M / 251 units; Skyvue 1.27B / 535 units; termination gap 134.6M | R38, R34 |
| SM6 | Dues Definitions | `DEFINITION_BLOCK` | OD% formula; 30d efficiency formula; 55d window (T-25/T+30); termination eligibility | Global |

> IC threshold flag = advisory only. Policy decision in standalone board business case — not on platform.

---

### S05 — Advance Collections (`sec-advance`)
**Audience:** AGM Dues, Advance team, GM Advance · **Mode:** Full (Ops) / Penetration + rebate summary (Board)

| Ref | Submodule | Type | Responsibility | Source |
|---|---|---|---|---|
| SM1 | Advance KPIs | `KPI_STRIP` | Advance growth KPIs | R08 |
| SM2 | Monthly Advance | `CHART_PANEL` | c-adv-monthly | R08 |
| SM3 | CY/FY Mix & Penetration | `KPI_STRIP` | CY mix 81.1%; penetration KPIs | R08, R36 |
| SM4 | Entity Advance Trend | `CHART_PANEL` | c-adv-ent | R08 |
| SM5 | Book Penetration | `KPI_STRIP` | 8.15% (2025) → 10.6% target (2026) | R08, R36 |
| SM6 | Rebate Strategy | `INSIGHT_BLOCK` | References S01 NPV finding by name only — **no NPV numbers here** | R08 + S01 ref |
| SM7 | Advance Definitions | `DEFINITION_BLOCK` | **PIPELINE_ADV_DENOM = 37.8B defined here only.** Not re-explained anywhere else. | R36 |
| SM8 | 3yr Monthly Overlay | `TREND_PANEL` | c-adv-hist — exclusively here. Single render only. | R08 |

---

### S06 — Operations & QCG (`sec-ops`)
**Audience:** Garima (QCG), Asjad (MIS), AGM Dues · **Mode:** Ops only (hidden in Board)

| Ref | Submodule | Type | Responsibility | Source |
|---|---|---|---|---|
| SM1 | QCG Quality Metrics | `KPI_STRIP` | PR 1st-pass 51%; doc gap 27%; manual error 23%; visibility gap 250–300M | R31 |
| SM2 | PR Quality & PCC TAT | `CHART_PANEL` | PR quality doughnut + PCC TAT bar | R31, R20 |
| SM3 | TAT Milestones | `KPI_STRIP` | PCC TAT: 20d pre → 3–5d post → 2d target; PR-SOA 0–2d: 25%→35%→51% | R20 |
| SM4 | Payment Channels & TAT | `CHART_PANEL` | 9-channel 3yr grouped bar (c-paych, COUNT); PR-SOA TAT band progression | R25, R20 |
| SM5 | Channel Metrics | `KPI_STRIP` | App: 0.1%→6%→25.9% YTD; wire 43.5%; PR-SOA 0–2d 51% | R25, R20 |
| SM6 | Other Charges & Helpdesk | `CHART_PANEL` | Annual charges stacked (c-ochg); helpdesk monthly (c-helpdesk) | R26, R29 |
| SM7 | Charges & Support Metrics | `KPI_STRIP` | DLD forfeiture 38.9M YTD ⚠ (> full-year 2025: 22.3M); helpdesk 120,700; within TAT 85.5% | R26, R29 |
| SM8 | Process Improvement | `INSIGHT_BLOCK` | PCC TAT initiative outcome; app adoption trajectory; DLD acceleration flag | Derived |
| SM9 | Process Definitions | `DEFINITION_BLOCK` | PCC process flow; PR approval criteria; LP calc basis; TAT measurement | Global |

> c-paych (3yr longitudinal) lives here. c-channel (current-period doughnut) lives in S03.

---

### S07 — Team (`sec-team`)
**Audience:** AGM Dues, HR, Leadership · **Mode:** Ops only (hidden in Board)

| Ref | Submodule | Type | Responsibility | Source |
|---|---|---|---|---|
| SM1 | Headcount Summary | `KPI_STRIP` | QCG 12 (2+10); MIS 15 (6+9); Mathews 38 (15+23); RMs 24 (12 direct + 12 via Rohan/Akkad) | Confirmed manual |
| SM2 | Organisation Chart | `JOURNEY_PANEL` | **Confirmed org only.** CCO: Ashish / GM Advance: Manuraj / AGM Dues Dubai: Priyanuj / AGM UAQ: Karan / AGM Siniya: Akkad | Confirmed manual |
| SM3 | Reporting Structure | `DEFINITION_BLOCK` | Priyanuj direct: Garima, Asjad, Mathews Babu, 12 RMs. Rohan → Akkad: 12 RMs. | Confirmed manual |

> **Critical:** Strategy doc org chart is factually wrong. S07 uses confirmed reporting lines from Part 0 only.

---

### S08 — Roadmap (`sec-roadmap`)
**Audience:** C-suite, AGM Dues, Strategy · **Mode:** Full (Ops) / Top 3 initiatives (Board)

| Ref | Submodule | Type | Responsibility | Source |
|---|---|---|---|---|
| SM1 | Risk Exposure Summary | `KPI_STRIP` | IC threshold 907.7M (251 units); Skyvue 1.27B (535 units); termination gap 134.6M (412 units) — reads S04 constants | R38, R34 |
| SM2 | Initiative Pipeline | `CHART_PANEL` | 10 expandable initiative cards — 5 Technology + 5 Commercial | strategy_doc |
| SM3 | Strategic Context | `INSIGHT_BLOCK` | PIPELINE_ADV_DENOM 37.8B framing; penetration 8.15%→10.6% thesis; IC threshold → standalone business case | R36, R38 |
| SM4 | Initiative Definitions | `DEFINITION_BLOCK` | Scope/owner/metric/timeline per initiative; IC threshold governance note | strategy_doc |

**10 Initiatives:**

| Priority | Track | Initiative | Timeline |
|---|---|---|---|
| P1 | Technology | Interim PR Module | Q1 2026 |
| P1 | Technology | LP Reversal Automation | Q2 2026 |
| P2 | Technology | Salesforce Internal Audit Integration | Q2–Q3 2026 |
| P2 | Technology | SQL Migration + Power BI (84 reports) | Q3–Q4 2026 |
| P3 | Technology | AI-Driven Audit + Auto-Training | Q1 2027 |
| **BOARD CASE FIRST** | Commercial | IC Threshold 20%→10% | Requires standalone business case before any action |
| P1 | Commercial | Advance Team Expansion + Booking-Stage Embedding | Q1–Q2 2026 |
| P2 | Commercial | Off-Plan Mortgage Scale-Up (ADIB MoU) | Q2 2026 |
| P2 | Commercial | App Adoption 57%→90% + Payment Link Sunset | Q3–Q4 2026 |
| P3 | Commercial | SOP Library + CCO Power BI + CSAT Live | Q4 2026–Q1 2027 |

---

## Part 9 — Live Pulse Section (Ops Mode only)

Live Pulse is hidden entirely in Board Mode.

### Layer 1 — Current Period Snapshot
Sources: R02, R04, R05, R06, R07, R10, R25, R30, R32

MTD snapshot and daily entity bar charts · YTD achievement vs MDO and Finance targets · Collector performance sorted DESC by achievement% · Coverage buckets (OD, FE, Term, Siniya) · Payment channel doughnut (COUNT basis only) · Performance flags

### Layer 2 — Deep Analytical Insights
Sources: R12, R18, R35, R36, R37, R38, R30

OD cohort ageing evolution · Collector trajectory analysis · Advance penetration trend vs rolling pipeline · Booking cohort vs collection year matrix · YoY milestone forward pipeline · Risk band movement

### Layer 3 — Calculator Tools

**Tool 1 — Collection Run Rate Calculator**
Inputs: Target AED M, Entity, Remaining working days
Outputs: Required daily run rate, collector load, achievement% vs MDO and Finance

**Tool 2 — Future Projection Engine**
Inputs: Current OD, monthly resolution rate%, advance mix assumption, pipeline drawdown rate
Outputs: Collections curve 3–6 months forward, confidence band high/low scenario

**Tool 3 — Stress Test Scenario Builder**
Inputs: OD increase%, advance mix deterioration%, new sales shortfall%, working days lost, IC band slider (251 units at 0-10% paid)
Outputs: Full-year target achievement impact, cash flow exposure estimate, IC threshold breach risk flag, board-ready scenario summary panel
Board export: Scenario summary pinned and available when user switches to Board Mode. State in React session memory.

### Layer 4 — Live Pulse Definitions
All metric definitions specific to pulse and tools. Formula governance. Data currency labels for all collector and daily data.

---

## Part 10 — Section Boundary Rules

No cross-contamination. Every piece of content lives in exactly one section.

| Content | Lives In | Not In |
|---|---|---|
| Nationality / CIV OD analysis | S01 (strategic risk) | S04 |
| Advance 3yr monthly chart (c-adv-hist) | S05 SM8 | S01 (removed) |
| NPV KPIs 652M / 21M / 31M | S01 SM3 [PROJECTED] | S05 (reference name only — no numbers) |
| PIPELINE_ADV_DENOM definition | S05 SM7 | S02 / S08 / tooltips |
| Bucket productivity % | S03 | S04 |
| OD ageing snapshot | S04 CHART_PANEL | — |
| OD ageing monthly trend | S04 TREND_PANEL | S01 / S03 |
| Channel doughnut (current period) | S03 | S06 |
| Channel 3yr bar (c-paych) | S06 | S03 |
| IC threshold policy decision | Standalone board business case | S04 / S08 (advisory flag only) |
| Org chart | S07 (confirmed lines only) | Anywhere else |

---

## Part 11 — Dependency Chain (non-negotiable)

### Backend
```
constants.py          imports nothing
pipeline_config.json  no imports (JSON)
utils.py              imports constants only
data_loader.py        imports constants, utils, pipeline_config
endpoints/            import data_loader outputs + utils
quickball.py          imports manifest.json, calls Claude API.
                      imports nothing from endpoints.
main.py               imports endpoint routers only. Zero logic.
```

### Frontend
```
shared components     import nothing from section components
section components    import shared components + call backend API
                      never import other section components
Quickball.jsx         imports no section components
                      calls backend. Renders response only.
navigation.jsx        imports section components only
App.jsx               imports navigation, filters, ModeToggle,
                      Quickball. Nothing else.
```

### Absolute rules
- `constants.py` never imports anything
- `utils.py` never imports `data_loader`
- Section components never import other section components
- Tools never import other tools
- `App.jsx` contains zero business logic
- `Quickball.jsx` contains zero computation
- `main.py` contains zero business logic
- `quickball.py` contains zero business logic

---

## Part 12 — Build Sequence and Smoke Test

### Phase 5 — Global Foundation (current phase)

Backend build order: `constants.py` → `pipeline_config.json` → `utils.py` → `data_loader.py` → `health.py` → `manifest.json` (seed) → `main.py` → `quickball.py` → Render deploy + `ANTHROPIC_API_KEY` env var confirmed

Frontend build order: `App.jsx` → `ModeToggle.jsx` → `filters.jsx` → `navigation.jsx` → `Quickball.jsx` → Netlify deploy + URL confirmed

### Phase 5 Smoke Test — 13 points (all must pass before Phase 6)

| # | Test | Proves |
|---|---|---|
| 1 | Backend reads R18 → OD_TODAY = 1,650.1M | Data pipeline |
| 2 | Frontend fetches OD_TODAY → displays correctly | Frontend-backend connection |
| 3 | Mode toggle switches Ops/Board without page reload | Mode state |
| 4 | Quickball: question → backend → Claude → response | Quickball round-trip |
| 5 | CY_ADV_MIX_YTD computed as 81.1% from R08 — not hardcoded | Data correctness |
| 6 | All 3 pipeline constants return with correct labels | Data correctness |
| 7 | Entity filter: Sobha 1,472.7M / Siniya 166.4M / DT 11.0M | Filter correctness |
| 8 | Remove one R-series file → graceful degradation, not crash | Resilience |
| 9 | Backend offline → Quickball offline state, platform loads | Resilience |
| 10 | Both URLs live — tested from different device | Deployment |
| 11 | /health ping confirmed in Render logs | Cold start eliminated |
| 12 | ?mode=present activates presentation mode correctly | Board readiness |
| 13 | Entity filter + section position preserved on mode switch | State management |

### Phase 6 — Context Sections
Build order: S05 → S04 → S02 → S06 → S01 → S07 → S08
One submodule per conversation. Backend endpoint + frontend component built together. Both mode="full" and mode="board" per section.

### Phase 7 — Board Mode Polish
All Context sections verified in Board Mode. ?mode=present tested. Offline graceful degradation confirmed. Static PDF export tested.

### Phase 7B — Live Pulse Layers
Layer 1 → Layer 2 → Tool 1 → Tool 2 → Tool 3 → Layer 4

### Phase 8 — Quickball Full Build
Build only after all submodules and tools are stable. Guided Workflows A, B, C built and tested.

### Phase 9 — Final Assembly and Handover
End-to-end journey. Break-glass document finalised. Both URLs documented. Render → Cloud Run migration guide produced.

---

## Part 13 — Development Rules

| Rule | Detail |
|---|---|
| No hardcoding | All values via `constants.py`. No literal AED amounts inline. |
| Reuse metrics only | No formula redefinition. All calculations from canonical formulas in Part 7. |
| No duplicate logic | One computation. N references. Never recompute per-section. |
| Submodules independent | Each component imports only its required data + constants. Never imports sibling sections. |
| One submodule per conversation | Non-negotiable. No conversation builds more than one submodule. |
| Smoke-test before next | No submodule ships without smoke-test confirmation in that session. |
| Source truth order | R-series reports > strategy_doc > narrative estimates |
| manifest.json | Updated with each confirmed submodule ID before next conversation starts |

---

## Part 14 — Key Validated Metrics (Mar 2026)

| Metric | Value |
|---|---|
| Group Sale Value ITD | 86.0B |
| Collected ITD | 43.3B (50.3%) |
| OD Today — Group (R18, 15 Mar 2026) | 1,650.1M · Sobha 1,472.7M · Siniya 166.4M · DT 11.0M |
| Future Pipeline (PIPELINE_GROSS) | 43.5B |
| 2025 Total Collections | 16,820M · D 9,706M · A 3,260M · NS 3,853M |
| Sobha 2025 | 14.06B · D 8,428M · A 2,862M · NS 2,774M |
| Siniya 2025 | 2,506M |
| DT 2025 | 250M |
| 2026 MDO FY Targets | Dues 11.5B · Advance 4.0B |
| 2026 Q1 Achievement | MDO Dues 91% · Advance 73% · NS 31% ⚠ CRITICAL GAP |
| D+A CAGR 2021–2025 | 97% |
| LP growth 2021–2025 | 22× |
| CY Advance Mix YTD 2026 | 81.1% |
| 2026 YTD rebate | 9.14M on 641M (1.4% rate) |
| Book Penetration 2025 → 2026 Target | 8.15% → 10.6% |
| App Payment Share YTD 2026 | 25.9% (COUNT basis) |
| PR 1st-Pass Approval | 51% |
| PCC TAT | 20d pre-initiative → 3–5d post → 2d target |
| PR-SOA 0–2d | 25% → 35% → 51% |
| OD ageing — 0–30d | 830M |
| OD ageing — 31–60d | 445M |
| OD ageing — 61–90d | 166M |
| IC threshold exposure | 907.7M (251 units at 0–10% paid) |
| Siniya coverage gap | 86.2% · 198 unworked units · 319M pool |
| Termination gap | 134.6M (412 not-in-system units) |
| MDO Jan 2026 actual | 787.4M (112% achievement) |
| Finance Jan 2026 actual | 1,069M (118% of 909M target) |

---

*CORE_CONTEXT v3.0 — End of document*
*Supersedes CORE_CONTEXT v2.0 entirely*
*Next action: Phase 5 build — new conversation — constants.py first*
