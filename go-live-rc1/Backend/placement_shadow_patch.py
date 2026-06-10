"""
SCIP placement_shadow_patch.py - Wave D-1 integration (read-only, reversible)

Attaches the Placement Binder output under result["placement_shadow"] without
changing the live command_centres cards or which functions produce them. Wave
D-1 only proves the binder reproduces placement and enforces the rules; the
cutover to make the binder the render source is Wave D-2.

INTEGRATION (one edit at the end of build_command_centres, after the existing
shadow/resolved hook):

    from placement_shadow_patch import attach_placement_shadow
    ...
    result = attach_shadow_insights(result, payload)        # Wave A-C hook
    return attach_placement_shadow(result, payload)         # <-- add this

ROLLBACK: delete the line, or set SCIP_PLACEMENT_SHADOW=off. The binder is never
in the critical path; any error is swallowed and the original result returned.
"""
from __future__ import annotations

import os
from typing import Any, Dict


def attach_placement_shadow(result: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    if os.environ.get("SCIP_PLACEMENT_SHADOW", "on").lower() == "off":
        return result
    try:
        import insight_compiler
        import placement_binder
        import section_rules
        compiled = result.get("resolved_insights") or insight_compiler.compile_insights(payload)
        mapping = section_rules.load_section_mapping()
        result["placement_shadow"] = placement_binder.bind_placements(compiled, mapping)
        result.setdefault("guardrails", {})["placement_shadow_attached"] = True
    except Exception as exc:  # never break live command centres
        result["placement_shadow"] = {"status": "shadow_error", "reason": str(exc)}
    return result
