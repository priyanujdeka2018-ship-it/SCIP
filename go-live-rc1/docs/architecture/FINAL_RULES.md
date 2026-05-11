# SOBHA COLLECTIONS PLATFORM — FINAL SYSTEM RULES
## v6 Build | March 2026

---

## BLOCK 1 — DATA INTEGRITY RULES

### R-D01: OD% Formula
```
od_pct = od_aed ÷ ms_due_itd_aed × 100
```
- Denominator is ALWAYS `ms_due_itd_aed` (milestones due inception-to-date)
- NEVER use `purchase_price_aed` as denominator
- Violation: India OD understated 2% (wrong) vs 4.33% (correct)
- Applies to: all OD% calculations in S01/S04/R16/R18

### R-D02: Finance vs MDO Target Disambiguation
- **MDO Dues** = Dues-only (Jan = 700.5M). Source: R02. Dynamic — adjusted mid-year.
- **Finance Dues** = D+A combined (Jan = 909M). Source: R04. Static.
- Both MUST be labelled on-screen in every panel where they appear
- Achievement% will differ for the same actual depending on which definition is used
- Never mix these two definitions in a single chart without explicit labels

### R-D03: CY vs FY Advance
- **CY** = advance collected on milestones due in the current calendar year
- **FY** = advance collected on future-year milestones
- Jan 2025 CY = 70.1%, FY = 29.9%
- Prior error swapped these — CY 70.1% is the CORRECT value; 30% was FY%
- Applies to: R08 column `cy_advance_aed`, `fy_advance_aed`

### R-D04: Pipeline Figures — Three Distinct Constants
| Constant | Value | Definition | Permitted Sections |
|---|---|---|---|
| `PIPELINE_GROSS` | 43.5B | Total remaining forward milestones (R36) | S02 hero, S04 hero |
| `PIPELINE_FORWARD_BOOK` | ~40B | Approx opening 2025 book (narrative only) | S01 narrative text |
| `PIPELINE_ADV_DENOM` | 37.8B | 43.5B − 5.7B prior advances (R36 derived) | S05 penetration calc, S08 context |

- NEVER display a pipeline figure without its inline label
- NEVER use PIPELINE_GROSS as the advance penetration denominator
- NEVER use PIPELINE_ADV_DENOM in S02 portfolio hero card

### R-D05: Units Count Disambiguation
- `active_excl_pcc` = 30,044 — use for: app adoption %, coverage calculations
- `all_qualified_itd` = 34,731 — use for: portfolio count, hero card
- Both MUST be labelled explicitly wherever displayed
- Never substitute one for the other without re-labelling

### R-D06: OD Today — Source of Truth
- Source: R18 (2026-03-15)
- Values: Sobha = 1,472.7M | Siniya = 166.4M | DT = 11.0M | Group = 1,650.1M
- Do NOT use strategy document estimate of 1.57B for Sobha — that figure is incorrect
- Always reference `OD_TODAY` constant — never hardcode

### R-D07: 30-Day Collection Efficiency
- Formula: `dues_collected_aed ÷ booksize_bom_aed × 100`
- 2025 average = 34.8%
- Deprecated value of 18% (v3) is WRONG — do not use or reference

### R-D08: App Payment Channel Share
- Formula: `app_txn_count ÷ total_da_txn_count × 100`
- Basis: Transaction COUNT only
- Do NOT compute using AED value — will produce a different, incorrect figure

### R-D09: Book Penetration Denominator
- Formula: `annual_advance_aed ÷ PIPELINE_ADV_DENOM × 100`
- 2026 denominator = PIPELINE_ADV_DENOM = 37.8B (not 43.5B, not 40B)
- Definition displayed ONCE in S05_SM7 DEFINITION_BLOCK
- Chart tooltips and KPI annotations reference the constant by name — do not re-explain per instance

### R-D10: Working Days
- March 2026 actual = 21 working days
- `WORKING_DAYS_MONTH` variable must be used — never hardcode 22
- Daily MDO avg formula: `monthly_dues_target ÷ WORKING_DAYS_MONTH`

