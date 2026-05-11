# SOBHA COLLECTIONS PLATFORM — ENGINEERING STRUCTURE REFERENCE
**Extracted from:** SystemMap v1 + Data Schema v1
**Build target:** v5 → v6
**Sections:** 8 | **Charts:** 52 | **Source Reports:** 38

---

## 1. SECTION_STRUCTURE

---

### S01 — 2025 Story (`sec-story`)

#### Submodule: Growth Trajectory
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| Annual entity stacked bar | Chart | `c-annual-entity` | Group: Dues / Adv / NS stacked by year 2021–2025 |
| Sobha annual stacked bar | Chart | `c-ann-sob` | Sobha entity only |
| Siniya + DT stacked bar | Chart | `c-ann-sin` | Siniya + Downtown combined |
| % mix trend (group) | Chart | `c-mix-year-grp` | Restored in v5 from v3; % split by year |
| % mix trend (Sobha) | Chart | `c-mix-year-sob` | Sobha % split by year |
| Monthly 2025 stacked (group/sob/sin) | Chart | `c-mix-grp` / `c-mix-sob` / `c-mix-sin` | Monthly entity stacked |
| LP annual (group/sob/sin) | Chart | `c-lp-grp` / `c-lp-sob` / `c-lp-sin` | Late payment trend |
| Units by year (group/sob/sin) | Chart | `c-port-grp` / `c-port-sob` / `c-port-sin` | Booking cohort units |
| D+A CAGR | KPI | — | 97% (2021–2025) |
| 15× headline growth | KPI | — | 867M → 12,966M |
| LP growth | KPI | — | 1.54M → 34.82M (22×) |
| Sobha 2025 total | KPI | — | AED 14.06B |
| Siniya 2025 total | KPI | — | AED 2.51B |
| DT 2025 total | KPI | — | AED 0.25B |

#### Submodule: Advance Deep Dive
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| 3-year monthly advance comparison | Chart | `c-adv-3yr` | 2023 / 2024 / 2025 monthly overlay |
| 2025 CY/FY monthly split | Chart | `c-adv-2025` | CY + FY stacked per month |
| Quarterly acceleration | Chart | `c-adv-qtr` | Q1=512M, Q2=857M, Q3=858M, Q4=1,032M |
| 2025 annual advance | KPI | — | 3,260M |
| Peak single month | KPI | — | Dec 2025 = 406M |
| CY mix range | KPI | — | Jan=70.1% → Dec=0% |

#### Submodule: NPV Rebate Panel
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| Incremental inflow | KPI | — | AED 652M |
| Rebate cost | KPI | — | AED 21M |
| Bank equivalent cost | KPI | — | AED 31M |
| Current NPV rate | KPI | — | 3.5% |
| Proposed NPV rate | KPI | — | 4.3% |
| 2026 YTD rebate | KPI | — | 9.14M on 641M (1.4% effective) |
| Avg advance lead time | KPI | — | 248 days |

#### Submodule: Nationality & CIV
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| Nationality bar + OD% line | Chart | `c-nat` | Top 10 nationalities; Purchase Price bar + OD% line |
| CIV band bar + OD% line | Chart | `c-civ` | CIV band segments + OD% overlay |
| OD ranking bars | Chart | — | Ranked by OD AED |
| India OD | KPI | — | 272M (4.33%) |
| Iran OD% | KPI | — | 9.14% |
| Russia OD% | KPI | — | 2.36% |
| China OD% | KPI | — | 1.73% |
| CIV portfolio total OD% | KPI | — | 3.88% (1,650M / 42,505M) |

**Entity toggle:** `story-etog` — Group / Sobha / Siniya / DT
**Cross-section feeds:** → S02 (entity totals), → S05 (advance baseline), → S06 (LP signal)

---

### S02 — Overview (`sec-overview`)

#### Submodule: Portfolio Cards
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| Group stat card | KPI | — | Sale Value 86.0B / Collected ITD 43.3B (50.3%) / Pipeline 43.5B / OD 1.65B |
| Sobha stat card | KPI | — | 2025: 14.06B / OD 1.47B |
| Siniya + DT stat card | KPI | — | 2025: 2.76B / OD 177M |

#### Submodule: Value Chain
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| 6-node swimlane visual | Visual | — | Booking 2%→10% / 55d window / 248d advance lead / LP 1%/15d / PCC TAT 3–5d / Title Deed |

