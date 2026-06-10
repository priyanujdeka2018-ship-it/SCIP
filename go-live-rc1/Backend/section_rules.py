"""
SCIP section_rules.py - Wave D-1

Loads the kept placement rules from FINAL_section_mapping.json and exposes them
as checkable structures for the Placement Binder. Nothing here is migrated or
deleted in Wave D-1; these rules are READ and ENFORCED, not rewritten. (The
submodules[].kpis -> registry migration is Wave D-2.)

Exposed:
  - submodule_ids(mapping): the 49 valid S0X_SMy ids.
  - VALID_ROUTES: the Liquid Glass two-door Arrival surfaces (no third door).
  - single_source_constants(mapping): constants that must have ONE origin and
    never be recomputed/hardcoded per section (from cross_section_feeds +
    global_component_rules).
  - CONTAINMENT: explicit containment table grounded in boundary_rules - a
    content family and the sections it may / may not live in.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

VALID_ROUTES = {"live_pulse", "narratives"}  # two-door Arrival; no third door


def load_section_mapping(path: str | None = None) -> Dict[str, Any]:
    if path:
        p = Path(path)
    else:
        # canonical repo copy lives in ../config; same-dir copy is the packaged fallback
        here = Path(__file__).resolve().parent
        p = here.parent / "config" / "FINAL_section_mapping.json"
        if not p.exists():
            p = here / "FINAL_section_mapping.json"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def submodule_ids(mapping: Dict[str, Any]) -> Set[str]:
    return {sm["id"] for s in mapping.get("sections", []) for sm in s.get("submodules", [])}


def single_source_constants(mapping: Dict[str, Any]) -> Set[str]:
    """Constants that must originate once and be referenced, never recomputed or
    hardcoded per section. Drawn from cross_section_feeds signals and
    global_component_rules constants."""
    out: Set[str] = set()
    for feed in mapping.get("cross_section_feeds", []):
        sig = feed.get("signal")
        if sig:
            out.add(sig)
    for rule in mapping.get("global_component_rules", {}).values():
        c = rule.get("constant")
        if c:
            out.add(c)
    return out


# Containment table - EXPLICIT and grounded in FINAL_section_mapping.boundary_rules.
# A content family may live only in allowed_sections and is forbidden in
# forbidden_sections. Matched against an insight's metric keys (or declared
# family) and the section implied by its surface_binding.submodule prefix.
CONTAINMENT: List[Dict[str, Any]] = [
    {
        "family": "civ_nationality_od",
        "metric_keys": ["CIV_OD_PCT", "NATIONALITY_OD_PCT"],
        "metric_codes": ["M056", "M057"],
        "allowed_sections": ["S01"],
        "forbidden_sections": ["S04"],
        "source_rule": "boundary_rules: 'Nationality & CIV OD analysis' lives_in S01, not_in S04; S01_SM4 boundary_rule.",
    },
    {
        "family": "npv_kpis",
        "metric_keys": ["NPV_REBATE_RATE_PCT", "NPV_INCREMENTAL_INFLOW"],
        "metric_codes": ["M037", "M038"],
        "allowed_sections": ["S01"],
        "forbidden_sections": ["S05"],
        "source_rule": "boundary_rules: 'NPV KPIs 652M/21M/31M' lives_in S01, not_in S05 (advisory reference only - no re-display).",
    },
    {
        "family": "advance_3yr_monthly",
        "metric_keys": ["ADV_3YR_MONTHLY"],
        "metric_codes": [],
        "allowed_sections": ["S05"],
        "forbidden_sections": ["S01"],
        "source_rule": "boundary_rules: 'Advance 3yr monthly comparison chart' lives_in S05, not_in S01 (was c-adv-3yr, removed from v6).",
    },
]


def section_of(submodule_id: str | None) -> str | None:
    if not submodule_id or "_" not in submodule_id:
        return None
    return submodule_id.split("_", 1)[0]


def containment_violation(metric_keys: List[str], submodule_id: str | None,
                          metric_codes: List[str] | None = None,
                          section: str | None = None) -> str | None:
    """Return a violation reason if any metric family is placed in a forbidden
    section, else None. Matches by metric key OR by M-code. Section is inferred
    from the submodule id unless given explicitly (for section-level bindings)."""
    sec = section or section_of(submodule_id)
    if not sec:
        return None
    keys_upper = {k.upper() for k in (metric_keys or [])}
    codes = set(metric_codes or [])
    for rule in CONTAINMENT:
        mk = keys_upper & {k.upper() for k in rule["metric_keys"]}
        mc = codes & set(rule["metric_codes"])
        if (mk or mc) and sec in rule["forbidden_sections"]:
            matched = sorted(mk | mc)
            return (f"Containment: {matched} ({rule['family']}) placed in {sec}, "
                    f"forbidden by {rule['source_rule']}")
    return None
