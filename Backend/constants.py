"""
SOBHA COLLECTIONS INTELLIGENCE PLATFORM
constants.py — Structural Constants
Version: v6
Authority: FINAL_ARCHITECTURE.md

Rules (non-negotiable):
  - This file imports NOTHING. Zero dependencies.
  - No business logic. No computation. No I/O.
  - All AED values stored in base units (AED, not millions).
"""

# ════════════════════════════════════════════════════════════════
# SECTION 1 — CALENDAR & WORKING DAY
# ════════════════════════════════════════════════════════════════
WORKING_DAYS_MONTH: int = 21
SNAPSHOT_LABEL: str = "Snapshot: Mar 2026 MTD"
PLATFORM_VERSION: str = "v6"

# ════════════════════════════════════════════════════════════════
# SECTION 2 — ENTITY DEFINITIONS
# ════════════════════════════════════════════════════════════════
ENTITY_LIST: list[str] = ["Group", "Sobha", "Siniya", "DT"]
ENTITY_CODES: dict[str, str] = {"Group": "group", "Sobha": "sobha", "Siniya": "siniya", "DT": "dt"}
ENTITY_COLOURS: dict[str, str] = {
    "Sobha":  "#1A3C5E",
    "Siniya": "#2E7D9F",
    "DT":     "#5BA3C9",
    "Group":  "#0D2B45",
    "Target": "#E8A030",
    "NS":     "#D94F3A",
}

# ════════════════════════════════════════════════════════════════
# SECTION 3 — TARGET VERSIONS
# ════════════════════════════════════════════════════════════════
TARGET_VERSIONS: list[str] = ["MDO Dues", "Finance Dues"]
MDO_DUES_FY_2026_AED: int = 11_500_000_000
MDO_ADV_FY_2026_AED:  int  = 4_000_000_000
MDO_MONTHLY_DUES_2026_AED: dict[str, int] = {
    "Jan": 700_500_000, "Feb": 712_400_000, "Mar": 695_400_000,
    "Apr": 777_800_000, "May": 711_000_000, "Jun": 816_200_000,
}
FINANCE_DUES_JAN_2026_AED: int = 909_000_000
FINANCE_DUES_LABEL: str = "Finance Dues (D+A combined)"
MDO_DUES_LABEL:     str = "MDO Dues (Dues only)"

# ════════════════════════════════════════════════════════════════
# SECTION 4 — PORTFOLIO UNIT COUNTS
# ════════════════════════════════════════════════════════════════
UNITS_ACTIVE_EXCL_PCC: int = 30_044
UNITS_ALL_QUALIFIED_ITD: int = 34_731
UNITS_ACTIVE_LABEL:    str = "Active units (excl. PCC)"
UNITS_QUALIFIED_LABEL: str = "Total qualified units (ITD)"

# ════════════════════════════════════════════════════════════════
# SECTION 5 — ADVANCE PROGRAMME CONSTANTS
# ════════════════════════════════════════════════════════════════
AVG_ADVANCE_LEAD_DAYS: int = 248
NPV_RATE_CURRENT:  float = 3.5
NPV_RATE_PROPOSED: float = 4.3
NPV_RATE_BANK:     float = 4.75
NPV_PROJECTED_ADDITIONAL_ADV_AED:  int = 652_000_000
NPV_PROJECTED_REBATE_COST_AED:     int =  21_000_000
NPV_PROJECTED_BANK_EQUIVALENT_AED: int =  31_000_000
NPV_LABEL: str = "[PROJECTED]"
ADVANCE_BASELINE_2025_AED: int = 3_260_000_000

# ════════════════════════════════════════════════════════════════
# SECTION 6 — RISK & TERMINATION THRESHOLDS
# ════════════════════════════════════════════════════════════════
IC_THRESHOLD_UNITS:       int = 251
IC_THRESHOLD_EXPOSURE_AED: int = 907_700_000
SKYVUE_RISK_UNITS:       int = 535
SKYVUE_RISK_EXPOSURE_AED: int = 1_270_000_000
TERMINATION_GAP_UNITS:       int = 412
TERMINATION_GAP_EXPOSURE_AED: int = 134_600_000

# ════════════════════════════════════════════════════════════════
# SECTION 7 — CHANNEL & COVERAGE BENCHMARKS
# ════════════════════════════════════════════════════════════════
CHANNEL_BASIS_LABEL: str = "Transaction Count basis"
APP_CHANNEL_PCT_2024: float = 0.1
APP_CHANNEL_PCT_2025: float = 6.0
APP_CHANNEL_PCT_2026_YTD: float = 25.9
COVERAGE_FE_PCT:     float = 99.7
COVERAGE_OD_PCT:     float = 99.9
COVERAGE_TERM_PCT:   float = 100.0
COVERAGE_SINIYA_PCT: float = 86.2
SINIYA_UNWORKED_UNITS: int = 198
SINIYA_UNWORKED_POOL_AED: int = 319_000_000