#### Submodule: 2026 Targets — MDO Version
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| MDO grouped bar (total) | Chart | `c-mdo-tot` | 9-month target vs actual |
| MDO grouped bar (Sobha) | Chart | `c-mdo-sob` | Entity split |
| MDO grouped bar (Siniya) | Chart | `c-mdo-sin` | Entity split |
| MDO grouped bar (DT) | Chart | `c-mdo-dt` | Entity split |
| Secondary MDO chart | Chart | `c-mdo2` | ⚠ Purpose unclear — possible duplicate of `c-mdo-tot` |
| FY Dues target | KPI | — | 11.5B |
| FY Advance target | KPI | — | 4.0B |
| Q1 Dues achievement | KPI | — | 91% (1.92B / 2.11B) |
| Q1 Advance achievement | KPI | — | 73% (702M / 960M) |

#### Submodule: 2026 Targets — Finance Version (toggle)
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| Finance Dues+NS grouped bar | Chart | `c-fin-tot` | Finance combined target vs actual |
| Siniya Finance bar | Chart | `c-fin-sin` | Siniya entity |
| Finance Jan Dues target | KPI | — | 909M |
| Finance Jan actual | KPI | — | 1,069M (118%) |
| NS Jan target | KPI | — | 507M |
| NS Jan actual | KPI | — | 231M (46%) |

#### Submodule: UAE Market Panel
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| Market stats panel | Static Text | — | 214,912 tx / 682.5B value / 65–72% off-plan / Sobha #4 ~10% share |

**Toggle (target version):** `tgt-mdo-btn` / `tgt-fin-btn` — inline `onclick` ⚠ inconsistent with `etog/ev` pattern
**Entity toggle:** `mdo-etog` / `fin-etog`
**Cross-section feeds:** → S03 (MDO targets as denominator), → S04 (OD sync from R18)

---

### S03 — Live Pulse (`sec-pulse`)

**Architecture:** Single entity toggle `pu-etog` (Total / Sobha / Siniya / Downtown) controls all three subpages simultaneously via mapped handler. Daily entity panels use `class="daily-ent"` (not `class="ev"`) to prevent generic toggle interference.

#### Submodule: MTD Performance
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| Total daily bar (Dues+NS, MDO dotted) | Chart | `c-daily` | Gold Dues + Slate NS stacked; MDO avg dotted line |
| Sobha daily canvas | Chart | `c-daily-sob` | Entity panel |
| Siniya daily canvas | Chart | `c-daily-sin` | Entity panel |
| Downtown daily canvas | Chart | `c-daily-dt` | Entity panel |
| Group Dues MTD | KPI | — | 547M (Finance target 873M, 62.7%) |
| Advance MTD | KPI | — | 124M (MDO target 320M, 38.8%) |
| NS MTD | KPI | — | 20M (target 507M, 4%) ⚠ critical |
| Group daily MDO avg | KPI | — | 46.4M/day (872M ÷ 22 days) |

#### Submodule: YTD Performance
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| Dues monthwise grouped bar (entity) | Chart | `c-ytd-dues` | Target outline vs solid actual |
| Advance CY/FY grouped bar | Chart | `c-ytd-adv` | CY/FY split |
| Advance entity stacked vs target | Chart | `c-ytd-adv-ent` | Entity stacked + target line |
| Q1 Dues | KPI | — | 1.92B vs 2.11B MDO (91%) |
| Q1 Advance | KPI | — | 702M vs 960M (73%) |
| Q1 NS | KPI | — | 473M vs 1.52B (31%) ⚠ critical |
| 2026 YTD CY mix | KPI | — | 81.1% (Jan 84%, Feb 77%, Mar 86%) |

#### Submodule: Collector Performance
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| Horizontal bars by achievement% | Chart | `c-coll` | Color-coded; ⚠ NOT sorted by achievement% |
| Top / Bottom performer tables | Table | — | Top: Walid 56%, Abdellatif 54.8%; Bottom: Ainur 29.5%, Oksana 32.1% |
| PTP pipeline | Chart | `c-ptp` | Promise-to-pay pipeline |
| Collector count | KPI | — | 24 |
| Bucket productivity | KPI | — | FE 44.1%, OD 35.4%, Term 27.2% |

