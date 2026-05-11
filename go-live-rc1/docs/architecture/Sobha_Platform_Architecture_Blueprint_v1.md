# SOBHA COLLECTIONS INTELLIGENCE PLATFORM
## FINAL ARCHITECTURE BLUEPRINT — v6 Target
**Issued by:** Strategic Advisory  
**Status:** Approved for Engineering Build  
**Date:** March 2026

---

## PART 1 — GLOBAL STANDARDS

### 1.1 Canonical Submodule Types

Every section is composed exclusively from these 6 submodule types.  
No other types are permitted.

| Type | Code | Purpose |
|---|---|---|
| Headline Metrics Strip | `KPI_STRIP` | 3–8 headline numbers; always top of section |
| Visual Data Panel | `CHART_PANEL` | One or more charts; scoped to a single data theme |
| Narrative Callouts | `INSIGHT_BLOCK` | Annotated flags, advisory alerts, editorial context |
| Business Rules | `DEFINITION_BLOCK` | Formulas, terminology, governance rules — always bottom of section |
| Longitudinal View | `TREND_PANEL` | Multi-year/multi-period only; distinct from current-period CHART_PANEL |
| Process Swimlane | `JOURNEY_PANEL` | Customer or operational flow visual; max one per section |

**Rule:** Each submodule has exactly one responsibility. A submodule that contains both a metric and a definition must be split.

---

### 1.2 Global Component Standards

#### Entity Toggle
- Single shared component: `etog`
- 5 states: `Group | Sobha | Siniya | DT | (All where applicable)`
- **Deprecated:** `story-etog`, `ann-etog`, `mdo-etog`, `fin-etog`, `mix-etog`, `port-etog`, `lp-etog`, `pu-etog`
- All 10 independent implementations REPLACE with one shared handler in v6

#### OD Today Constant
- Single source: `OD_TODAY` ← R18 (refreshed on load)
- **Deprecated:** 3 separate hardcoded instances in S02 / S04 / S08
- All sections reference `OD_TODAY`; never duplicate

#### Pipeline Constants (3 named, always labelled)
| Constant | Value | Definition | Used In |
|---|---|---|---|
| `PIPELINE_GROSS` | 43.5B | Remaining units × future milestones | S02 hero, S04 hero |
| `PIPELINE_FORWARD_BOOK` | ~40B | Narrative / opening book approx | S01 narrative |
| `PIPELINE_ADV_DENOM` | 37.8B | 43.5B − 5.7B prior advances | S05 penetration only |

**Rule:** Each pipeline figure must carry its label inline. Never display a pipeline figure without its definition label.

#### Dues Target Disambiguation (always labelled on-screen)
| Label | Value (Jan) | Definition |
|---|---|---|
| `MDO Dues` | 700.5M | Dues only; dynamic mid-year |
| `Finance Dues` | 909M | Dues + Advance combined; static |

---

## PART 2 — SECTION × SUBMODULE HIERARCHY

---

### S01 — STRATEGIC NARRATIVE
**ID:** `sec-story`  
**Purpose:** Executive-layer story — growth trajectory, value creation, portfolio risk profile.  
**Audience:** C-suite, board, investor review.  
**Entity Toggle:** `etog` (Group / Sobha / Siniya / DT)

| # | Submodule Name | Type | Responsibility | Source |
|---|---|---|---|---|
| 1.1 | Growth Headlines | `KPI_STRIP` | D+A CAGR 97%, 15× growth (867M→12,966M), LP 22× growth, entity 2025 totals | R01, R26 |
| 1.2 | Growth Trajectory | `CHART_PANEL` | Annual entity stacked bars; % mix trend (group + Sobha); units by year | R01, R03 |
| 1.3 | Advance Story | `CHART_PANEL` | 3-year monthly overlay; 2025 CY/FY monthly split; quarterly acceleration | R08 |
| 1.4 | NPV Rebate Analysis | `KPI_STRIP` | Incremental inflow 652M, rebate cost 21M, bank equivalent 31M, NPV rates, avg lead 248d | R08 |
| 1.5 | Portfolio Risk Profile | `CHART_PANEL` | Nationality bar + OD% line; CIV band bar + OD% line; OD ranking | R16 |
| 1.6 | Narrative Callouts | `INSIGHT_BLOCK` | Editorial flags: growth inflection, LP acceleration, rebate ROI, top-risk nationalities | Derived |
| 1.7 | Metric Definitions | `DEFINITION_BLOCK` | OD% formula (OD ÷ MS Due ITD); NPV methodology; D+A CAGR formula; projected vs actual labels on NPV | Global |

