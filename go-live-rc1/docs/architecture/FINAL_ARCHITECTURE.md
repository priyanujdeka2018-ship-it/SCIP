# SOBHA COLLECTIONS INTELLIGENCE PLATFORM
## FINAL ARCHITECTURE — v6
**Authority:** Supersedes SystemMap v1, Engineering Structure v1, Architecture Blueprint v1, platform_final_structure.json
**Status:** Approved for v6 engineering build
**Date:** March 2026

---

## PART 1 — GLOBAL STANDARDS

### 1.1 Submodule Types (6 canonical — no others permitted)

| Code | Name | Rule |
|---|---|---|
| `KPI_STRIP` | Headline Metrics Strip | 3–8 numbers. Always top of section. |
| `CHART_PANEL` | Visual Data Panel | One data theme. Current-period only. |
| `TREND_PANEL` | Longitudinal View | Multi-year/period only. Distinct from CHART_PANEL. |
| `INSIGHT_BLOCK` | Narrative Callouts | Flags, alerts, editorial context. |
| `DEFINITION_BLOCK` | Business Rules | Formulas, governance. Always bottom of section. |
| `JOURNEY_PANEL` | Process Swimlane | Customer/operational flow. Max 1 per section. |

**Rule:** Each submodule has exactly one responsibility. A submodule that contains both a metric and a definition must be split.

---

### 1.2 Global Constants (never hardcode inline)

| Constant | Value | Source | Rule |
|---|---|---|---|
| `OD_TODAY` | 1,650.1M (live) | R18 | Refresh on load. Replaces 3 deprecated hardcoded instances. |
| `PIPELINE_GROSS` | 43.5B | R36 | Total forward pipeline. Label: "Total Forward Pipeline". |
| `PIPELINE_FORWARD_BOOK` | ~40B | Narrative | Opening 2025 book approximation. Label: "~Opening 2025 Book". |
| `PIPELINE_ADV_DENOM` | 37.8B | R36 derived | 43.5B − 5.7B. Label: "2026 Penetration Denominator". S05/S08 only. |
| `CY_ADV_MIX_YTD` | 81.1% | R08 | Computed once. Referenced in S01/S03/S05. Never recompute. |
| `DAILY_DAYS[]` | Array | R04 | Replaces 4 duplicate days[] declarations. |
| `WORKING_DAYS_MONTH` | 21 | Calendar | March 2026. Replaces hardcoded 22. |

**Pipeline disambiguation rule:** `PIPELINE_GROSS` ≠ `PIPELINE_FORWARD_BOOK` ≠ `PIPELINE_ADV_DENOM`. Always display with inline label. Never show an unlabelled pipeline figure.

---

### 1.3 Global Component Rules

**Entity Toggle:** Single `etog` component (Group / Sobha / Siniya / DT). Replaces all 10 v5 per-section implementations. S03 entity panels use `class="daily-ent"` to avoid interference.

**Finance vs MDO Toggle:** `etog/ev` pattern. Deprecated inline `onclick` in S02 removed.

**OD Formula (canonical):** `od_pct = od_aed ÷ ms_due_itd_aed × 100`. NEVER divide by purchase_price_aed.

**NPV Label Rule:** 652M / 21M / 31M are [PROJECTED]. Never label as Actual.

**Channel Share Rule:** Always COUNT basis. Never AED value.

**CY/FY Rule:** CY = advance on milestones due current year. FY = future-year milestones. Jan 2025 CY = 70.1% (NOT 30%).

**Units Rule:** `active_excl_pcc` = 30,044 (app adoption, coverage). `all_qualified_itd` = 34,731 (portfolio count). Always label which is displayed.

---

## PART 2 — SECTION × SUBMODULE HIERARCHY

---

### S01 — STRATEGIC NARRATIVE (`sec-story`)
**Charts:** 52→12 (−3: consolidate mix; remove c-adv-3yr to S05)
**Toggle:** etog | **Audience:** C-suite, Board, Investor

