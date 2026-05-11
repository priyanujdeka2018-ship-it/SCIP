"""
SOBHA COLLECTIONS INTELLIGENCE PLATFORM
utils.py — Pure Formatting & Helper Functions
Version: v6
Authority: FINAL_ARCHITECTURE.md

Rules (non-negotiable):
  - Imports constants only. Zero other dependencies.
  - No business logic. No computation of business metrics.
  - No I/O. No API calls. No database reads.
  - Every function is pure: same inputs → same output, no side effects.
  - No function here replicates any formula from CANONICAL BUSINESS LOGIC.
    (Those formulas live in data_loader.py / endpoint functions only.)

Dependency rule:
  utils.py  →  imports: constants only
  utils.py  →  NEVER imports: data_loader, endpoints, any third-party lib
  utils.py  →  imported by: data_loader.py, all endpoint files
"""

from __future__ import annotations
import math
from typing import Optional, Union
import constants as C


# ════════════════════════════════════════════════════════════════
# SECTION 1 — AED CURRENCY FORMATTERS
# ════════════════════════════════════════════════════════════════

def fmt_aed_millions(value_aed: Union[int, float], decimals: int = 1) -> str:
    """
    Format a raw AED value into a compact millions string.

    Args:
        value_aed:  Raw value in AED (e.g. 1_472_700_000)
        decimals:   Decimal places (default 1)

    Returns:
        str: e.g. "1,472.7M"

    Usage:
        KPI_STRIP cards, INSIGHT_BLOCK callouts, chart axis labels.
    """
    if value_aed is None or (isinstance(value_aed, float) and math.isnan(value_aed)):
        return "—"
    m = value_aed / 1_000_000
    return f"{m:,.{decimals}f}M"


def fmt_aed_billions(value_aed: Union[int, float], decimals: int = 1) -> str:
    """
    Format a raw AED value into a compact billions string.

    Args:
        value_aed:  Raw value in AED (e.g. 43_500_000_000)
        decimals:   Decimal places (default 1)

    Returns:
        str: e.g. "43.5B"

    Usage:
        Portfolio totals, pipeline figures, Group-level KPIs.
    """
    if value_aed is None or (isinstance(value_aed, float) and math.isnan(value_aed)):
        return "—"
    b = value_aed / 1_000_000_000
    return f"{b:,.{decimals}f}B"


def fmt_aed_auto(value_aed: Union[int, float], decimals: int = 1) -> str:
    """
    Auto-select B or M based on magnitude. Threshold: ≥1B → billions.

    Args:
        value_aed:  Raw value in AED
        decimals:   Decimal places (default 1)

    Returns:
        str: e.g. "1.5B" or "472.3M"

    Usage:
        General-purpose KPI cards where scale is not pre-determined.
        Do NOT use for pipeline figures — those must use explicit
        fmt_aed_billions() to ensure correct label pairing.
    """
    if value_aed is None or (isinstance(value_aed, float) and math.isnan(value_aed)):
        return "—"
    if abs(value_aed) >= 1_000_000_000:
        return fmt_aed_billions(value_aed, decimals)
    return fmt_aed_millions(value_aed, decimals)


def fmt_millions_raw(value_m: Union[int, float], decimals: int = 1) -> str:
    """
    Format a value that is already expressed in AED millions.
    Use when source data column is already in M (e.g. R08 advance_aed_m).

    Returns:
        str: e.g. "3,260.0M"
    """
    if value_m is None or (isinstance(value_m, float) and math.isnan(value_m)):
        return "—"
    return f"{value_m:,.{decimals}f}M"


# ════════════════════════════════════════════════════════════════
# SECTION 2 — PERCENTAGE FORMATTERS
# ════════════════════════════════════════════════════════════════