**Boundary rules:**  
- Nationality & CIV stays in S01 — it is a strategic risk lens, not an operational OD list  
- Advance Story in S01 is the **narrative summary only**; detailed advance management lives in S05  
- NPV panel carries label "Projected" on 652M / 21M / 31M figures — not "Actual"

---

### S02 — PORTFOLIO OVERVIEW
**ID:** `sec-overview`  
**Purpose:** Single-screen portfolio entry point — stock position, targets (MDO vs Finance), market context.  
**Audience:** Department head, finance, senior leadership.  
**Toggle:** Target version selector (MDO | Finance) + `etog`

| # | Submodule Name | Type | Responsibility | Source |
|---|---|---|---|---|
| 2.1 | Portfolio Cards | `KPI_STRIP` | Sale Value ITD 86B / Collected 43.3B (50.3%) / Pipeline `PIPELINE_GROSS` / OD `OD_TODAY` | R13, R18, R36 |
| 2.2 | Customer Payment Journey | `JOURNEY_PANEL` | 6-node swimlane: Booking 2%→10% / 55d window / 248d advance lead / LP / PCC TAT / Title Deed | R20, R08 |
| 2.3 | MDO Target Performance | `CHART_PANEL` | 9-month grouped bar — target vs actual (Group + entity split: Sobha, Siniya, DT) | R02 |
| 2.4 | Finance Target Performance | `CHART_PANEL` | Dues+NS grouped bar — Finance target vs actual; Siniya entity bar | R04 |
| 2.5 | Target Achievement Summary | `KPI_STRIP` | FY Dues 11.5B, FY Advance 4.0B; Q1 MDO 91%; Q1 Advance 73%; Q1 NS 31% ⚠ | R02, R04 |
| 2.6 | UAE Market Context | `INSIGHT_BLOCK` | 214,912 transactions / 682.5B value / 65–72% off-plan / Sobha #4 ~10% share | External |
| 2.7 | Target Definitions | `DEFINITION_BLOCK` | MDO Dues vs Finance Dues definition; entity split logic; NS target basis | R02, R04 |

**Boundary rules:**  
- `c-mdo2` (current purpose unclear) → **REMOVE** unless confirmed as entity-level drill; do not carry forward to v6  
- Finance toggle uses `etog/ev` pattern — deprecate inline `onclick`  
- Market Context is static editorial, not a KPI strip; it lives in INSIGHT_BLOCK

---

### S03 — LIVE PULSE
**ID:** `sec-pulse`  
**Purpose:** Real-time collection performance — MTD, YTD, collector productivity, coverage.  
**Audience:** Operations lead, AGM, daily management review.  
**Entity Toggle:** `etog` (single handler controlling all panels simultaneously)