| Ref | Submodule | Type | Responsibility | Source |
|---|---|---|---|---|
| 1.1 | Annual Collections Story | `KPI_STRIP` + `CHART_PANEL` | Entity annual stacked bars + CAGR 97%, 15× growth, entity 2025 totals | R01, R26 |
| 1.2 | Collections Composition | `TREND_PANEL` | Mix % trend 2021–2025 (annual + monthly); LP charges; units by year | R01, R08, R26, R03 |
| 1.3 | Advance Narrative | `KPI_STRIP` | Advance growth KPIs + c-adv-qtr (quarterly acceleration). NPV KPIs [PROJECTED]. No 3yr monthly chart. | R08 |
| 1.4 | Portfolio Risk Profile | `CHART_PANEL` | Nationality bar + OD% line (c-nat); CIV band bar + OD% line (c-civ) | R16 |
| 1.5 | Narrative Callouts | `INSIGHT_BLOCK` | Growth inflection; LP acceleration; NPV rebate ROI; top-risk nationality flags | Derived |
| 1.6 | Metric Definitions | `DEFINITION_BLOCK` | OD% formula; NPV methodology; CAGR formula; [PROJECTED] label rule | Global |

**Boundary:** Nationality/CIV stays in S01 (strategic risk). Advance 3yr monthly chart lives exclusively in S05.

---

### S02 — PORTFOLIO OVERVIEW (`sec-overview`)
**Charts:** 7→5 (−2: remove c-mdo2; consolidate Finance)
**Toggle:** etog + target-version (MDO/Finance via etog/ev) | **Audience:** Department head, Finance, Senior leadership

| Ref | Submodule | Type | Responsibility | Source |
|---|---|---|---|---|
| 2.1 | Portfolio Snapshot | `KPI_STRIP` + `JOURNEY_PANEL` | 86B/43.3B(50.3%)/43.5B pipeline/1,650.1M OD + 6-node payment journey | R13, R18, R36, R08, R20 |
| 2.2 | MDO Target Performance | `CHART_PANEL` + `KPI_STRIP` | 9-month grouped bars (c-mdo-tot/sob/sin/dt); FY targets; Q1 achievement (Strategic framing) | R02 |
| 2.3 | Finance Target Performance | `CHART_PANEL` + `KPI_STRIP` | Finance D+A bars (c-fin-tot, c-fin-sin); Finance vs MDO disambiguation | R04 |
| 2.4 | Target Achievement Summary | `KPI_STRIP` | FY Dues 11.5B; FY Advance 4.0B; Q1 MDO 91%; Q1 Advance 73%; Q1 NS 31% ⚠ | R02, R04 |
| 2.5 | UAE Market Context | `INSIGHT_BLOCK` | 214,912 tx / 682.5B / 65–72% off-plan / Sobha #4 ~10% share | External |
| 2.6 | Target Definitions | `DEFINITION_BLOCK` | MDO Dues vs Finance Dues; entity split logic; NS target basis | R02, R04 |

**Removed:** c-mdo2 (purpose unconfirmed — not in v6).

---

### S03 — LIVE PULSE (`sec-pulse`)
**Charts:** 10=10 | **Toggle:** etog (single handler) | **Audience:** Ops lead, AGM, Daily review

| Ref | Submodule | Type | Responsibility | Source |
|---|---|---|---|---|
| 3.1 | MTD Snapshot | `KPI_STRIP` | Dues MTD / Advance MTD / NS MTD ⚠ / daily MDO avg (÷WORKING_DAYS_MONTH) | R04–R07 |
| 3.2 | Daily Bar Charts | `CHART_PANEL` | c-daily + entity panels (c-daily-sob/sin/dt). class="daily-ent". | R04–R07 |
| 3.3 | YTD Achievement | `KPI_STRIP` | Q1 Dues 91% / Advance 73% / NS 31% ⚠ / CY mix 81.1% (Operational Pulse framing) | R02, R04, R08 |
| 3.4 | YTD Trend Charts | `CHART_PANEL` | Monthly MDO target vs actual (c-ytd-dues); Advance CY/FY entity stacked (c-ytd-adv/ent) | R02, R08 |
| 3.5 | Collector Performance | `CHART_PANEL` | Horizontal bars SORTED DESC by achievement% (fixed); top/bottom table; PTP (c-coll) | R30, R32 |
| 3.6 | Coverage & Channel | `CHART_PANEL` | 5-bucket coverage bars + current-period channel doughnut (c-channel, COUNT); bucket productivity % | R10, R25 |
| 3.7 | Performance Flags | `INSIGHT_BLOCK` | NS critical gap; Siniya 86.2% gap (198 units/319M); collector outlier flags | Derived |
| 3.8 | Operational Definitions | `DEFINITION_BLOCK` | MDO daily avg formula; achievement% formula; coverage% formula; Finance vs MDO label | Global |

**Fixed:** Collector chart sorted by achievement%. DAILY_DAYS[] centralised. Collector data labelled "Snapshot: Mar 2026 MTD".

---

### S04 — DUES COLLECTIONS (`sec-dues`)
**Charts:** 7=7 | **Toggle:** etog | **Audience:** AGM Dues, Collections ops, Risk function