#### Submodule: Coverage & Channel
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| Coverage bars (5 buckets) | Inline HTML | — | FE 99.7%, OD 99.9%, Term 100%, Siniya 86.2% ⚠, Total 97.1% |
| Payment channel doughnut | Chart | `c-channel` | Units paid by channel (COUNT basis) |
| FE coverage | KPI | — | 2,691 / 2,700 (834M pool) |
| OD coverage | KPI | — | 2,685 / 2,687 (1.04B pool) |
| Siniya coverage | KPI | — | 1,231 / 1,429 = 86.2% ⚠ (198 unworked, 319M) |
| Channel split | KPI | — | Email 37%, Call 34%, Self 25%, WhatsApp 2.7% |

**Entity toggle:** `pu-etog`
**Cross-section feeds:** → S02 (MDO targets as denominator), → S04 (coverage gaps)

---

### S04 — Dues Collections (`sec-dues`)

#### Submodule: OD Analysis
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| OD ageing doughnut (6 bands) | Chart | `c-od-ageing` | 0-30 / 31-60 / 61-90 / 91-120 / 121-180 / 180+ |
| Top 10 projects OD bar | Chart | `c-od-proj` | Horizontal; tooltip = AED M; top = Riverside Crescent 237.4M |
| Monthly ageing stacked 2025 | Chart | `c-od-trend` | Jan–Dec 2025 monthly trend |
| SPA legal status | Chart | `c-spa` | 4 legal status types |
| OD Today | KPI | — | 1.65B ⚠ hardcoded static — stale daily |
| EOM OD | KPI | — | 2.17B |
| Collectible window | KPI | — | 2.56B (OD 1.65B + Mar MS 0.91B) |
| Termination gap | KPI | — | 134.6M (412 units not-in-system) |
| Ageing: 0–30d | KPI | — | 830M |
| Ageing: 31–60d | KPI | — | 445M |
| Ageing: 61–90d | KPI | — | 166M |
| Ageing: 91–120d | KPI | — | 79M |
| Ageing: 121–180d | KPI | — | 47M |
| Ageing: 180+d | KPI | — | 225M |
| SPA: Pre-reg complete | KPI | — | 77% (1.28B) |
| SPA: Not signed | KPI | — | 2.2% (36.4M) |

#### Submodule: Dues Efficiency
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| Booksize BOM bar + dues line | Chart | `c-dues-book` | Monthly booksize vs dues collected |
| Termination volume bars | Chart | `c-term` | Monthly termination volumes |
| 30-day efficiency | KPI | — | 34.8% avg 2025 (Dues / Booksize BOM) |
| Termination avg/month | KPI | — | 427 units (Apr–Dec 2025) |
| Total eligible | KPI | — | 1,314 units / 700.7M |
| Dev notice sent | KPI | — | 251 units / 138.5M |

#### Submodule: Bucket Architecture
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| Bucket stat cards + SPA status bar | Static HTML | — | FE 35% / Other OD 55% / Term 10% |
| FE accountability rule | Definition | — | RM stays with unit even after OD status change |
| Termination exit rule | Definition | — | 100% OD required; no partials; collections cease post-DLD notice |

**Cross-section feeds:** → S08 (termination gap, IC threshold advisory)

---

### S05 — Advance Collections (`sec-advance`)

#### Submodule: 2025 Monthly Performance
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| Monthly CY/FY stacked 2025 | Chart | `c-adv-main` | CY + FY per month |
| 3-year monthly comparison | Chart | `c-adv-hist` | 2023 / 2024 / 2025 overlay |
| 2025 annual advance | KPI | — | 3,260M |
| vs 2024 | KPI | — | +125% |
| vs 2023 | KPI | — | +238% |
| Dec 2025 CY | KPI | — | 0% (100% FY by December) |

#### Submodule: 2026 Performance vs Target
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| Monthly CY/FY bar + 320M/month target line | Chart | `c-adv-2026` | 2026 YTD monthly |
| 2026 YTD advance | KPI | — | 640.9M |
| Q1 vs target | KPI | — | 73% (640.9M / 960M) |
| 2026 YTD CY mix | KPI | — | 81.1% |

#### Submodule: Book Penetration
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| Penetration % chart | Chart | `c-adv-pen` | % of opening book collected as advance |
| 2025 penetration | KPI | — | 8.15% (3,260M / ~40B opening book) |
| 2026 target penetration | KPI | — | 10.6% (4,000M / ~37.8B corrected denominator) |
| Denominator definition | Definition | — | 43.5B pipeline − 5.7B 2025 advances = 37.8B ⚠ NOT static 40B |