| # | Submodule Name | Type | Responsibility | Source |
|---|---|---|---|---|
| 3.1 | MTD Snapshot | `KPI_STRIP` | Group Dues MTD, Advance MTD, NS MTD ⚠, daily MDO avg (single constant) | R04-R07 |
| 3.2 | Daily Bar Charts | `CHART_PANEL` | Daily stacked Dues+NS bars + MDO dotted avg line; entity panels (Sobha, Siniya, DT) | R05, R06, R07 |
| 3.3 | YTD Achievement | `KPI_STRIP` | Q1 Dues 1.92B/2.11B (91%), Q1 Advance 702M/960M (73%), Q1 NS 473M/1.52B (31%) ⚠ | R02, R04 |
| 3.4 | YTD Trend Charts | `CHART_PANEL` | Monthly grouped bar — Dues MDO target vs actual; Advance CY/FY entity stacked vs target | R02, R08 |
| 3.5 | Collector Performance | `CHART_PANEL` | Horizontal bars sorted by achievement% (fix); top/bottom table; PTP pipeline | R30, R32 |
| 3.6 | Coverage & Channel | `CHART_PANEL` | 5-bucket coverage bars; payment channel doughnut (COUNT basis) | R10, R25 |
| 3.7 | Performance Flags | `INSIGHT_BLOCK` | NS critical gap alert; Siniya 86.2% coverage gap 198 units / 319M; collector outlier flags | Derived |
| 3.8 | Operational Definitions | `DEFINITION_BLOCK` | MDO daily avg formula (target÷working days — not hardcoded 22); collector achievement% formula; coverage% formula | Global |

**Boundary rules:**  
- Daily arrays (`days[]`) centralised to a **single shared constant** — 4 duplicate declarations removed  
- `class="daily-ent"` pattern retained for entity daily panels (prevents generic toggle interference)  
- Collector data is Mar 2026 snapshot — label as "Snapshot: Mar 2026" in INSIGHT_BLOCK; add refresh date field  
- Bucket productivity (FE 44.1%, OD 35.4%, Term 27.2%) moves here from S04 — it is a pulse metric, not a structural definition

---

### S04 — DUES COLLECTIONS
**ID:** `sec-dues`  
**Purpose:** OD stock analysis, delinquency risk, collection efficiency, bucket governance.  
**Audience:** AGM Dues, QCG team, risk review.

| # | Submodule Name | Type | Responsibility | Source |
|---|---|---|---|---|
| 4.1 | OD Position | `KPI_STRIP` | OD Today `OD_TODAY`, EOM OD 2.17B, Collectible Window 2.56B, Termination Gap 134.6M (412 units) | R18, R02 |
| 4.2 | OD Composition | `CHART_PANEL` | OD ageing doughnut (6 bands); top 10 projects bar (horizontal); SPA legal status chart | R18, R17 |
| 4.3 | OD Ageing Progression | `TREND_PANEL` | Monthly ageing stacked bar — Jan–Dec 2025 longitudinal view | R18 |
| 4.4 | Collection Efficiency | `CHART_PANEL` | Booksize BOM bar + dues collected line (monthly 2025); termination volume bars | R12, R34 |
| 4.5 | Efficiency Metrics | `KPI_STRIP` | 30-day efficiency 34.8% avg; termination avg 427 units/month; eligible 1,314 units / 700.7M; dev notice 251 units | R12, R34 |
| 4.6 | Risk Flags | `INSIGHT_BLOCK` | IC threshold: 251 units at 0–10% paid = 907.7M exposure; Skyvue 535 units/1.27B at 10–20%; SPA not-signed 36.4M | R38, R17 |
| 4.7 | Bucket Architecture | `DEFINITION_BLOCK` | FE / Other OD / Term split (35% / 55% / 10%); FE accountability rule; termination exit rule (100% OD, no partials); 55-day window definition; OD% formula (OD ÷ MS Due ITD, not Purchase Price) | R34, Global |

**Boundary rules:**  
- Ageing doughnut (current snapshot) and ageing trend (monthly series) are **separate submodules** — 4.2 vs 4.3  
- IC threshold advisory: flagged here in 4.6 AND referenced in S08; do not duplicate the data, only the alert link  
- `OD_TODAY` is the **only** live value in this section — all others are calculated or period-fixed  
- SPA status chart stays here (legal governance of OD pool) — it is not a journey element

---

### S05 — ADVANCE COLLECTIONS
**ID:** `sec-advance`  
**Purpose:** Advance payment performance, CY/FY mix strategy, book penetration trajectory.  
**Audience:** AGM Dues, Finance, strategy review.

