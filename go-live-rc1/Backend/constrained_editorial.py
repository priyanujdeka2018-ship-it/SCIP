"""
SCIP constrained_editorial.py - Wave C

Renders a crisp Narratives editorial phrase over a VERIFIED fact set, behind the
existing Quickball provider gate, and validates the output so no unverified
number can ever surface. This is the only place the editorial LLM is used; it is
optional, bounded to Narratives, and incapable of introducing a figure.

Flow (matches the plan's constrained-LLM contract):
  withheld fact set      -> deterministic withheld frame; LLM NOT called
  provider gate blocks   -> blocked frame; LLM NOT called
  provider error         -> deterministic fallback; status "unavailable"
  LLM output fails token  -> REJECT: deterministic fallback; status "rejected_
    whitelist                unverified_token"; the LLM text is discarded & logged
  LLM output passes       -> editorial published with provider metadata + lineage

The editorial is ALWAYS criticality "standard": this path can never be used for
a critical Live Pulse surface (those use the deterministic frame path, Wave B).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from editorial_token_validator import validate_editorial

logger = logging.getLogger("scip.constrained_editorial")

try:  # real modules on the deployment take precedence
    from quickball_provider_gate import should_block_quickball_answer  # type: ignore
    from llm_providers import build_llm_request, get_llm_provider  # type: ignore
except Exception:  # local fallback for testing
    from _wave_c_shim import should_block_quickball_answer, build_llm_request, get_llm_provider


SYSTEM_CONTRACT = (
    "You are the SCIP Narratives editorial writer. You rephrase ONLY. "
    "You are given a set of verified facts, each with an exact value token. "
    "Write at most two calm, board-safe sentences. You MUST reuse every value "
    "token exactly as written. You MUST NOT introduce, infer, compute, compare, "
    "round, or estimate any number, percentage, multiple, or claim that is not "
    "present in the provided facts. Do not name source files, formulas, or "
    "owners that are not provided. If you cannot write a sentence using only the "
    "provided facts, return the facts as a plain list."
)


def _build_user_prompt(chapter: str, role: str, facts: List[Dict[str, Any]]) -> str:
    lines = [f"Chapter: {chapter}", f"Role: {role}", "Verified facts (value tokens are exact):"]
    for f in facts:
        basis = f.get("reporting_basis") or ""
        lines.append(f"  - {f['phrase_slot']}: {f['value_token']} ({basis})")
    lines.append("Write the editorial using ONLY these value tokens.")
    return "\n".join(lines)


def _deterministic_editorial(fact_set: Dict[str, Any]) -> str:
    """Safe fallback built only from verified value tokens - no model involved."""
    parts = []
    for f in fact_set["facts"]:
        label = f["phrase_slot"].replace("_", " ")
        basis = f.get("reporting_basis")
        parts.append(f"{label}: {f['value_token']}" + (f" ({basis})" if basis else ""))
    return "; ".join(parts) + "." if parts else "No verified facts available for this chapter."


def _withheld_frame(fact_set: Dict[str, Any]) -> str:
    return (
        f"The {fact_set['chapter']} narrative is withheld because the underlying "
        f"figures are not lineage-verified yet. No fallback figure is published."
    )


def _result(status: str, editorial: str, fact_set: Dict[str, Any],
            provider_metadata: Optional[Dict[str, Any]] = None,
            offending: Optional[List[str]] = None) -> Dict[str, Any]:
    return {
        "status": status,                 # ok | rejected_unverified_token | unavailable | withheld | blocked
        "criticality": "standard",        # editorial is NEVER critical
        "chapter": fact_set["chapter"],
        "role": fact_set["role"],
        "editorial": editorial,
        "language_strategy": "editorial_llm" if status == "ok" else "deterministic_fallback",
        "lineage_refs": [ref for f in fact_set["facts"] for ref in f.get("lineage_refs", [])],
        "value_tokens": fact_set["value_tokens"],
        "provider_metadata": provider_metadata,
        "rejected_tokens": offending or [],
    }


def render_chapter_editorial(fact_set: Dict[str, Any], role: str, *,
                             provider: Any = None, correlation_id: str = "wave_c") -> Dict[str, Any]:
    # 1) Withheld fact set: never call the model.
    if fact_set.get("status") != "ready":
        return _result("withheld", _withheld_frame(fact_set), fact_set)

    # 2) Provider gate. Editorial is non-critical, but we still pass a lineage
    #    presence check; a fact set with no value tokens is treated as nothing
    #    to say. (Critical lineage hard-block is enforced upstream on numbers.)
    lineage_present = {"lineage_hash": fact_set["facts"][0].get("lineage_hash")}
    blocked, reason, missing = should_block_quickball_answer(is_critical=False, lineage=lineage_present)
    if blocked:
        return _result("blocked", _deterministic_editorial(fact_set), fact_set)

    # 3) Call the constrained LLM behind the provider abstraction.
    prov = provider or get_llm_provider()
    user_prompt = _build_user_prompt(fact_set["chapter"], role, fact_set["facts"])
    request = build_llm_request(
        system_prompt=SYSTEM_CONTRACT,
        user_prompt=user_prompt,
        correlation_id=correlation_id,
        metadata={
            "chapter": fact_set["chapter"], "role": role,
            # mock provider echoes this; real providers ignore it
            "_mock_echo": _deterministic_editorial(fact_set),
        },
    )
    try:
        resp = prov.complete(request)
    except Exception as exc:  # provider outage -> safe fallback, never a stack trace
        logger.warning("editorial provider error (%s); falling back deterministically", exc)
        return _result("unavailable", _deterministic_editorial(fact_set), fact_set)

    # 4) Structural guarantee: validate the output against the whitelist.
    ok, offending = validate_editorial(resp.text, fact_set["value_tokens"])
    provider_metadata = {
        "provider": getattr(resp, "provider", None),
        "model": getattr(resp, "model", None),
        "prompt_policy_version": getattr(resp, "prompt_policy_version", None),
        "response_hash": getattr(resp, "response_hash", None),
        "latency_ms": getattr(resp, "latency_ms", None),
    }
    if not ok:
        logger.warning(
            "editorial REJECTED for chapter=%s role=%s: unverified tokens %s",
            fact_set["chapter"], role, offending,
        )
        # The model's text is discarded; user sees the verified deterministic phrase.
        return _result("rejected_unverified_token", _deterministic_editorial(fact_set),
                       fact_set, provider_metadata, offending)

    return _result("ok", resp.text.strip(), fact_set, provider_metadata)
