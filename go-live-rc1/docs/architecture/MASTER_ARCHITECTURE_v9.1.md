# Sobha Collections Intelligence Platform
## Master Architecture — v9.1

**Authority:** Consolidated from all conversation decisions Mar 2026
**Supersedes:** v9, v8, v6, and all prior documents
**Status:** Approved for Phase 5 engineering build
**Development Model:** AI-maintained | Solo product owner | Claude as permanent engineering resource

---

## Part 0 — Operating Model

| Field | Value |
|---|---|
| Product Owner | Priyanuj Deka — AGM Dues, Sobha Realty Dubai |
| Development | Claude AI — sole engineering resource |
| Team Role | Source data refresh only — no platform code responsibility |
| Deployment Authority | Priyanuj only — GitHub Desktop push = deployment |
| Platform Purpose | Collections intelligence, decision support, and board-grade reporting for Sobha Realty Dubai collections function |
| Data Governance | Priyanuj reviews all source files before any push to live platform |

### Confirmed Reporting Lines
> Strategy doc org chart is factually incorrect. S07 must be built from these lines only.

| Team | Lead | Dubai | India | Total | Notes |
|---|---|---|---|---|---|
| QCG | Garima | 2 | 10 | 12 | — |
| MIS | Asjad | 6 | 9 | 15 | India growing |
| Mathews team | Mathews Babu | 15 | 23 | 38 | India growing |
| RMs direct to Priyanuj | — | 12 | — | 12 | — |
| RMs via Rohan → Akkad | — | 12 | — | 12 | — |

**Leadership:** CCO: Ashish · GM Advance: Manuraj · AGM Dues Dubai: Priyanuj · AGM UAQ: Karan · AGM Siniya: Akkad

### Core Design Principle

> One URL. One visual identity. One mental model.
> User never leaves the application regardless of task or audience.
> Ops mode and Board mode are states within the same shell — not separate platforms.

---

## Part 1 — Two-Tier Architecture

v9.1 is a production two-tier web application. The prior single-file HTML+JS and Streamlit approaches are fully superseded. One GitHub repository. Two top-level folders. One shared data layer.

