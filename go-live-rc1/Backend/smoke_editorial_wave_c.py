"""
SCIP smoke_editorial_wave_c.py - Wave C behavior gate

Proves the constrained-LLM editorial path cannot surface an unverified number:
  1. Clean fact set + compliant model -> editorial published, validation passes.
  2. ROGUE model injects 'grew 22x' -> REJECTED, model text discarded, user sees
     the verified deterministic phrase, offending token logged.
  3. Withheld chapter (lineage not resolved) -> model is NEVER called.
  4. Provider error -> safe deterministic fallback, status 'unavailable', no crash.
  5. Validator unit checks (AED/%/x/year tokens; source codes like R18 ignored).
  6. Editorial is always criticality 'standard' (never a critical surface).

Run: python smoke_editorial_wave_c.py
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

os.environ["SCIP_INSIGHT_CUTOVER"] = "shadow"

import smoke_insight_shadow_parity as wa
import insight_compiler
import narrative_fact_builder as nfb
import constrained_editorial as ce
from editorial_token_validator import extract_number_tokens, validate_editorial

FAILS = 0


def check(cond, msg):
    global FAILS
    if cond:
        print(f"    ok   - {msg}")
    else:
        FAILS += 1
        print(f"    FAIL - {msg}")


@dataclass
class Resp:
    text: str
    provider: str = "mock"
    model: str = "mock-1"
    prompt_policy_version: str = "quickball-prompt-policy-v1"
    response_hash: str = "0" * 64
    latency_ms: int = 1


class CompliantProvider:
    """Rephrases using only the value tokens it was given."""
    def __init__(self): self.calls = 0
    def complete(self, request):
        self.calls += 1
        return Resp("Advance mix holds at CY 61.4% / FY 38.6% on the R08 basis.")


class RogueProvider:
    """Echoes real tokens but injects an unverified multiple - must be rejected."""
    def __init__(self): self.calls = 0
    def complete(self, request):
        self.calls += 1
        return Resp("CY advance mix is 61.4% / FY 38.6%, and the portfolio grew 22x year over year.")


class ErrorProvider:
    def __init__(self): self.calls = 0
    def complete(self, request):
        self.calls += 1
        raise RuntimeError("provider timeout")


class NeverCalledProvider:
    def __init__(self): self.calls = 0
    def complete(self, request):
        self.calls += 1
        return Resp("should never be produced")


def advance_factset(role="board_cxo", fixture=None):
    payload = fixture or wa.fixture_full()
    compiled = insight_compiler.compile_insights(payload)
    return nfb.build_chapter_fact_set("advance", role, compiled), compiled


# ---------------------------------------------------------------------------

def scenario_compliant():
    print("\n=== 1. Compliant model -> published editorial ===")
    fs, _ = advance_factset()
    check(fs["status"] == "ready", "advance fact set is ready (R08 resolved)")
    check(fs["value_tokens"] == ["CY 61.4% / FY 38.6%"], "value token is the governed display string")
    prov = CompliantProvider()
    r = ce.render_chapter_editorial(fs, "board_cxo", provider=prov)
    check(r["status"] == "ok", "status ok")
    check(prov.calls == 1, "provider called exactly once")
    check("61.4%" in r["editorial"] and "38.6%" in r["editorial"], "editorial carries the verified numbers")
    check(len(r["lineage_refs"]) >= 1, "lineage refs attached to editorial")
    check(r["criticality"] == "standard", "editorial criticality is standard")
    check(r["provider_metadata"]["response_hash"], "provider metadata recorded")


def scenario_rogue():
    print("\n=== 2. ROGUE model injects '22x' -> REJECTED (headline test) ===")
    fs, _ = advance_factset()
    prov = RogueProvider()
    r = ce.render_chapter_editorial(fs, "board_cxo", provider=prov)
    check(r["status"] == "rejected_unverified_token", "status rejected_unverified_token")
    check("22x" in r["rejected_tokens"], "offending token '22x' was caught")
    check("22x" not in r["editorial"] and "22×" not in r["editorial"], "rogue multiple NOT in published text")
    check("grew" not in r["editorial"], "rogue model wording discarded entirely")
    check("61.4%" in r["editorial"], "fallback still shows the verified numbers")
    check(r["language_strategy"] == "deterministic_fallback", "fell back to deterministic phrase")


def scenario_withheld():
    print("\n=== 3. Withheld chapter -> model NEVER called ===")
    fixture = wa.fixture_full()
    fixture["computed"]["CY_ADV_MIX_YTD"] = None
    fixture["computed"]["R08_LINEAGE"] = {}          # R08 did not resolve
    fs, _ = advance_factset(fixture=fixture)
    check(fs["status"] == "withheld", "advance fact set withheld (no resolved lineaged facts)")
    prov = NeverCalledProvider()
    r = ce.render_chapter_editorial(fs, "board_cxo", provider=prov)
    check(prov.calls == 0, "provider was NOT called for a withheld chapter")
    check(r["status"] == "withheld", "result status withheld")
    check("withheld" in r["editorial"].lower(), "withheld frame shown")
    check(not extract_number_tokens(r["editorial"]), "withheld frame carries no number")


def scenario_unavailable():
    print("\n=== 4. Provider error -> safe deterministic fallback ===")
    fs, _ = advance_factset()
    prov = ErrorProvider()
    r = ce.render_chapter_editorial(fs, "board_cxo", provider=prov)
    check(r["status"] == "unavailable", "status unavailable on provider error")
    check("61.4%" in r["editorial"], "fallback still shows verified numbers")
    check(r["criticality"] == "standard", "still standard criticality")


def scenario_validator_units():
    print("\n=== 5. Validator unit checks ===")
    toks = extract_number_tokens("AED 1.650B grew 22x since R18 in 2026, S05_SM2, M032")
    check("1.650b" in toks, "AED amount token extracted")
    check("22x" in toks, "multiple token extracted")
    check("2026" in toks, "standalone year extracted (must be whitelisted to use)")
    check("18" not in toks, "source code R18 NOT treated as number 18")
    check("5" not in toks and "032" not in toks, "S05_SM2 / M032 NOT treated as numbers")

    ok, off = validate_editorial("holds at CY 61.4% / FY 38.6%", ["CY 61.4% / FY 38.6%"])
    check(ok and not off, "valid when all tokens are in the whitelist")
    ok, off = validate_editorial("grew 22x", ["AED 1B"])
    check((not ok) and off == ["22x"], "invalid when a token is outside the whitelist")
    ok, off = validate_editorial("rounded to 70%", ["70.0%"])
    check(not ok, "rounding 70.0% -> 70% is rejected (no silent rounding)")


def scenario_criticality_guard():
    print("\n=== 6. Editorial is never critical ===")
    fs, _ = advance_factset()
    for prov in (CompliantProvider(), RogueProvider(), ErrorProvider()):
        r = ce.render_chapter_editorial(fs, "board_cxo", provider=prov)
        check(r["criticality"] == "standard", f"criticality standard ({prov.__class__.__name__})")


if __name__ == "__main__":
    scenario_compliant()
    scenario_rogue()
    scenario_withheld()
    scenario_unavailable()
    scenario_validator_units()
    scenario_criticality_guard()
    print("\n" + ("WAVE C: ALL CHECKS PASSED" if FAILS == 0 else f"WAVE C: {FAILS} CHECK(S) FAILED"))
    sys.exit(1 if FAILS else 0)