def fmt_pct(value: Union[int, float], decimals: int = 1, show_sign: bool = False) -> str:
    """
    Format a percentage value (0–100 scale).

    Args:
        value:      Percentage already on 0–100 scale (e.g. 97.0)
        decimals:   Decimal places (default 1)
        show_sign:  If True, prefix positive values with "+" (for delta display)

    Returns:
        str: e.g. "97.0%" or "+12.3%"

    Usage:
        Achievement%, OD%, coverage%, penetration%.
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    sign = "+" if show_sign and value > 0 else ""
    return f"{sign}{value:.{decimals}f}%"


def fmt_pct_delta(new: Union[int, float], old: Union[int, float], decimals: int = 1) -> str:
    """
    Format a percentage-point delta between two period values.
    Always shows sign (+ or -).

    Returns:
        str: e.g. "+3.2pp" or "-1.1pp"
    """
    if any(v is None or (isinstance(v, float) and math.isnan(v)) for v in [new, old]):
        return "—"
    delta = new - old
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.{decimals}f}pp"


def fmt_achievement(actual_aed: Union[int, float], target_aed: Union[int, float]) -> str:
    """
    Format collector or entity achievement percentage.
    Returns "—" if target is zero to avoid division errors.

    Formula:  achievement% = actual ÷ target × 100
    Matches:  FORMULA_ACHIEVEMENT_PCT in constants.py

    Returns:
        str: e.g. "112.0%"
    """
    if not target_aed or target_aed == 0:
        return "—"
    ach = (actual_aed / target_aed) * 100
    return fmt_pct(ach)


# ════════════════════════════════════════════════════════════════
# SECTION 3 — DATE & PERIOD FORMATTERS
# ════════════════════════════════════════════════════════════════

def fmt_month_label(month_str: str) -> str:
    """
    Normalise month string to 3-char title-case.
    Accepts: "january", "Jan", "JAN", "01", "1"

    Returns:
        str: e.g. "Jan"
    """
    _month_map = {
        "01": "Jan", "1": "Jan",  "jan": "Jan", "january": "Jan",
        "02": "Feb", "2": "Feb",  "feb": "Feb", "february": "Feb",
        "03": "Mar", "3": "Mar",  "mar": "Mar", "march": "Mar",
        "04": "Apr", "4": "Apr",  "apr": "Apr", "april": "Apr",
        "05": "May", "5": "May",  "may": "May",
        "06": "Jun", "6": "Jun",  "jun": "Jun", "june": "Jun",
        "07": "Jul", "7": "Jul",  "jul": "Jul", "july": "Jul",
        "08": "Aug", "8": "Aug",  "aug": "Aug", "august": "Aug",
        "09": "Sep", "9": "Sep",  "sep": "Sep", "september": "Sep",
        "10": "Oct",              "oct": "Oct", "october": "Oct",
        "11": "Nov",              "nov": "Nov", "november": "Nov",
        "12": "Dec",              "dec": "Dec", "december": "Dec",
    }
    return _month_map.get(str(month_str).strip().lower(), str(month_str))


def fmt_period_label(year: Union[int, str], month: Union[int, str, None] = None) -> str:
    """
    Construct a human-readable period label.

    Args:
        year:   e.g. 2025 or "2025"
        month:  Optional. int 1–12, or string like "Jan", "january", "01"

    Returns:
        str: "2025" or "Jan 2025"
    """
    if month is None:
        return str(year)
    return f"{fmt_month_label(str(month))} {year}"


def fmt_snapshot_label(data_date: Optional[str] = None) -> str:
    """
    Produce a data currency label for INSIGHT_BLOCK and KPI_STRIP footers.
    If no date provided, falls back to SNAPSHOT_LABEL from constants.

    Args:
        data_date:  ISO date string "YYYY-MM-DD" or None

    Returns:
        str: e.g. "Data as of 15 Mar 2026" or constants.SNAPSHOT_LABEL
    """
    if not data_date:
        return C.SNAPSHOT_LABEL
    try:
        parts = data_date.strip().split("-")
        y, m, d = parts[0], int(parts[1]), int(parts[2])
        month = fmt_month_label(parts[1])
        return f"Data as of {d} {month} {y}"
    except Exception:
        return C.SNAPSHOT_LABEL


# ════════════════════════════════════════════════════════════════
# SECTION 4 — NUMBER & COUNT FORMATTERS
# ════════════════════════════════════════════════════════════════

def fmt_count(value: Union[int, float], suffix: str = "") -> str:
    """
    Format an integer count with comma thousands separator.

    Returns:
        str: e.g. "30,044" or "30,044 units"
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    s = f"{int(value):,}"
    return f"{s} {suffix}".strip() if suffix else s


def fmt_days(value: Union[int, float]) -> str:
    """
    Format a day count (e.g. advance lead days).

    Returns:
        str: e.g. "248 days"
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    return f"{int(value)} days"


def fmt_multiple(value: Union[int, float], decimals: int = 0) -> str:
    """
    Format a growth multiple (e.g. LP 22×, collector capacity 15×).

    Returns:
        str: e.g. "22×"
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    return f"{value:.{decimals}f}×"