```
┌─────────────────────────────────────────────────────────────────┐
│             SOBHA COLLECTIONS INTELLIGENCE PLATFORM             │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   FRONTEND — REACT                      │   │
│  │                                                         │   │
│  │   ┌───────────────────┐   ┌─────────────────────────┐  │   │
│  │   │     OPS MODE      │   │      BOARD MODE          │  │   │
│  │   │ Daily collections │   │ C-suite / Board /        │  │   │
│  │   │ Team performance  │   │ Investor presentation    │  │   │
│  │   │ Calculator tools  │   │ Narrative-first layout   │  │   │
│  │   │ Deep analytics    │   │ Full-screen mode         │  │   │
│  │   └───────────────────┘   └─────────────────────────┘  │   │
│  │                                                         │   │
│  │   ┌─────────────────────────────────────────────────┐  │   │
│  │   │          QUICKBALL — PERSISTENT PANEL           │  │   │
│  │   │  Embedded AI assistant. Floats in both modes.   │  │   │
│  │   │  Routes within the same app. No cross-URL jumps.│  │   │
│  │   └─────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                   │
│                     HTTP API calls                              │
│                             │                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  BACKEND — FASTAPI                      │   │
│  │                                                         │   │
│  │  Computation engine. Data processing. Claude API relay. │   │
│  │  Pre-aggregation for frontend (~100KB payload).         │   │
│  │  Business logic in Python. Stateless.                   │   │
│  │  Claude API key held server-side only.                  │   │
│  │  SUBMODULE_MANIFEST lives here.                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                   │
│                     reads /data folder                          │
│                             │                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           SHARED DATA LAYER — GitHub /data              │   │
│  │                                                         │   │
│  │  R-series xlsx files. One push refreshes both tiers.   │   │
│  │  Backend reads via raw GitHub URL on every request.     │   │
│  │  Single push refreshes both frontend and backend        │   │
│  │  simultaneously. No redeployment required.              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Frontend — React

| Field | Value |
|---|---|
| Hosting | Netlify (free permanent tier) |
| URL | sobha-collections.netlify.app — one URL shared with all users |
| Deployment | Auto-deploys on GitHub push via GitHub Desktop |
| Stack | React + Recharts / Plotly.js. Single-file build. No separate CSS or JS files. |
| Quickball | Embedded persistent panel. Calls backend API. No Claude API key in client. No cross-URL routing. |
| Data | Fetches pre-aggregated ~100KB summary JSON from backend on load. Never reads raw R-series files directly. |
| Device | Ops Mode: optimised for laptop, acceptable on iPad. Board Mode: excellent on laptop, iPad, large screen. Mobile: KPI strips 2-column, complex charts excluded. |
| Presentation | `?mode=present` removes all chrome, scales fonts 140%, arrow key navigation. Operates as live-data presentation tool on any screen. |
| Offline | Core content cached after initial load. Quickball shows graceful offline state. Static PDF export from Claude on demand for venues with unreliable internet. |

### Backend — FastAPI

| Field | Value |
|---|---|
| Prototype hosting | Render (free permanent tier) — auto-deploy from GitHub |
| Production hosting | Google Cloud Run (always-free tier) — switching requires deployment config change only, zero code change |
| Stack | Python + FastAPI — ~200–300 lines total across all endpoint files. Claude writes entirely. Priyanuj never edits. |
| Security | Claude API key: `ANTHROPIC_API_KEY` as Render environment variable only. Never in any file, Drive folder, or repository. Never returned in any API response. Frontend URL whitelisted in CORS config. |
| State | Stateless. No session data. No database. No persistent storage. |
| Warming | Frontend pings `/health` endpoint every 10 minutes via background effect. UptimeRobot provides secondary 5-minute ping backup. Backend never idles beyond 5 minutes. |
| R-series reads | `openpyxl` only. xlsx format only. One library. One read path. No format detection logic. |

---

## Part 2 — Data Pipeline Architecture

### Source Format Rule (non-negotiable)

All R-series files: **xlsx only**. Single file per report. Multi-sheet files (e.g. R08 — 24 sheets) kept intact. No xlsb, PDF, or Word. ERP systems that export xlsb: resave as xlsx before sending — two-click operation, one-time habit change. Non-xlsx file in `/data` triggers graceful degradation — never a crash.

### Layer 1 — Source (Team responsibility)

| Field | Value |
|---|---|
| Who | Asjad (MIS), Garima (QCG), Mathews Ops team |
| Format | xlsx only. Single file per R-series report. Multi-sheet files intact. |
| Action | Export from ERP → save as xlsx → drop into shared Google Drive staging folder |
| Rule | Team never touches GitHub, platform, or backend. Team never pushes directly to live data. |

### Layer 2 — Staging (Priyanuj oversight — sole authority)

| Field | Value |
|---|---|
| Who | Priyanuj only |
| Staging | Shared Google Drive folder — team drops files here. Priyanuj reviews in Drive before any push. |
| Action | Download reviewed file → drag into GitHub Desktop `/data` folder → Commit → Push (2–3 minutes) |
| Effect | Backend reads from raw GitHub URL on next request. Frontend fetches fresh computed payload on next load. No redeployment of either tier required. |
| Rule | Drive is staging only — not the platform data source. GitHub `/data` is the authoritative source. |

**Future (when platform is stable):**
Power Automate for R18 daily OD: ERP export → email attachment detected → Drive staging folder → Priyanuj approves → pushes to GitHub. Human review preserved. Manual extraction reduced.

### Layer 3 — Processing (Claude-built, fully automated)

- `data_loader.py` reads all R-series xlsx files on request via `openpyxl`
- `pipeline_config.json` defines column mappings and aggregations
- Pre-aggregation produces lean summary JSON (~100KB) for frontend
- `computed` dict populated automatically — no manual calculation
- `SNAPSHOT_DATE` read from file metadata — never manually entered
- Missing or malformed file → graceful degradation: section shows last known value with "data pending refresh" label. Never an error to end user.

### Layer 4 — Platform (zero maintenance once built)

| Tier | Hosting | Behaviour |
|---|---|---|
| Frontend | Netlify | Permanent free. Auto-deploys on push. |
| Backend prototype | Render | Permanent free. Auto-deploys on push. |
| Backend production | Cloud Run | Always-free at internal usage scale. |
| Data push | GitHub `/data` | Priyanuj pushes → platform refreshes on next load. |
| Code push | GitHub | Claude writes → Priyanuj pushes → live in 60 seconds. |

---

## Part 3 — Mode Architecture

Mode toggle is a React state variable in the application shell. Switching mode re-renders the section content area. Header, Quickball panel, and filters persist across mode switches. URL reflects mode: `?mode=ops` (default) or `?mode=board`. Bookmarked URLs restore mode state on reload.

### Ops Mode — Default Landing State

| Field | Value |
|---|---|
| Primary users | AGM Dues, RMs, Collectors, Ops leads, MIS |
| Layout | Sidebar navigation + main content area. Dense information display. Interactive inputs visible. Collector and entity-level granularity. |
| Sections | Full Context sections (all sub-groups A, B, C) + full Live Pulse section (all 4 layers) |
| Charts | Plotly interactive — hover tooltips, zoom enabled |
| Filters | Entity toggle + Target version toggle. Persistent in header. Apply across all sections. |

### Board Mode — Presentation and C-suite State

| Field | Value |
|---|---|
| Primary users | CCO, GM Advance, Board members, Investors |
| Layout | Full-width narrative panels. Minimal chrome. Large typography. Charts full-width, no interactive complexity. |
| Sections | S01, S02, S04, S05, S08 (summary views only). S06, S07, and entire Live Pulse hidden. |
| Charts | Recharts static. Clean. Print-friendly. Complex multi-axis charts excluded. |
| Filters | Entity toggle retained. Target version toggle hidden. |
| Presentation | `?mode=present` removes header and Quickball panel. Arrow key navigation. Font scale 140%. Quickball accessible via keyboard shortcut during Q&A. |
| Offline | All Board Mode content cached after initial load. |

### Section Visibility by Mode

| Section | Ops Mode | Board Mode |
|---|---|---|
| S01 Strategic Narrative | Full | Curated headline version, large typography |
| S02 Portfolio Overview | Full | KPI strip + headline chart only |
| S04 Dues Collections | Full | OD position, IC exposure flag, trend direction |
| S05 Advance Collections | Full | Penetration headline, rebate opportunity, mix direction |
| S06 Operations & QCG | Full | **Hidden** |
| S07 Team Structure | Full | **Hidden** |
| S08 Strategic Roadmap | Full | Top 3 initiatives, headline status |
| Live Pulse — all layers | Full | **Hidden entirely** |

### Mode Switching Behaviour

| Behaviour | Detail |
|---|---|
| Toggle location | Persistent header — always visible. `[Ops]` `[Board]` with clear visual state. |
| State preserved | Entity filter and section position carry across mode switch. User does not lose context. |
| Quickball | Conversation held in React memory for session duration. Carries across mode switches. |
| URL | `?mode=` parameter updates on switch. Bookmarking captures mode and section state. |

---

## Part 4 — Quickball Architecture

Quickball is a persistent floating panel in the React shell. It is an embedded AI assistant — not a navigation router. Operates identically in Ops Mode and Board Mode. Calls backend → backend calls Claude API via `ANTHROPIC_API_KEY`. No key in client. No cross-URL routing. No page reloads.

### SUBMODULE_MANIFEST — Single Source of Truth

| Field | Value |
|---|---|
| Location | `/backend/manifest.json` |
| Ownership | Claude maintains. Updated when submodules are added. |
| Content | Every submodule with: question it answers, mode(s) it appears in, audience it serves, whether it contains a calculator tool, related submodules for cross-referencing. |
| Rule | One manifest governs the entire platform. Backend serves it to frontend on load. Quickball routing intelligence generated by Claude API at query time using this manifest. |

### Quickball Response Anatomy — every response carries all three

```
[AI Annotation]
2–3 sentence Claude-generated interpretation of the question
in context of current data. References actual metrics.

