"""
SOBHA COLLECTIONS INTELLIGENCE PLATFORM
utils.py — Pure Formatting & Helper Functions
Version: v6
Authority: FINAL_ARCHITECTURE.md
"""

from __future__ import annotations
import math
from typing import Optional, Union
import constants as C


def fmt_aed_millions(value_aed: Union[int, float], decimals: int = 1) -> str:
    if value_aed is None or (isinstance(value_aed, float) and math.isnan(value_aed)):
        return "—"
    m = value_aed / 1_000_000
    return f"{m:,.{decimals}f}M"

def fmt_aed_billions(value_aed: Union[int, float], decimals: int = 1) -> str:
    if value_aed is None or (isinstance(value_aed, float) and math.isnan(value_aed)):
        return "—"
    b = value_aed / 1_000_000_000
    return f"{b:,.{decimals}f}B"

def fmt_aed_auto(value_aed: Union[int, float], decimals: int = 1) -> str:
    if value_aed is None or (isinstance(value_aed, float) and math.isnan(value_aed)):
        return "—"
    if abs(value_aed) >= 1_000_000_000:
        return fmt_aed_billions(value_aed, decimals)
    return fmt_aed_millions(value_aed, decimals)

def fmt_millions_raw(value_m: Union[int, float], decimals: int = 1) -> str:
    if value_m is None or (isinstance(value_m, float) and math.isnan(value_m)):
        return "—"
    return f"{value_m:,.{decimals}f}M"

def fmt_pct(value: Union[int, float], decimals: int = 1, show_sign: bool = False) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    sign = "+" if show_sign and value > 0 else ""
    return f"{sign}{value:.{decimals}f}%"

def fmt_pct_delta(new: Union[int, float], old: Union[int, float], decimals: int = 1) -> str:
    if any(v is None or (isinstance(v, float) and math.isnan(v)) for v in [new, old]):
        return "—"
    delta = new - old
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.{decimals}f}pp"

def fmt_achievement(actual_aed: Union[int, float], target_aed: Union[int, float]) -> str:
    if not target_aed or target_aed == 0:
        return "—"
    ach = (actual_aed / target_aed) * 100
    return fmt_pct(ach)

def fmt_month_label(month_str: str) -> str:
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
    if month is None:
        return str(year)
    return f"{fmt_month_label(str(month))} {year}"

def fmt_snapshot_label(data_date: Optional[str] = None) -> str:
    if not data_date:
        return C.SNAPSHOT_LABEL
    try:
        parts = data_date.strip().split("-")
        y, m, d = parts[0], int(parts[1]), int(parts[2])
        month = fmt_month_label(parts[1])
        return f"Data as of {d} {month} {y}"
    except Exception:
        return C.SNAPSHOT_LABEL

def fmt_count(value: Union[int, float], suffix: str = "") -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    s = f"{int(value):,}"
    return f"{s} {suffix}".strip() if suffix else s

def fmt_days(value: Union[int, float]) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    return f"{int(value)} days"

def fmt_multiple(value: Union[int, float], decimals: int = 0) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    return f"{value:.{decimals}f}×"

def fmt_cagr(value_pct: Union[int, float]) -> str:
    if value_pct is None:
        return "—"
    return f"{value_pct:.0f}% CAGR"

def pipeline_display(value_aed: Union[int, float], label_key: str) -> dict:
    label_map = {
        "gross":        C.PIPELINE_GROSS_LABEL,
        "forward_book": C.PIPELINE_FORWARD_BOOK_LABEL,
        "adv_denom":    C.PIPELINE_ADV_DENOM_LABEL,
    }
    label = label_map.get(label_key, f"Pipeline ({label_key})")
    return {"value": fmt_aed_billions(value_aed), "label": label}

def npv_display(value_aed: Union[int, float], decimals: int = 0) -> str:
    return f"{fmt_aed_millions(value_aed, decimals)} {C.NPV_LABEL}"

def target_label(version: str) -> str:
    if version == "MDO Dues":
        return C.MDO_DUES_LABEL
    if version == "Finance Dues":
        return C.FINANCE_DUES_LABEL
    return version

def units_label(unit_type: str) -> str:
    if unit_type == "active":
        return C.UNITS_ACTIVE_LABEL
    if unit_type == "qualified":
        return C.UNITS_QUALIFIED_LABEL
    return unit_type

def entity_colour(entity: str) -> str:
    return C.ENTITY_COLOURS.get(entity, "#888888")

def entity_code(entity: str) -> str:
    return C.ENTITY_CODES.get(entity, entity.lower())

def is_valid_entity(entity: str) -> bool:
    return entity in C.ENTITY_LIST

def safe_divide(numerator: Union[int, float], denominator: Union[int, float],
                fallback: float = 0.0) -> float:
    if not denominator or denominator == 0:
        return fallback
    return numerator / denominator

def data_pending_label(section_id: str) -> dict:
    return {
        "status":  "data_pending",
        "message": f"Data pending refresh — {section_id} will update on next pipeline load.",
        "value":   None,
    }

def coerce_aed(value: Union[int, float, str, None], unit: str = "aed") -> Optional[float]:
    if value is None:
        return None
    try:
        v = float(value)
    except (ValueError, TypeError):
        return None
    multipliers = {"aed": 1, "m": 1_000_000, "b": 1_000_000_000}
    return v * multipliers.get(unit.lower(), 1)

def channel_chart_title(base_title: str) -> str:
    return f"{base_title} — {C.CHANNEL_BASIS_LABEL}"

def collector_sort_config() -> dict:
    return {"by": C.COLLECTOR_SORT_BY, "order": C.COLLECTOR_SORT_ORDER}

def mdo_daily_avg(monthly_target_aed: Union[int, float]) -> float:
    return safe_divide(monthly_target_aed, C.WORKING_DAYS_MONTH)

def kpi_card(label: str, value: str, sub: Optional[str] = None,
             delta: Optional[str] = None, flag: Optional[str] = None,
             data_date: Optional[str] = None) -> dict:
    card: dict = {"label": label, "value": value}
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
    return {
        "section":   section_id,
        "submodule": submodule_id,
        "mode":      mode,
        "data":      data,
        "platform":  C.PLATFORM_VERSION,
    }
