"""
SCIP quickball.py - Batch 4 lineage-first analytics copilot

Purpose
- Explain trusted Batch 1-3 critical metrics with source-level lineage.
- Block critical answers when lineage, validation, or confidence is missing.
- Provide role-aware interpretation without changing the underlying number.
- Expose FastAPI endpoints for explain-this-number and role command centres.

Dependency rule
- quickball imports data_loader and command_centres only.
- quickball never parses Excel directly; it only consumes the trusted payload.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional

try:  # FastAPI is available in deployment; keep import optional for smoke tests.
    from fastapi import APIRouter, Query
except Exception:  # pragma: no cover - allows pure Python smoke tests without FastAPI.
    APIRouter = None
    Query = None

import data_loader
import command_centres


# ---------------------------------------------------------------------------
# Role model - Batch 4 approved roles
# ---------------------------------------------------------------------------

ROLE_MODES: Dict[str, Dict[str, Any]] = {
    "board_cxo": {
        "label": "Board/CXO",
        "purpose": "Decision clarity, strategic risk, and source trust.",
        "tone": "executive",
        "focus": ["variance", "risk", "cash visibility", "decision needed"],
    },
    "cco_gm_agm": {
        "label": "CCO/GM/AGM",
        "purpose": "Daily intervention control and month-end landing.",
        "tone": "operational leadership",
        "focus": ["shortfall", "entity split", "intervention", "owner action"],
    },
    "finance": {
        "label": "Finance",
        "purpose": "Reconciliation, reporting basis, and audit traceability.",
        "tone": "control and reconciliation",
        "focus": ["source", "basis", "cell", "validation", "tolerance"],
    },
    "mis_qcg_admin": {
        "label": "MIS/QCG/Admin",
        "purpose": "Source freshness, validation, smoke gates, and data quality.",
        "tone": "data operations",
        "focus": ["lineage", "validation", "missing sources", "fallback policy"],
    },
    "collector_rm": {
        "label": "Collector/RM",
        "purpose": "Actionable collection focus without exposing unverified account detail.",
        "tone": "frontline action",
        "focus": ["priority", "follow-up", "OD", "daily target"],
    },
}

ROLE_ALIASES = {
    "board": "board_cxo",
    "cxo": "board_cxo",
    "board/cxo": "board_cxo",
    "executive": "board_cxo",
    "cco": "cco_gm_agm",
    "gm": "cco_gm_agm",
    "agm": "cco_gm_agm",
    "cco/gm/agm": "cco_gm_agm",
    "finance": "finance",
    "mis": "mis_qcg_admin",
    "qcg": "mis_qcg_admin",
    "admin": "mis_qcg_admin",
    "mis/qcg/admin": "mis_qcg_admin",
    "collector": "collector_rm",
    "rm": "collector_rm",
    "collector/rm": "collector_rm",
}


# ---------------------------------------------------------------------------
# Critical metric catalogue (loaded dynamically)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MetricSpec:
    canonical_key: str
    label: str
    computed_key: Optional[str]
    lineage_bucket: str
    lineage_key: str
    reporting_basis: str
    source_code: str
    unit: str = "AED"
    critical: bool = True
    business_definition: str = ""


# Load metric definitions from the external JSON catalogue using the helper.
try:  # package import path
    from .metric_loader import load_metric_catalog
except ImportError:  # top-level runtime import path used by uvicorn main:app
    from metric_loader import load_metric_catalog

_raw_metric_catalog = load_metric_catalog()

METRIC_CATALOG: Dict[str, MetricSpec] = {
    key: MetricSpec(**fields) for key, fields in _raw_metric_catalog.items()
}

ALIASES: Dict[str, str] = {
    "od": "OD_TODAY",
    "od today": "OD_TODAY",
    "overdue": "OD_TODAY",
    "group od": "OD_TODAY",
    "sobha od": "OD_SOBHA",
    "uaq od": "OD_UAQ",
    "mtd collections": "MTD_TOTAL_COLLECTIONS",
    "daily collections": "MTD_TOTAL_COLLECTIONS",
    "r04 collections": "MTD_TOTAL_COLLECTIONS",
    "finance d+a": "MTD_DA_TOTAL",
    "new sales": "MTD_NS_TOTAL",
    "may target": "MAY_TOTAL_COLLECTIONS_TARGET",
    "may d+a target": "MAY_DA_TARGET",
    "mdo target": "MAY_TOTAL_COLLECTIONS_TARGET",
    "fy target": "FY_TOTAL_COLLECTIONS_TARGET",
    "advance": "ADVANCE_2026_TOTAL",
    "advance total": "ADVANCE_2026_TOTAL",
    "cy advance": "ADVANCE_2026_CY",
    "fy advance": "ADVANCE_2026_FY",
    "cy mix": "CY_ADV_MIX_YTD",
    "fy mix": "FY_ADV_MIX_YTD",
    "rebate": "YTD_2026_REBATE",
    "npv": "YTD_2026_REBATE",
    "pipeline": "PIPELINE_GROSS",
    "pipeline gross": "PIPELINE_GROSS",
    "r36 pipeline": "PIPELINE_GROSS",
    "2026 forward": "PIPELINE_FORWARD_2026",
    "2027 forward": "PIPELINE_FORWARD_2027",
    "2028 forward": "PIPELINE_FORWARD_2028",
}


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def normalize_role(role: Optional[str]) -> str:
    if not role:
        return "board_cxo"
    text = str(role).strip().lower().replace(" ", "_")
    text_slash = str(role).strip().lower()
    if text in ROLE_MODES:
        return text
    if text_slash in ROLE_ALIASES:
        return ROLE_ALIASES[text_slash]
    return ROLE_ALIASES.get(text, "board_cxo")


def normalize_metric_key(metric: str) -> Optional[str]:
    if not metric:
        return None
    raw = str(metric).strip()
    upper = raw.upper().replace(" ", "_").replace("-", "_")
    if upper in METRIC_CATALOG:
        return upper
    lower = raw.strip().lower().replace("_", " ")
    if lower in ALIASES:
        return ALIASES[lower]
    for alias, canonical in ALIASES.items():
        if alias in lower:
            return canonical
    return None


def _fmt_value(value: Any, unit: str) -> str:
    if value is None:
        return "Unavailable"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if unit == "pct":
        return f"{number:.2f}%"
    if unit == "AED":
        abs_n = abs(number)
        if abs_n >= 1_000_000_000:
            return f"AED {number / 1_000_000_000:,.3f}B"
        if abs_n >= 1_000_000:
            return f"AED {number / 1_000_000:,.1f}M"
        return f"AED {number:,.0f}"
    return f"{number:,.2f}"


def _get_metric_value(payload: Dict[str, Any], spec: MetricSpec, lineage: Dict[str, Any]) -> Any:
    computed = payload.get("computed", {})
    if spec.computed_key:
        return computed.get(spec.computed_key)
    # R36 forward buckets are stored inside FORWARD_COLLECTIBLE_CALENDAR.
    if spec.canonical_key.startswith("PIPELINE_FORWARD_"):
        year = spec.canonical_key.rsplit("_", 1)[-1]
        return (computed.get("FORWARD_COLLECTIBLE_CALENDAR") or {}).get(year)
    return lineage.get("value")


def _lineage_is_usable(lineage: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(lineage, dict) or not lineage:
        return False
    required = ["source_file", "sheet", "cell_or_range", "validation_status", "confidence_state"]
    return all(lineage.get(k) not in (None, "") for k in required)


def _answer_blocked(spec: MetricSpec, reason: str, role_key: str) -> Dict[str, Any]:
    return {
        "status": "blocked_untrusted_metric",
        "role": ROLE_MODES[role_key],
        "metric_key": spec.canonical_key,
        "metric_label": spec.label,
        "reason": reason,
        "answer": (
            f"I cannot explain {spec.label} because the trusted lineage gate failed. "
            f"Reason: {reason}. The no-silent-fallback rule is active for {spec.source_code}."
        ),
        "lineage": None,
        "guardrail": {
            "critical_metric": spec.critical,
            "no_silent_fallback": True,
            "requires_lineage": True,
        },
    }


def _role_interpretation(role_key: str, spec: MetricSpec, value: Any, payload: Dict[str, Any]) -> str:
    computed = payload.get("computed", {})
    if role_key == "board_cxo":
        if spec.source_code == "R18":
            return "Board view: treat this as the current cash-risk exposure requiring entity-level review before the next executive discussion."
        if spec.source_code == "R36":
            return "Board view: this is the forward collectible base for strategic cash visibility and pipeline concentration review."
        if spec.source_code == "R08":
            return "Board view: use this to judge advance acceleration quality and current-year versus future-year cash pull-forward."
        if spec.source_code == "R02":
            return "Board view: this is an MDO target, so compare it with Finance actuals only when the reporting basis is shown."
        if spec.source_code == "R04":
            return "Board view: this is Finance-basis daily collection progress, useful for month-end landing visibility."
    if role_key == "cco_gm_agm":
        if spec.source_code == "R04":
            target = computed.get("MAY_TOTAL_COLLECTIONS_TARGET") or computed.get("MAY_DA_TARGET")
            if target:
                pct = (float(value or 0) / float(target)) * 100
                return f"Ops view: this is the working MTD progress signal. Current progress is about {pct:.1f}% of the comparable May MDO target basis, subject to Finance-vs-MDO labelling."
            return "Ops view: use this as the daily intervention baseline and pair it with remaining working days."
        if spec.source_code == "R18":
            return "Ops view: review the Sobha and UAQ splits first, then assign OD recovery actions by project/account owner."
        return "Ops view: convert this number into a weekly intervention queue and owner-wise follow-up."
    if role_key == "finance":
        return "Finance view: verify reporting basis, source file, sheet, cell/range, and validation status before using this in reconciliation or official reporting."
    if role_key == "mis_qcg_admin":
        return "MIS/QCG/Admin view: this metric passed the lineage gate; monitor source freshness, validation status, and any warnings before release."
    if role_key == "collector_rm":
        if spec.source_code == "R18":
            return "Collector/RM view: use the OD exposure to prioritise overdue follow-up; account-level action lists require account-level source onboarding."
        return "Collector/RM view: use this as a directional target/progress signal; customer-level tasking must come from lineaged account-level reports."
    return "Use this figure only with its reporting basis and source lineage visible."


# ---------------------------------------------------------------------------
# Public API functions
# ---------------------------------------------------------------------------

def explain_metric(payload: Dict[str, Any], metric: str, role: Optional[str] = "board_cxo") -> Dict[str, Any]:
    role_key = normalize_role(role)
    canonical = normalize_metric_key(metric)
    if not canonical or canonical not in METRIC_CATALOG:
        return {
            "status": "unknown_metric",
            "role": ROLE_MODES[role_key],
            "input": metric,
            "answer": "I could not map that request to a trusted SCIP critical metric. Try OD_TODAY, MTD_TOTAL_COLLECTIONS, MAY_DA_TARGET, ADVANCE_2026_TOTAL, or PIPELINE_GROSS.",
            "available_examples": sorted(list(METRIC_CATALOG.keys()))[:20],
        }

    spec = METRIC_CATALOG[canonical]
    computed = payload.get("computed", {})
    lineage_bucket = computed.get(spec.lineage_bucket, {}) or {}
    lineage = lineage_bucket.get(spec.lineage_key)

    if spec.critical and not _lineage_is_usable(lineage):
        return _answer_blocked(spec, f"Missing or incomplete lineage for {spec.lineage_bucket}.{spec.lineage_key}", role_key)

    if spec.critical and lineage.get("validation_status") not in ("passed", "disclosed", "warning"):
        return _answer_blocked(spec, f"Validation status is {lineage.get('validation_status')}", role_key)

    if spec.critical and lineage.get("confidence_state") not in ("live_validated", "live_warning", "disclosed"):
        return _answer_blocked(spec, f"Confidence state is {lineage.get('confidence_state')}", role_key)

    value = _get_metric_value(payload, spec, lineage)
    if value is None and spec.critical:
        return _answer_blocked(spec, "Metric value is unavailable despite lineage lookup", role_key)

    displayed_value = _fmt_value(value, spec.unit)
    role_note = _role_interpretation(role_key, spec, value, payload)
    basis = lineage.get("reporting_basis") or spec.reporting_basis
    business_definition = lineage.get("business_definition") or spec.business_definition

    answer = (
        f"{spec.label} is {displayed_value}. "
        f"Reporting basis: {basis}. "
        f"Source: {lineage.get('source_file')} / sheet {lineage.get('sheet')} / cell or range {lineage.get('cell_or_range')}. "
        f"Validation: {lineage.get('validation_status')}; confidence: {lineage.get('confidence_state')}. "
        f"Definition: {business_definition} "
        f"{role_note}"
    )

    return {
        "status": "answered",
        "role": ROLE_MODES[role_key],
        "metric_key": spec.canonical_key,
        "metric_label": spec.label,
        "value": value,
        "display_value": displayed_value,
        "unit": spec.unit,
        "reporting_basis": basis,
        "source_code": spec.source_code,
        "business_definition": business_definition,
        "answer": answer,
        "role_interpretation": role_note,
        "lineage": lineage,
        "guardrail": {
            "critical_metric": spec.critical,
            "no_silent_fallback": True,
            "requires_lineage": True,
            "lineage_gate_passed": True,
        },
    }


def build_sample_answers(payload: Dict[str, Any]) -> Dict[str, Any]:
    samples = [
        ("OD_TODAY", "board_cxo"),
        ("MTD_TOTAL_COLLECTIONS", "cco_gm_agm"),
        ("MAY_DA_TARGET", "finance"),
        ("ADVANCE_2026_TOTAL", "board_cxo"),
        ("YTD_2026_REBATE", "finance"),
        ("PIPELINE_GROSS", "board_cxo"),
        ("PIPELINE_FORWARD_2026", "mis_qcg_admin"),
    ]
    return {
        "samples": [explain_metric(payload, metric, role) for metric, role in samples],
        "catalog_count": len(METRIC_CATALOG),
    }


def load_payload(data_dir: Optional[str] = None) -> Dict[str, Any]:
    path = Path(data_dir) if data_dir else None
    return data_loader.load_all(data_dir=path)


# ---------------------------------------------------------------------------
# FastAPI router
# ---------------------------------------------------------------------------

if APIRouter is not None:
    router = APIRouter(tags=["quickball"])

    @router.get("/quickball")
    async def quickball_status() -> Dict[str, Any]:
        return {
            "status": "ok",
            "mode": "lineage_first",
            "roles": ROLE_MODES,
            "metric_catalog_count": len(METRIC_CATALOG),
            "guardrails": {
                "no_silent_fallback": True,
                "critical_metrics_require_lineage": True,
                "reporting_basis_required": True,
            },
        }

    @router.get("/quickball/explain")
    async def quickball_explain(
        metric: str = Query(..., description="Metric name or natural-language alias, e.g. OD_TODAY or pipeline gross"),
        role: str = Query("board_cxo", description="board_cxo, cco_gm_agm, finance, mis_qcg_admin, collector_rm"),
    ) -> Dict[str, Any]:
        payload = load_payload()
        return explain_metric(payload, metric, role)

    @router.get("/quickball/sample-answers")
    async def quickball_sample_answers() -> Dict[str, Any]:
        payload = load_payload()
        return build_sample_answers(payload)

    @router.get("/command-centres")
    async def get_command_centres() -> Dict[str, Any]:
        payload = load_payload()
        return command_centres.build_command_centres(payload)

    @router.get("/command-centres/{role}")
    async def get_command_centre(role: str) -> Dict[str, Any]:
        payload = load_payload()
        centres = command_centres.build_command_centres(payload)
        role_key = normalize_role(role)
        return centres.get("roles", {}).get(role_key, {"status": "unknown_role", "role": role})
else:
    router = None
