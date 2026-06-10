"""
SCIP insight_compiler.py - Wave B (Live Pulse deterministic frames + blocked degrade)

Builds on Wave A. New in Wave B:
  - Predicate engine: threshold_cross, delta_sign (+ suppress_if_unchanged).
  - Deterministic frame resolution from registry frame_sets: the headline is now
    a function of current data state, not a static string.
  - Blocked degrade on CUTOVER surfaces: when the critical lineage gate fails,
    the insight is emitted with NO number (value None, "Unavailable"), the
    blocked frame, and severity "blocked". This is the real behavioral change
    vs Wave A, and it replaces the old `"risk" if ach < 50` ternary with a
    registry predicate.

Cutover is env-gated and defaults to SHADOW:
  - SCIP_INSIGHT_CUTOVER=shadow      (default) -> Wave A behavior everywhere;
    numbers mirror the static cards even when the gate fails (annotate only).
  - SCIP_INSIGHT_CUTOVER=live_pulse  -> the three Live Pulse surfaces render
    live frames + blocked degrade; every other surface stays shadow.
So dropping these files in changes nothing until the env is flipped, which
should only happen after live shadow parity (Wave A) is confirmed green.

Honesty guarantees:
  - Numbers always come from governed payload["computed"]; frames only bind
    them. A frame can never introduce a number.
  - delta_sign needs a prior snapshot at payload["prior"]["computed"][metric].
    When absent (current reality), the outcome is the neutral "level" frame -
    a direction (rising/falling) is NEVER fabricated.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Formatting - identical semantics to command_centres._fmt_aed/_fmt_pct
# ---------------------------------------------------------------------------

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


def _fmt(value: Any, fmt: str) -> str:
    return _fmt_aed(value) if fmt == "aed" else _fmt_pct(value) if fmt == "pct" else str(value)


_BUCKET_CODE = {"OD_LINEAGE": "R18", "R04_LINEAGE": "R04", "R02_LINEAGE": "R02",
                "R08_LINEAGE": "R08", "R36_LINEAGE": "R36"}


# ---------------------------------------------------------------------------
# Lineage ref - identical shape to command_centres._metric_ref
# ---------------------------------------------------------------------------

def _metric_ref(metric_key: str, bucket: str, key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    lin = (payload.get("computed", {}).get(bucket, {}) or {}).get(key, {}) or {}
    return {
        "metric_key": metric_key, "lineage_bucket": bucket, "lineage_key": key,
        "has_lineage": bool(lin), "source_file": lin.get("source_file"), "sheet": lin.get("sheet"),
        "cell_or_range": lin.get("cell_or_range"), "validation_status": lin.get("validation_status"),
        "confidence_state": lin.get("confidence_state"), "reporting_basis": lin.get("reporting_basis"),
    }


_CRITICAL_BUCKETS = {"R18": "OD_LINEAGE", "R04": "R04_LINEAGE", "R02": "R02_LINEAGE",
                     "R08": "R08_LINEAGE", "R36": "R36_LINEAGE"}


def _trust_field(field: str, payload: Dict[str, Any]) -> Any:
    computed = payload.get("computed", {})
    if field == "critical_lineage_counts":
        return {k: len(computed.get(b, {}) or {}) for k, b in _CRITICAL_BUCKETS.items()}
    if field == "sources_missing":
        return payload.get("summary", {}).get("meta", {}).get("sources_missing", [])
    return None


# ---------------------------------------------------------------------------
# Value resolution
# ---------------------------------------------------------------------------

def _resolve_value(spec: Dict[str, Any], payload: Dict[str, Any]) -> Any:
    computed = payload.get("computed", {})
    v = spec["value"]; src = v["source"]
    if src == "metric":
        return computed.get(v["metric"])
    if src == "ratio_pct":
        num = computed.get(v["numerator"]) or 0
        den = computed.get(v["denominator"]) or 0
        return (num / den * 100) if den else None
    if src == "literal_none":
        return None
    if src == "trust_field":
        return _trust_field(v["field"], payload)
    return None


def _value_display(spec: Dict[str, Any], value: Any, payload: Dict[str, Any]) -> str:
    """The bare formatted number/label - equals command_centres._card display_value."""
    computed = payload.get("computed", {})
    d = spec["display"]; kind = d["kind"]
    if kind == "aed":
        return _fmt_aed(value)
    if kind == "pct":
        return _fmt_pct(value)
    if kind == "literal":
        return d["literal"]
    if kind == "raw_count":
        return str(value)
    if kind == "missing_list":
        return ", ".join(value or []) or d.get("empty_text", "None")
    if kind == "composite":
        parts = [_fmt(computed.get(p["metric"]), p["fmt"]) for p in d["parts"]]
        return d["template"].format(*parts)
    return str(value)


def _resolve_severity(spec: Dict[str, Any], value: Any) -> str:
    s = spec["severity"]
    if s["kind"] == "static":
        return s["value"]
    if s["kind"] == "threshold":
        return s["below"] if (value is not None and value < s["lt"]) else s["else"]
    return "info"


# ---------------------------------------------------------------------------
# Lineage gate - same gate quickball enforces on critical metrics
# ---------------------------------------------------------------------------

_REQUIRED_LINEAGE_FIELDS = ["source_file", "sheet", "cell_or_range", "validation_status", "confidence_state"]
_OK_VALIDATION = {"passed", "disclosed", "warning"}
_OK_CONFIDENCE = {"live_validated", "live_warning", "disclosed"}


def _gate(spec: Dict[str, Any], value: Any, refs: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """Returns (passes, blocked_reason). Standard (non-critical) specs always pass."""
    if spec.get("criticality") != "critical":
        return True, None
    for ref in refs:
        if not ref.get("has_lineage"):
            return False, f"Missing lineage for {ref['lineage_bucket']}.{ref['lineage_key']}"
        for f in _REQUIRED_LINEAGE_FIELDS:
            if ref.get(f) in (None, ""):
                return False, f"Incomplete lineage field '{f}' for {ref['metric_key']}"
        if ref.get("validation_status") not in _OK_VALIDATION:
            return False, f"Validation status is {ref.get('validation_status')} for {ref['metric_key']}"
        if ref.get("confidence_state") not in _OK_CONFIDENCE:
            return False, f"Confidence state is {ref.get('confidence_state')} for {ref['metric_key']}"
    if value is None:
        return False, "Metric value unavailable despite lineage lookup"
    return True, None


# ---------------------------------------------------------------------------
# Predicate engine (G2): a phrase is a pure function of current state
# ---------------------------------------------------------------------------

def _prior_value(spec: Dict[str, Any], payload: Dict[str, Any]) -> Any:
    metric = spec.get("data_state", {}).get("trigger", [{}])[0].get("args", {}).get("metric")
    if not metric:
        return None
    return payload.get("prior", {}).get("computed", {}).get(metric)


def _eps(spec: Dict[str, Any]) -> float:
    for s in spec.get("data_state", {}).get("suppress", []):
        if s.get("predicate") == "suppress_if_unchanged":
            return float(s.get("args", {}).get("eps", 0))
    return 0.0


def _resolve_outcome(spec: Dict[str, Any], value: Any, payload: Dict[str, Any]) -> str:
    """Maps current data state to a frame_set outcome key. delta_sign falls to
    'level' when no prior snapshot exists - never fabricates a direction."""
    if value is None:
        return "level"
    trig = (spec.get("data_state", {}).get("trigger") or [{}])[0]
    pred = trig.get("predicate")
    if pred == "threshold_cross":
        a = trig["args"]; op = a["op"]; thr = a["value"]
        hit = (value < thr) if op == "lt" else (value > thr) if op == "gt" else (value == thr)
        return a.get("true", "breach") if hit else a.get("false", "ok")
    if pred == "delta_sign":
        prior = _prior_value(spec, payload)
        if prior is None:
            return "level"
        try:
            d = float(value) - float(prior)
        except (TypeError, ValueError):
            return "level"
        if abs(d) <= _eps(spec):
            return "flat"
        return "rising" if d > 0 else "falling"
    return "level"


def _primary_source(refs: List[Dict[str, Any]]) -> str:
    if refs:
        return _BUCKET_CODE.get(refs[0].get("lineage_bucket"), refs[0].get("lineage_bucket", ""))
    return ""


# ---------------------------------------------------------------------------
# Cutover surface gate
# ---------------------------------------------------------------------------

def _cutover_mode() -> str:
    return os.environ.get("SCIP_INSIGHT_CUTOVER", "shadow").lower()


def _is_live_surface(spec: Dict[str, Any], reg: Dict[str, Any]) -> bool:
    if _cutover_mode() != "live_pulse":
        return False
    if spec.get("language_strategy") != "deterministic_frame":
        return False
    sb = spec.get("surface_binding", {})
    live = reg.get("cutover", {}).get("live_surfaces", [])
    return any(sb.get("route") == s.get("route") and sb.get("focus") == s.get("focus") for s in live)


# ---------------------------------------------------------------------------
# Compile one insight
# ---------------------------------------------------------------------------

def _compile_one(spec: Dict[str, Any], reg: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    refs = [_metric_ref(l["metric_key"], l["bucket"], l["key"], payload) for l in spec.get("lineage", [])]
    value = _resolve_value(spec, payload)
    value_display = _value_display(spec, value, payload)
    trust_state = "lineaged" if all(r.get("has_lineage") for r in refs) else "blocked_or_partial_lineage"
    passes, blocked_reason = _gate(spec, value, refs)
    target_state = "resolved" if passes else "blocked_untrusted_metric"

    base = {
        "card_id": spec["insight_id"],
        "title": spec["headline_frame"]["default"],
        "reporting_basis": spec["reporting_basis"],
        "action": spec["editorial_frame"]["default"],
        "lineage_refs": refs,
        "trust_state": trust_state,
        "criticality": spec.get("criticality"),
        "governance_state": spec.get("governance_state"),
        "surface_placement": spec.get("surface_binding"),
        "target_state": target_state,
        "blocked_reason": blocked_reason,
    }

    live = _is_live_surface(spec, reg)
    base["render_mode"] = "live" if live else "shadow"

    if not live:
        # SHADOW (Wave A parity): mirror the static card exactly.
        base.update({
            "status": "shadow",
            "headline": spec["headline_frame"]["default"],
            "value": value,
            "value_display": value_display,
            "display_value": value_display,
            "severity": _resolve_severity(spec, value),
            "outcome": None,
        })
        return base

    # LIVE (Wave B): deterministic frame + blocked degrade.
    fset = reg.get("frame_sets", {}).get(spec["frame_set"], {})
    subject = spec.get("subject", spec["headline_frame"]["default"])
    if not passes:
        headline = fset.get("blocked", "{subject} unavailable. No fallback figure published.").format(
            subject=subject, source=_primary_source(refs))
        base.update({
            "status": "blocked_untrusted_metric",
            "headline": headline,
            "value": None,
            "value_display": "Unavailable",
            "display_value": "Unavailable",
            "severity": "blocked",
            "outcome": "blocked",
        })
        return base

    outcome = _resolve_outcome(spec, value, payload)
    frame = fset.get(outcome) or fset.get("level") or "{subject}: {value} ({basis})."
    headline = frame.format(subject=subject, value=value_display, basis=spec["reporting_basis"],
                            source=_primary_source(refs))
    base.update({
        "status": "resolved",
        "headline": headline,
        "value": value,                 # number unchanged - parity preserved
        "value_display": value_display, # bare number string == old display_value
        "display_value": value_display, # frontend still gets the number on a solid surface
        "severity": _resolve_severity(spec, value),
        "outcome": outcome,
    })
    return base


# ---------------------------------------------------------------------------
# Compile set
# ---------------------------------------------------------------------------

def load_registry(registry_path: Optional[str] = None) -> Dict[str, Any]:
    path = Path(registry_path) if registry_path else Path(__file__).resolve().parent / "insight_registry.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compile_insights(payload: Dict[str, Any], registry: Optional[Dict[str, Any]] = None,
                     registry_path: Optional[str] = None) -> Dict[str, Any]:
    reg = registry or load_registry(registry_path)
    specs = reg.get("insights", [])
    by_role: Dict[str, List[Tuple[int, Dict[str, Any]]]] = {}
    for spec in specs:
        resolved = _compile_one(spec, reg, payload)
        for role in spec.get("role_visibility", []):
            by_role.setdefault(role, []).append((spec.get("surface_binding", {}).get("priority", 0), resolved))
    roles: Dict[str, List[Dict[str, Any]]] = {}
    for role, items in by_role.items():
        items.sort(key=lambda t: -t[0])
        roles[role] = [r for _, r in items]

    blocked_live = [
        {"card_id": r["card_id"], "role": role, "reason": r["blocked_reason"]}
        for role, items in roles.items() for r in items
        if r["render_mode"] == "live" and r["status"] == "blocked_untrusted_metric"
    ]
    blocked_preview = [
        {"card_id": r["card_id"], "role": role, "reason": r["blocked_reason"]}
        for role, items in roles.items() for r in items
        if r["target_state"] == "blocked_untrusted_metric"
    ]
    return {
        "status": "ok",
        "mode": _cutover_mode(),
        "registry_version": reg.get("registry_version"),
        "cutover": reg.get("cutover"),
        "roles": roles,
        "guardrails": {
            "no_silent_fallback": True,
            "critical_requires_lineage": True,
            "frames_never_originate_numbers": True,
            "delta_requires_prior_else_neutral": True,
        },
        "blocked_live": blocked_live,             # cards actually rendering blocked now
        "wave_b_blocked_preview": blocked_preview,  # all cards the strict gate would block
    }


if __name__ == "__main__":
    import sys
    payload = json.loads(Path(sys.argv[1]).read_text()) if len(sys.argv) > 1 else {}
    print(json.dumps(compile_insights(payload), indent=2, default=str))
