"""
SCIP smoke_insight_shadow_parity.py - Wave A parity gate

Proves the registry+compiler reproduce the current command_centres batch4 static
cards EXACTLY (value, display_value, reporting_basis, severity, lineage, trust_
state, and card order per role) before any cutover. Also prints the Wave B
"would-block" preview.

By default it diffs against a faithful in-file transcription of the current
static card builders (so it runs anywhere, including here). On the live
deployment, set SCIP_USE_REAL_COMMAND_CENTRES=1 to diff against the real
command_centres module instead - that is the authoritative parity check.

Run:
    python smoke_insight_shadow_parity.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import insight_compiler  # noqa: E402


# ---------------------------------------------------------------------------
# Faithful transcription of command_centres batch4 static builders (reference)
# Source: SCIP release codebase, command_centres.py. Used only as the parity
# oracle when the real module is not importable.
# ---------------------------------------------------------------------------

def _fmt_aed(value):
    if value is None:
        return "Unavailable"
    try:
        n = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(n) >= 1_000_000_000:
        return f"AED {n / 1_000_000_000:,.3f}B"
    if abs(n) >= 1_000_000:
        return f"AED {n / 1_000_000:,.1f}M"
    return f"AED {n:,.0f}"


def _fmt_pct(value):
    if value is None:
        return "Unavailable"
    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return str(value)


def _metric_ref(metric_key, bucket, key, payload):
    lin = (payload.get("computed", {}).get(bucket, {}) or {}).get(key, {}) or {}
    return {
        "metric_key": metric_key, "lineage_bucket": bucket, "lineage_key": key,
        "has_lineage": bool(lin), "source_file": lin.get("source_file"), "sheet": lin.get("sheet"),
        "cell_or_range": lin.get("cell_or_range"), "validation_status": lin.get("validation_status"),
        "confidence_state": lin.get("confidence_state"), "reporting_basis": lin.get("reporting_basis"),
    }


def _card(card_id, title, value, display, basis, action, refs, severity="info"):
    return {
        "card_id": card_id, "title": title, "value": value, "display_value": display,
        "reporting_basis": basis, "action": action, "severity": severity, "lineage_refs": refs,
        "trust_state": "lineaged" if all(r.get("has_lineage") for r in refs) else "blocked_or_partial_lineage",
    }


def _trust(payload):
    computed = payload.get("computed", {})
    meta = payload.get("summary", {}).get("meta", {})
    buckets = {"R18": "OD_LINEAGE", "R04": "R04_LINEAGE", "R02": "R02_LINEAGE", "R08": "R08_LINEAGE", "R36": "R36_LINEAGE"}
    return {
        "critical_lineage_counts": {k: len(computed.get(b, {}) or {}) for k, b in buckets.items()},
        "sources_missing": meta.get("sources_missing", []),
    }


def static_cards_by_role(payload) -> Dict[str, List[Dict[str, Any]]]:
    c = payload.get("computed", {})
    mtd = c.get("MTD_TOTAL_COLLECTIONS") or 0
    may_target = c.get("MAY_TOTAL_COLLECTIONS_TARGET") or 0
    ach = (mtd / may_target * 100) if may_target else None
    trust = _trust(payload)
    return {
        "board_cxo": [
            _card("board_od_exposure", "Current OD exposure", c.get("OD_TODAY"), _fmt_aed(c.get("OD_TODAY")),
                  "R18 overdue", "Review Sobha/UAQ split before executive action review.",
                  [_metric_ref("OD_TODAY", "OD_LINEAGE", "OD_TODAY", payload)], "risk"),
            _card("board_mtd_collection_progress", "MTD total collections", c.get("MTD_TOTAL_COLLECTIONS"),
                  _fmt_aed(c.get("MTD_TOTAL_COLLECTIONS")), "Finance",
                  "Compare with May MDO target only with basis label visible.",
                  [_metric_ref("MTD_TOTAL_COLLECTIONS", "R04_LINEAGE", "mtd_total_collections", payload)], "monitor"),
            _card("board_advance_mix", "2026 advance mix", c.get("CY_ADV_MIX_YTD"),
                  f"CY {_fmt_pct(c.get('CY_ADV_MIX_YTD'))} / FY {_fmt_pct(c.get('FY_ADV_MIX_YTD'))}",
                  "R08 advance summary", "Use to evaluate cash pull-forward quality and future-year exposure.",
                  [_metric_ref("CY_ADV_MIX_YTD", "R08_LINEAGE", "CY_ADV_MIX_YTD", payload),
                   _metric_ref("FY_ADV_MIX_YTD", "R08_LINEAGE", "FY_ADV_MIX_YTD", payload)], "strategic"),
            _card("board_pipeline_gross", "Forward collectible calendar", c.get("PIPELINE_GROSS"),
                  _fmt_aed(c.get("PIPELINE_GROSS")), "R36 milestone cohort",
                  "Use as the 2026-onwards active forward collectible base.",
                  [_metric_ref("PIPELINE_GROSS", "R36_LINEAGE", "PIPELINE_GROSS", payload)], "strategic"),
        ],
        "cco_gm_agm": [
            _card("ops_mtd_vs_may_target", "MTD collections vs May MDO target", ach, _fmt_pct(ach),
                  "Finance actual vs MDO target", "Use as directional pacing only; keep Finance/MDO basis label visible.",
                  [_metric_ref("MTD_TOTAL_COLLECTIONS", "R04_LINEAGE", "mtd_total_collections", payload),
                   _metric_ref("MAY_TOTAL_COLLECTIONS_TARGET", "R02_LINEAGE", "may_total_collections_target_group", payload)],
                  "risk" if ach is not None and ach < 50 else "monitor"),
            _card("ops_sobha_od", "Sobha OD", c.get("OD_SOBHA"), _fmt_aed(c.get("OD_SOBHA")), "R18 overdue",
                  "Break into Sobha Dubai and Sobha AUH recovery actions.",
                  [_metric_ref("OD_SOBHA", "OD_LINEAGE", "OD_SOBHA", payload)], "risk"),
            _card("ops_uaq_od", "UAQ OD", c.get("OD_UAQ"), _fmt_aed(c.get("OD_UAQ")), "R18 overdue",
                  "Review Siniya and Downtown UAQ separately.",
                  [_metric_ref("OD_UAQ", "OD_LINEAGE", "OD_UAQ", payload)], "risk"),
            _card("ops_new_sales_collections", "MTD new-sales collections", c.get("MTD_NS_TOTAL"),
                  _fmt_aed(c.get("MTD_NS_TOTAL")), "Finance", "Escalate if new-sales conversion is below month pacing.",
                  [_metric_ref("MTD_NS_TOTAL", "R04_LINEAGE", "mtd_ns_total", payload)], "monitor"),
        ],
        "finance": [
            _card("finance_basis_control", "Finance actual vs MDO target basis", None, "Finance actuals / MDO targets",
                  "Finance + MDO", "Keep R04 actuals and R02 targets separated in all reporting.",
                  [_metric_ref("MTD_TOTAL_COLLECTIONS", "R04_LINEAGE", "mtd_total_collections", payload),
                   _metric_ref("MAY_TOTAL_COLLECTIONS_TARGET", "R02_LINEAGE", "may_total_collections_target_group", payload)],
                  "control"),
            _card("finance_r08_rebate", "YTD 2026 rebate / NPV applied", c.get("YTD_2026_REBATE"),
                  _fmt_aed(c.get("YTD_2026_REBATE")), "R08 advance summary",
                  "Use the R08 rebate lineage before reporting NPV or rebate impact.",
                  [_metric_ref("YTD_2026_REBATE", "R08_LINEAGE", "ytd_2026_rebate", payload)], "control"),
            _card("finance_r36_pipeline", "Pipeline gross source control", c.get("PIPELINE_GROSS"),
                  _fmt_aed(c.get("PIPELINE_GROSS")), "R36 milestone cohort",
                  "Use only with Active-sheet source and forward-year range disclosed.",
                  [_metric_ref("PIPELINE_GROSS", "R36_LINEAGE", "PIPELINE_GROSS", payload)], "control"),
        ],
        "mis_qcg_admin": [
            _card("mis_lineage_coverage", "Critical lineage coverage", trust.get("critical_lineage_counts"),
                  str(trust.get("critical_lineage_counts")), "Data governance",
                  "Release only when R18/R04/R02/R08/R36 lineage counts are non-zero.", [], "control"),
            _card("mis_missing_sources", "Missing sources", trust.get("sources_missing"),
                  ", ".join(trust.get("sources_missing") or []) or "None for loaded critical layer",
                  "Data governance", "Triage missing non-critical reports without blocking critical command centres.",
                  [], "monitor"),
        ],
        "collector_rm": [
            _card("collector_od_priority", "OD follow-up pool", c.get("OD_TODAY"), _fmt_aed(c.get("OD_TODAY")),
                  "R18 overdue", "Use as the verified pool for prioritisation; account-level tasking awaits lineaged account report onboarding.",
                  [_metric_ref("OD_TODAY", "OD_LINEAGE", "OD_TODAY", payload)], "risk"),
            _card("collector_daily_progress_signal", "MTD collection progress signal", c.get("MTD_TOTAL_COLLECTIONS"),
                  _fmt_aed(c.get("MTD_TOTAL_COLLECTIONS")), "Finance",
                  "Use for daily pace awareness; individual RM scorecards require R30/account-level refresh.",
                  [_metric_ref("MTD_TOTAL_COLLECTIONS", "R04_LINEAGE", "mtd_total_collections", payload)], "monitor"),
        ],
    }


def get_static(payload):
    if os.environ.get("SCIP_USE_REAL_COMMAND_CENTRES") == "1":
        import command_centres
        built = command_centres.build_command_centres(payload)
        # extract only the batch4 authored cards by the registry's known ids
        known = set()
        reg = insight_compiler.load_registry()
        for s in reg["insights"]:
            known.add(s["insight_id"])
        out = {}
        for role, rp in built.get("roles", {}).items():
            out[role] = [card for card in rp.get("cards", []) if card.get("card_id") in known]
        return out
    return static_cards_by_role(payload)


# ---------------------------------------------------------------------------
# Diff
# ---------------------------------------------------------------------------

PARITY_FIELDS = ["title", "value", "display_value", "reporting_basis", "action", "severity", "trust_state"]
LINEAGE_FIELDS = ["metric_key", "has_lineage", "source_file", "sheet", "cell_or_range",
                  "validation_status", "confidence_state", "reporting_basis"]


def _num_eq(a, b):
    if isinstance(a, float) or isinstance(b, float):
        try:
            return abs(float(a) - float(b)) < 1e-9
        except (TypeError, ValueError):
            return a == b
    return a == b


def diff_card(stat, dyn):
    issues = []
    for f in PARITY_FIELDS:
        sv, dv = stat.get(f), dyn.get(f)
        if f == "value":
            if not _num_eq(sv, dv):
                issues.append(f"value: static={sv!r} dynamic={dv!r}")
        elif sv != dv:
            issues.append(f"{f}: static={sv!r} dynamic={dv!r}")
    sr, dr = stat.get("lineage_refs", []), dyn.get("lineage_refs", [])
    if len(sr) != len(dr):
        issues.append(f"lineage_refs length: static={len(sr)} dynamic={len(dr)}")
    else:
        for i, (a, b) in enumerate(zip(sr, dr)):
            for lf in LINEAGE_FIELDS:
                if a.get(lf) != b.get(lf):
                    issues.append(f"lineage[{i}].{lf}: static={a.get(lf)!r} dynamic={b.get(lf)!r}")
    return issues


def run_scenario(name, payload):
    print(f"\n=== SCENARIO: {name} ===")
    static = get_static(payload)
    compiled = insight_compiler.compile_insights(payload)
    dyn = {role: rp for role, rp in compiled["roles"].items()}
    total, failures = 0, 0
    for role in static:
        s_cards = {c["card_id"]: c for c in static[role]}
        d_cards = {c["card_id"]: c for c in dyn.get(role, [])}
        s_order = [c["card_id"] for c in static[role]]
        d_order = [c["card_id"] for c in dyn.get(role, [])]
        if s_order != d_order:
            print(f"  [ORDER] {role}: static={s_order} dynamic={d_order}")
            failures += 1
        if set(s_cards) != set(d_cards):
            print(f"  [SET]   {role}: missing={set(s_cards) - set(d_cards)} extra={set(d_cards) - set(s_cards)}")
            failures += 1
        for cid in s_cards:
            total += 1
            if cid not in d_cards:
                continue
            issues = diff_card(s_cards[cid], d_cards[cid])
            if issues:
                failures += 1
                print(f"  [DIFF]  {role}/{cid}:")
                for it in issues:
                    print(f"            - {it}")
    status = "PARITY OK" if failures == 0 else f"PARITY FAILED ({failures} issue groups)"
    print(f"  {status}  ({total} cards compared)")
    preview = compiled["wave_b_blocked_preview"]
    if preview:
        print(f"  Wave B would block {len(preview)} card(s):")
        for p in preview:
            print(f"            - {p['role']}/{p['card_id']}: {p['reason']}")
    else:
        print("  Wave B would block 0 cards (all critical lineage gates pass).")
    return failures


# ---------------------------------------------------------------------------
# Synthetic fixtures
# ---------------------------------------------------------------------------

def _good_lin(source_file, sheet, cell, basis):
    return {"source_file": source_file, "sheet": sheet, "cell_or_range": cell,
            "validation_status": "passed", "confidence_state": "live_validated", "reporting_basis": basis}


def fixture_full():
    return {
        "summary": {"meta": {"snapshot_date": "2026-03-18", "sources_missing": []}},
        "computed": {
            "OD_TODAY": 1_650_000_000, "OD_SOBHA": 1_470_000_000, "OD_UAQ": 177_000_000,
            "MTD_TOTAL_COLLECTIONS": 980_000_000, "MTD_NS_TOTAL": 320_000_000,
            "MAY_TOTAL_COLLECTIONS_TARGET": 1_400_000_000,
            "CY_ADV_MIX_YTD": 61.4, "FY_ADV_MIX_YTD": 38.6,
            "PIPELINE_GROSS": 43_500_000_000, "YTD_2026_REBATE": 9_140_000,
            "OD_LINEAGE": {"OD_TODAY": _good_lin("R18.xlsx", "OD", "B2", "R18 overdue"),
                           "OD_SOBHA": _good_lin("R18.xlsx", "OD", "B3", "R18 overdue"),
                           "OD_UAQ": _good_lin("R18.xlsx", "OD", "B4", "R18 overdue")},
            "R04_LINEAGE": {"mtd_total_collections": _good_lin("R04.xlsx", "Daily", "C10", "Finance"),
                            "mtd_ns_total": _good_lin("R04.xlsx", "Daily", "C12", "Finance")},
            "R02_LINEAGE": {"may_total_collections_target_group": _good_lin("R02.xlsx", "Dynamic", "D5", "MDO")},
            "R08_LINEAGE": {"CY_ADV_MIX_YTD": _good_lin("R08.xlsx", "Summary", "E2", "R08 advance"),
                            "FY_ADV_MIX_YTD": _good_lin("R08.xlsx", "Summary", "E3", "R08 advance"),
                            "ytd_2026_rebate": _good_lin("R08.xlsx", "Rebate", "F9", "R08 advance")},
            "R36_LINEAGE": {"PIPELINE_GROSS": _good_lin("R36.xlsx", "Active", "G2", "R36 milestone cohort")},
        },
    }


def fixture_partial():
    """13/28-style: R36 did not resolve (bucket empty, value None); R08 rebate
    loaded but failed validation. Static still renders what it has; Wave B blocks."""
    f = fixture_full()
    f["summary"]["meta"]["sources_missing"] = ["R09", "R10", "R17", "R20", "R30", "R31", "R32", "R34", "R36", "R38"]
    f["computed"]["PIPELINE_GROSS"] = None
    f["computed"]["R36_LINEAGE"] = {}
    f["computed"]["R08_LINEAGE"]["ytd_2026_rebate"] = {
        "source_file": "R08.xlsx", "sheet": "Rebate", "cell_or_range": "F9",
        "validation_status": "stale", "confidence_state": "live_warning", "reporting_basis": "R08 advance"}
    return f


if __name__ == "__main__":
    fails = 0
    fails += run_scenario("full clean load (28/28)", fixture_full())
    fails += run_scenario("partial load (13/28-style: R36 missing, R08 rebate stale)", fixture_partial())
    print("\n" + ("ALL SCENARIOS: PARITY OK" if fails == 0 else f"PARITY REGRESSIONS: {fails}"))
    sys.exit(1 if fails else 0)