def fmt_cagr(value_pct: Union[int, float]) -> str:
    """
    Format a CAGR value with % and standard label.

    Returns:
        str: e.g. "97% CAGR"
    """
    if value_pct is None:
        return "—"
    return f"{value_pct:.0f}% CAGR"


# ════════════════════════════════════════════════════════════════
# SECTION 5 — PIPELINE LABEL HELPERS
# ════════════════════════════════════════════════════════════════

def pipeline_display(value_aed: Union[int, float], label_key: str) -> dict:
    """
    Build a display-ready pipeline figure dict with mandatory inline label.
    Architecture rule: never display a pipeline figure without its label.

    Args:
        value_aed:   Raw AED value from data_loader computed dict
        label_key:   One of "gross" | "forward_book" | "adv_denom"

    Returns:
        dict: { "value": "43.5B", "label": "Total Forward Pipeline (R36)" }

    Usage:
        KPI_STRIP hero cards in S02, S04, S05, S08.
    """
    label_map = {
        "gross":        C.PIPELINE_GROSS_LABEL,
        "forward_book": C.PIPELINE_FORWARD_BOOK_LABEL,
        "adv_denom":    C.PIPELINE_ADV_DENOM_LABEL,
    }
    label = label_map.get(label_key, f"Pipeline ({label_key})")
    return {
        "value": fmt_aed_billions(value_aed),
        "label": label,
    }


def npv_display(value_aed: Union[int, float], decimals: int = 0) -> str:
    """
    Format an NPV figure and append the [PROJECTED] label.
    Architecture rule: NPV figures always carry [PROJECTED] tag.

    Returns:
        str: e.g. "652M [PROJECTED]"
    """
    return f"{fmt_aed_millions(value_aed, decimals)} {C.NPV_LABEL}"


# ════════════════════════════════════════════════════════════════
# SECTION 6 — TARGET LABEL HELPERS
# ════════════════════════════════════════════════════════════════

def target_label(version: str) -> str:
    """
    Return the canonical on-screen label for a target version.
    Architecture rule: target version must always be labelled on-screen.

    Args:
        version:  "MDO Dues" | "Finance Dues"

    Returns:
        str: full label string from constants
    """
    if version == "MDO Dues":
        return C.MDO_DUES_LABEL
    if version == "Finance Dues":
        return C.FINANCE_DUES_LABEL
    return version


def units_label(unit_type: str) -> str:
    """
    Return the canonical on-screen label for a unit count type.
    Architecture rule: unit count type must always be labelled on-screen.

    Args:
        unit_type:  "active" | "qualified"

    Returns:
        str: label string from constants
    """
    if unit_type == "active":
        return C.UNITS_ACTIVE_LABEL
    if unit_type == "qualified":
        return C.UNITS_QUALIFIED_LABEL
    return unit_type


# ════════════════════════════════════════════════════════════════
# SECTION 7 — ENTITY HELPERS
# ════════════════════════════════════════════════════════════════

def entity_colour(entity: str) -> str:
    """
    Return the hex colour for a given entity. Falls back to grey.

    Args:
        entity:  "Sobha" | "Siniya" | "DT" | "Group" | "Target" | "NS"

    Returns:
        str: hex colour string e.g. "#1A3C5E"
    """
    return C.ENTITY_COLOURS.get(entity, "#888888")


def entity_code(entity: str) -> str:
    """
    Return the lowercase entity code used in pipeline_config.json.

    Returns:
        str: e.g. "sobha"
    """
    return C.ENTITY_CODES.get(entity, entity.lower())


def is_valid_entity(entity: str) -> bool:
    """
    Validate that an entity string is in the canonical entity list.

    Returns:
        bool
    """
    return entity in C.ENTITY_LIST


# ════════════════════════════════════════════════════════════════
# SECTION 8 — GRACEFUL DEGRADATION HELPERS
# ════════════════════════════════════════════════════════════════

def safe_divide(numerator: Union[int, float], denominator: Union[int, float],
                fallback: float = 0.0) -> float:
    """
    Safe division that returns fallback on zero denominator.
    Use wherever a ratio could encounter missing or zero data.

    Returns:
        float: result or fallback
    """
    if not denominator or denominator == 0:
        return fallback
    return numerator / denominator