[Summary Panel]
Target submodule rendered in mode="summary" inline within
the Quickball panel. Answer appears immediately without
navigating away from current section.

[Action Buttons — up to 3]
  "See full section →"    Scrolls to section in same mode
  "Run [Tool name] →"     Opens calculator panel inline
  "Switch to Board view"  Toggles mode — same app
```

### Guided Workflows — triggered by pre-written prompt buttons

**Workflow A — "Prepare for board meeting"**

| Step | Action |
|---|---|
| 1 | S01 Strategic Narrative — growth story to open with |
| 2 | S02 Portfolio Overview — snapshot metrics |
| 3 | Live Pulse Snapshot — verify numbers before presenting |
| 4 | Stress Test Tool — run downside scenario for Q&A |
| 5 | S08 Roadmap — initiatives current status |

Each step: AI annotation explains what moved since last snapshot.

**Workflow B — "Review collector performance"**

| Step | Action |
|---|---|
| 1 | Live Pulse Snapshot SM5 — collectors by achievement% |
| 2 | Live Pulse Snapshot SM6 — coverage buckets |
| 3 | Run Rate Calculator — required daily rate for target |

**Workflow C — "Morning operations check"**

| Step | Action |
|---|---|
| 1 | Live Pulse SM1 — MTD snapshot and daily bars |
| 2 | S04 SM1 — OD Today position |
| 3 | Coverage section — gaps flagged |

### Quickball Operational Rules

| Rule | Detail |
|---|---|
| Cold start | Eliminated by 10-min frontend health ping + UptimeRobot 5-min backup |
| API cost | Identical queries cached 1 hour in backend. Usage logging active. |
| Offline | Graceful "AI unavailable" state. Navigation and tools still work. Not an error — clearly communicated. |
| Session memory | Conversation history in React state for browser session duration only. Each new session starts fresh — accepted. |

---

## Part 5 — Platform Section Hierarchy

### Context Master Section — Available in Both Modes

Character: Static intelligence. Historical. Narrative-first. No daily data. No user inputs.
Audience: C-suite, Board, Investor, AGM strategic planning.

#### Sub-group A — Portfolio Intelligence

**S01 — Strategic Narrative (`sec-story`)**
- Ops Mode: Full narrative + supporting data
- Board Mode: Curated headline version, large typography
- Boundary: Advance data in S01 = KPI-only. No charts duplicated from S05. Exception: c-adv-qtr (quarterly acceleration story — not in S05).

**S02 — Portfolio Overview (`sec-overview`)**
- Ops Mode: Full detail with entity breakdown
- Board Mode: Summary KPI strip + headline chart only
- Boundary: Entity-level OD lives here. Group-level OD analysis lives in S04.

#### Sub-group B — Risk and Revenue Collections

**S04 — Dues Collections (`sec-dues`)**
- Ops Mode: Full detail — OD ageing, risk bands, collector exposure, nationality breakdown
- Board Mode: Summary — OD position, IC exposure flag, trend direction only
- Boundary: IC threshold flag = advisory only. Policy decision in standalone business case — not on platform.

**S05 — Advance Collections (`sec-advance`)**
- Ops Mode: Full detail — CY/FY mix, penetration trend, rebate analysis, NPV comparison
- Board Mode: Summary — penetration headline, rebate opportunity, mix direction only
- Boundary: S05 owns all monthly/CY/FY/penetration charts. NPV figures always labelled [PROJECTED].

#### Sub-group C — Operations and Roadmap

**S06 — Operations & QCG (`sec-ops`)**
- Ops Mode: Full — TAT, PR quality, payment channels, helpdesk, customer journey flow
- Board Mode: Hidden
- Boundary: c-paych (3yr longitudinal) lives here. c-channel (current-period doughnut) lives in S03.

**S07 — Team Structure (`sec-team`)**
- Ops Mode: Full org structure — built from confirmed reporting lines only (Part 0). Strategy doc org chart not used.
- Board Mode: Hidden

**S08 — Strategic Roadmap (`sec-roadmap`)**
- Ops Mode: Full initiatives pipeline with status detail
- Board Mode: Summary — top 3 initiatives, headline status
- Boundary: IC threshold initiative flagged as BOARD CASE FIRST — not an ops action item.

---

### Live Pulse Master Section — Ops Mode Only

Character: Dynamic. Current-period. Interactive. User inputs.
Audience: AGM Dues, Ops leads, RMs, Collectors.
Board Mode: Entire Live Pulse section hidden. Board users who need ops data switch to Ops Mode.

#### Layer 1 — Current Period Snapshot
Sources: R02, R04, R05, R06, R07, R10, R25, R30, R32

- MTD snapshot and daily entity bar charts
- YTD achievement vs MDO and Finance targets
- Collector performance sorted **DESC by achievement%**
- Coverage buckets — OD, FE, Term, Siniya
- Payment channel doughnut (COUNT basis only — never AED)
- Performance flags and operational definitions

#### Layer 2 — Deep Analytical Insights
Sources: R12, R18, R35, R36, R37, R38, R30

- OD cohort ageing evolution — multi-month trend
- Collector trajectory analysis — not just snapshot
- Advance penetration trend vs rolling pipeline
- Booking cohort vs collection year matrix
- YoY milestone forward pipeline view
- Risk band movement across periods

#### Layer 3 — Scenario and Calculator Tools

**Tool 1 — Collection Run Rate Calculator**

| Field | Value |
|---|---|
| Inputs | Target AED M, Entity, Remaining working days |
| Outputs | Required daily run rate, collector load, achievement% vs MDO and Finance targets |

**Tool 2 — Future Projection Engine**

| Field | Value |
|---|---|
| Inputs | Current OD, monthly resolution rate%, advance mix assumption, pipeline drawdown rate |
| Outputs | Collections curve 3–6 months forward, confidence band high/low scenario |

**Tool 3 — Stress Test Scenario Builder**

| Field | Value |
|---|---|
| Inputs | OD increase%, advance mix deterioration%, new sales shortfall%, working days lost, IC band slider (251 units at 0–10% paid) |
| Outputs | Full-year target achievement impact, cash flow exposure estimate, IC threshold breach risk flag, board-ready scenario summary panel |
| Board export | Scenario summary pinned and available when user switches to Board Mode. State held in React session memory. |

#### Layer 4 — Live Pulse Definitions
All metric definitions specific to pulse and tools. Formula governance for calculator outputs. Data currency labels for all collector and daily data.

---

## Part 6 — Global Submodule Standards

### Six Canonical Types — no others permitted anywhere in platform

| Code | Name | Rule |
|---|---|---|
| `KPI_STRIP` | Headline Metrics Strip | 3–8 numbers. Always top of section. |
| `CHART_PANEL` | Visual Data Panel | One data theme. Current-period only. |
| `TREND_PANEL` | Longitudinal View | Multi-year/period only. Distinct from CHART_PANEL — never combined. |
| `INSIGHT_BLOCK` | Narrative Callouts | Flags, alerts, editorial context. |
| `DEFINITION_BLOCK` | Business Rules | Formulas, governance. Always bottom of section. |
| `JOURNEY_PANEL` | Process Swimlane | Customer or operational flow. Max 1 per section. |

> **Rule:** Each submodule has exactly one responsibility. Mixed responsibility = mandatory split.

### Submodule Function Signature (non-negotiable)

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

| Mode value | Renders |
|---|---|
| `mode="full"` | Complete submodule for section view |
| `mode="summary"` | Compact version for Quickball surfacing |
| `mode="board"` | Board-appropriate version where relevant |

No exceptions. No alternative calling conventions in either tier.

---

## Part 7 — Global Constants and Business Logic

### Structural Constants — `constants.py` (never refreshed)

| Constant | Value | Notes |
|---|---|---|
| `WORKING_DAYS_MONTH` | 21 | March 2026 calendar |
| `ENTITY_LIST` | [Sobha, Siniya, DT, Group] | — |
| `TARGET_VERSIONS` | [MDO Dues, Finance Dues] | — |
| `MDO_DUES_FY_2026` | 11,500M | — |
| `MDO_ADV_FY_2026` | 4,000M | — |

### Derived Constants — owned by `data_loader.py` via `pipeline_config.json`

| Constant | Value | Source | Inline label required |
|---|---|---|---|
| `OD_TODAY` | Refreshed on load | R18 | Never hardcode |
| `OD_SOBHA` | 1,472.7M | R18 derived | — |
| `OD_SINIYA` | 166.4M | R18 derived | — |
| `OD_DT` | 11.0M | R18 derived | — |
| `PIPELINE_GROSS` | 43.5B | R36 | "Total Forward Pipeline" |
| `PIPELINE_FORWARD_BOOK` | ~40B | Narrative | "~Opening 2025 Book" |
| `PIPELINE_ADV_DENOM` | 37.8B | R36 derived (43.5B − 5.7B) | "2026 Penetration Denominator" — S05 and S08 only |
| `CY_ADV_MIX_YTD` | 81.1% | R08 | Computed once. Referenced in S01/S03/S05. Never recompute. |
| `AVG_ADVANCE_LEAD_DAYS` | 248 days | R08 | — |
| `SNAPSHOT_DATE` | From file metadata | pipeline | Never manually entered |
| `DAILY_DAYS[]` | Array | R04 | Single array. No duplicates. |

> **Pipeline disambiguation:** `PIPELINE_GROSS` ≠ `PIPELINE_FORWARD_BOOK` ≠ `PIPELINE_ADV_DENOM`. Always display with inline label. Never display an unlabelled pipeline figure.

### Canonical Business Logic — never recalculated per submodule

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

### Target Disambiguation — always labelled on-screen

| Label | Jan value | Definition | Source |
|---|---|---|---|
| MDO Dues | 700.5M | Dues only. Dynamic — adjusted mid-year. | R02 |
| Finance Dues | 909M | Dues + Advance combined. Static. | R04 |

### Units Disambiguation — always labelled on-screen

| Constant | Value | Use for |
|---|---|---|
| `active_excl_pcc` | 30,044 | App adoption%, coverage calculations |
| `all_qualified_itd` | 34,731 | Portfolio count, hero card |

---

## Part 8 — File Structure

One GitHub repository. Two top-level folders: `/frontend` `/backend`. One `/data` folder at repository root.

### Backend File Structure

```
/backend
  main.py                  FastAPI entry point. Routes only.
                           No business logic. No computation.

  constants.py             Structural constants only.
                           No imports. No dependencies.

  pipeline_config.json     Column mappings and aggregations per
                           R-series source. Only file edited when
                           pipeline sources change.

  data_loader.py           Reads R-series xlsx via openpyxl.
                           Uses pipeline_config.json for mappings.
                           Returns { dataframes: dict,
                                     computed: dict }
                           Stateless. Pre-aggregates lean summary
                           JSON for frontend (~100KB total).

  utils.py                 Pure formatting and helpers.
                           Imports constants only. No side effects.

  quickball.py             Receives question + manifest.
                           Calls Claude API via ANTHROPIC_API_KEY
                           environment variable.
                           Returns annotation + route + actions.
                           Response cache: 1 hour identical queries.
                           Usage logging built in.
                           Zero computation. Zero business logic.

  manifest.json            SUBMODULE_MANIFEST.
                           Claude maintains. Served to frontend.

  /endpoints
    context.py             API endpoints for all Context sections
    pulse.py               API endpoints for all Pulse layers
    tools.py               API endpoints for all calculator tools
    health.py              /health ping endpoint for warming

  /pipeline
    schema_core.json       R-series file manifest and schema
