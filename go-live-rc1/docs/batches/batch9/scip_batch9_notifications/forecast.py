"""
SCIP forecast.py - Batch 5 month-end landing forecast

Purpose
- Build a transparent month-end landing forecast using trusted Batch 1-4 metrics.
- Use R04 Finance MTD actuals and R02 May MDO targets with explicit mixed-basis disclosure.
- Require lineaged inputs for all critical values.
- Infer working-day progress from the R04 pro-rata target row when possible.

The forecast is intentionally simple and auditable:
    current_run_rate = R04 MTD total collections / elapsed working days
    projected_landing = current_run_rate * total working days
    gap_to_mdo_target = projected_landing - R02 May total collections target
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from fastapi import APIRouter, Query
except Exception:  # pragma: no cover
    APIRouter = None
    Query = None

import data_loader

TOLERANCE_PCT = 0.05


def _to_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt_aed(value: Any) -> str:
    n = _to_float(value)
    if n is None:
        return "Unavailable"
    if abs(n) >= 1_000_000_000:
        return f"AED {n / 1_000_000_000:,.3f}B"
    if abs(n) >= 1_000_000:
        return f"AED {n / 1_000_000:,.1f}M"
    return f"AED {n:,.0f}"


def _fmt_pct(value: Any) -> str:
    n = _to_float(value)
    if n is None:
        return "Unavailable"
    return f"{n:.1f}%"


def _lineage(payload: Dict[str, Any], bucket: str, key: str) -> Dict[str, Any]:
    return (payload.get("computed", {}).get(bucket, {}) or {}).get(key, {}) or {}


def _lineage_is_usable(lineage: Dict[str, Any]) -> bool:
    required = ["source_file", "sheet", "cell_or_range", "validation_status", "confidence_state", "reporting_basis"]
    return bool(lineage) and all(lineage.get(k) not in (None, "") for k in required)


def _lineage_ref(metric_key: str, bucket: str, key: str, lineage: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "metric_key": metric_key,
        "lineage_bucket": bucket,
        "lineage_key": key,
        "has_lineage": _lineage_is_usable(lineage),
        "source_file": lineage.get("source_file"),
        "sheet": lineage.get("sheet"),
        "cell_or_range": lineage.get("cell_or_range"),
        "validation_status": lineage.get("validation_status"),
        "confidence_state": lineage.get("confidence_state"),
        "reporting_basis": lineage.get("reporting_basis"),
        "value": lineage.get("value"),
    }


def _infer_working_days(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Infer elapsed/total working days from the R04 pro-rata total target ratio.

    R04 sample exposes:
      month_target_total = E5
      mtd_prorata_total_target = E6
    The ratio is expected to be elapsed_working_days / total_working_days.
    We search small denominator candidates and pick the closest fraction.
    """
    c = payload.get("computed", {})
    month_target_total = _to_float(c.get("MONTH_TARGET_TOTAL"))
    prorata_total = _to_float(c.get("MTD_PRORATA_TOTAL_TARGET"))
    # Batch 2 stored these values primarily in R04_LINEAGE, not always as top-level computed keys.
    if month_target_total is None:
        month_target_total = _to_float(_lineage(payload, "R04_LINEAGE", "month_target_total").get("value"))
    if prorata_total is None:
        prorata_total = _to_float(_lineage(payload, "R04_LINEAGE", "mtd_prorata_total_target").get("value"))

    if not month_target_total or not prorata_total:
        return {
            "status": "fallback_default",
            "elapsed_working_days": 5,
            "total_working_days": 17,
            "remaining_working_days": 12,
            "source": "default_batch5_assumption",
            "basis": "R04 pro-rata values unavailable; default must be reviewed before production release.",
        }

    ratio = prorata_total / month_target_total
    best = None
    for total in range(10, 32):
        for elapsed in range(1, total + 1):
            err = abs((elapsed / total) - ratio)
            candidate = (err, elapsed, total)
            if best is None or candidate < best:
                best = candidate

    err, elapsed, total = best
    return {
        "status": "inferred_from_r04_prorata",
        "elapsed_working_days": elapsed,
        "total_working_days": total,
        "remaining_working_days": max(total - elapsed, 0),
        "source": "R04 mtd_prorata_total_target / month_target_total",
        "ratio": ratio,
        "fraction_error": err,
        "basis": "Elapsed and total working days inferred from visible R04 MTD pro-rata target row.",
        "lineage_refs": [
            _lineage_ref("MONTH_TARGET_TOTAL", "R04_LINEAGE", "month_target_total", _lineage(payload, "R04_LINEAGE", "month_target_total")),
            _lineage_ref("MTD_PRORATA_TOTAL_TARGET", "R04_LINEAGE", "mtd_prorata_total_target", _lineage(payload, "R04_LINEAGE", "mtd_prorata_total_target")),
        ],
    }