| Ref | Submodule | Type | Responsibility | Source |
|---|---|---|---|---|
| 4.1 | OD Position | `KPI_STRIP` | OD_TODAY / entity split / march collectible window / EOM projection / 30d efficiency | R18, R02, R12 |
| 4.2 | OD Snapshot | `CHART_PANEL` | Ageing doughnut (c-od-ageing) + project ranking bar (c-od-project) + SPA bar (c-spa) + IC risk heatmap (c-risk-heatmap) | R18, R17, R38 |
| 4.3 | OD Progression | `TREND_PANEL` | Monthly OD ageing evolution (c-od-trend) — distinct from snapshot in 4.2 | R12, R18 |
| 4.4 | Collection Efficiency & Governance | `CHART_PANEL` | 30d efficiency trend (c-efficiency); termination pipeline (c-termination) | R12, R34 |
| 4.5 | OD Flags & Risk Alerts | `INSIGHT_BLOCK` | IC threshold advisory 907.7M/251 units; Skyvue 1.27B/535 units; termination gap 134.6M | R38, R34 |
| 4.6 | Dues Definitions | `DEFINITION_BLOCK` | OD% formula; 30d efficiency formula; 55d window (T-25/T+30); termination eligibility | Global |

**Boundary:** IC threshold flag is advisory only — policy decision in standalone business case. Operational OD list lives here; strategic risk lens lives in S01.

---

### S05 — ADVANCE COLLECTIONS (`sec-advance`)
**Charts:** 6→7 (+1: separate c-adv-hist TREND_PANEL) | **Toggle:** etog | **Audience:** AGM Dues, Advance team, GM Advance

| Ref | Submodule | Type | Responsibility | Source |
|---|---|---|---|---|
| 5.1 | Advance Position | `KPI_STRIP` | 2025 advance 3,260M; +125% vs 2024; +238% vs 2023; Dec 406M peak; 2026 YTD | R08 |
| 5.2 | Historical Performance | `TREND_PANEL` | 3yr monthly advance comparison 2023/2024/2025 (c-adv-hist) — authoritative render | R08 |
| 5.3 | 2026 Advance Progress | `CHART_PANEL` | 2026 monthly CY/FY vs target (c-adv-2026, c-adv-2026-ent) | R08 |
| 5.4 | 2025 Monthly CY/FY Detail | `CHART_PANEL` | 2025 intra-year CY/FY stacked monthly (c-adv-2025) | R08 |
| 5.5 | Book Penetration | `CHART_PANEL` | Penetration % trend (c-penetration); 2025=8.15%; 2026 target=10.6%; denominator=PIPELINE_ADV_DENOM | R08, R36 |
| 5.6 | Rebate Strategy | `INSIGHT_BLOCK` | NPV rebate ROI context — references S01 NPV finding by name. NO re-display of 652M/21M/31M. | R08 |
| 5.7 | Advance Definitions | `DEFINITION_BLOCK` | PIPELINE_ADV_DENOM=37.8B (defined once here only); CY/FY distinction; book penetration formula | Global |

**New:** c-adv-hist replaces c-adv-3yr which was removed from S01.

---

### S06 — OPERATIONS & QCG (`sec-ops`)
**Charts:** 6=6 | **Toggle:** none | **Audience:** QCG (Garima), MIS (Asjad), AGM Dues

| Ref | Submodule | Type | Responsibility | Source |
|---|---|---|---|---|
| 6.1 | QCG Quality Metrics | `KPI_STRIP` | PR 1st-pass 51%; doc gap 27%; manual error 23%; visibility gap 250–300M; call audit 30%; SLA 87% | R31 |
| 6.2 | PR Quality & PCC TAT | `CHART_PANEL` | PR quality doughnut (c-pr-quality) + PCC TAT bar (c-pcc-tat) — same panel, coupled QCG outputs | R31, R20 |
| 6.3 | TAT Milestones | `KPI_STRIP` | PCC TAT: 20d pre → 3–5d post → 2d target; PR-SOA 0–2d: 25%→35%→51% | R20 |
| 6.4 | Payment Channels & TAT | `CHART_PANEL` | 9-channel 3yr grouped bar (c-paych, COUNT); PR-SOA TAT band progression (c-pr-soa-tat) | R25, R20 |
| 6.5 | Channel Metrics | `KPI_STRIP` | App: 0.1%→6%→25.9% YTD; wire 43.5%; PR-SOA 0–2d 51% | R25, R20 |
| 6.6 | Other Charges & Helpdesk | `CHART_PANEL` | Annual charges stacked (c-ochg): LP/DLD Forf/IC Forf/NOC+Admin; helpdesk monthly (c-helpdesk) | R26, R29 |
| 6.7 | Charges & Support Metrics | `KPI_STRIP` | DLD forfeiture 38.9M YTD ⚠ (> full-year 2025: 22.3M); helpdesk 120,700; within TAT 85.5% | R26, R29 |
| 6.8 | Process Improvement Narrative | `INSIGHT_BLOCK` | PCC TAT initiative outcome; app adoption trajectory; DLD acceleration flag; PR quality roadmap | Derived |
| 6.9 | Process Definitions | `DEFINITION_BLOCK` | PCC process flow; PR approval criteria; LP calc basis; TAT measurement start/end | Global |