| # | Submodule Name | Type | Responsibility | Source |
|---|---|---|---|---|
| 5.1 | 2025 Advance Summary | `KPI_STRIP` | Annual total 3,260M; vs 2024 +125%; vs 2023 +238%; peak month Dec 2025 = 406M | R08 |
| 5.2 | Historical Performance | `TREND_PANEL` | 3-year monthly overlay (2023/2024/2025); quarterly acceleration Q1=512M → Q4=1,032M | R08 |
| 5.3 | 2025 Monthly CY/FY | `CHART_PANEL` | CY + FY stacked per month; Dec CY = 0% annotation | R08 |
| 5.4 | 2026 YTD vs Target | `CHART_PANEL` | Monthly CY/FY bar + 320M/month target line; entity stacked vs target | R08 |
| 5.5 | 2026 Progress | `KPI_STRIP` | YTD 640.9M; Q1 73% (640.9M / 960M); YTD CY mix 81.1% (Jan 84%, Feb 77%, Mar 86%) | R08 |
| 5.6 | Book Penetration | `CHART_PANEL` | Penetration % chart by year; 2025 = 8.15%; 2026 target = 10.6% | R08, R36 |
| 5.7 | Rebate Strategy | `INSIGHT_BLOCK` | NPV effective rate 1.4% YTD 2026; 248d avg lead time; NPV uplift 3.5% → 4.3% advisory; note all NPV scenario figures are "Projected" | R08 |
| 5.8 | Advance Definitions | `DEFINITION_BLOCK` | CY vs FY definition; penetration denominator: `PIPELINE_ADV_DENOM` = 43.5B − 5.7B = 37.8B (NOT static 40B); NPV bank equivalent basis (4.75% × 248/365) | R08, R36 |

**Boundary rules:**  
- Historical 3-year overlay is `TREND_PANEL` (not `CHART_PANEL`) — it is longitudinal, not current-period  
- NPV rebate detail is `INSIGHT_BLOCK` here (advisory context); the financial model KPIs live in S01 1.4 — no duplication  
- CY advance mix % is computed once from R08; S01 and S03 reference same derived constant — not recalculated

---

### S06 — OPERATIONS & QCG
**ID:** `sec-ops`  
**Purpose:** Process quality, payment infrastructure, operational charges, helpdesk governance.  
**Audience:** QCG lead (Garima), MIS lead (Asjad), AGM Dues.

| # | Submodule Name | Type | Responsibility | Source |
|---|---|---|---|---|
| 6.1 | QCG Quality Metrics | `KPI_STRIP` | 1st-pass approval 51%; doc gap 27%; manual error 23%; PR visibility gap 250–300M | R31 |
| 6.2 | PR Quality & PCC TAT | `CHART_PANEL` | PR quality doughnut (Approved/Doc-gap/Manual-error); PCC TAT bar Jan 2025–Feb 2026 | R31, R20 |
| 6.3 | TAT Milestones | `KPI_STRIP` | PCC TAT: pre-initiative 20d → post-initiative 3–5d → target 2d | R20 |
| 6.4 | Payment Channels & TAT | `CHART_PANEL` | 9-channel grouped bar 3 years (COUNT); PR-SOA TAT band progression (2024/2025/2026 YTD) | R25, R20 |
| 6.5 | Channel Metrics | `KPI_STRIP` | App share: 0.1% → 6% → 25.9% YTD; wire transfer 43.5%; 0–2d TAT: 25% → 35% → 51% | R25, R20 |
| 6.6 | Other Charges & Helpdesk | `CHART_PANEL` | Annual charges stacked (LP / DLD Forfeiture / IC Forfeiture / NOC+Admin); helpdesk monthly closed + within-TAT% line | R26, R29 |
| 6.7 | Charges & Support Metrics | `KPI_STRIP` | 2026 YTD DLD forfeiture 38.9M (> full-year 2025: 22.3M) ⚠; helpdesk YTD 120,700 cases; within TAT 85.5% | R26, R29 |
| 6.8 | Process Improvement Narrative | `INSIGHT_BLOCK` | PCC TAT initiative outcome; app adoption trajectory; DLD forfeiture acceleration flag; PR quality improvement roadmap | Derived |
| 6.9 | Process Definitions | `DEFINITION_BLOCK` | PCC process flow steps; PR approval criteria; LP calculation basis; TAT measurement start/end points | Global |