def build_month_end_forecast(payload: Dict[str, Any]) -> Dict[str, Any]:
    c = payload.get("computed", {})

    mtd_total = _to_float(c.get("MTD_TOTAL_COLLECTIONS"))
    mtd_da = _to_float(c.get("MTD_DA_TOTAL"))
    mtd_ns = _to_float(c.get("MTD_NS_TOTAL"))
    may_target = _to_float(c.get("MAY_TOTAL_COLLECTIONS_TARGET"))
    may_da_target = _to_float(c.get("MAY_DA_TARGET"))
    may_ns_target = _to_float(c.get("MAY_NEW_SALES_TARGET"))

    input_lineage = {
        "mtd_total_collections": _lineage(payload, "R04_LINEAGE", "mtd_total_collections"),
        "mtd_da_total": _lineage(payload, "R04_LINEAGE", "mtd_da_total"),
        "mtd_ns_total": _lineage(payload, "R04_LINEAGE", "mtd_ns_total"),
        "may_total_collections_target": _lineage(payload, "R02_LINEAGE", "may_total_collections_target_group"),
        "may_da_target": _lineage(payload, "R02_LINEAGE", "may_da_target_group"),
        "may_new_sales_target": _lineage(payload, "R02_LINEAGE", "may_new_sales_target_group"),
    }
    lineage_refs = [
        _lineage_ref("MTD_TOTAL_COLLECTIONS", "R04_LINEAGE", "mtd_total_collections", input_lineage["mtd_total_collections"]),
        _lineage_ref("MTD_DA_TOTAL", "R04_LINEAGE", "mtd_da_total", input_lineage["mtd_da_total"]),
        _lineage_ref("MTD_NS_TOTAL", "R04_LINEAGE", "mtd_ns_total", input_lineage["mtd_ns_total"]),
        _lineage_ref("MAY_TOTAL_COLLECTIONS_TARGET", "R02_LINEAGE", "may_total_collections_target_group", input_lineage["may_total_collections_target"]),
        _lineage_ref("MAY_DA_TARGET", "R02_LINEAGE", "may_da_target_group", input_lineage["may_da_target"]),
        _lineage_ref("MAY_NEW_SALES_TARGET", "R02_LINEAGE", "may_new_sales_target_group", input_lineage["may_new_sales_target"]),
    ]

    if mtd_total is None or may_target is None:
        return {
            "status": "blocked_untrusted_forecast",
            "reason": "Missing R04 MTD total or R02 May MDO target.",
            "lineage_refs": lineage_refs,
            "assumptions": [],
            "guardrails": {"no_silent_fallback": True, "critical_forecasts_require_lineage": True},
        }

    if not all(ref["has_lineage"] for ref in [lineage_refs[0], lineage_refs[3]]):
        return {
            "status": "blocked_untrusted_forecast",
            "reason": "Forecast critical inputs failed lineage gate.",
            "lineage_refs": lineage_refs,
            "assumptions": [],
            "guardrails": {"no_silent_fallback": True, "critical_forecasts_require_lineage": True},
        }

    wd = _infer_working_days(payload)
    elapsed = wd["elapsed_working_days"] or 1
    total_days = wd["total_working_days"] or elapsed
    remaining = wd["remaining_working_days"]

    current_run_rate = mtd_total / elapsed
    projected_landing = current_run_rate * total_days
    remaining_required = max(may_target - mtd_total, 0)
    required_daily_run_rate = remaining_required / remaining if remaining else 0.0
    gap_to_target = projected_landing - may_target
    achievement_pct = (mtd_total / may_target * 100) if may_target else None
    projected_achievement_pct = (projected_landing / may_target * 100) if may_target else None
    mdo_prorata_target = may_target * (elapsed / total_days) if total_days else None
    mdo_prorata_gap = mtd_total - mdo_prorata_target if mdo_prorata_target is not None else None

    da_run_rate = (mtd_da / elapsed) if mtd_da is not None else None
    ns_run_rate = (mtd_ns / elapsed) if mtd_ns is not None else None

    forecast = {
        "status": "ok",
        "contract_version": "forecast.month_end.v1.batch5",
        "forecast_date": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "forecast_name": "May month-end landing forecast",
        "reporting_basis": "R04 Finance actuals vs R02 MDO target",
        "basis_disclosure": "Actuals are R04 Finance daily collections; targets are R02 MDO targets. This is allowed only with visible basis labelling.",
        "tolerance_pct": TOLERANCE_PCT,
        "inputs": {
            "mtd_total_collections": mtd_total,
            "mtd_da_total": mtd_da,
            "mtd_new_sales_total": mtd_ns,
            "may_total_collections_target": may_target,
            "may_da_target": may_da_target,
            "may_new_sales_target": may_ns_target,
        },
        "working_days": wd,
        "outputs": {
            "current_daily_run_rate": current_run_rate,
            "required_daily_run_rate_remaining": required_daily_run_rate,
            "projected_month_end_landing": projected_landing,
            "gap_to_may_mdo_target": gap_to_target,
            "mtd_achievement_pct": achievement_pct,
            "projected_achievement_pct": projected_achievement_pct,
            "mdo_prorata_target_as_of_snapshot": mdo_prorata_target,
            "mdo_prorata_gap_as_of_snapshot": mdo_prorata_gap,
            "da_daily_run_rate": da_run_rate,
            "new_sales_daily_run_rate": ns_run_rate,
        },
        "display": {
            "mtd_total_collections": _fmt_aed(mtd_total),
            "may_total_collections_target": _fmt_aed(may_target),
            "current_daily_run_rate": _fmt_aed(current_run_rate),
            "required_daily_run_rate_remaining": _fmt_aed(required_daily_run_rate),
            "projected_month_end_landing": _fmt_aed(projected_landing),
            "gap_to_may_mdo_target": _fmt_aed(gap_to_target),
            "mtd_achievement_pct": _fmt_pct(achievement_pct),
            "projected_achievement_pct": _fmt_pct(projected_achievement_pct),
        },
        "assumptions": [
            "Month-end landing uses a straight-line current run-rate projection.",
            "Working days are inferred from the R04 pro-rata row unless an explicit calendar is later onboarded.",
            "Actuals use R04 Finance basis while target uses R02 MDO basis; UI must show the mixed-basis disclosure.",
            "R04 does not expose pure advance split; Batch 5 forecast therefore forecasts total collections, D+A and new-sales signals only.",
            "No silent fallback: forecast blocks if R04 MTD total or R02 May target lineage is missing.",
        ],
        "lineage_refs": lineage_refs + wd.get("lineage_refs", []),
        "guardrails": {
            "no_silent_fallback": True,
            "critical_forecasts_require_lineage": True,
            "forecast_assumptions_required": True,
            "finance_vs_mdo_label_required": True,
        },
    }
    return forecast


def load_payload(data_dir: Optional[str] = None) -> Dict[str, Any]:
    path = Path(data_dir) if data_dir else None
    return data_loader.load_all(data_dir=path)


if APIRouter is not None:
    router = APIRouter(tags=["forecast"])

    @router.get("/forecast/month-end")
    async def get_month_end_forecast(data_dir: Optional[str] = Query(None, description="Optional data directory override for smoke tests")) -> Dict[str, Any]:
        payload = load_payload(data_dir)
        return build_month_end_forecast(payload)
else:  # pragma: no cover
    router = None