---

## BLOCK 2 — LABELLING RULES

### R-L01: NPV Scenario Figures
- 652M (incremental inflow) / 21M (rebate cost) / 31M (bank equivalent) are PROJECTED figures
- These come from a proposal model, not historical actuals
- ALL THREE must carry [PROJECTED] label in every display context
- S01 is the single source of these KPIs; S05 references by name only (no re-display of numbers)

### R-L02: Finance vs MDO On-Screen Label
- Every panel showing a dues target must display one of:
  - "MDO Dues Target (Dues only)"
  - "Finance Dues Target (D+A combined)"
- Showing a number without this label is a display defect

### R-L03: Collector Data Currency
- All collector arrays are a static Mar 2026 MTD snapshot
- Must be labelled "Snapshot: Mar 2026 MTD" with a `refresh_date` field
- No live refresh mechanism — make this explicit to users

### R-L04: Advance Monthly Arrays
- CY/FY advance arrays (`grp_a`, `cy25`, `fy25`) declared at module level only
- No re-declaration inside JS blocks — shadow variable risk removed in v6

---

## BLOCK 3 — COMPONENT RULES

### R-C01: Entity Toggle
- Single component: `etog`
- States: Group / Sobha / Siniya / DT
- S03 entity daily panels: use `class="daily-ent"` — NOT `class="ev"` — to prevent interference
- All 10 per-section v5 implementations (story-etog, ann-etog, mdo-etog, fin-etog, mix-etog, port-etog, lp-etog, pu-etog + 2 others) are DEPRECATED and removed

### R-C02: Finance Version Toggle
- Pattern: `etog/ev`
- Deprecated: inline `onclick` in S02
- All finance-target panel toggles must use `etog/ev` pattern

### R-C03: OD Today Constant
- `OD_TODAY` is the only permitted reference to group/entity OD stock
- Must be refreshed from R18 on page load
- Three deprecated hardcoded instances (S02/S04/S08) removed

### R-C04: Daily Days Array
- Single shared constant `DAILY_DAYS[]` sourced from R04
- Four duplicate `days[]` declarations in entity closures removed

### R-C05: Working Days Variable
- Variable: `WORKING_DAYS_MONTH`
- Hardcoded value 22 deprecated and removed
- March 2026 = 21; update per month

### R-C06: CY Advance Mix
- Computed once as `CY_ADV_MIX_YTD = 81.1%` global constant from R08
- Referenced in S01/S03/S05 — never recomputed per-section

### R-C07: Collector Chart Sort
- `c-coll` horizontal bars MUST be sorted DESCENDING by `achievement_pct`
- v5 is unsorted — fix is mandatory in v6

### R-C08: Removed Component
- `c-mdo2` is REMOVED from v6
- Purpose was unconfirmed; do not recreate without explicit specification

---

## BLOCK 4 — SECTION BOUNDARY RULES

### R-B01: S01 Advance Content
- S01 Advance Narrative = KPI_STRIP only (totals, growth %, NPV KPIs)
- `c-adv-qtr` (quarterly acceleration) is the only chart permitted in S01 advance — unique narrative
- `c-adv-3yr` (3yr monthly overlay) is REMOVED from S01
- The 3yr monthly overlay lives exclusively in S05 as `c-adv-hist` TREND_PANEL

### R-B02: S01 Advance NPV
- S01 owns NPV financial model KPIs (652M/21M/31M) — clearly labelled [PROJECTED]
- S05 Rebate Strategy INSIGHT_BLOCK references the S01 finding by name only
- S05 must NOT re-display the numerical values 652M/21M/31M

### R-B03: S01 vs S04 OD Analysis
- S01 Nationality/CIV = strategic risk lens (who are our riskiest customer segments)
- S04 = operational OD list (what is our current overdue stock, ageing, and project ranking)
- These are distinct questions — content must not cross sections