**Boundary rules:**  
- PR Quality and PCC TAT are in the **same** CHART_PANEL (6.2) — they are tightly coupled QCG outputs  
- Payment channels (6.4) and PR quality (6.2) are **separate** panels — different processes, different owners  
- Other Charges and Helpdesk are in the **same** CHART_PANEL (6.6) — both are ops volume metrics with no entity toggle needed  
- LP signal cross-feeds S01 — sourced once from R26

---

### S07 — TEAM
**ID:** `sec-team`  
**Purpose:** Accurate organisational structure, headcount, and reporting accountability.  
**Audience:** AGM Dues, HR, leadership.

| # | Submodule Name | Type | Responsibility | Source |
|---|---|---|---|---|
| 7.1 | Headcount Summary | `KPI_STRIP` | QCG: 12 (2 Dubai + 10 India); MIS: 15 (6 Dubai + 9 India); Mathews team: 38 (15 Dubai + 23 India); RMs: 24 total (12 direct to Priyanuj, 12 via Rohan/Akkad) | Manual |
| 7.2 | Organisation Chart | `JOURNEY_PANEL` | **CORRECTED** org chart replacing inaccurate v5 version; reflects actual reporting lines | Manual |
| 7.3 | Reporting Structure | `DEFINITION_BLOCK` | Priyanuj direct reports: QCG (Garima), MIS (Asjad), Mathews Babu, 12 RMs; Rohan reports to Akkad (12 RMs); India teams growing | Manual |

**Boundary rules:**  
- Org chart in v5 is **factually incorrect** — must be rebuilt from scratch using confirmed reporting lines  
- India team growth trajectory noted in 7.3 DEFINITION_BLOCK (not a KPI — no targets set yet)  
- No charts in this section — headcount is editorial, not analytical

---

### S08 — ROADMAP
**ID:** `sec-roadmap`  
**Purpose:** Strategic initiative pipeline, risk-linked advisories, transformation governance.  
**Audience:** C-suite, AGM Dues, strategy function.

| # | Submodule Name | Type | Responsibility | Source |
|---|---|---|---|---|
| 8.1 | Risk Exposure Summary | `KPI_STRIP` | IC threshold exposure: 907.7M (251 units, 0–10% paid); Skyvue cluster: 1.27B (535 units); termination unactioned: 134.6M (412 units) | R38, R34 |
| 8.2 | Initiative Dashboard | `CHART_PANEL` | 10 expandable initiative drill-downs (`toggleRd()`) with impact badges and status indicators | Strategy |
| 8.3 | Strategic Context | `INSIGHT_BLOCK` | Forward book framing (`PIPELINE_ADV_DENOM` 37.8B); advance penetration uplift thesis; IC threshold policy change scoped as **separate standalone business case** | R36, R38 |
| 8.4 | Initiative Definitions | `DEFINITION_BLOCK` | Scope, owner, success metric, and timeline for each of the 10 initiatives; IC threshold advisory governance note | Strategy |

**Boundary rules:**  
- `OD_TODAY` advisory flag in S08 must reference the global constant — not a hardcoded 1.65B  
- IC threshold policy change is flagged here but **not decided here** — it is referenced as a separate business case document  
- Forward pipeline figure displayed here uses `PIPELINE_ADV_DENOM` with label — not the gross 43.5B figure

---

## PART 3 — CROSS-SECTION DATA FEEDS (Canonical)