def data_pending_label(section_id: str) -> dict:
    """
    Return a standard graceful-degradation payload when a source
    file is missing. Shown instead of an error to the end user.
    Architecture rule: missing R-series file → graceful degradation, not crash.

    Args:
        section_id:  e.g. "S04", "S01"

    Returns:
        dict with status and user-facing message
    """
    return {
        "status":  "data_pending",
        "message": f"Data pending refresh — {section_id} will update on next pipeline load.",
        "value":   None,
    }


def coerce_aed(value: Union[int, float, str, None],
               unit: str = "aed") -> Optional[float]:
    """
    Coerce a value to AED base units from a declared unit.
    Used by data_loader when source columns may be in M or B.

    Args:
        value:  Raw value
        unit:   "aed" | "m" (millions) | "b" (billions)

    Returns:
        float in AED or None if coercion fails
    """
    if value is None:
        return None
    try:
        v = float(value)
    except (ValueError, TypeError):
        return None
    multipliers = {"aed": 1, "m": 1_000_000, "b": 1_000_000_000}
    return v * multipliers.get(unit.lower(), 1)


# ════════════════════════════════════════════════════════════════
# SECTION 9 — CHART CONVENTION HELPERS
# ════════════════════════════════════════════════════════════════

def channel_chart_title(base_title: str) -> str:
    """
    Append the mandatory channel basis note to any payment channel
    chart title. Architecture rule: channel charts must carry basis label.

    Args:
        base_title:  e.g. "Payment Channel Mix 2026 YTD"

    Returns:
        str: "Payment Channel Mix 2026 YTD — Transaction Count basis"
    """
    return f"{base_title} — {C.CHANNEL_BASIS_LABEL}"


def collector_sort_config() -> dict:
    """
    Return the canonical collector chart sort configuration.
    Architecture rule: collector chart always sorted DESC by achievement_pct.

    Returns:
        dict: { "by": "achievement_pct", "order": "desc" }
    """
    return {
        "by":    C.COLLECTOR_SORT_BY,
        "order": C.COLLECTOR_SORT_ORDER,
    }


def mdo_daily_avg(monthly_target_aed: Union[int, float]) -> float:
    """
    Compute the MDO daily average target.
    Formula: mdo_daily_avg = monthly_target ÷ WORKING_DAYS_MONTH

    Architecture rule: always use WORKING_DAYS_MONTH (21), never hardcode 22.

    Args:
        monthly_target_aed:  Monthly Dues target in AED

    Returns:
        float: daily average in AED
    """
    return safe_divide(monthly_target_aed, C.WORKING_DAYS_MONTH)


# ════════════════════════════════════════════════════════════════
# SECTION 10 — JSON / API RESPONSE HELPERS
# ════════════════════════════════════════════════════════════════

def kpi_card(label: str, value: str,
             sub: Optional[str] = None,
             delta: Optional[str] = None,
             flag: Optional[str] = None,
             data_date: Optional[str] = None) -> dict:
    """
    Build a standardised KPI card dict for frontend KPI_STRIP rendering.

    Args:
        label:      Display name e.g. "Group OD Today"
        value:      Formatted value string e.g. "1,650.1M"
        sub:        Optional sub-label e.g. "as of 15 Mar 2026"
        delta:      Optional delta string e.g. "+3.2pp vs last month"
        flag:       Optional flag colour: "green" | "amber" | "red" | None
        data_date:  Optional ISO date string for auto sub-label

    Returns:
        dict suitable for JSON serialisation and frontend rendering
    """
    card: dict = {
        "label": label,
        "value": value,
    }
    if sub:
        card["sub"] = sub
    elif data_date:
        card["sub"] = fmt_snapshot_label(data_date)
    if delta:
        card["delta"] = delta
    if flag:
        card["flag"] = flag
    return card


def section_response(section_id: str, submodule_id: str,
                     data: dict, mode: str = "full") -> dict:
    """
    Wrap a submodule data payload in the standard section response envelope.
    All endpoints return this structure — consistent for frontend parsing.

    Args:
        section_id:    e.g. "S04"
        submodule_id:  e.g. "S04_SM1"
        data:          The submodule payload dict
        mode:          "full" | "summary" | "board"

    Returns:
        dict: standard response envelope
    """
    return {
        "section":   section_id,
        "submodule": submodule_id,
        "mode":      mode,
        "data":      data,
        "platform":  C.PLATFORM_VERSION,
    }
