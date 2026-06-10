"""
SCIP smoke_insight_wave_b.py - Wave B behavior gate

Asserts:
  1. SHADOW regression: with SCIP_INSIGHT_CUTOVER=shadow the output equals Wave A
     (numbers + lineage mirror the static cards; nothing blocked-rendered).
  2. LIVE number/lineage parity: with SCIP_INSIGHT_CUTOVER=live_pulse the cutover
     Live Pulse cards keep the EXACT same number and lineage as the static cards;
     only the headline becomes a data-state frame.
  3. DATA-STATE outcomes: delta_sign yields rising/falling/flat with a prior and
     the neutral 'level' with no prior (a direction is never fabricated);
     threshold_cross yields breach/ok and reproduces the old severity ternary.
  4. BLOCKED degrade: when a critical Live Pulse source fails the gate, the card
     renders with value None, 'Unavailable', the blocked frame, and NO digit in
     the headline.

Run: python smoke_insight_wave_b.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import smoke_insight_shadow_parity as wa   # static reference + fixtures + diff
import insight_compiler                      # noqa: E402

FAILS = 0


def check(cond, msg):
    global FAILS
    if cond:
        print(f"    ok   - {msg}")
    else:
        FAILS += 1
        print(f"    FAIL - {msg}")


def reload_compiler():
    """Compiler reads SCIP_INSIGHT_CUTOVER at call time, so no reload needed; the
    function is here only to make intent explicit in the test body."""
    return insight_compiler


def card(compiled, role, cid):
    for c in compiled["roles"].get(role, []):
        if c["card_id"] == cid:
            return c
    return None


def has_financial_figure(s):
    """A leaked governed value would render as an AED amount or a percentage.
    A source identifier like 'R18' is metadata, not a value - it is allowed."""
    s = s or ""
    return ("AED" in s) or bool(re.search(r"\d+(\.\d+)?\s*%", s))


# ---------------------------------------------------------------------------
# 1. SHADOW regression == Wave A
# ---------------------------------------------------------------------------

def scenario_shadow_regression():
    print("\n=== 1. SHADOW mode regression (must equal Wave A) ===")
    os.environ["SCIP_INSIGHT_CUTOVER"] = "shadow"
    payload = wa.fixture_full()
    static = wa.static_cards_by_role(payload)
    compiled = insight_compiler.compile_insights(payload)
    issues_total = 0
    for role in static:
        s = {c["card_id"]: c for c in static[role]}
        d = {c["card_id"]: c for c in compiled["roles"].get(role, [])}
        for cid in s:
            issues = wa.diff_card(s[cid], d.get(cid, {}))
            issues_total += len(issues)
            for it in issues:
                print(f"      DIFF {role}/{cid}: {it}")
    check(issues_total == 0, "shadow output is byte-parity with static cards (all roles)")
    check(len(compiled["blocked_live"]) == 0, "no cards rendered blocked in shadow mode")
    check(all(c["render_mode"] == "shadow" for items in compiled["roles"].values() for c in items),
          "every insight render_mode == shadow")


# ---------------------------------------------------------------------------
# 2 + 3. LIVE parity + data-state outcomes (no prior)
# ---------------------------------------------------------------------------

def scenario_live_no_prior():
    print("\n=== 2/3. LIVE cutover, full load, no prior snapshot ===")
    os.environ["SCIP_INSIGHT_CUTOVER"] = "live_pulse"
    payload = wa.fixture_full()
    static = wa.static_cards_by_role(payload)
    compiled = insight_compiler.compile_insights(payload)

    # number + lineage parity for a representative cutover card
    s_od = next(c for c in static["board_cxo"] if c["card_id"] == "board_od_exposure")
    d_od = card(compiled, "board_cxo", "board_od_exposure")
    check(d_od["render_mode"] == "live", "board_od_exposure is rendered live")
    check(d_od["value"] == s_od["value"], "live OD value identical to static (number parity)")
    check(d_od["value_display"] == s_od["display_value"], "live OD value_display == static display number")
    check(d_od["lineage_refs"] == s_od["lineage_refs"], "live OD lineage identical to static")
    check(d_od["outcome"] == "level", "no prior -> neutral 'level' outcome (no fabricated direction)")
    check(d_od["value_display"] in d_od["headline"], "headline contains the governed number")
    check(d_od["severity"] == s_od["severity"], "live OD severity == static (risk)")

    # pacing threshold: full fixture is 70% -> ok / monitor
    d_pace = card(compiled, "cco_gm_agm", "ops_mtd_vs_may_target")
    check(abs(d_pace["value"] - 70.0) < 1e-6, "pacing ratio computed = 70.0% (parity with static formula)")
    check(d_pace["outcome"] == "ok", "pacing >=50 -> outcome 'ok'")
    check(d_pace["severity"] == "monitor", "pacing >=50 -> severity 'monitor' (matches old ternary)")
    check(d_pace["headline"].startswith("Pacing on track"), "pacing ok frame fired")

    # non-cutover card stays shadow with parity
    s_adv = next(c for c in static["board_cxo"] if c["card_id"] == "board_advance_mix")
    d_adv = card(compiled, "board_cxo", "board_advance_mix")
    check(d_adv["render_mode"] == "shadow", "Narratives advance-mix stays shadow in Wave B")
    check(d_adv["display_value"] == s_adv["display_value"], "advance-mix display parity preserved")


# ---------------------------------------------------------------------------
# 3b. DATA-STATE outcomes with a prior snapshot
# ---------------------------------------------------------------------------

def scenario_live_with_prior():
    print("\n=== 3b. LIVE cutover, with prior snapshot (delta directions) ===")
    os.environ["SCIP_INSIGHT_CUTOVER"] = "live_pulse"

    base = wa.fixture_full()  # OD_TODAY = 1,650,000,000

    rising = dict(base); rising["prior"] = {"computed": {"OD_TODAY": 1_500_000_000}}
    c = insight_compiler.compile_insights(rising)
    od = card(c, "board_cxo", "board_od_exposure")
    check(od["outcome"] == "rising", "prior lower -> 'rising'")
    check(od["value"] == 1_650_000_000, "rising: number still parity")
    check("risen" in od["headline"], "rising frame text fired")

    falling = dict(base); falling["prior"] = {"computed": {"OD_TODAY": 1_800_000_000}}
    od = card(insight_compiler.compile_insights(falling), "board_cxo", "board_od_exposure")
    check(od["outcome"] == "falling", "prior higher -> 'falling'")

    flat = dict(base); flat["prior"] = {"computed": {"OD_TODAY": 1_650_000_000}}
    od = card(insight_compiler.compile_insights(flat), "board_cxo", "board_od_exposure")
    check(od["outcome"] == "flat", "prior equal (within eps) -> 'flat'")


# ---------------------------------------------------------------------------
# 3c. pacing breach side
# ---------------------------------------------------------------------------

def scenario_pacing_breach():
    print("\n=== 3c. LIVE cutover, pacing breach (<50%) ===")
    os.environ["SCIP_INSIGHT_CUTOVER"] = "live_pulse"
    payload = wa.fixture_full()
    payload["computed"]["MTD_TOTAL_COLLECTIONS"] = 560_000_000  # 560/1400 = 40%
    c = insight_compiler.compile_insights(payload)
    p = card(c, "cco_gm_agm", "ops_mtd_vs_may_target")
    check(abs(p["value"] - 40.0) < 1e-6, "pacing ratio = 40.0%")
    check(p["outcome"] == "breach", "pacing <50 -> outcome 'breach'")
    check(p["severity"] == "risk", "pacing <50 -> severity 'risk' (matches old ternary)")
    check(p["headline"].startswith("Pacing risk"), "pacing breach frame fired")


# ---------------------------------------------------------------------------
# 4. BLOCKED degrade on a Live Pulse critical surface (OD source fails)
# ---------------------------------------------------------------------------

def scenario_blocked_livepulse():
    print("\n=== 4. LIVE cutover, OD source fails validation -> blocked with NO number ===")
    os.environ["SCIP_INSIGHT_CUTOVER"] = "live_pulse"
    payload = wa.fixture_full()
    # OD_TODAY lineage loaded but validation failed (value still present in computed)
    payload["computed"]["OD_LINEAGE"]["OD_TODAY"] = {
        "source_file": "R18.xlsx", "sheet": "OD", "cell_or_range": "B2",
        "validation_status": "failed", "confidence_state": "blocked_missing_fact",
        "reporting_basis": "R18 overdue"}
    c = insight_compiler.compile_insights(payload)

    for role, cid in [("board_cxo", "board_od_exposure"), ("collector_rm", "collector_od_priority")]:
        d = card(c, role, cid)
        check(d["status"] == "blocked_untrusted_metric", f"{cid}: status blocked")
        check(d["value"] is None, f"{cid}: value is None (no number)")
        check(d["value_display"] == "Unavailable", f"{cid}: display 'Unavailable'")
        check(not has_financial_figure(d["headline"]), f"{cid}: blocked headline carries NO financial figure (AED/pct)")
        check("unavailable" in d["headline"].lower(), f"{cid}: blocked frame fired")
        check(d["severity"] == "blocked", f"{cid}: severity 'blocked'")
        check(len(d["lineage_refs"]) == 1, f"{cid}: lineage ref still attached (shows why blocked)")

    # a Live Pulse card on a healthy source must still resolve with its number
    d_mtd = card(c, "board_cxo", "board_mtd_collection_progress")
    check(d_mtd["status"] == "resolved", "board_mtd still resolves (R04 healthy)")
    check(d_mtd["value"] == 980_000_000, "board_mtd number unchanged")
    check(len(c["blocked_live"]) == 2, "exactly 2 Live Pulse cards rendered blocked")


if __name__ == "__main__":
    scenario_shadow_regression()
    scenario_live_no_prior()
    scenario_live_with_prior()
    scenario_pacing_breach()
    scenario_blocked_livepulse()
    print("\n" + ("WAVE B: ALL CHECKS PASSED" if FAILS == 0 else f"WAVE B: {FAILS} CHECK(S) FAILED"))
    sys.exit(1 if FAILS else 0)
