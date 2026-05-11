"""
SOBHA COLLECTIONS INTELLIGENCE PLATFORM
constants.py — Structural Constants
Version: v6
Authority: FINAL_ARCHITECTURE.md

Rules (non-negotiable):
  - This file imports NOTHING. Zero dependencies.
  - No business logic. No computation. No I/O.
  - All AED values stored in base units (AED, not millions).
  - Derived constants (OD_TODAY, PIPELINE figures, CY_ADV_MIX_YTD, etc.)
    are NOT here — they belong to data_loader.py via pipeline_config.json.
  - Any value that changes when R-series source files update is DERIVED,
    not structural, and must never appear here.

Dependency rule:
  constants.py  →  imported by: utils.py, data_loader.py, endpoints/*
  constants.py  →  NEVER imports from any of the above
"""


# ════════════════════════════════════════════════════════════════
# SECTION 1 — CALENDAR & WORKING DAY
# ════════════════════════════════════════════════════════════════

# March 2026 calendar. Used for MDO daily average calculation.
# Formula: mdo_daily_avg = monthly_dues_target ÷ WORKING_DAYS_MONTH
# WARNING: v5 used 22. Corrected to 21 in v6. Do not revert.
WORKING_DAYS_MONTH: int = 21

# Snapshot reference month (used for labelling collector data).
# Collector data is a Mar 2026 MTD snapshot — static until refreshed.
SNAPSHOT_LABEL: str = "Snapshot: Mar 2026 MTD"

# Platform data currency label (used in INSIGHT_BLOCK and KPI_STRIP footers).
PLATFORM_VERSION: str = "v8-batch1"


# ════════════════════════════════════════════════════════════════
# SECTION 2 — ENTITY DEFINITIONS
# ════════════════════════════════════════════════════════════════

# Canonical entity list. Order is fixed — controls display order
# in all entity toggles, dropdown filters, and chart legends.
# Batch 1 locked hierarchy:
# Group -> Sobha(Sobha Dubai, Sobha AUH) + UAQ(Siniya, Downtown UAQ).
ENTITY_LIST: list[str] = [
    "Group",
    "Sobha",
    "Sobha Dubai",
    "Sobha AUH",
    "UAQ",
    "Siniya",
    "Downtown UAQ",
]

ENTITY_HIERARCHY: dict[str, dict] = {
    "group": {"display": "Group", "parent": None, "children": ["sobha", "uaq"]},
    "sobha": {"display": "Sobha", "parent": "group", "children": ["sobha_dubai", "sobha_auh"]},
    "sobha_dubai": {"display": "Sobha Dubai", "parent": "sobha", "children": []},
    "sobha_auh": {"display": "Sobha AUH", "parent": "sobha", "children": []},
    "uaq": {"display": "UAQ", "parent": "group", "children": ["siniya", "downtown_uaq"]},
    "siniya": {"display": "Siniya", "parent": "uaq", "children": []},
    "downtown_uaq": {"display": "Downtown UAQ", "parent": "uaq", "children": []},
}

# Entity short codes used in pipeline_config.json column mappings.
ENTITY_CODES: dict[str, str] = {
    "Group": "group",
    "Sobha": "sobha",
    "Sobha Dubai": "sobha_dubai",
    "Sobha AUH": "sobha_auh",
    "UAQ": "uaq",
    "Siniya": "siniya",
    "Downtown UAQ": "downtown_uaq",
    "DT": "downtown_uaq",  # backward-compatible alias only
}

# User-approved general reconciliation tolerance.
RECONCILIATION_TOLERANCE_PCT: float = 0.0005  # 0.05%

# Display colours — consistent across all chart panels.
# Changing here propagates to every chart that references ENTITY_COLOURS.
ENTITY_COLOURS: dict[str, str] = {
    "Group": "#0D2B45",
    "Sobha": "#1A3C5E",
    "Sobha Dubai": "#24537A",
    "Sobha AUH": "#3E6C8F",
    "UAQ": "#2E7D9F",
    "Siniya": "#3F94B5",
    "Downtown UAQ": "#5BA3C9",
    "DT": "#5BA3C9",  # backward-compatible alias only
    "Target": "#E8A030",
    "NS": "#D94F3A",
}