| Signal | Source Section | Target Section(s) | Value | Method |
|---|---|---|---|---|
| OD Today | R18 → `OD_TODAY` constant | S02, S04, S08 | 1,650.1M (live) | Single constant, referenced not duplicated |
| LP signal | S01 / R26 | S06 | 34.82M (2025) | Read-only reference |
| Advance baseline | S05 / R08 | S01, S03 | 3,260M (2025) | Shared constant |
| Termination gap | S04 / R34 | S08 | 134.6M / 412 units | Advisory link only |
| IC threshold | S04 / R38 | S08 | 907.7M (251 units) | Advisory link only |
| Forward book | R36 | S05 denominator, S08 context | 37.8B | `PIPELINE_ADV_DENOM` |
| MDO targets | R02 | S02, S03 | Monthly dynamic | Single source reference |
| CY advance mix | R08 derived | S01, S03, S05 | 81.1% (2026 YTD) | Computed once, referenced 3× |

---

## PART 4 — DUPLICATION RESOLUTION REGISTER

| Issue | v5 State | v6 Resolution |
|---|---|---|
| OD Today hardcoded ×3 | S02, S04, S08 | Single `OD_TODAY` constant from R18 |
| Entity toggle ×10 implementations | Per-section | Single `etog` shared component |
| `days[]` array ×4 | 4 entity closures | Single shared constant `DAILY_DAYS[]` |
| `c-mdo2` (unknown purpose) | S02 | **REMOVE** — not carried to v6 |
| Advance arrays redeclared | Module + JS block | Module-level declaration only; no shadow |
| NPV figures labelled "Actual" | S01, S05 | Relabelled "Projected" in both |
| Pipeline figure unlabelled | S02, S04, S05 | All 3 named constants with inline labels |
| Finance vs MDO gap unlabelled | S02, S03 | Both panels carry definition label on-screen |
| Collector chart unsorted | S03 `c-coll` | Sort descending by achievement% |
| Finance toggle uses inline `onclick` | S02 | Migrated to `etog/ev` pattern |
| Org chart factually wrong | S07 | Rebuilt from confirmed reporting lines |

---

## PART 5 — SECTION BOUNDARY SUMMARY

| Content | Lives In | Does NOT live in |
|---|---|---|
| Nationality & CIV OD analysis | S01 (strategic risk lens) | S04 (that's operational OD list) |
| Advance 3yr narrative summary | S01 (story context) | S05 (that's management detail) |
| NPV KPIs (652M / 21M / 31M) | S01 (financial model) | S05 (has advisory insight only) |
| Market context (UAE stats) | S02 INSIGHT_BLOCK | Not a KPI strip |
| Bucket productivity % | S03 (pulse metric) | S04 (that's definitions) |
| Ageing doughnut (snapshot) | S04 CHART_PANEL | S04 TREND_PANEL (trend ≠ snapshot) |
| Ageing monthly progression | S04 TREND_PANEL | S01 / S03 |
| SPA legal status | S04 (OD governance) | S02 / S06 |
| Penetration denominator definition | S05 DEFINITION_BLOCK | S02 / S08 |
| PR quality + PCC TAT | S06 (same panel) | S03 / S04 |
| DLD forfeiture trend | S06 CHART_PANEL | S04 |
| IC threshold policy decision | Standalone business case | S08 (advisory flag only) |
| Org chart | S07 (corrected) | S02 / S01 |

---

## PART 6 — SECTION CHART COUNT TARGET (v6)

| Section | v5 Charts | v6 Target | Change |
|---|---|---|---|
| S01 Strategic Narrative | 15 | 12 | −3 (consolidate mix charts) |
| S02 Portfolio Overview | 7 | 5 | −2 (remove c-mdo2, consolidate Finance) |
| S03 Live Pulse | 10 | 10 | = |
| S04 Dues Collections | 7 | 7 | = |
| S05 Advance Collections | 6 | 7 | +1 (separate historical TREND_PANEL) |
| S06 Operations & QCG | 6 | 6 | = |
| S07 Team | 0 | 0 | = |
| S08 Roadmap | 1 | 1 | = |
| **TOTAL** | **52** | **48** | **−4** |

---

*Blueprint version: 1.0 — approved for v6 engineering build*  
*Supersedes: SystemMap v1, Engineering Structure v1*  
*Next step: v6 HTML build — implement global constants, shared etog, corrected org chart, remove c-mdo2*