### R-B04: S02 vs S04 OD Values
- S02 = entity-level OD in portfolio snapshot context (entity toggle, part of stock position)
- S04 = group-level OD analysis (ageing, composition, trend)
- Both use `OD_TODAY` constant from R18 — no conflict; different granularity of same signal

### R-B05: S02 vs S03 MDO Achievement
- S02 Q1 MDO framing = "Year-to-Date Summary (Strategic)"
- S03 Q1 MDO framing = "Q1 Actuals vs MDO (Operational Pulse)"
- Same source (R02), same values — different section context labels. Both are correct.

### R-B06: S03 vs S04 Bucket Productivity
- Bucket productivity % (FE=44.1%, OD=35.4%, Term=27.2%) lives in S03 as a pulse metric
- S04 contains definitions and governance — NOT productivity KPIs

### R-B07: S03 vs S06 Payment Channel
- S03 `c-channel` = current-period doughnut (what channel did customers use THIS month). COUNT basis.
- S06 `c-paych` = 3yr grouped bar (how has channel mix shifted 2024–2026). COUNT basis.
- These are different chart types answering different questions — must not be merged or swapped

### R-B08: S04 vs S08 IC Threshold
- S04 = operational flag: risk data, paid band distribution, advisory note
- S08 = strategic advisory: what the board should decide about IC threshold
- S08 reads S04 constants via advisory link — does NOT independently fetch data
- IC threshold policy change requires a standalone board business case — decision is NOT made on platform

### R-B09: S05 Penetration Definition
- PIPELINE_ADV_DENOM = 37.8B is defined ONCE in S05_SM7 DEFINITION_BLOCK
- Not re-explained in S02, S08, or in chart tooltips/annotations
- All other references use the constant name with its value inline

### R-B10: S08 Risk KPIs
- S08_SM1 KPI strip carries an advisory link label: "Source: S04 Risk Flags"
- S08 adds policy context — it does not recalculate or re-fetch the underlying data

---

## BLOCK 5 — GOVERNANCE RULES

### R-G01: IC Threshold Policy
- The IC threshold change (20%→10%) is flagged as advisory on the platform
- The policy decision is made in a SEPARATE standalone board business case document
- The platform (S04 and S08) shows the risk data — it does not make or endorse the decision

### R-G02: Org Chart
- S07 org chart is rebuilt from confirmed reporting lines
- The v5 org chart is factually incorrect and must not be reused
- Confirmed structure: CCO (Ashish) → AGM Dues Dubai (Priyanuj) → direct: Garima (QCG), Asjad (MIS), Mathews Babu, 12 RMs; Rohan Nair → 12 RMs (reports via Akkad)

### R-G03: India Team Growth
- India team growth (QCG, MIS, Mathews) is editorial context in S07_SM3
- It is NOT a KPI — no targets are set for India team growth
- Do not add a KPI card or metric for India headcount targets

### R-G04: Deprecated OD Formula
- OD% = OD ÷ Purchase Price (v1–v3) is DEPRECATED
- Any cached document, tooltip, or annotation using this formula is WRONG
- All instances must be replaced with: OD% = OD ÷ MS Due ITD

### R-G05: Strategy Document as Source
- `strategy_doc` is a valid source reference for roadmap initiatives and governance context
- It is NOT a valid source for financial KPIs, OD values, or collection targets
- Financial values in strategy_doc may conflict with R-series source reports — source reports win

### R-G06: UAE Market Context
- UAE market data (214,912 transactions, 682.5B value) is static editorial
- No source file exists; no update mechanism
- Displayed in S02_SM5 as INSIGHT_BLOCK only — never in a KPI strip

### R-G07: Collector Data
- Collector performance arrays are a static Mar 2026 MTD snapshot
- No live refresh mechanism exists
- Must be explicitly labelled with data currency date on-screen

---

## BLOCK 6 — METRIC INTEGRITY RULES

