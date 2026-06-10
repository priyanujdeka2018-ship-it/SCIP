"""
SCIP smoke_placement_wave_d1.py - Wave D-1 gate

1. PARITY: the Placement Binder reproduces the command_centres per-role card
   order and membership exactly (clean fixture -> zero violations).
2. SINGLE-SOURCE: the kept cross_section_feeds / global constants are recognised.
3. ENFORCEMENT: injected violations are rejected with the correct rule -
   CIV in S04 (R3), a third Arrival door (R1), a divergent OD_TODAY origin (R4),
   a non-existent submodule (R2), and a duplicate slot (R5).

Run: python smoke_placement_wave_d1.py
"""
from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

os.environ["SCIP_INSIGHT_CUTOVER"] = "shadow"

import smoke_insight_shadow_parity as wa
import insight_compiler
import section_rules
import placement_binder as pb

FAILS = 0


def check(cond, msg):
    global FAILS
    if cond:
        print(f"    ok   - {msg}")
    else:
        FAILS += 1
        print(f"    FAIL - {msg}")


def compiled_clean():
    return insight_compiler.compile_insights(wa.fixture_full())


# ---------------------------------------------------------------------------

def scenario_parity():
    print("\n=== 1. Placement parity vs command_centres ===")
    payload = wa.fixture_full()
    static = wa.static_cards_by_role(payload)
    mapping = section_rules.load_section_mapping()
    out = pb.bind_placements(insight_compiler.compile_insights(payload), mapping)
    order = pb.placement_order(out)
    for role in static:
        static_order = [c["card_id"] for c in static[role]]
        bound_order = order.get(role, [])
        check(static_order == bound_order, f"{role}: binder order == static order {static_order}")
    check(out["violations"] == [], "zero violations on the clean compiled set")


def scenario_single_source():
    print("\n=== 2. Single-source constants recognised ===")
    mapping = section_rules.load_section_mapping()
    ss = section_rules.single_source_constants(mapping)
    for c in ["OD_TODAY", "CY_ADV_MIX_YTD", "PIPELINE_ADV_DENOM", "MDO_targets", "DAILY_DAYS"]:
        check(c in ss, f"single-source constant recognised: {c}")


def _ins(card_id, route, focus, slot, priority, metric_key, bucket, key, submodule=None):
    return {
        "card_id": card_id,
        "lineage_refs": [{"metric_key": metric_key, "lineage_bucket": bucket, "lineage_key": key}],
        "surface_placement": {"route": route, "focus": focus, "submodule": submodule,
                              "slot": slot, "priority": priority},
    }


def _violation(out, card_id):
    for v in out["violations"]:
        if v["card_id"] == card_id:
            return " ".join(v["reasons"])
    return ""


def scenario_enforcement():
    print("\n=== 3. Rule enforcement on injected violations ===")
    mapping = section_rules.load_section_mapping()

    # R3 containment: CIV in S04
    civ = _ins("inj_civ_s04", "narratives", "portfolio", 0, 50, "CIV_OD_PCT", "R16_LINEAGE", "civ_od_pct", submodule="S04_SM2")
    # R1 third door
    door = _ins("inj_third_door", "dashboard", "home", 0, 40, "FOO", "FOO_LINEAGE", "foo")
    # R2 bad submodule
    badsm = _ins("inj_bad_submodule", "narratives", "roadmap", 1, 30, "BAR", "BAR_LINEAGE", "bar", submodule="S99_SM9")
    # R4 divergent OD_TODAY origin (two refs, different buckets)
    od_a = _ins("inj_od_a", "live_pulse", "current_signal", 0, 100, "OD_TODAY", "OD_LINEAGE", "OD_TODAY")
    od_b = _ins("inj_od_b", "live_pulse", "current_signal", 1, 99, "OD_TODAY", "BOGUS_LINEAGE", "od_today")
    # R5 duplicate slot (same route/focus/slot, same origin so no R4)
    dup_a = _ins("inj_dup_a", "live_pulse", "risk_action", 0, 80, "BAZ", "BAZ_LINEAGE", "baz")
    dup_b = _ins("inj_dup_b", "live_pulse", "risk_action", 0, 79, "BAZ", "BAZ_LINEAGE", "baz")

    compiled = {"roles": {"test_role": [civ, door, badsm, od_a, od_b, dup_a, dup_b]}}
    out = pb.bind_placements(compiled, mapping)

    check("R3" in _violation(out, "inj_civ_s04") and "S04" in _violation(out, "inj_civ_s04"),
          "CIV placed in S04 rejected (R3 containment)")
    check("R1" in _violation(out, "inj_third_door"),
          "third Arrival door rejected (R1 route)")
    check("R2" in _violation(out, "inj_bad_submodule") and "S99_SM9" in _violation(out, "inj_bad_submodule"),
          "non-existent submodule rejected (R2)")
    check("R4" in _violation(out, "inj_od_a") and "R4" in _violation(out, "inj_od_b"),
          "divergent OD_TODAY origin rejected on both refs (R4 single-source)")
    check("R5" in _violation(out, "inj_dup_b"),
          "duplicate slot rejected (R5)")
    # dup_a (first occupant) should be placed, dup_b rejected
    placed_ids = [c["card_id"] for c in out["roles"]["test_role"]]
    check("inj_dup_a" in placed_ids and "inj_dup_b" not in placed_ids,
          "first slot occupant placed, duplicate dropped")


def scenario_clean_again():
    print("\n=== 4. Clean set still binds with no violations (idempotent) ===")
    mapping = section_rules.load_section_mapping()
    out = pb.bind_placements(compiled_clean(), mapping)
    check(out["violations"] == [], "no violations on clean compiled set")
    total = sum(len(v) for v in out["roles"].values())
    check(total == 15, f"all 15 insights placed ({total})")


if __name__ == "__main__":
    scenario_parity()
    scenario_single_source()
    scenario_enforcement()
    scenario_clean_again()
    print("\n" + ("WAVE D-1: ALL CHECKS PASSED" if FAILS == 0 else f"WAVE D-1: {FAILS} CHECK(S) FAILED"))
    sys.exit(1 if FAILS else 0)
