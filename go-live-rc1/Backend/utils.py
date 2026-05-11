"""
SCIP utility helpers.
Pure formatting and safe helper functions used by data_loader, health, forecast, and quickball.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Optional, Union, Any

try:
    import constants as C
except Exception:
    C = None


def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


def fmt_aed_millions(value_aed: Union[int, float, None], decimals: int = 1) -> str:
    if _is_missing(value_aed):
        return "-"
    return f"{float(value_aed) / 1_000_000:,.{decimals}f}M"


def fmt_aed_billions(value_aed: Union[int, float, None], decimals: int = 1) -> str:
    if _is_missing(value_aed):
        return "-"
    return f"{float(value_aed) / 1_000_000_000:,.{decimals}f}B"


def fmt_aed_auto(value_aed: Union[int, float, None], decimals: int = 1) -> str:
    if _is_missing(value_aed):
        return "-"
    if abs(float(value_aed)) >= 1_000_000_000:
        return fmt_aed_billions(value_aed, decimals)
    return fmt_aed_millions(value_aed, decimals)


def fmt_millions_raw(value_m: Union[int, float, None], decimals: int = 1) -> str:
    if _is_missing(value_m):
        return "-"
    return f"{float(value_m):,.{decimals}f}M"


def fmt_pct(value: Union[int, float, None], decimals: int = 1, show_sign: bool = False) -> str:
    if _is_missing(value):
        return "-"
    sign = "+" if show_sign and float(value) > 0 else ""
    return f"{sign}{float(value):.{decimals}f}%"


def fmt_pct_delta(new: Union[int, float, None], old: Union[int, float, None], decimals: int = 1) -> str:
    if _is_missing(new) or _is_missing(old):
        return "-"
    delta = float(new) - float(old)
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.{decimals}f}pp"


def fmt_achievement(actual_aed: Union[int, float, None], target_aed: Union[int, float, None]) -> str:
    if not target_aed:
        return "-"
    return fmt_pct((float(actual_aed or 0) / float(target_aed)) * 100)


def fmt_month_label(month_str: Union[str, int]) -> str:
    month_map = {
        "01": "Jan", "1": "Jan", "jan": "Jan", "january": "Jan",
        "02": "Feb", "2": "Feb", "feb": "Feb", "february": "Feb",
        "03": "Mar", "3": "Mar", "mar": "Mar", "march": "Mar",
        "04": "Apr", "4": "Apr", "apr": "Apr", "april": "Apr",
        "05": "May", "5": "May", "may": "May",
        "06": "Jun", "6": "Jun", "jun": "Jun", "june": "Jun",
        "07": "Jul", "7": "Jul", "jul": "Jul", "july": "Jul",
        "08": "Aug", "8": "Aug", "aug": "Aug", "august": "Aug",
        "09": "Sep", "9": "Sep", "sep": "Sep", "september": "Sep",
        "10": "Oct", "oct": "Oct", "october": "Oct",
        "11": "Nov", "nov": "Nov", "november": "Nov",
        "12": "Dec", "dec": "Dec", "december": "Dec",
    }
    return month_map.get(str(month_str).strip().lower(), str(month_str))


def fmt_period_label(year: Union[int, str], month: Union[int, str, None] = None) -> str:
    if month is None:
        return str(year)
    return f"{fmt_month_label(month)} {year}"


def fmt_snapshot_label(data_date: Optional[str] = None) -> str:
    fallback = getattr(C, "SNAPSHOT_LABEL", "Data date unavailable") if C else "Data date unavailable"
    if not data_date:
        return fallback
    try:
        dt = datetime.fromisoformat(str(data_date).replace("Z", "+00:00"))
        return f"Data as of {dt.day} {fmt_month_label(dt.month)} {dt.year}"
    except Exception:
        try:
            parts = str(data_date).split("-")
            return f"Data as of {int(parts[2])} {fmt_month_label(parts[1])} {parts[0]}"
        except Exception:
            return fallback


def fmt_count(value: Union[int, float, None], suffix: str = "") -> str:
    if _is_missing(value):
        return "-"
    out = f"{int(value):,}"
    return f"{out} {suffix}".strip()


def safe_divide(numerator: Union[int, float, None], denominator: Union[int, float, None], fallback: float = 0.0) -> float:
    try:
        if denominator is None or float(denominator) == 0:
            return fallback
        return float(numerator or 0) / float(denominator)
    except Exception:
        return fallback


def data_pending_label(section_id: str) -> dict:
    return {
        "status": "data_pending",
        "message": f"Data pending refresh - {section_id} will update on next pipeline load.",
        "value": None,
    }


def coerce_aed(value: Union[int, float, str, None], unit: str = "aed") -> Optional[float]:
    if value is None:
        return None
    try:
        n = float(str(value).replace(",", "").strip())
        unit_l = str(unit).lower()
        if unit_l in {"m", "mn", "million", "millions"}:
            return n * 1_000_000
        if unit_l in {"b", "bn", "billion", "billions"}:
            return n * 1_000_000_000
        return n
    except Exception:
        return None