```

### Frontend File Structure

```
/frontend
  /src
    App.jsx                Shell. Mode state. Header. Layout.
                           Mounts Quickball panel.
                           Imports section components only.
                           Zero business logic.

    navigation.jsx         Two-level navigation.
                           Mode-aware: hides Pulse in Board Mode.
                           Zero business logic.

    ModeToggle.jsx         [Ops] [Board] toggle component.
                           Updates ?mode= URL parameter.

    filters.jsx            Entity toggle + Target version toggle.
                           State in React context + URL params.
                           URL parameter state preserves on reload.

    Quickball.jsx          Floating panel component.
                           Calls backend /quickball endpoint.
                           Conversation history in React state
                           (session only — resets on tab close).
                           Graceful offline state built in.
                           Pings /health every 10 minutes.

    /components
      /context
        S01/               Strategic Narrative submodule components
        S02/               Portfolio Overview submodule components
        S04/               Dues Collections submodule components
        S05/               Advance Collections submodule components
        S06/               Operations submodule components
        S07/               Team Structure (confirmed org only)
        S08/               Strategic Roadmap submodule components

      /pulse
        /snapshot/         Current period submodule components
        /insights/         Deep analytical insight components
        ToolRunRate.jsx    Collection Run Rate Calculator
        ToolProjection.jsx Future Projection Engine
        ToolStressTest.jsx Stress Test Scenario Builder
        PulseDefinitions.jsx  DEFINITION_BLOCK for pulse + tools

      /shared
        KpiStrip.jsx       Reusable KPI strip component
        ChartPanel.jsx     Reusable chart wrapper
        TrendPanel.jsx     Reusable trend chart wrapper
        InsightBlock.jsx   Reusable flag/alert component
        DefinitionBlock.jsx Reusable formula governance block