### R-M01: Global Metric Compute-Once
| Metric | Constant | Sections Using |
|---|---|---|
| CY Advance Mix % | `CY_ADV_MIX_YTD = 81.1%` | S01, S03, S05 |
| OD Today | `OD_TODAY = 1,650.1M` | S02, S04, S08 |
| Advance penetration denom | `PIPELINE_ADV_DENOM = 37.8B` | S05, S08 |

Each computed ONCE. Referenced N× from that single computation.

### R-M02: Achievement% Context
- `achievement_pct = actual ÷ target × 100`
- Applies at: collector level (R30), entity monthly (R02), entity quarterly (R02/R04)
- Context determines which target definition is used (MDO Dues vs Finance Dues vs Advance)
- Always label the target definition alongside the achievement%

### R-M03: D+A CAGR
- Formula: `(12,966 / 867)^(1/4) − 1 = 97%`
- Base year 2021 = 867M. Current year 2025 = 12,966M.
- Source: R01 only

### R-M04: Book Penetration
- 2025 = 8.15% (annual advance 3,260M ÷ opening book ~40B)
- 2026 target = 10.6% (advance target ÷ PIPELINE_ADV_DENOM 37.8B)
- Denominator MUST be labelled with its constant name in every display

### R-M05: LP Growth
- 1.54M (2021) → 34.82M (2025) = 22× growth
- Source: R26
- Used as delinquency proxy signal in S01 and as volume metric in S06

---

## APPENDIX A — STATIC HARDCODES (Staleness Risk Register)

| Value | Location | Risk | v6 Resolution |
|---|---|---|---|
| OD Today = 1.65B | S02/S04/S08 (×3) | Changes daily | `OD_TODAY` constant from R18 |
| Collector arrays | `c-coll` | Mar 2026 snapshot | Label "Snapshot: Mar 2026 MTD" + refresh_date field |
| Daily collections Mar 1–18 | 4 entity closures | Snapshot | `DAILY_DAYS[]` constant; label snapshot date |
| NPV figures 652M/21M/31M | S01, S05 | Proposal model | Labelled [PROJECTED] throughout |
| UAE market data | S02 | No update mechanism | INSIGHT_BLOCK with static label |
| Working days = 22 | S03 daily avg | March = 21 | `WORKING_DAYS_MONTH` variable |
| Avg advance lead = 248d | S01/S05 | Historical avg; no real-time | Derived constant from R08; note calculation basis |

---

## APPENDIX B — v5 KNOWN ISSUES (All Resolved in v6)

| Issue | v5 | v6 Fix |
|---|---|---|
| Entity toggle ×10 implementations | Per-section | Single `etog` |
| `days[]` array ×4 | 4 entity closures | Single `DAILY_DAYS[]` |
| `c-mdo2` unknown purpose | S02 | REMOVED |
| Advance arrays re-declared in JS block | Shadow risk | Module-level only |
| NPV labelled "Actual" | S01/S05 | [PROJECTED] |
| Pipeline figures unlabelled | S02/S04/S05 | 3 named constants with inline labels |
| Finance/MDO gap unlabelled | S02/S03 | On-screen definition labels |
| Collector chart unsorted | S03 | Sorted DESC by achievement_pct |
| Finance toggle inline onclick | S02 | etog/ev pattern |
| Org chart factually wrong | S07 | Rebuilt from confirmed lines |
| `c-adv-3yr` duplicated in S01+S05 | Both | S01 removed; S05 authoritative as c-adv-hist |
| OD% using purchase price | v1–v3 cached | ms_due_itd denominator throughout |
| `CY_ADV_MIX_YTD` recomputed ×3 | S01/S03/S05 | Global constant computed once |
| OD Today hardcoded ×3 | S02/S04/S08 | `OD_TODAY` constant |

---

*Final Rules version: 2.0 — approved for v6 engineering build*
*Supersedes: all prior rule sets embedded in SystemMap v1, Engineering Structure v1, Architecture Blueprint v1*