**Boundary:** c-paych (3yr longitudinal) lives here. c-channel (current-period doughnut) lives in S03.

---

### S07 — TEAM (`sec-team`)
**Charts:** 0=0 | **Toggle:** none | **Audience:** AGM Dues, HR, Leadership

| Ref | Submodule | Type | Responsibility | Source |
|---|---|---|---|---|
| 7.1 | Headcount Summary | `KPI_STRIP` | QCG 12 (2+10); MIS 15 (6+9); Mathews 38 (15+23); RMs 24 (12 direct + 12 via Rohan/Akkad) | Manual |
| 7.2 | Organisation Chart | `JOURNEY_PANEL` | CORRECTED org chart. CCO: Ashish / GM Advance: Manuraj / AGM Dues Dubai: Priyanuj / AGM UAQ: Karan / AGM Siniya: Akkad | Manual |
| 7.3 | Reporting Structure | `DEFINITION_BLOCK` | Priyanuj direct: Garima (QCG), Asjad (MIS), Mathews Babu, 12 RMs. Rohan→Akkad: 12 RMs. India growing — not a KPI. | Manual |

**CRITICAL FIX:** v5 org chart is factually incorrect — rebuild from confirmed reporting lines.

---

### S08 — ROADMAP (`sec-roadmap`)
**Charts:** 1=1 | **Toggle:** none | **Audience:** C-suite, AGM Dues, Strategy

| Ref | Submodule | Type | Responsibility | Source |
|---|---|---|---|---|
| 8.1 | Risk Exposure Summary | `KPI_STRIP` | IC threshold 907.7M (251 units); Skyvue 1.27B (535 units); termination gap 134.6M (412 units) — reads S04 constants | R38, R34 |
| 8.2 | Initiative Pipeline | `CHART_PANEL` | 10 expandable initiative cards (toggleRd()): 5 Technology (P1→P3) + 5 Commercial | strategy_doc |
| 8.3 | Strategic Context | `INSIGHT_BLOCK` | PIPELINE_ADV_DENOM 37.8B framing; penetration 8.15%→10.6% thesis; IC threshold → standalone business case | R36, R38 |
| 8.4 | Initiative Definitions | `DEFINITION_BLOCK` | Scope/owner/metric/timeline per initiative; IC threshold governance: "standalone business case required" | strategy_doc |

**Initiatives (10):**
| Priority | Track | Initiative | Timeline |
|---|---|---|---|
| P1 | Technology | Interim PR Module | Q1 2026 |
| P1 | Technology | LP Reversal Automation | Q2 2026 |
| P2 | Technology | Salesforce Internal Audit Integration | Q2–Q3 2026 |
| P2 | Technology | SQL Migration + Power BI (84 reports) | Q3–Q4 2026 |
| P3 | Technology | AI-Driven Audit + Auto-Training | Q1 2027 |
| BOARD CASE FIRST | Commercial | IC Threshold 20%→10% | Requires standalone business case |
| P1 | Commercial | Advance Team Expansion + Booking-Stage Embedding | Q1–Q2 2026 |
| P2 | Commercial | Off-Plan Mortgage Scale-Up (ADIB MoU) | Q2 2026 |
| P2 | Commercial | App Adoption 57%→90% + Payment Link Sunset | Q3–Q4 2026 |
| P3 | Commercial | SOP Library + CCO Power BI + CSAT Live | Q4 2026–Q1 2027 |

---

## PART 3 — CROSS-SECTION DATA FEEDS

