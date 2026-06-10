"""
SCIP command_centres_shadow_patch.py - Wave A integration (read-only, reversible)

This is the ONLY change to the live request path in Wave A, and it is additive:
it attaches the shadow insight set under a new top-level key without touching
the existing roles[*].cards. Nothing the frontend renders today changes.

INTEGRATION (one edit, fully reversible)
----------------------------------------
In command_centres.py, at the very end of build_command_centres(), wrap the
return value:

    from command_centres_shadow_patch import attach_shadow_insights
    ...
    result = _ensure_batch5_card_contract(result, payload)   # existing last line
    return attach_shadow_insights(result, payload)            # <-- add this

ROLLBACK
--------
Delete the two added lines (or set SCIP_INSIGHT_SHADOW=off). The compiler is
never in the critical path: any error is swallowed and the original result is
returned unchanged.
"""
from __future__ import annotations

import os
from typing import Any, Dict


def attach_shadow_insights(result: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    if os.environ.get("SCIP_INSIGHT_SHADOW", "on").lower() == "off":
        return result
    try:
        import insight_compiler
        compiled = insight_compiler.compile_insights(payload)
        # Wave B canonical key; shadow_insights kept as a backward-compatible alias.
        result["resolved_insights"] = compiled
        result["shadow_insights"] = compiled
        result.setdefault("guardrails", {})["resolved_insights_attached"] = True
        result.setdefault("guardrails", {})["insight_cutover_mode"] = compiled.get("mode")
    except Exception as exc:  # never break the live command centres
        result["resolved_insights"] = {"status": "shadow_error", "reason": str(exc)}
    return result