# ════════════════════════════════════════════════════════════════
# SECTION 3 — TARGET VERSIONS
# ════════════════════════════════════════════════════════════════

# Two target systems used in the platform. Always shown with label on-screen.
# See PART 7 of FINAL_ARCHITECTURE.md for full disambiguation rules.
TARGET_VERSIONS: list[str] = ["MDO Dues", "Finance Dues"]

# MDO target definitions (structural — values confirmed in R02 headers).
# Monthly values are DYNAMIC (R02 updates mid-year). FY total is structural.
MDO_DUES_FY_2026_AED: int = 11_500_000_000    # 11,500M — Dues only
MDO_ADV_FY_2026_AED:  int  = 4_000_000_000    # 4,000M  — Advance only

# MDO monthly Dues targets 2026 (AED M → stored as AED).
# Source: R02 (dynamic). These are the confirmed values at time of build.
# If R02 updates, data_loader.py overwrites these at runtime.
# Stored here as a fallback reference only — never used in computation
# if R02 is available.
MDO_MONTHLY_DUES_2026_AED: dict[str, int] = {
    "Jan": 700_500_000,
    "Feb": 712_400_000,
    "Mar": 695_400_000,
    "Apr": 777_800_000,
    "May": 711_000_000,
    "Jun": 816_200_000,
}

# Finance Dues target is D+A combined (not Dues-only like MDO).
# January reference value — static.
FINANCE_DUES_JAN_2026_AED: int = 909_000_000  # 909M

# Finance target label (must be rendered on-screen wherever this value appears).
FINANCE_DUES_LABEL: str = "Finance Dues (D+A combined)"
MDO_DUES_LABEL:     str = "MDO Dues (Dues only)"


# ════════════════════════════════════════════════════════════════
# SECTION 4 — PORTFOLIO UNIT COUNTS
# ════════════════════════════════════════════════════════════════

# Two distinct unit count figures. Always label on-screen — never display
# as a generic "bookings" or "units" number without specifying which.
# See PART 7 — UNITS DISAMBIGUATION in FINAL_ARCHITECTURE.md.

# Use for: app adoption %, coverage calculations, collector ratios.
UNITS_ACTIVE_EXCL_PCC: int = 30_044

# Use for: portfolio count, hero card, ITD totals.
UNITS_ALL_QUALIFIED_ITD: int = 34_731

UNITS_ACTIVE_LABEL:    str = "Active units (excl. PCC)"
UNITS_QUALIFIED_LABEL: str = "Total qualified units (ITD)"


# ════════════════════════════════════════════════════════════════
# SECTION 5 — ADVANCE PROGRAMME CONSTANTS
# ════════════════════════════════════════════════════════════════

# Average lead days between advance payment date and milestone due date.
# Source: R08. Used in S05 advance narrative and S08 strategic context.
AVG_ADVANCE_LEAD_DAYS: int = 248

# NPV rebate parameters — always labelled [PROJECTED], never Actual.
# Current rate (v5 deck), proposed rate, bank equivalent benchmark.
NPV_RATE_CURRENT:  float = 3.5    # % — current rebate NPV rate
NPV_RATE_PROPOSED: float = 4.3    # % — proposed rate (strategy doc)
NPV_RATE_BANK:     float = 4.75   # % — bank equivalent benchmark

# NPV projected figures (AED M → stored as AED).
# Source: R08 + strategy doc NPV model. Label: [PROJECTED] everywhere.
NPV_PROJECTED_ADDITIONAL_ADV_AED:  int = 652_000_000   # 652M [PROJECTED]
NPV_PROJECTED_REBATE_COST_AED:     int =  21_000_000   #  21M [PROJECTED]
NPV_PROJECTED_BANK_EQUIVALENT_AED: int =  31_000_000   #  31M [PROJECTED]
NPV_LABEL: str = "[PROJECTED]"  # Append to every NPV figure on render

# Advance baseline (2025 full-year actual). Used as reference in S01/S03/S05.
ADVANCE_BASELINE_2025_AED: int = 3_260_000_000   # 3,260M


# ════════════════════════════════════════════════════════════════
# SECTION 6 — RISK & TERMINATION THRESHOLDS
# ════════════════════════════════════════════════════════════════

