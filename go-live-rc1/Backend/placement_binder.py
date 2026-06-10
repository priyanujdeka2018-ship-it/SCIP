"""
SCIP placement_binder.py - Wave D-1 (shadow)

Resolves card placement from the registry surface_binding instead of the
hardcoded _board_cards/_ops_cards lists, while enforcing the kept
FINAL_section_mapping rules. In Wave D-1 this runs in SHADOW: its output is
attached alongside the live command_centres cards and diffed for placement
parity. It does not yet become the render source (that is Wave D-2).

Enforcement (rejects = not placed, logged with reason):
  R1 route        - route must be a Liquid Glass Arrival door (no third door).
  R2 submodule    - if a submodule is bound, it must exist in section_mapping.
  R3 containment  - a content family must not be placed in a forbidden section
                    (CIV stays S01 not S04; NPV not re-displayed in S05; etc.).
  R4 single-source- a single-source constant (OD_TODAY, CY_ADV_MIX_YTD, ...)
                    must resolve to ONE lineage origin across all insights -
                    never recomputed or hardcoded per section.
  R5 no-dup slot  - no two placed insights may occupy the same (role,route,
                    focus,slot).

Placement order per role = priority desc, then slot asc - which reproduces the
current command_centres per-role card order.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

import section_rules as sr

logger = logging.getLogger("scip.placement_binder")


def _origins_by_metric(insights: List[Dict[str, Any]]) -> Dict[str, set]:
    """metric_key -> set of (bucket,key) lineage origins seen across all insights."""
    origins: Dict[str, set] = {}
    for ins in insights:
        for ref in ins.get("lineage_refs", []):
            mk = ref.get("metric_key")
            if not mk:
                continue
            origins.setdefault(mk, set()).add(
                (ref.get("lineage_bucket"), ref.get("lineage_key"))
            )
    return origins


def bind_placements(compiled: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
    valid_submodules = sr.submodule_ids(mapping)
    single_source = sr.single_source_constants(mapping)

    # Flatten all insights once for the cross-cutting single-source check.
    all_insights = [c for items in compiled.get("roles", {}).values() for c in items]
    origins = _origins_by_metric(all_insights)

    # R4: any single-source constant with >1 origin is a global violation.
    multi_origin = {
        mk: sorted(f"{b}.{k}" for (b, k) in o)
        for mk, o in origins.items()
        if mk in single_source and len(o) > 1
    }

    placed_roles: Dict[str, List[Dict[str, Any]]] = {}
    violations: List[Dict[str, Any]] = []

    for role, items in compiled.get("roles", {}).items():
        candidates: List[Tuple[int, int, Dict[str, Any]]] = []
        seen_slots: set = set()
        for ins in items:
            sb = ins.get("surface_placement") or {}
            route = sb.get("route")
            focus = sb.get("focus")
            submodule = sb.get("submodule")
            slot = sb.get("slot", 0)
            priority = sb.get("priority", 0)
            metric_keys = [r.get("metric_key") for r in ins.get("lineage_refs", [])]
            reasons: List[str] = []

            # R1 route
            if route not in sr.VALID_ROUTES:
                reasons.append(f"R1 invalid route '{route}' (no third Arrival door)")
            # R2 submodule existence
            if submodule and submodule not in valid_submodules:
                reasons.append(f"R2 submodule '{submodule}' not in section_mapping")
            # R3 containment
            cv = sr.containment_violation(metric_keys, submodule)
            if cv:
                reasons.append("R3 " + cv)
            # R4 single-source (global)
            for mk in metric_keys:
                if mk in multi_origin:
                    reasons.append(f"R4 single-source '{mk}' has divergent origins {multi_origin[mk]}")
            # R5 no-duplicate slot
            slot_key = (route, focus, slot)
            if slot_key in seen_slots:
                reasons.append(f"R5 duplicate slot {slot_key} in role {role}")
            else:
                seen_slots.add(slot_key)

            if reasons:
                violations.append({"role": role, "card_id": ins.get("card_id"), "reasons": reasons})
                logger.warning("placement rejected %s/%s: %s", role, ins.get("card_id"), reasons)
                continue

            candidates.append((priority, slot, ins))

        candidates.sort(key=lambda t: (-t[0], t[1]))  # priority desc, slot asc
        placed_roles[role] = [ins for _, _, ins in candidates]

    return {
        "status": "ok",
        "mode": "shadow",
        "roles": placed_roles,
        "violations": violations,
        "single_source_constants": sorted(single_source),
        "rules_enforced": ["R1_route", "R2_submodule", "R3_containment", "R4_single_source", "R5_no_dup_slot"],
        "binder_version": "placement_binder.wave_d1",
    }


def placement_order(binder_output: Dict[str, Any]) -> Dict[str, List[str]]:
    """role -> ordered list of card_ids, for parity diffing against command_centres."""
    return {role: [c["card_id"] for c in items] for role, items in binder_output["roles"].items()}