| Signal | Source | Consumed By | Method |
|---|---|---|---|
| `OD_TODAY` | R18 | S02_SM1, S04_SM1, S08_SM1 | Single constant — never per-section hardcode |
| LP signal | R26 → S01 | S06_SM6 | Read-only reference |
| advance_baseline | R08 → S05 | S01_SM3, S03_SM3 | Shared constant 3,260M (2025) |
| termination_gap | R34 → S04 | S08_SM1 | Advisory link — data not duplicated |
| IC_threshold | R38 → S04 | S08_SM1, S08_SM3 | Advisory link — policy decision separate |
| `PIPELINE_ADV_DENOM` | R36 | S05_SM5, S08_SM3 | Named constant with inline label |
| MDO_targets | R02 | S02_SM2, S02_SM4, S03_SM3 | Single dynamic source |
| `CY_ADV_MIX_YTD` | R08 derived | S01_SM3, S03_SM3, S05_SM3 | Computed once — referenced 3×, never recalculated |

---

## PART 4 — DUPLICATION RESOLUTION REGISTER

| Issue | v5 State | v6 Resolution |
|---|---|---|
| OD Today hardcoded ×3 | S02/S04/S08 | Single `OD_TODAY` constant from R18 |
| Entity toggle ×10 implementations | Per-section | Single `etog` shared component |
| `days[]` array ×4 | 4 entity closures | Single shared `DAILY_DAYS[]` constant |
| `c-mdo2` unknown purpose | S02 | REMOVED |
| `c-adv-3yr` in S01 duplicates S05 | S01+S05 | REMOVED from S01; single render in S05 as `c-adv-hist` |
| NPV figures labelled "Actual" | S01, S05 | Labelled [PROJECTED] throughout |
| Pipeline figure unlabelled | S02/S04/S05 | All 3 named constants with mandatory inline labels |
| Finance vs MDO gap unlabelled | S02/S03 | Both panels carry definition label on-screen |
| Collector chart unsorted | S03 `c-coll` | Sorted DESCENDING by achievement_pct |
| Finance toggle inline `onclick` | S02 | Migrated to `etog/ev` pattern |
| Org chart factually wrong | S07 | Rebuilt from confirmed reporting lines |
| `CY_ADV_MIX_YTD` recomputed ×3 | S01/S03/S05 | Computed once as global constant |
| Advance monthly arrays shadow-declared | JS block | Module-level declaration only |
| Working days hardcoded = 22 | S03 daily avg | `WORKING_DAYS_MONTH` variable (March=21) |
| OD% formula using purchase_price | v1–v3 | Corrected: `od_aed ÷ ms_due_itd_aed` |

---

## PART 5 — SECTION BOUNDARY SUMMARY

| Content | Lives In | Does NOT Live In |
|---|---|---|
| Nationality & CIV OD analysis | S01 (strategic risk lens) | S04 |
| Advance 3yr monthly chart | S05 c-adv-hist TREND_PANEL | S01 (removed) |
| NPV KPIs 652M/21M/31M | S01 KPI_STRIP [PROJECTED] | S05 (reference only, no numbers) |
| Market context UAE stats | S02 INSIGHT_BLOCK | Any KPI strip |
| Bucket productivity % | S03 (pulse metric) | S04 (definitions) |
| OD ageing snapshot | S04 CHART_PANEL | S04 TREND_PANEL |
| OD ageing monthly trend | S04 TREND_PANEL | S01/S03 |
| SPA legal status | S04 (OD governance) | S02/S06 |
| PIPELINE_ADV_DENOM definition | S05 DEFINITION_BLOCK (once) | S02/S08/chart annotations |
| PR quality + PCC TAT | S06 (same CHART_PANEL) | S03/S04 |
| DLD forfeiture trend | S06 CHART_PANEL | S04 |
| Channel 3yr trend (c-paych) | S06 Payment Infrastructure | S03 |
| Channel current-period doughnut (c-channel) | S03 Operational Pulse | S06 |
| IC threshold policy decision | Standalone business case | S08 (advisory flag only) |
| Org chart | S07 (corrected) | S01/S02 |

---

## PART 6 — CHART COUNT SUMMARY

| Section | v5 | v6 | Δ |
|---|---|---|---|
| S01 Strategic Narrative | 15 | 12 | −3 |
| S02 Portfolio Overview | 7 | 5 | −2 |
| S03 Live Pulse | 10 | 10 | 0 |
| S04 Dues Collections | 7 | 7 | 0 |
| S05 Advance Collections | 6 | 7 | +1 |
| S06 Operations & QCG | 6 | 6 | 0 |
| S07 Team | 0 | 0 | 0 |
| S08 Roadmap | 1 | 1 | 0 |
| **TOTAL** | **52** | **48** | **−4** |