**Cross-section feeds:** ← S01 (CY baseline), → S08 (forward book framing)

---

### S06 — Operations & QCG (`sec-ops`)

#### Submodule: PR Quality
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| PR quality doughnut | Chart | `c-prq` | Approved / Doc-gap / Manual-error split |
| PCC TAT bar by month | Chart | `c-pcc` | Jan 2025 – Feb 2026 monthly |
| 1st-pass approval rate | KPI | — | 51% (Dec 2025 sample, n=1,818) |
| Doc gap rate | KPI | — | 27% |
| Manual error rate | KPI | — | 23% |
| PCC TAT (pre-initiative) | KPI | — | avg 20 days |
| PCC TAT (post-initiative) | KPI | — | 3–5 days |
| PCC TAT (target) | KPI | — | 2 days |
| PR visibility gap | KPI | — | 250–300M (uncommitted PRs) |

#### Submodule: Payment Channels
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| 9-channel grouped bar (3 years) | Chart | `c-paych` | COUNT basis; 2024 / 2025 / 2026 YTD |
| PR-to-SOA TAT band progression | Chart | `c-prtat` | 2024 / 2025 / 2026 YTD by TAT band |
| App payment share | KPI | — | 0.1% (2024) → 6% (2025) → 25.9% (2026 YTD) |
| Wire transfer share | KPI | — | 43.5% of 2026 transactions |
| 0–2d TAT band (PR→SOA) | KPI | — | 25% → 35% → 51% |

#### Submodule: Other Charges & Helpdesk
| Component | Type | ID | Value/Notes |
|---|---|---|---|
| Annual charges stacked | Chart | `c-ochg` | LP / DLD Forfeiture / IC Forfeiture / NOC+Admin |
| Helpdesk monthly closed + TAT% line | Chart | `c-helpdesk` | Monthly volume + within-TAT % |
| 2026 YTD DLD forfeiture | KPI | — | 38.9M (> full 2025: 22.3M) |
| Helpdesk YTD closed | KPI | — | 120,700 cases |
| Helpdesk within TAT | KPI | — | 85.5% |

**Cross-section feeds:** ← S01 (LP signal from R26)

---

### S07 — Team (`sec-team`)

| Component | Type | Notes |
|---|---|---|
| Org chart | Visual | ⚠ NOT factual per Priyanuj — dashboard org chart does not reflect actual structure |
| Headcount cards | KPI | QCG: 12 (Garima leads; 2 Dubai + 10 India), MIS: 15 (Asjad leads; 6 Dubai + 9 India), Mathews: 38 (15 Dubai + 23 India) |
| RM reporting structure | Definition | 12 RMs report to Priyanuj directly; 12 report to Rohan (under Akkad) |

---

### S08 — Roadmap (`sec-roadmap`)

| Component | Type | ID | Value/Notes |
|---|---|---|---|
| 10 initiative drill-downs | Expandable | `toggleRd()` → `rd-body.open` | Each with impact badges |
| IC threshold advisory flag | Flag | — | Sourced from S04 termination gap + R38 risk data |
| Strategic context panel | Static | — | Sourced from S05 advance penetration denominator (R36) |
| OD advisory flags | KPI | — | ⚠ 1.65B hardcoded same as S02/S04 |

---

## 2. DATA_USAGE

