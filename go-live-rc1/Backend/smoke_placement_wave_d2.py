"""
SCIP smoke_placement_wave_d2.py - Wave D-2 gate

1. RENDER PARITY: build_role_cards_from_binder reproduces the static
   command_centres role cards exactly (id, value, display, basis, action,
   severity, lineage, trust_state, order) - the cutover is safe to flip.
2. CROSSWALK INTEGRITY: every asserted M-code exists in the catalog (no
   fabrication); command keys resolve; candidates are explicit.
3. MIGRATION COMPLETENESS: every section kpi M-code and metric used_in binding
   is represented in section_placement.json; nothing dropped.
4. ENFORCEMENT ON MIGRATION: every migrated submodule exists; no CIV/NPV entry
   sits in a forbidden section.

Run: python smoke_placement_wave_d2.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["SCIP_INSIGHT_CUTOVER"] = "shadow"

import smoke_insight_shadow_parity as wa
import command_centres_v2 as cc2
import section_rules

FAILS = 0


def check(cond, msg):
    global FAILS
    print(("    ok   - " if cond else "    FAIL - ") + msg)
    if not cond:
        FAILS += 1


def scenario_render_parity():
    print("\n=== 1. Render parity: binder cutover == static cards ===")
    payload = wa.fixture_full()
    static = wa.static_cards_by_role(payload)
    roles = cc2.build_role_cards_from_binder(payload)
    issues = 0
    for role in static:
        s = {c["card_id"]: c for c in static[role]}
        d = {c["card_id"]: c for c in roles[role]["cards"]}
        s_order = [c["card_id"] for c in static[role]]
        d_order = [c["card_id"] for c in roles[role]["cards"]]
        if s_order != d_order:
            print(f"      ORDER {role}: {s_order} != {d_order}"); issues += 1
        for cid in s:
            diffs = wa.diff_card(s[cid], d.get(cid, {}))
            for it in diffs:
                print(f"      DIFF {role}/{cid}: {it}"); issues += 1
    check(issues == 0, "all role cards identical to static (value, display, lineage, severity, order)")
    check(cc2.build_command_centres_v2(payload)["contract_version"] == "command_centres.v2.binder",
          "v2 contract version emitted")


def scenario_crosswalk():
    print("\n=== 2. Crosswalk integrity ===")
    xw = json.loads((HERE / "metric_crosswalk.json").read_text())
    by_mcode = xw["by_mcode"]
    bad = [(k, v["m_code"]) for k, v in xw["by_command_key"].items() if v["m_code"] and v["m_code"] not in by_mcode]
    check(not bad, "no command key asserts a non-existent M-code (fabrication guard)")
    check(set(xw["by_command_key"]) >= {
        "OD_TODAY", "MTD_TOTAL_COLLECTIONS", "CY_ADV_MIX_YTD", "FY_ADV_MIX_YTD",
        "PIPELINE_GROSS", "YTD_2026_REBATE"}, "all command-centre keys present in crosswalk")
    check(xw["by_command_key"]["CY_ADV_MIX_YTD"]["m_code"] == "M033", "CY_ADV_MIX_YTD -> M033")
    check(xw["by_command_key"]["PIPELINE_GROSS"]["m_code"] == "M005", "PIPELINE_GROSS -> M005")
    check(xw["by_command_key"]["OD_TODAY"]["status"] == "constant", "OD_TODAY flagged as R18 constant (not invented M-code)")


def scenario_completeness():
    print("\n=== 3. Migration completeness (normalized targets) ===")
    from build_d2_migration import _norm_target
    sp = json.loads((HERE / "section_placement.json").read_text())
    from build_d2_migration import _final_json
    mapping = json.loads(_final_json("FINAL_section_mapping.json").read_text())
    metrics = json.loads(_final_json("FINAL_metrics.json").read_text())

    def nk(raw, code_or_name):
        sub, sec, _ = _norm_target(raw)
        return (sub or sec or raw, code_or_name)

    placed = {(e["target"], e["m_code"] or e["metric_name"]) for e in sp["entries"]}

    kpi_keys = set()
    for s in mapping["sections"]:
        for sm in s.get("submodules", []):
            for k in sm.get("kpis", []):
                m = re.search(r"\((M\d+)\)", k)
                name = re.sub(r"\s*\(M\d+\)\s*", "", k).strip()
                kpi_keys.add(nk(sm["id"], m.group(1) if m else name))

    used_keys = set()
    for cat in metrics["categories"]:
        for met in cat["metrics"]:
            ui = list(met.get("used_in", []))
            for var in (met.get("variants") or {}).values():
                ui += var.get("used_in", [])
            for sub in ui:
                used_keys.add(nk(sub, met["id"]))

    check(kpi_keys <= placed, f"every section kpi binding migrated ({len(kpi_keys)} normalized kpi bindings)")
    check(used_keys <= placed, f"every metric used_in binding migrated ({len(used_keys)} normalized used_in bindings)")
    check(sp["count"] == len(placed), f"entry count consistent ({sp['count']})")


def scenario_enforcement_on_migration():
    print("\n=== 4. Enforcement holds on migrated placement ===")
    sp = json.loads((HERE / "section_placement.json").read_text())
    mapping = section_rules.load_section_mapping()
    valid = section_rules.submodule_ids(mapping)

    bad_sub = [e["insight_id"] for e in sp["entries"]
               if e["surface_binding"]["submodule"] and e["surface_binding"]["submodule"] not in valid]
    check(not bad_sub, "every submodule-level migrated target exists in section_mapping")

    quarantined = sp["quarantined"]
    check(quarantined == ["s05_sm4__m037"],
          "exactly the known stale binding quarantined: M037 npv_rebate bound into S05 (boundary_rules forbid)")

    civ = [e for e in sp["entries"] if e["m_code"] in ("M056", "M057")]
    check(civ and all(e["governance_state"] == "governed" for e in civ),
          "CIV (M056/M057) bindings are governed and stay in S01 (not quarantined)")

    rej = [e for e in sp["entries"] if e["governance_state"].startswith("rejected")]
    check(all(e["violations"] for e in rej), "every quarantined entry carries an explicit violation reason")


if __name__ == "__main__":
    scenario_render_parity()
    scenario_crosswalk()
    scenario_completeness()
    scenario_enforcement_on_migration()
    print("\n" + ("WAVE D-2: ALL CHECKS PASSED" if FAILS == 0 else f"WAVE D-2: {FAILS} CHECK(S) FAILED"))
    sys.exit(1 if FAILS else 0)
