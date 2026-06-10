"""
SCIP command_centres_v2.py - Wave D-2 cutover

Makes the Placement Binder the render source for the role command-centre cards,
replacing the hardcoded _board_cards/_ops_cards/... lists. Env-gated and default
OFF: build_command_centres uses this only when SCIP_PLACEMENT_RENDER=binder.
Until then, the legacy static path renders and this module is inert.

The card contract emitted here is byte-identical to command_centres._card, so
the frontend sees no change. Forecast cards and _ensure_batch5_card_contract are
applied by build_command_centres AFTER this returns the role cards (unchanged).

INTEGRATION (build_command_centres roles assignment):

    import os
    from command_centres_v2 import build_role_cards_from_binder
    ...
    if os.environ.get("SCIP_PLACEMENT_RENDER", "static") == "binder":
        roles = build_role_cards_from_binder(payload, trust_bar)
    else:
        roles = { ... legacy _board_cards(payload) etc ... }   # retained for rollback

ROLLBACK: SCIP_PLACEMENT_RENDER=static (instant). Legacy functions stay until
the Wave D-2 deletion step is applied (see WAVE_D2_DELETIONS.md).
"""
from __future__ import annotations

from typing import Any, Dict, List

import insight_compiler
import placement_binder
import section_rules

ROLE_ORDER = ["board_cxo", "cco_gm_agm", "finance", "mis_qcg_admin", "collector_rm"]

ROLE_LABELS = {
    "board_cxo": "Board/CXO", "cco_gm_agm": "CCO/GM/AGM", "finance": "Finance",
    "mis_qcg_admin": "MIS/QCG/Admin", "collector_rm": "Collector/RM",
}

ROLE_PURPOSES = {
    "board_cxo": "Decision clarity, source trust, cash risk, and strategic forward visibility.",
    "cco_gm_agm": "Daily operating review, intervention queue, and month-end pacing.",
    "finance": "Reconciliation, reporting-basis control, and audit traceability.",
    "mis_qcg_admin": "Data quality, source freshness, validation, and release governance.",
    "collector_rm": "Frontline action focus while avoiding unverified account-level claims.",
}


def card_from_insight(ins: Dict[str, Any]) -> Dict[str, Any]:
    """Project a resolved insight to the exact command_centres._card contract."""
    return {
        "card_id": ins["card_id"],
        "title": ins.get("title"),
        "value": ins.get("value"),
        "display_value": ins.get("display_value"),
        "reporting_basis": ins.get("reporting_basis"),
        "action": ins.get("action"),
        "severity": ins.get("severity"),
        "lineage_refs": ins.get("lineage_refs", []),
        "trust_state": ins.get("trust_state"),
    }


def build_role_cards_from_binder(payload: Dict[str, Any], trust_bar: Dict[str, Any] | None = None,
                                 compiled: Dict[str, Any] | None = None) -> Dict[str, Any]:
    compiled = compiled or insight_compiler.compile_insights(payload)
    mapping = section_rules.load_section_mapping()
    bound = placement_binder.bind_placements(compiled, mapping)

    roles: Dict[str, Any] = {}
    for role in ROLE_ORDER:
        placed: List[Dict[str, Any]] = bound["roles"].get(role, [])
        roles[role] = {
            "role_label": ROLE_LABELS[role],
            "purpose": ROLE_PURPOSES[role],
            "trust_bar": trust_bar,
            "cards": [card_from_insight(i) for i in placed],
        }
    return roles


def build_command_centres_v2(payload: Dict[str, Any], trust_bar: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Full structure (without forecast/batch5 overlay, which the caller adds)."""
    roles = build_role_cards_from_binder(payload, trust_bar)
    return {
        "status": "ok",
        "contract_version": "command_centres.v2.binder",
        "roles": roles,
        "role_order": ROLE_ORDER,
        "guardrails": {
            "no_silent_fallback": True,
            "critical_cards_require_lineage_refs": True,
            "finance_vs_mdo_label_required": True,
            "entity_head_removed": True,
            "placement_source": "registry_binder",
        },
    }