# IC (Involuntary Cancellation) threshold exposure band.
# Units paid ≤10% of purchase price. Source: R38.
# Policy decision (threshold change) is a SEPARATE board business case.
# This data lives in S04 and is referenced (read-only) from S08.
IC_THRESHOLD_UNITS:       int = 251
IC_THRESHOLD_EXPOSURE_AED: int = 907_700_000   # 907.7M

# Skyvue risk band (10–20% paid). Source: R38.
SKYVUE_RISK_UNITS:       int = 535
SKYVUE_RISK_EXPOSURE_AED: int = 1_270_000_000  # 1.27B

# Termination gap — units in termination pipeline not yet in system.
# Source: R34. Advisory reference for S08.
TERMINATION_GAP_UNITS:       int = 412
TERMINATION_GAP_EXPOSURE_AED: int = 134_600_000  # 134.6M


# ════════════════════════════════════════════════════════════════
# SECTION 7 — CHANNEL & COVERAGE BENCHMARKS
# ════════════════════════════════════════════════════════════════

# Payment channel share is COUNT basis only. Never AED value.
# Label: "Transaction Count basis" in all channel chart titles.
CHANNEL_BASIS_LABEL: str = "Transaction Count basis"

# App payment channel benchmarks (COUNT basis, % of D+A transactions).
APP_CHANNEL_PCT_2024: float = 0.1   # 0.1% (2024 full year)
APP_CHANNEL_PCT_2025: float = 6.0   # 6.0% (2025 full year)
APP_CHANNEL_PCT_2026_YTD: float = 25.9  # 25.9% (2026 YTD Mar)

# Coverage benchmarks. Source: R10.
COVERAGE_FE_PCT:     float = 99.7   # Future Events coverage
COVERAGE_OD_PCT:     float = 99.9   # Overdue coverage
COVERAGE_TERM_PCT:   float = 100.0  # Termination coverage
COVERAGE_SINIYA_PCT: float = 86.2   # Siniya coverage (gap = 198 unworked units)
SINIYA_UNWORKED_UNITS: int = 198
SINIYA_UNWORKED_POOL_AED: int = 319_000_000  # 319M pool


# ════════════════════════════════════════════════════════════════
# SECTION 8 — OD AGEING BUCKETS
# ════════════════════════════════════════════════════════════════

# OD ageing snapshot (AED M → stored as AED). Source: R18 (15 Mar 2026).
# These are STRUCTURAL labels only. Values are DERIVED (loaded from R18).
OD_AGEING_BUCKETS: list[str] = [
    "0–30d", "31–60d", "61–90d", "91–120d", "121–180d", "180d+"
]

# Reference values (for fallback / smoke test only — data_loader owns live values).
OD_AGEING_REF_AED: dict[str, int] = {
    "0–30d":   830_000_000,
    "31–60d":  445_000_000,
    "61–90d":  166_000_000,
    "91–120d":  79_000_000,
    "121–180d": 47_000_000,
    "180d+":   225_000_000,
}

# Top project OD reference. Source: R18.
TOP_PROJECT_OD_NAME: str = "Riverside Crescent"
TOP_PROJECT_OD_AED:  int = 237_400_000  # 237.4M


# ════════════════════════════════════════════════════════════════
# SECTION 9 — COLLECTOR OPERATIONS
# ════════════════════════════════════════════════════════════════

# Total collector headcount (R30).
COLLECTOR_COUNT: int = 24

# Collector chart sort rule — enforced everywhere c-coll appears.
# v5 bug: chart was unsorted. v6 fix: always DESC by achievement_pct.
COLLECTOR_SORT_BY:    str = "achievement_pct"
COLLECTOR_SORT_ORDER: str = "desc"   # Always descending

# PR quality snapshot (Dec 2025, n=1,818 PRs). Source: R31.
PR_QUALITY_N: int = 1_818
PR_APPROVED_PCT:    float = 51.0
PR_DOC_GAPS_PCT:    float = 27.0
PR_MANUAL_ERRORS_PCT: float = 23.0

# PR-SOA TAT milestones (0–2 day turnaround %). Source: R20.
PCC_TAT_PRE_AED:  str = "20 days"   # Pre-improvement
PCC_TAT_POST_AED: str = "3–5 days"  # Post-improvement
PCC_TAT_TARGET:   str = "2 days"    # Target