# ════════════════════════════════════════════════════════════════
# SECTION 8 — OD AGEING BUCKETS
# ════════════════════════════════════════════════════════════════
OD_AGEING_BUCKETS: list[str] = ["0–30d", "31–60d", "61–90d", "91–120d", "121–180d", "180d+"]
OD_AGEING_REF_AED: dict[str, int] = {
    "0–30d":   830_000_000,
    "31–60d":  445_000_000,
    "61–90d":  166_000_000,
    "91–120d":  79_000_000,
    "121–180d": 47_000_000,
    "180d+":   225_000_000,
}
TOP_PROJECT_OD_NAME: str = "Riverside Crescent"
TOP_PROJECT_OD_AED:  int = 237_400_000

# ════════════════════════════════════════════════════════════════
# SECTION 9 — COLLECTOR OPERATIONS
# ════════════════════════════════════════════════════════════════
COLLECTOR_COUNT: int = 24
COLLECTOR_SORT_BY:    str = "achievement_pct"
COLLECTOR_SORT_ORDER: str = "desc"
PR_QUALITY_N: int = 1_818
PR_APPROVED_PCT:    float = 51.0
PR_DOC_GAPS_PCT:    float = 27.0
PR_MANUAL_ERRORS_PCT: float = 23.0
PCC_TAT_PRE_AED:  str = "20 days"
PCC_TAT_POST_AED: str = "3–5 days"
PCC_TAT_TARGET:   str = "2 days"
PR_SOA_TAT_0_2D_2024: float = 25.0
PR_SOA_TAT_0_2D_2025: float = 35.0
PR_SOA_TAT_0_2D_2026_YTD: float = 51.0
VISIBILITY_GAP_AED: int = 275_000_000

# ════════════════════════════════════════════════════════════════
# SECTION 10 — HISTORICAL PORTFOLIO MILESTONES
# ════════════════════════════════════════════════════════════════
GROUP_SALE_VALUE_ITD_AED:  int = 86_000_000_000
GROUP_COLLECTED_ITD_AED:   int = 43_300_000_000
GROUP_COLLECTED_ITD_PCT:   float = 50.3
DA_CAGR_2021_2025: float = 97.0
LP_GROWTH_MULTIPLIER: float = 22.0
SOBHA_UNITS_SOLD_ITD: dict[str, int] = {
    "2021": 1_879, "2022": 5_009, "2023": 5_211,
    "2024": 6_837, "2025": 8_468, "2026_YTD": 957,
}
COLLECTIONS_2025: dict[str, int] = {
    "dues": 9_706_000_000, "advance": 3_260_000_000,
    "ns": 3_853_000_000, "total": 16_820_000_000,
}
COLLECTIONS_2025_ENTITY: dict[str, dict[str, int]] = {
    "Sobha":  {"dues": 8_428_000_000, "advance": 2_862_000_000, "ns": 2_774_000_000, "total": 14_064_000_000},
    "Siniya": {"total": 2_506_000_000},
    "DT":     {"total": 250_000_000},
}
COLLECTIONS_2026_Q1_YTD: dict[str, int] = {"da": 2_619_000_000, "ns": 473_000_000}
ACD_DEC_2026_AED: int = 5_620_000_000

# ════════════════════════════════════════════════════════════════
# SECTION 11 — PIPELINE LABELS
# ════════════════════════════════════════════════════════════════
PIPELINE_GROSS_LABEL:        str = "Total Forward Pipeline (R36)"
PIPELINE_FORWARD_BOOK_LABEL: str = "~Opening 2025 Book (narrative)"
PIPELINE_ADV_DENOM_LABEL:    str = "2026 Advance Penetration Denominator (S05/S08 only)"
PIPELINE_ADV_DENOM_OFFSET_AED: int = 5_700_000_000

# ════════════════════════════════════════════════════════════════
# SECTION 12 — NATIONALITY OD REFERENCE
# ════════════════════════════════════════════════════════════════
NATIONALITY_OD_REF: dict[str, dict] = {
    "India":  {"od_aed": 272_000_000, "od_pct": 4.33},
    "Iran":   {"od_pct": 9.14},
    "Russia": {"od_pct": 2.36},
    "China":  {"od_pct": 1.73},
}
CIV_TOTAL_OD_PCT: float = 3.88

# ════════════════════════════════════════════════════════════════
# SECTION 13 — FORMULA GOVERNANCE STRINGS
# ════════════════════════════════════════════════════════════════
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
FORMULA_DA_CAGR: str = "D+A CAGR 2021–2025 = (12,966M ÷ 867M)^(1/4) − 1 = 97%"

# ════════════════════════════════════════════════════════════════
# SECTION 14 — DEPRECATED VALUES REGISTER
# ════════════════════════════════════════════════════════════════
_DEPRECATED = {
    "WORKING_DAYS_MONTH_V5": 22,
    "OD_PCT_DENOMINATOR_V5": "purchase_price",
    "JAN_2025_CY_ADV_PCT_V5": 30.0,
    "EFFICIENCY_30D_V5": 18.0,
    "ENTITY_TOGGLE_COUNT_V5": 10,
    "DAYS_ARRAY_DUPLICATES_V5": 4,
    "C_MDO2_PURPOSE_V5": "unknown",
    "OD_TODAY_HARDCODED_V5": 3,
    "ADV_3YR_CHART_IN_S01_V5": True,
    "NPV_LABEL_ACTUAL_V5": "Actual",
    "INLINE_ONCLICK_FINANCE_V5": True,
    "ORG_CHART_FACTUAL_V5": False,
}