/data
  [R-series xlsx files]    Team → Drive staging → Priyanuj reviews
                           → GitHub push
                           Raw GitHub URL read by backend on load
```

---

## Part 9 — Dependency Chain (non-negotiable)

### Backend

```
constants.py          imports nothing
pipeline_config.json  no imports (JSON)
utils.py              imports constants only
data_loader.py        imports constants, utils, pipeline_config
endpoints/            import data_loader outputs + utils
quickball.py          imports manifest.json, calls Claude API
                      imports nothing from endpoints
main.py               imports endpoint routers only
                      zero business logic
```

### Frontend

```
shared components     import nothing from section components
section components    import shared components + call backend API
                      never import other section components
Quickball.jsx         imports no section components
                      calls backend, renders response only
navigation.jsx        imports section components only
App.jsx               imports navigation, filters, ModeToggle,
                      Quickball — nothing else
```

### Absolute Rules

| Component | Rule |
|---|---|
| `constants.py` | Never imports anything |
| `utils.py` | Never imports `data_loader` |
| Section components | Never import other section components |
| Tools | Never import other tools |
| `App.jsx` | Contains zero business logic |
| `Quickball.jsx` | Contains zero computation |
| `main.py` | Contains zero business logic |
| `quickball.py` | Contains zero business logic |

---

## Part 10 — Build Sequence

### Phase 5 — Global Foundation

**Backend build order:**
1. `constants.py`
2. `pipeline_config.json`
3. `utils.py`
4. `data_loader.py` (xlsx/openpyxl reads + pre-aggregation)
5. `health.py` endpoint
6. `manifest.json` (seed — placeholder submodule IDs)
7. `main.py` (routes only)
8. `quickball.py` (1-hour cache + usage logging)
9. Render deployment + `ANTHROPIC_API_KEY` env var confirmed

**Frontend build order:**
1. `App.jsx` (mode state, layout, header)
2. `ModeToggle.jsx`
3. `filters.jsx` (URL parameter state from start)
4. `navigation.jsx` (mode-aware, two-level)
5. `Quickball.jsx` (ping effect, offline graceful state)
6. Netlify deployment + URL confirmation

**Phase 5 Smoke Test — 13 points (all must pass before Phase 6 begins):**

| # | Test | What it proves |
|---|---|---|
| 1 | Backend reads R18 → `OD_TODAY` = 1,650.1M | Data pipeline |
| 2 | Frontend fetches `OD_TODAY` → displays correctly | Frontend-backend connection |
| 3 | Mode toggle switches Ops/Board without page reload | Mode state |
| 4 | Quickball: question → backend → Claude → response | Quickball round-trip |
| 5 | `CY_ADV_MIX_YTD` computed as 81.1% from R08 — not hardcoded | Data correctness |
| 6 | All 3 pipeline constants return with correct labels | Data correctness |
| 7 | Entity filter: Sobha 1,472.7M / Siniya 166.4M / DT 11.0M | Filter correctness |
| 8 | Remove one R-series file → graceful degradation, not crash | Resilience |
| 9 | Backend offline → Quickball offline state, platform still loads | Resilience |
| 10 | Both URLs live — tested from different device, not dev machine | Deployment |
| 11 | `/health` ping confirmed in Render logs — cold start eliminated | Warming |
| 12 | `?mode=present` activates presentation mode correctly | Board readiness |
| 13 | Entity filter + section position preserved on mode switch | State management |

Break-glass document produced as parallel Phase 5 deliverable.

### Phase 6 — Context Sections

- Build order: S05 → S04 → S02 → S06 → S01 → S07 → S08
- One submodule per build conversation
- Backend endpoint + frontend component built together
- Both `mode="full"` and `mode="board"` variants per section
- Smoke-test each submodule before next begins
- `manifest.json` updated with each confirmed submodule ID

### Phase 7 — Board Mode Polish

All Context sections verified in Board Mode. `?mode=present` implemented and tested end-to-end. Offline graceful degradation confirmed. Static PDF export tested.

### Phase 7B — Live Pulse Layers (Ops Mode only)

Build order: Layer 1 → Layer 2 → Tool 1 → Tool 2 → Tool 3 → Layer 4 definitions. Tools are standalone — no tool imports another. Stress Test board export panel built in this phase.

### Phase 8 — Quickball Full Build

Build only after all submodules and tools are stable. `manifest.json` complete with all confirmed submodule IDs. Guided Workflows A, B, C built and tested. All action buttons tested: scroll-to, tool-open, mode-switch.

### Phase 9 — Final Assembly and Handover

App.jsx final assembly review. End-to-end user journey — all sections, both modes. Both deployment URLs confirmed and documented. Break-glass document finalised and distributed. Render → Cloud Run migration guide produced.

### One-Submodule-Per-Conversation Rule (non-negotiable)

Every submodule is built in its own Claude conversation. That conversation receives: v9.1 architecture document + relevant R-series schema + submodule specification + prior submodule output if dependency exists. No conversation builds more than one submodule. No submodule ships without smoke-test confirmation in that session.

---

## Part 11 — Constraint Register with Mitigations

### CONSTRAINT 01 — Single point of failure (Priyanuj)

| Field | Value |
|---|---|
| Severity | Critical |
| Risk | Platform breaks while Priyanuj unavailable |
| Mitigation | Break-glass document produced in Phase 5. Plain English: 5 most likely failures with exact Claude prompt to fix each. Any team member can paste error + prompt into Claude. Graceful degradation prevents hard errors reaching users. |
| Status | Mandatory Phase 5 deliverable |

### CONSTRAINT 02 — Backend cold starts

| Field | Value |
|---|---|
| Severity | Medium (prototype) / Low (production) |
| Risk | First Quickball query of the day is slow (1–3 seconds) if backend has been idle |
| Mitigation | Frontend pings `/health` every 10 minutes. UptimeRobot secondary 5-minute ping. Backend never idles beyond 5 minutes. |
| Status | Built into frontend from Day 1 |

### CONSTRAINT 03 — React session state loss on browser close

| Field | Value |
|---|---|
| Severity | Low |
| Risk | Quickball conversation history lost on tab close. Calculator inputs reset. |
| Mitigation | URL parameter state for filters and section position. Mode preserved in URL. Quickball reset per session — accepted. |
| Status | URL parameter state built into `filters.jsx` Phase 5 |

### CONSTRAINT 04 — Data volume and load time

| Field | Value |
|---|---|
| Severity | Low |
| Risk | Large R-series files cause slow initial load |
| Mitigation | Backend pre-aggregates all R-series into ~100KB JSON. Frontend never loads raw source files. |
| Status | Architectural requirement — Phase 5 backend build |

### CONSTRAINT 05 — Stress Test scenario in Board Mode

| Field | Value |
|---|---|
| Severity | Low |
| Risk | Scenario built in Ops Mode tools not visible when user switches to Board Mode |
| Mitigation | Tool 3 generates board-ready scenario summary panel on completion. User can pin this panel. Switching to Board Mode shows pinned scenario as additional section. State held in React session memory. |
| Status | Design requirement for `ToolStressTest.jsx` Phase 7B |

### CONSTRAINT 06 — Prototype to production migration

| Field | Value |
|---|---|
| Severity | Low |
| Risk | Switching Render to Cloud Run causes downtime or requires code changes |
| Mitigation | Stateless backend. Deployment config change only — zero code change. Migration under 30 minutes. |
| Status | Accepted. Future Priyanuj decision. |

### CONSTRAINT 07 — Offline access for board meetings

| Field | Value |
|---|---|
| Severity | Medium |
| Risk | Venue WiFi failure. Quickball unavailable. |
| Mitigation | React frontend core content cached after initial load. Both modes available offline. Quickball shows graceful "offline" state — not error. Static PDF export generated by Claude on demand before critical meetings. |
| Status | Graceful degradation built into frontend Phase 7 |

### CONSTRAINT 08 — Mobile collector access

| Field | Value |
|---|---|
| Severity | Low |
| Risk | Collectors checking performance on phones see degraded experience for complex Ops Mode charts |
| Mitigation | Responsive breakpoints exclude complex multi-axis charts on mobile. KPI strips, achievement tables, and collector rankings fully readable. Accepted remaining limitation. |
| Status | Responsive layout from Phase 5 build start |

### CONSTRAINT 09 — Claude API cost at scale

| Field | Value |
|---|---|
| Severity | Low currently. Monitor as usage grows. |
| Risk | Heavy Quickball usage generates ongoing API cost |
| Mitigation | Identical queries cached 1 hour in backend. Usage logging gives cost trajectory visibility. Guided workflow queries are pre-scripted — low cost. |
| Status | Cache built into `quickball.py` Phase 5 |

### CONSTRAINT 10 — No role-based access control

| Field | Value |
|---|---|
| Severity | Medium |
| Risk | Any user with the URL can access all sections |
| Mitigation | Platform is internal-only. URL not published externally. Mode toggle controls view complexity — not access. Formal access control deferred to production phase. |
| Status | Accepted for prototype |

### CONSTRAINT 11 — Live data during board presentation

| Field | Value |
|---|---|
| Severity | Low |
| Risk | Team member pushes broken data file during board presentation |
| Mitigation | Priyanuj controls all pushes — no automated push path. Board Mode uses pre-aggregated summary JSON. Malformed raw file triggers graceful degradation. Static PDF backup covers worst case. |
| Status | Graceful degradation in `data_loader` covers this |

### CONSTRAINT 12 — xlsx-only data format

| Field | Value |
|---|---|
| Severity | Low |
| Risk | Team member exports xlsb or PDF instead of xlsx |
| Mitigation | Explicit instruction at build handover: xlsx only. `data_loader.py` uses `openpyxl` only — one read path. Non-xlsx file in `/data` triggers graceful degradation with "data pending refresh" label. No platform crash. |
| Status | Team instruction at Phase 5 handover. Enforced by single-library pipeline design. |

### CONSTRAINT 13 — Google Drive as staging (not source of truth)

| Field | Value |
|---|---|
| Severity | Low |
| Risk | Team or Priyanuj treats Drive as the live data source |
| Mitigation | Architecture is explicit: GitHub `/data` is authoritative. Drive is staging only. Priyanuj always downloads from Drive and pushes to GitHub — two distinct steps. Platform backend reads raw GitHub URL only. |
| Status | Governance rule. Documented in team handover. |

---

## Part 12 — Operational Workflows After Build

### Routine Data Refresh

```
Team exports R-series file as xlsx from ERP
  → Drops into shared Google Drive staging folder

