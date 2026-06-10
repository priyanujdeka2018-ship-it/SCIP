"""
SCIP narrative_fact_builder.py - Wave C

Assembles the frozen `verified_fact_set` that is the ONLY input the editorial
LLM ever sees. A fact is built solely from a governed insight that passed the
lineage gate (target_state == "resolved"). Numbers enter as pre-tokenized
strings (value_token = the governed value_display). The LLM cannot reach any
other number, so it cannot state one.

If a chapter has no resolved facts (e.g. its source did not load, or failed
validation), the chapter editorial is WITHHELD - the LLM is not called and no
number is published. This is the lineage gate for the editorial path.

A chapter maps to a Narratives focus: story, portfolio, dues, advance, roadmap.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List

NARRATIVE_CHAPTERS = ("story", "portfolio", "dues", "advance", "roadmap")


def _lineage_hash(refs: List[Dict[str, Any]]) -> str:
    """Deterministic lineage hash from the ref fields. In the real system this
    comes from the Batch 18 FactRecord; here it is derived stably."""
    basis = "|".join(
        f"{r.get('source_file')}:{r.get('sheet')}:{r.get('cell_or_range')}:"
        f"{r.get('validation_status')}:{r.get('confidence_state')}"
        for r in refs
    )
    return hashlib.sha256(basis.encode()).hexdigest()


def _phrase_slot(insight: Dict[str, Any]) -> str:
    return insight["card_id"]


def build_chapter_fact_set(chapter: str, role: str, compiled: Dict[str, Any]) -> Dict[str, Any]:
    """Build the verified fact set for one Narratives chapter and role."""
    facts: List[Dict[str, Any]] = []
    blocked_inputs: List[str] = []
    role_insights = (compiled.get("roles", {}) or {}).get(role, [])

    for ins in role_insights:
        sp = ins.get("surface_placement") or {}
        if sp.get("route") != "narratives" or sp.get("focus") != chapter:
            continue
        if ins.get("target_state") != "resolved":
            blocked_inputs.append(ins["card_id"])
            continue
        if ins.get("value_display") in (None, "", "Unavailable"):
            blocked_inputs.append(ins["card_id"])
            continue
        facts.append({
            "phrase_slot": _phrase_slot(ins),
            "value_token": ins["value_display"],
            "reporting_basis": ins.get("reporting_basis"),
            "lineage_hash": _lineage_hash(ins.get("lineage_refs", [])),
            "lineage_refs": ins.get("lineage_refs", []),
        })

    status = "ready" if facts else "withheld"
    return {
        "chapter": chapter,
        "role": role,
        "status": status,
        "withheld_reason": None if facts else "no_resolved_lineaged_facts_for_chapter",
        "blocked_inputs": blocked_inputs,
        "facts": facts,
        "value_tokens": [f["value_token"] for f in facts],
    }