PR_SOA_TAT_0_2D_2024: float = 25.0  # % of PRs resolved in 0–2d
PR_SOA_TAT_0_2D_2025: float = 35.0
PR_SOA_TAT_0_2D_2026_YTD: float = 51.0

# Visibility gap (AED M → AED) from PR-SOA mismatch. Source: R20 derived.
VISIBILITY_GAP_AED: int = 275_000_000  # ~250–300M midpoint


# ════════════════════════════════════════════════════════════════
# SECTION 10 — HISTORICAL PORTFOLIO MILESTONES
# ════════════════════════════════════════════════════════════════

# ITD (Inception-to-Date) portfolio totals. Source: R01.
# These are structural reference figures used in S01 Strategic Narrative.
GROUP_SALE_VALUE_ITD_AED:  int = 86_000_000_000  # 86.0B
GROUP_COLLECTED_ITD_AED:   int = 43_300_000_000  # 43.3B
GROUP_COLLECTED_ITD_PCT:   float = 50.3           # %

# D+A CAGR 2021–2025.
DA_CAGR_2021_2025: float = 97.0  # % (four-year CAGR)

# LP (Late Payment) growth multiplier 2021–2025.
LP_GROWTH_MULTIPLIER: float = 22.0  # 22× growth

# Sobha units sold ITD by year. Source: R01.
SOBHA_UNITS_SOLD_ITD: dict[str, int] = {
    "2021": 1_879,
    "2022": 5_009,
    "2023": 5_211,
    "2024": 6_837,
    "2025": 8_468,
    "2026_YTD": 957,
}

# 2025 full-year collections summary (AED M → AED). Source: R01/R35.
COLLECTIONS_2025: dict[str, int] = {
    "dues":    9_706_000_000,
    "advance": 3_260_000_000,
    "ns":      3_853_000_000,
    "total":  16_820_000_000,
}

# Entity 2025 splits. Source: R01.
COLLECTIONS_2025_ENTITY: dict[str, dict[str, int]] = {
    "Sobha": {
        "dues":    8_428_000_000,
        "advance": 2_862_000_000,
        "ns":      2_774_000_000,
        "total":  14_064_000_000,
    },
    "Siniya": {
        "total": 2_506_000_000,
    },
    "DT": {
        "total": 250_000_000,
    },
}

# 2026 YTD Q1 actuals (partial). Source: R04/R02.
COLLECTIONS_2026_Q1_YTD: dict[str, int] = {
    "da":  2_619_000_000,  # D+A combined
    "ns":    473_000_000,
}

# ACD (Anticipated Collections Denominator) — Dec 2026 projection. Source: R37.
ACD_DEC_2026_AED: int = 5_620_000_000  # 5.62B


# ════════════════════════════════════════════════════════════════
# SECTION 11 — PIPELINE LABELS (disambiguation — no values here)
# ════════════════════════════════════════════════════════════════

# Pipeline constants MUST be derived in data_loader.py from R36.
# These labels are stored here so every submodule uses consistent wording.
# Rule: never display a pipeline figure without its label.
# See FINAL_ARCHITECTURE Part 1.2 — Pipeline Disambiguation Rule.

PIPELINE_GROSS_LABEL:        str = "Total Forward Pipeline (R36)"
PIPELINE_FORWARD_BOOK_LABEL: str = "~Opening 2025 Book (narrative)"
PIPELINE_ADV_DENOM_LABEL:    str = "2026 Advance Penetration Denominator (S05/S08 only)"

# Pipeline ADV_DENOM derivation note (for data_loader.py reference).
# PIPELINE_ADV_DENOM = PIPELINE_GROSS − 5,700M (prior advances already paid)
PIPELINE_ADV_DENOM_OFFSET_AED: int = 5_700_000_000  # 5.7B offset


# ════════════════════════════════════════════════════════════════
# SECTION 12 — NATIONALITY OD REFERENCE (S01 only)
# ════════════════════════════════════════════════════════════════

# Nationality OD analysis LIVES IN S01. Not in S04. (Boundary rule.)
# Source: R16. OD% = OD ÷ MS Due ITD (not ÷ purchase_price).
NATIONALITY_OD_REF: dict[str, dict] = {
    "India":  {"od_aed": 272_000_000, "od_pct": 4.33},
    "Iran":   {"od_pct": 9.14},
    "Russia": {"od_pct": 2.36},
    "China":  {"od_pct": 1.73},
}

