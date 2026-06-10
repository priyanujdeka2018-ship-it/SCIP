"""
SCIP command_centres.py - Batch 5 role-specific summary payloads with forecast cards

Purpose
- Convert the trusted data_loader payload into role-specific command centres.
- Keep reporting basis visible on every card.
- Attach lineage references to all critical metrics used in cards.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from command_centres_shadow_patch import attach_shadow_insights
from placement_shadow_patch import attach_placement_shadow


ROLE_ORDER = ["board_cxo", "cco_gm_agm", "finance", "mis_qcg_admin", "collector_rm"]

ROLE_LABELS = {
    "board_cxo": "Board/CXO",
    "cco_gm_agm": "CCO/GM/AGM",
    "finance": "Finance",
    "mis_qcg_admin": "MIS/QCG/Admin",
    "collector_rm": "Collector/RM",
}


def _fmt_aed(value: Any) -> str:
    if value is None:
        return "Unavailable"
    try:
        n = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(n) >= 1_000_000_000:
        return f"AED {n / 1_000_000_000:,.3f}B"
    if abs(n) >= 1_000_000:
        return f"AED {n / 1_000_000:,.1f}M"
    return f"AED {n:,.0f}"


def _fmt_pct(value: Any) -> str:
    if value is None:
        return "Unavailable"
    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return str(value)


def _metric_ref(metric_key: str, lineage_bucket: str, lineage_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    lin = (payload.get("computed", {}).get(lineage_bucket, {}) or {}).get(lineage_key, {}) or {}
    return {
        "metric_key": metric_key,
        "lineage_bucket": lineage_bucket,
        "lineage_key": lineage_key,
        "has_lineage": bool(lin),
        "source_file": lin.get("source_file"),
        "sheet": lin.get("sheet"),
        "cell_or_range": lin.get("cell_or_range"),
        "validation_status": lin.get("validation_status"),
        "confidence_state": lin.get("confidence_state"),
        "reporting_basis": lin.get("reporting_basis"),
    }


def _card(card_id: str, title: str, value: Any, display: str, basis: str, action: str, refs: List[Dict[str, Any]], severity: str = "info") -> Dict[str, Any]:
    return {
        "card_id": card_id,
        "title": title,
        "value": value,
        "display_value": display,
        "reporting_basis": basis,
        "action": action,
        "severity": severity,
        "lineage_refs": refs,
        "trust_state": "lineaged" if all(r.get("has_lineage") for r in refs) else "blocked_or_partial_lineage",
    }


def _build_trust_bar(payload: Dict[str, Any]) -> Dict[str, Any]:
    summary = payload.get("summary", {})
    meta = summary.get("meta", {})
    computed = payload.get("computed", {})
    critical_buckets = {
        "R18": computed.get("OD_LINEAGE", {}),
        "R04": computed.get("R04_LINEAGE", {}),
        "R02": computed.get("R02_LINEAGE", {}),
        "R08": computed.get("R08_LINEAGE", {}),
        "R36": computed.get("R36_LINEAGE", {}),
    }
    validation_buckets = {
        "R18": computed.get("OD_VALIDATIONS", {}),
        "R04": computed.get("R04_VALIDATIONS", {}),
        "R02": computed.get("R02_VALIDATIONS", {}),
        "R08": computed.get("R08_VALIDATIONS", {}),
        "R36": computed.get("R36_VALIDATIONS", {}),
    }
    return {
        "snapshot_date": meta.get("snapshot_date"),
        "load_timestamp": meta.get("load_timestamp"),
        "platform_version": meta.get("platform_version"),
        "sources_loaded": meta.get("sources_loaded", []),
        "sources_missing": meta.get("sources_missing", []),
        "critical_sources": ["R18", "R04", "R02", "R08", "R36"],
        "critical_lineage_counts": {k: len(v or {}) for k, v in critical_buckets.items()},
        "critical_validation_counts": {k: len(v or {}) for k, v in validation_buckets.items()},
        "no_silent_fallback": True,
        "tolerance_pct": 0.05,
    }


def _board_cards(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    c = payload.get("computed", {})
    return [
        _card(
            "board_od_exposure",
            "Current OD exposure",
            c.get("OD_TODAY"),
            _fmt_aed(c.get("OD_TODAY")),
            "R18 overdue",
            "Review Sobha/UAQ split before executive action review.",
            [_metric_ref("OD_TODAY", "OD_LINEAGE", "OD_TODAY", payload)],
            "risk",
        ),
        _card(
            "board_mtd_collection_progress",
            "MTD total collections",
            c.get("MTD_TOTAL_COLLECTIONS"),
            _fmt_aed(c.get("MTD_TOTAL_COLLECTIONS")),
            "Finance",
            "Compare with May MDO target only with basis label visible.",
            [_metric_ref("MTD_TOTAL_COLLECTIONS", "R04_LINEAGE", "mtd_total_collections", payload)],
            "monitor",
        ),
        _card(
            "board_advance_mix",
            "2026 advance mix",
            c.get("CY_ADV_MIX_YTD"),
            f"CY {_fmt_pct(c.get('CY_ADV_MIX_YTD'))} / FY {_fmt_pct(c.get('FY_ADV_MIX_YTD'))}",
            "R08 advance summary",
            "Use to evaluate cash pull-forward quality and future-year exposure.",
            [
                _metric_ref("CY_ADV_MIX_YTD", "R08_LINEAGE", "CY_ADV_MIX_YTD", payload),
                _metric_ref("FY_ADV_MIX_YTD", "R08_LINEAGE", "FY_ADV_MIX_YTD", payload),
            ],
            "strategic",
        ),
        _card(
            "board_pipeline_gross",
            "Forward collectible calendar",
            c.get("PIPELINE_GROSS"),
            _fmt_aed(c.get("PIPELINE_GROSS")),
            "R36 milestone cohort",
            "Use as the 2026-onwards active forward collectible base.",
            [_metric_ref("PIPELINE_GROSS", "R36_LINEAGE", "PIPELINE_GROSS", payload)],
            "strategic",
        ),
    ]


def _ops_cards(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    c = payload.get("computed", {})
    mtd = c.get("MTD_TOTAL_COLLECTIONS") or 0
    may_target = c.get("MAY_TOTAL_COLLECTIONS_TARGET") or 0
    ach = (mtd / may_target * 100) if may_target else None
    return [
        _card(
            "ops_mtd_vs_may_target",
            "MTD collections vs May MDO target",
            ach,
            _fmt_pct(ach),
            "Finance actual vs MDO target",
            "Use as directional pacing only; keep Finance/MDO basis label visible.",
            [
                _metric_ref("MTD_TOTAL_COLLECTIONS", "R04_LINEAGE", "mtd_total_collections", payload),
                _metric_ref("MAY_TOTAL_COLLECTIONS_TARGET", "R02_LINEAGE", "may_total_collections_target_group", payload),
            ],
            "risk" if ach is not None and ach < 50 else "monitor",
        ),
        _card(
            "ops_sobha_od",
            "Sobha OD",
            c.get("OD_SOBHA"),
            _fmt_aed(c.get("OD_SOBHA")),
            "R18 overdue",
            "Break into Sobha Dubai and Sobha AUH recovery actions.",
            [_metric_ref("OD_SOBHA", "OD_LINEAGE", "OD_SOBHA", payload)],
            "risk",
        ),
        _card(
            "ops_uaq_od",
            "UAQ OD",
            c.get("OD_UAQ"),
            _fmt_aed(c.get("OD_UAQ")),
            "R18 overdue",
            "Review Siniya and Downtown UAQ separately.",
            [_metric_ref("OD_UAQ", "OD_LINEAGE", "OD_UAQ", payload)],
            "risk",
        ),
        _card(
            "ops_new_sales_collections",
            "MTD new-sales collections",
            c.get("MTD_NS_TOTAL"),
            _fmt_aed(c.get("MTD_NS_TOTAL")),
            "Finance",
            "Escalate if new-sales conversion is below month pacing.",
            [_metric_ref("MTD_NS_TOTAL", "R04_LINEAGE", "mtd_ns_total", payload)],
            "monitor",
        ),
    ]


def _finance_cards(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    c = payload.get("computed", {})
    return [
        _card(
            "finance_basis_control",
            "Finance actual vs MDO target basis",
            None,
            "Finance actuals / MDO targets",
            "Finance + MDO",
            "Keep R04 actuals and R02 targets separated in all reporting.",
            [
                _metric_ref("MTD_TOTAL_COLLECTIONS", "R04_LINEAGE", "mtd_total_collections", payload),
                _metric_ref("MAY_TOTAL_COLLECTIONS_TARGET", "R02_LINEAGE", "may_total_collections_target_group", payload),
            ],
            "control",
        ),
        _card(
            "finance_r08_rebate",
            "YTD 2026 rebate / NPV applied",
            c.get("YTD_2026_REBATE"),
            _fmt_aed(c.get("YTD_2026_REBATE")),
            "R08 advance summary",
            "Use the R08 rebate lineage before reporting NPV or rebate impact.",
            [_metric_ref("YTD_2026_REBATE", "R08_LINEAGE", "ytd_2026_rebate", payload)],
            "control",
        ),
        _card(
            "finance_r36_pipeline",
            "Pipeline gross source control",
            c.get("PIPELINE_GROSS"),
            _fmt_aed(c.get("PIPELINE_GROSS")),
            "R36 milestone cohort",
            "Use only with Active-sheet source and forward-year range disclosed.",
            [_metric_ref("PIPELINE_GROSS", "R36_LINEAGE", "PIPELINE_GROSS", payload)],
            "control",
        ),
    ]


def _mis_cards(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    trust = _build_trust_bar(payload)
    return [
        _card(
            "mis_lineage_coverage",
            "Critical lineage coverage",
            trust.get("critical_lineage_counts"),
            str(trust.get("critical_lineage_counts")),
            "Data governance",
            "Release only when R18/R04/R02/R08/R36 lineage counts are non-zero.",
            [],
            "control",
        ),
        _card(
            "mis_missing_sources",
            "Missing sources",
            trust.get("sources_missing"),
            ", ".join(trust.get("sources_missing") or []) or "None for loaded critical layer",
            "Data governance",
            "Triage missing non-critical reports without blocking critical command centres.",
            [],
            "monitor",
        ),
    ]


def _collector_cards(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    c = payload.get("computed", {})
    return [
        _card(
            "collector_od_priority",
            "OD follow-up pool",
            c.get("OD_TODAY"),
            _fmt_aed(c.get("OD_TODAY")),
            "R18 overdue",
            "Use as the verified pool for prioritisation; account-level tasking awaits lineaged account report onboarding.",
            [_metric_ref("OD_TODAY", "OD_LINEAGE", "OD_TODAY", payload)],
            "risk",
        ),
        _card(
            "collector_daily_progress_signal",
            "MTD collection progress signal",
            c.get("MTD_TOTAL_COLLECTIONS"),
            _fmt_aed(c.get("MTD_TOTAL_COLLECTIONS")),
            "Finance",
            "Use for daily pace awareness; individual RM scorecards require R30/account-level refresh.",
            [_metric_ref("MTD_TOTAL_COLLECTIONS", "R04_LINEAGE", "mtd_total_collections", payload)],
            "monitor",
        ),
    ]


def build_command_centres(payload: Dict[str, Any]) -> Dict[str, Any]:
    trust_bar = _build_trust_bar(payload)
    if os.environ.get("SCIP_PLACEMENT_RENDER", "static") == "binder":
        # Wave D-2 cutover: Placement Binder is the render source (default off).
        from command_centres_v2 import build_role_cards_from_binder
        roles = build_role_cards_from_binder(payload, trust_bar)
    else:
        # Legacy static render — retained for rollback until WAVE_D2_DELETIONS.
        roles = {
            "board_cxo": {
                "role_label": ROLE_LABELS["board_cxo"],
                "purpose": "Decision clarity, source trust, cash risk, and strategic forward visibility.",
                "trust_bar": trust_bar,
                "cards": _board_cards(payload),
            },
            "cco_gm_agm": {
                "role_label": ROLE_LABELS["cco_gm_agm"],
                "purpose": "Daily operating review, intervention queue, and month-end pacing.",
                "trust_bar": trust_bar,
                "cards": _ops_cards(payload),
            },
            "finance": {
                "role_label": ROLE_LABELS["finance"],
                "purpose": "Reconciliation, reporting-basis control, and audit traceability.",
                "trust_bar": trust_bar,
                "cards": _finance_cards(payload),
            },
            "mis_qcg_admin": {
                "role_label": ROLE_LABELS["mis_qcg_admin"],
                "purpose": "Data quality, source freshness, validation, and release governance.",
                "trust_bar": trust_bar,
                "cards": _mis_cards(payload),
            },
            "collector_rm": {
                "role_label": ROLE_LABELS["collector_rm"],
                "purpose": "Frontline action focus while avoiding unverified account-level claims.",
                "trust_bar": trust_bar,
                "cards": _collector_cards(payload),
            },
        }
    return {
        "status": "ok",
        "contract_version": "command_centres.v1.batch4",
        "roles": roles,
        "role_order": ROLE_ORDER,
        "guardrails": {
            "no_silent_fallback": True,
            "critical_cards_require_lineage_refs": True,
            "finance_vs_mdo_label_required": True,
            "entity_head_removed": True,
        },
    }

# ---------------------------------------------------------------------------
# Batch 5 extension: attach forecast cards and enforce frontend card contract
# ---------------------------------------------------------------------------

_build_command_centres_batch4 = build_command_centres


def _first_lineaged_ref(payload: Dict[str, Any]) -> Dict[str, Any]:
    candidates = [
        ("OD_TODAY", "OD_LINEAGE", "OD_TODAY"),
        ("MTD_TOTAL_COLLECTIONS", "R04_LINEAGE", "mtd_total_collections"),
        ("MAY_TOTAL_COLLECTIONS_TARGET", "R02_LINEAGE", "may_total_collections_target_group"),
        ("ADVANCE_2026_TOTAL", "R08_LINEAGE", "ADVANCE_2026_TOTAL"),
        ("PIPELINE_GROSS", "R36_LINEAGE", "PIPELINE_GROSS"),
    ]
    for metric_key, bucket, key in candidates:
        ref = _metric_ref(metric_key, bucket, key, payload)
        if ref.get("has_lineage"):
            return ref
    return {"metric_key": "PLATFORM_TRUST", "has_lineage": False, "reporting_basis": "Data governance"}


def _forecast_card(forecast_payload: Dict[str, Any], role_key: str) -> Optional[Dict[str, Any]]:
    if not forecast_payload or forecast_payload.get("status") != "ok":
        return None
    outputs = forecast_payload.get("outputs", {})
    display = forecast_payload.get("display", {})
    refs = forecast_payload.get("lineage_refs", [])
    card = _card(
        f"{role_key}_month_end_forecast",
        "May month-end landing forecast",
        outputs.get("projected_month_end_landing"),
        display.get("projected_month_end_landing", "Unavailable"),
        forecast_payload.get("reporting_basis", "R04 Finance actuals vs R02 MDO target"),
        "Use as a pacing signal only; assumptions and mixed-basis disclosure must remain visible.",
        refs,
        "forecast",
    )
    card["forecast"] = forecast_payload
    card["assumptions"] = forecast_payload.get("assumptions", [])
    card["basis_disclosure"] = forecast_payload.get("basis_disclosure")
    return card


def _ensure_batch5_card_contract(result: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    fallback_ref = _first_lineaged_ref(payload)
    for role_key, role_payload in (result.get("roles") or {}).items():
        for card in role_payload.get("cards", []) or []:
            card.setdefault("reporting_basis", "Data governance")
            refs = card.get("lineage_refs") or []
            if not refs:
                refs = [{**fallback_ref, "contract_note": "Governance/control card uses platform trust lineage reference."}]
                card["lineage_refs"] = refs
            card["lineage_display"] = [
                {
                    "metric_key": ref.get("metric_key"),
                    "source_file": ref.get("source_file"),
                    "sheet": ref.get("sheet"),
                    "cell_or_range": ref.get("cell_or_range"),
                    "validation_status": ref.get("validation_status"),
                    "confidence_state": ref.get("confidence_state"),
                    "reporting_basis": ref.get("reporting_basis") or card.get("reporting_basis"),
                    "has_lineage": bool(ref.get("has_lineage")),
                }
                for ref in refs
            ]
            card["trust_state"] = "lineaged" if all(ref.get("has_lineage") for ref in refs) else "blocked_or_partial_lineage"
    return result


def build_command_centres(payload: Dict[str, Any]) -> Dict[str, Any]:
    result = _build_command_centres_batch4(payload)
    result["contract_version"] = "command_centres.v2.batch5"
    result.setdefault("guardrails", {})["every_card_requires_reporting_basis"] = True
    result.setdefault("guardrails", {})["every_card_requires_lineage_display"] = True
    result.setdefault("guardrails", {})["month_end_forecast_assumptions_required"] = True

    try:
        import forecast as _forecast
        forecast_payload = _forecast.build_month_end_forecast(payload)
    except Exception as exc:  # keep command centres bootable but explicit
        forecast_payload = {"status": "forecast_error", "reason": str(exc), "assumptions": []}

    result["forecast"] = forecast_payload
    if forecast_payload.get("status") == "ok":
        for role_key in ["board_cxo", "cco_gm_agm", "finance"]:
            role_payload = result.get("roles", {}).get(role_key)
            if role_payload is not None:
                fc = _forecast_card(forecast_payload, role_key)
                if fc:
                    role_payload.setdefault("cards", []).insert(1, fc)

    result = _ensure_batch5_card_contract(result, payload)
    result = attach_shadow_insights(result, payload)   # Wave A–C shadow hook (env: SCIP_INSIGHT_SHADOW)
    return attach_placement_shadow(result, payload)    # Wave D-1 shadow hook (env: SCIP_PLACEMENT_SHADOW)