| Section | Datasets Used | Key Columns |
|---|---|---|
| S01 Growth | R01, R08, R26, R03 | Year, Entity, Dues, Advance, NS, LP, Units |
| S01 Advance | R08 | Month, Entity, CY AED, FY AED, Total Advance |
| S01 NPV | R08 (Rebate Summary) | NPV applied, Rebate %, Advance with/without rebate |
| S01 Nationality | R16 | Nationality, Purchase Price, MS Due ITD, Paid ITD, Overdues |
| S01 CIV | R16 | CIV Band, Units, MS Due ITD, Overdues, OD% |
| S02 Portfolio | R13, R18, R36 | Collected ITD, OD Today, Pipeline AED, Entity |
| S02 MDO Targets | R02 | Month, Entity, Static target, Dynamic target, Advance target, Actuals |
| S02 Finance Targets | R04 | Month, Finance Dues target, NS target, MTD actuals |
| S02 Market | External (no source file) | Transaction count, Value, Off-plan %, Market share |
| S03 MTD | R04, R05, R06, R07 | Date, Dues, Advance, NS, Monthly target |
| S03 YTD | R02, R04, R08 | Month, MDO target, Finance actual, CY advance, FY advance |
| S03 Collectors | R30, R32 | Collector name, Target AED, Actual AED, Units allocated, Units paid |
| S03 Coverage | R10, R30 | Bucket, Units allocated, Units contacted, OD pool AED |
| S04 OD Analysis | R18, R12, R17, R34 | OD Today, Ageing bands (6), Project OD, Legal status, Termination status |
| S04 Efficiency | R12, R34 | Month, Booksize BOM, Dues collected, Eligible units, In-system units |
| S05 2025 Advance | R08 | Month, CY AED, FY AED, Entity |
| S05 2026 Advance | R08 (2026CYFY) | Month, CY AED, FY AED, Target (320M/month) |
| S05 Penetration | R08 (numerator), R36 (denominator) | Annual advance, Booking Year, Forward milestone obligations |
| S06 PR Quality | R31, Strategy doc | Date, PRs submitted, Approved, Rejected, Reason (doc/manual) |
| S06 Channels | R25, R20 | Channel (9), Year, COUNT, %; TAT band, Year, Count |
| S06 Other Charges | R26 | Year, LP, DLD Forfeiture, IC Forfeiture, NOC/Admin |
| S06 Helpdesk | R29 | Month, Cases closed, Within TAT % |
| S07 Team | Manual / org chart | Headcount, Reporting lines |
| S08 Roadmap | S04 (termination), S05 (forward book), R38 (risk bands) | Paid% band, CIV band, Units, Sale Value, Balance collectible |

---

## 3. METRICS_CANDIDATES

| Metric | Formula | Source | Sections |
|---|---|---|---|
| **OD% (Delinquency Rate)** | `Overdues ÷ MS Due Till Date × 100` | R16 | S01, S02, S04 |
| ~~OD% (OLD — WRONG)~~ | ~~Overdues ÷ Purchase Price × 100~~ | — | Deprecated v1–v3 |
| **30-Day Collection Efficiency** | `Dues collected in month ÷ Booksize BOM × 100` | R12 | S04 |
| **Book Penetration %** | `Annual advance collected ÷ Opening forward book × 100` | R08, R36 | S05 |
| **CY Advance Mix %** | `CY advance ÷ Total advance × 100` | R08 | S01, S03, S05 |
| **Collector Achievement %** | `ROUND(collAct[i] / collTgt[i] × 100)` — JS runtime | R30 | S03 |
| **Agent Coverage %** | `Units contacted ÷ Units allocated × 100` | R10 | S03 |
| **PR 1st-Pass Approval Rate** | `Approved ÷ Total submitted × 100` | R31 | S06 |
| **NPV Effective Rate** | `Total rebate applied ÷ Total advance collected × 100` | R08 | S01, S05 |
| **Finance Dues Target** | `Dues + Advance combined (static)` | R04 | S02, S03 |
| **MDO Dues Target** | `Dues only (dynamic, adjusted mid-year)` | R02 | S02, S03 |
| **March Collectible Window** | `OD Today + March milestones due` | R18 + R02 | S04 |
| **EOM OD** | `OD Today + remaining current-month milestones if zero collection` | R18 + R02 | S04 |
| **D+A CAGR** | `(12,966 / 867)^(1/4) − 1` | R01 | S01 |
| **15× growth** | `12,966M / 867M` | R01 | S01 |
| **LP 22× growth** | `34.82M / 1.54M` | R26 | S01 |
| **2026 Advance Book Denominator** | `43.5B pipeline − 5.7B prior advances = ~37.8B` | R36 | S05 |
| **MDO Daily Avg (Dues)** | `872M ÷ 22 working days = 39.6M/day` | R02 | S03 |
| **Siniya Coverage Gap** | `1,429 − 1,231 = 198 units unworked` | R10 | S03 |
| **Termination Unactioned** | `1,314 eligible − 902 in-system = 412 units / 134.6M` | R34 | S04, S08 |
| **CIV Total OD%** | `1,650M ÷ 42,505M × 100 = 3.88%` | R16 | S01 |
| **NPV Bank Cost** | `652M × 4.75% × (248/365) = ~31M` | R08 | S01 |
| **NPV Rebate Cost** | `652M × 4.3% × (248/365) = ~21M` | R08 | S01 |

---

## 4. DUPLICATION_CHECK