Priyanuj opens Drive
  → Reviews file (spot-check key metrics)
  → Downloads file
  → Opens GitHub Desktop
  → Drags file into /data folder
  → Commit → Push

Backend reads fresh data on next frontend request
Total time: 3–5 minutes
```

### Board Meeting Preparation

```
Open platform 24 hours before meeting
Switch to Board Mode — verify all sections load correctly
Trigger Workflow A via Quickball
Switch to Ops Mode — run Stress Test with agreed scenario
Switch to Board Mode — confirm scenario panel is pinned
If venue WiFi uncertain: request static PDF from Claude
PDF generated and saved locally as backup
```

### Platform Modification

```
Describe requirement to Claude in new conversation
Pass v9.1 architecture document as context
Claude writes backend endpoint + frontend component
Priyanuj copies files into correct folders
Updates manifest.json with new submodule ID
Pushes via GitHub Desktop — live in 60 seconds
```

### Break-Glass Procedure

```
Team member opens break-glass document
Identifies which failure scenario matches
Copies error message from platform
Opens Claude conversation
Pastes break-glass prompt + error message
Claude produces fix
Team member pushes fix via GitHub Desktop
```

### Prototype to Production Migration (future)

```
Open Google Cloud Console → Enable Cloud Run API
Connect GitHub repository
Configure environment variables (same as Render)
Deploy — source-based Python, no Dockerfile needed
Update frontend API base URL to Cloud Run URL → Push
Disable Render service
Total time: under 30 minutes. Zero code changes.
```

---

## Part 13 — Decisions Log (v9.1 additions over v9)

| ID | Decision | Resolution |
|---|---|---|
| D01 | API key storage | Render environment variable `ANTHROPIC_API_KEY` only. Never in any file, Drive folder, or repository. |
| D02 | R-series file format | xlsx only. `openpyxl` as sole read library. No xlsb, PDF, or Word. Multi-sheet files intact. Non-xlsx triggers graceful degradation. |
| D03 | Google Drive role | Staging and team drop zone only. GitHub `/data` is the authoritative platform data source. Drive not connected to backend. Review layer only. |
| D04 | Smoke test criteria | 13-point criteria confirmed. All must pass before Phase 6. Points 1–4: connectivity. Points 5–7: correctness. Points 8–9: resilience. Points 10–11: deployment. Points 12–13: board readiness. |
| D05 | Org chart source | S07 built from confirmed reporting lines in Part 0. Strategy document org chart is factually incorrect — not used anywhere on platform. |

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
| OD ageing 0–30d | 830M |
| OD ageing 31–60d | 445M |
| OD ageing 61–90d | 166M |
| IC threshold exposure | 907.7M (251 units at 0–10% paid) |
| Siniya coverage gap | 86.2% · 198 unworked units · 319M pool |
| Termination gap | 134.6M (412 not-in-system units) |
| MDO Jan 2026 actual | 787.4M (112% achievement) |
| Finance Jan 2026 actual | 1,069M (118% of 909M target) |

---

*Sobha Collections Intelligence Platform — Master Architecture v9.1*
*Authority: March 2026 consolidated decisions*
*Supersedes v9, v8, v6, and all prior documents*
*Next action: Phase 5 build — new conversation — `constants.py` first*