# CIV total OD% (portfolio-wide). Source: R16/R18.
CIV_TOTAL_OD_PCT: float = 3.88   # 1,650M ÷ 42,505M MS Due ITD


# ════════════════════════════════════════════════════════════════
# SECTION 13 — FORMULA GOVERNANCE STRINGS
# ════════════════════════════════════════════════════════════════

# These strings are used by DEFINITION_BLOCK submodules across all sections.
# Stored here so formula wording is consistent platform-wide.

FORMULA_OD_PCT: str = (
    "OD% = od_aed ÷ ms_due_itd_aed × 100\n"
    "NEVER divide by purchase_price_aed — deprecated in v5, removed in v6."
)

FORMULA_EFFICIENCY_30D: str = (
    "30-Day Efficiency = Dues Collected (AED) ÷ Booksize BOM (AED) × 100\n"
    "Platform average: 34.8%. Prior figure of 18% was incorrect and deprecated."
)

FORMULA_PENETRATION: str = (
    "Advance Penetration = Annual Advance (AED) ÷ PIPELINE_ADV_DENOM (AED) × 100\n"
    "PIPELINE_ADV_DENOM = 37.8B (43.5B gross pipeline − 5.7B prior advances).\n"
    "Used in S05 and S08 only."
)

FORMULA_ACHIEVEMENT_PCT: str = (
    "Achievement% = Actual (AED) ÷ Target (AED) × 100\n"
    "Always label which target: MDO Dues OR Finance Dues."
)

FORMULA_CHANNEL_SHARE: str = (
    "Channel Share = App Transaction Count ÷ Total D+A Transaction Count × 100\n"
    "COUNT basis only. Never AED value."
)

FORMULA_COLLECTOR_ACHIEVEMENT: str = (
    "Collector Achievement% = Collector Actual (AED) ÷ Collector Target (AED) × 100\n"
    "Chart always sorted DESCENDING by achievement_pct."
)

FORMULA_MDO_DAILY_AVG: str = (
    "MDO Daily Average = Monthly Dues Target (AED) ÷ WORKING_DAYS_MONTH\n"
    f"WORKING_DAYS_MONTH = {WORKING_DAYS_MONTH} (March 2026). Not 22."
)

FORMULA_DA_CAGR: str = (
    "D+A CAGR 2021–2025 = (12,966M ÷ 867M)^(1/4) − 1 = 97%"
)


# ════════════════════════════════════════════════════════════════
# SECTION 14 — DEPRECATED VALUES REGISTER
# ════════════════════════════════════════════════════════════════

# This section documents v5 values that were incorrect and are now removed.
# Retained for audit trail. Never reference these in any computation.
# Any attempt to use these values will fail CI lint check (TODO: add lint rule).

_DEPRECATED = {
    "WORKING_DAYS_MONTH_V5":     22,       # Was 22. Corrected to 21.
    "OD_PCT_DENOMINATOR_V5":     "purchase_price",  # Wrong. Use ms_due_itd.
    "JAN_2025_CY_ADV_PCT_V5":    30.0,    # Was 30% (FY%). CY% is 70.1%.
    "EFFICIENCY_30D_V5":         18.0,    # Was 18%. Correct avg is 34.8%.
    "ENTITY_TOGGLE_COUNT_V5":    10,      # 10 per-section instances. Now 1 (etog).
    "DAYS_ARRAY_DUPLICATES_V5":  4,       # 4 duplicate days[] arrays. Now 1.
    "C_MDO2_PURPOSE_V5":         "unknown",  # Removed. Purpose unconfirmed.
    "OD_TODAY_HARDCODED_V5":     3,       # 3 hardcoded instances. Now 1 constant.
    "ADV_3YR_CHART_IN_S01_V5":   True,    # c-adv-3yr duplicated S05. Removed from S01.
    "NPV_LABEL_ACTUAL_V5":       "Actual", # Was labelled Actual. Now [PROJECTED].
    "INLINE_ONCLICK_FINANCE_V5": True,    # S02 finance toggle was inline onclick.
    "ORG_CHART_FACTUAL_V5":      False,   # Org chart was wrong. Corrected in v6.
}