### 4.1 — Repeated Metrics Across Sections

| Metric | Sections | Risk |
|---|---|---|
| OD Today (1,650.1M) | S02 hero, S04 hero, S08 advisory | Hardcoded in 3 locations. Changes daily. All must sync from R18. ⚠ |
| Entity toggle (Group/Sobha/Siniya/DT) | S01, S02, S03, S04, S05 | 10 independent implementations. No shared component. |
| Forward pipeline size | S02 hero (43.5B), S04 hero (43.5B), S05 denominator (~37.8B), narrative (~40B) | 3 distinct numbers, different definitions, not always labelled. ⚠ |
| MDO target values | S02 MDO panel, S03 YTD | Same R02 source but separate hardcoded references. |
| CY advance mix % | S01, S03, S05 | Computed from R08 in each section independently. |
| Active bookings count | S02 value chain (30,044), S07 implied | 30,044 = active excl. PCC; 34,731 = all qualified ITD. Not always differentiated. ⚠ |
| 55-day window definition | S04 bucket, S02 value chain | Consistent (T-25 pre-due to T+30 post-due). No risk. |
| AED M/B formatting callback | All chart tooltips | Global `dflt` callback (v≥1000 → B, v<1000 → M) — some charts override. Low risk. |

### 4.2 — Repeated Logic (Cross-Section)

| Logic | Locations | Risk |
|---|---|---|
| Entity toggle handler | `pu-etog`, `ann-etog`, `story-etog`, `mdo-etog`, `fin-etog`, `mix-etog`, `port-etog`, `lp-etog` | Implemented independently per section. Each future chart addition risks misalignment. |
| OD% formula | S01 CIV/Nationality, S04 OD analysis | Same corrected formula (OD ÷ MS Due ITD) must be applied consistently. Old formula in any cached doc is wrong. |
| Finance vs MDO Dues definition | S02 Finance panel, S03 MTD cards | 909M vs 700.5M for January. Gap = unidentified receipts. Must be labelled on both panels. |
| Advance monthly arrays (`grp_a`, `cy25`, `fy25`) | `c-adv-3yr` closure, `c-adv-main` closure, end-of-file JS block | Declared at module level and redeclared inside new JS block. Shadow risk. ⚠ |
| Days array | `dues[]`, `ns[]` in 4 entity closures (R04/R05/R06/R07) | 4 identical `days[]` arrays. Duplication. Centralise to single constant. |
| Collector data arrays (`collNames[]`, `collAct[]`, `collTgt[]`) | `c-coll` chart only | Static Mar 2026 snapshot. No refresh mechanism. ⚠ |
| NPV scenario figures (652M, 21M, 31M) | S01 NPV panel, S05 context | Labelled as actuals in some places; should be labelled "projected" consistently. |

### 4.3 — Metric Definition Conflicts

| Metric | Definition A | Definition B | Conflict |
|---|---|---|---|
| "Dues target" | MDO: Dues only (Jan = 700.5M) | Finance: Dues + Advance (Jan = 909M) | Achievement% differs across S02 MDO vs S03 MTD Finance tabs |
| "OD%" | Corrected (v4+): OD ÷ MS Due Till Date | Old (v1–v3): OD ÷ Purchase Price | Old value in any cached document is wrong |
| "Forward pipeline" | 43.5B (S04 hero) | ~40B (narrative) | ~37.8B (S05 penetration denominator) |
| "Active bookings" | 30,044 (active excl. PCC'd) | 34,731 (all qualified ITD incl. completed) | Hero shows 34,731; app adoption uses 30,044 |

---

## APPENDIX — STATIC HARDCODES (Staleness Risk Register)

| Value | Location | Staleness Risk |
|---|---|---|
| OD Today = 1.65B | S02, S04, S08 | Changes daily |
| Collector arrays (24 names, targets, actuals) | `c-coll` | Mar 2026 snapshot; no refresh |
| Daily collections Mar 1–18 | 4 entity closures | Snapshot; 4 duplicate `days[]` arrays |
| NPV figures (652M, 21M, 31M) | S01, S05 | Proposal model; label as projected |
| UAE market data (214,912 tx, 682.5B) | S02 | No source file; no update mechanism |
| Working days/month = 22 | Daily avg calc | Hardcoded; March has ~21 |
| Avg advance lead = 248 days | S01, S05 | Derived from R08 historical; hardcoded |
