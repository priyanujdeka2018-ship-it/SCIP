"""
SCIP build_d2_migration.py - Wave D-2 generator

Produces two artifacts from the REAL source files, with zero fabrication:

  metric_crosswalk.json   - metric_key <-> M-code <-> lineage <-> submodule
                            bindings. Any M-code asserted here is validated to
                            exist in FINAL_metrics.json; unknowns are marked
                            status="candidate", m_code=null (never invented).

  section_placement.json  - the submodules[].kpis (M-code -> submodule) and the
                            metrics[].used_in bindings, rewritten as registry-
                            shaped placement entries so the Placement Binder
                            becomes the single placement authority. After this,
                            the kpis/used_in fields are deprecated reference, not
                            the source of truth.

Run: python build_d2_migration.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import section_rules as sr

HERE = Path(__file__).resolve().parent


def _final_json(name: str) -> Path:
    # canonical repo copy lives in ../config; same-dir copy is the packaged fallback
    p = HERE.parent / "config" / name
    return p if p.exists() else HERE / name


METRICS = json.loads(_final_json("FINAL_metrics.json").read_text())
MAPPING = json.loads(_final_json("FINAL_section_mapping.json").read_text())

# Section -> Narratives chapter (focus), grounded in section slugs where known.
SECTION_FOCUS = {
    "S01": "story", "S05": "advance", "S08": "roadmap",
    # others left null until their chapter binding is confirmed (honest gap)
}

# Command-centre runtime keys -> lineage + best-known M-code. m_code is asserted
# ONLY where the catalog supports it; otherwise null + candidate. Grounded in the
# registry lineage refs and FINAL_metrics names/variants.
COMMAND_KEYS = {
    "OD_TODAY":                     {"bucket": "OD_LINEAGE", "key": "OD_TODAY", "m_code": None, "status": "constant", "note": "R18 global constant (cross_section_feeds OD_TODAY)"},
    "OD_SOBHA":                     {"bucket": "OD_LINEAGE", "key": "OD_SOBHA", "m_code": None, "status": "constant", "note": "R18 OD entity split (Sobha)"},
    "OD_UAQ":                       {"bucket": "OD_LINEAGE", "key": "OD_UAQ", "m_code": None, "status": "constant", "note": "R18 OD entity split (UAQ)"},
    "MTD_TOTAL_COLLECTIONS":        {"bucket": "R04_LINEAGE", "key": "mtd_total_collections", "m_code": "M009", "status": "governed", "note": "total_collections at MTD grain (R04 Finance)"},
    "MTD_NS_TOTAL":                 {"bucket": "R04_LINEAGE", "key": "mtd_ns_total", "m_code": None, "status": "candidate", "note": "MTD new-sales component (R04 Finance)"},
    "MAY_TOTAL_COLLECTIONS_TARGET": {"bucket": "R02_LINEAGE", "key": "may_total_collections_target_group", "m_code": None, "status": "candidate", "note": "R02 MDO May target"},
    "CY_ADV_MIX_YTD":               {"bucket": "R08_LINEAGE", "key": "CY_ADV_MIX_YTD", "m_code": "M033", "status": "governed", "note": "cy_advance_mix_pct global constant"},
    "FY_ADV_MIX_YTD":               {"bucket": "R08_LINEAGE", "key": "FY_ADV_MIX_YTD", "m_code": "M034", "status": "governed", "note": "fy_advance_mix_pct"},
    "PIPELINE_GROSS":               {"bucket": "R36_LINEAGE", "key": "PIPELINE_GROSS", "m_code": "M005", "status": "governed", "note": "future_milestone_pipeline variant PIPELINE_GROSS (43.5B)"},
    "YTD_2026_REBATE":              {"bucket": "R08_LINEAGE", "key": "ytd_2026_rebate", "m_code": None, "status": "candidate", "note": "R08 YTD rebate AED (no single M-code yet)"},
}


def catalog_index():
    idx = {}
    for cat in METRICS["categories"]:
        for met in cat["metrics"]:
            used_in = list(met.get("used_in", []))
            for var in (met.get("variants") or {}).values():
                used_in += var.get("used_in", [])
            idx[met["id"]] = {
                "name": met.get("name"), "label": met.get("label"),
                "sources": met.get("sources", []), "used_in": sorted(set(used_in)),
            }
    return idx


def parse_kpi_bindings():
    out = []
    for s in MAPPING["sections"]:
        for sm in s.get("submodules", []):
            for k in sm.get("kpis", []):
                m = re.search(r"\((M\d+)\)", k)
                name = re.sub(r"\s*\(M\d+\)\s*", "", k).strip()
                out.append({"submodule": sm["id"], "section": s["id"],
                            "m_code": m.group(1) if m else None, "name": name})
    return out


def build_crosswalk(idx):
    # validate every asserted command-key m_code exists in the catalog
    bad = [(k, v["m_code"]) for k, v in COMMAND_KEYS.items() if v["m_code"] and v["m_code"] not in idx]
    if bad:
        raise SystemExit(f"FABRICATION GUARD: asserted M-codes not in catalog: {bad}")
    kpi_bindings = parse_kpi_bindings()
    return {
        "generated_from": ["FINAL_metrics.json", "FINAL_section_mapping.json"],
        "fabrication_guard": "every non-null m_code validated against FINAL_metrics.json",
        "by_command_key": COMMAND_KEYS,
        "by_mcode": idx,
        "kpi_bindings": kpi_bindings,
        "command_keys_with_mcode": sorted(k for k, v in COMMAND_KEYS.items() if v["m_code"]),
        "command_keys_candidate": sorted(k for k, v in COMMAND_KEYS.items() if not v["m_code"]),
    }


def _norm_target(raw: str):
    """Normalize a used_in/kpi target. Returns (submodule_or_None, section, kind)."""
    s = re.sub(r"\s*\(.*?\)\s*", "", raw or "").strip()  # strip '(strategic)' etc.
    if re.fullmatch(r"S\d+_SM\d+", s):
        return s, s.split("_", 1)[0], "submodule"
    if re.fullmatch(r"S\d+", s):
        return None, s, "section"
    return None, None, "malformed"


def build_section_placement(idx):
    """Rewrite kpis + used_in bindings as registry-shaped placement entries.
    Normalizes dirty targets and quarantines boundary violations."""
    valid_subs = sr.submodule_ids(MAPPING)
    entries = []
    seen = set()

    def add(raw_target, m_code, name, origin):
        submodule, section, kind = _norm_target(raw_target)
        target = submodule or section or raw_target
        key = (target, m_code or name)
        if key in seen:
            return
        seen.add(key)
        reasons = []
        if kind == "malformed":
            reasons.append(f"malformed placement target '{raw_target}'")
        if submodule and submodule not in valid_subs:
            reasons.append(f"submodule '{submodule}' not in section_mapping")
        cv = sr.containment_violation([name or ""], submodule, metric_codes=[m_code] if m_code else None, section=section)
        if cv:
            reasons.append(cv)
        governed = bool(m_code and idx.get(m_code, {}).get("sources"))
        gov_state = "rejected_boundary" if cv else ("rejected_invalid" if reasons else ("governed" if governed else "candidate"))
        entries.append({
            "insight_id": f"{(submodule or section or 'na').lower()}__{(m_code or name).lower().replace(' ', '_')}",
            "m_code": m_code,
            "metric_name": name or (idx.get(m_code, {}).get("name")),
            "target": target,
            "surface_binding": {
                "route": "narratives",
                "focus": SECTION_FOCUS.get(section),
                "submodule": submodule,
                "section": section,
                "slot": None, "priority": None,
            },
            "governance_state": gov_state,
            "violations": reasons,
            "origin": origin,
        })

    for b in parse_kpi_bindings():
        add(b["submodule"], b["m_code"], b["name"], "section_kpis")
    for m_code, info in idx.items():
        for sub in info["used_in"]:
            add(sub, m_code, info["name"], "metric_used_in")

    by_state = {}
    for e in entries:
        by_state[e["governance_state"]] = by_state.get(e["governance_state"], 0) + 1
    return {
        "generated_from": ["FINAL_section_mapping.json:submodules[].kpis", "FINAL_metrics.json:metrics[].used_in"],
        "note": "Registry-shaped placement migrated from kpis/used_in. Targets normalized; boundary violations quarantined as rejected_boundary. After cutover these fields are deprecated reference, not authority.",
        "entries": entries,
        "count": len(entries),
        "by_state": by_state,
        "quarantined": [e["insight_id"] for e in entries if e["governance_state"].startswith("rejected")],
    }


def main():
    idx = catalog_index()
    crosswalk = build_crosswalk(idx)
    placement = build_section_placement(idx)
    (HERE / "metric_crosswalk.json").write_text(json.dumps(crosswalk, indent=2))
    (HERE / "section_placement.json").write_text(json.dumps(placement, indent=2))

    # completeness on NORMALIZED targets (so 'S02_SM2 (strategic)' == 'S02_SM2')
    def norm_key(raw, code_or_name):
        sub, sec, _ = _norm_target(raw)
        return (sub or sec or raw, code_or_name)

    kpi_keys = {norm_key(b["submodule"], b["m_code"] or b["name"]) for b in crosswalk["kpi_bindings"]}
    used_keys = {norm_key(sub, mc) for mc, info in idx.items() for sub in info["used_in"]}
    placed_keys = {(e["target"], e["m_code"] or e["metric_name"]) for e in placement["entries"]}
    missing = (kpi_keys | used_keys) - placed_keys

    print(f"crosswalk: {len(crosswalk['by_mcode'])} M-codes, "
          f"{len(crosswalk['command_keys_with_mcode'])} command keys mapped, "
          f"{len(crosswalk['command_keys_candidate'])} candidate")
    print(f"section_placement: {placement['count']} entries; states={placement['by_state']}")
    print(f"quarantined (boundary/invalid): {placement['quarantined']}")
    print(f"completeness: missing bindings={len(missing)}")
    if missing:
        print("  MISSING:", sorted(missing)[:10])
        raise SystemExit("MIGRATION INCOMPLETE")
    print("OK: every kpi and used_in binding migrated (normalized); no fabricated M-codes")


if __name__ == "__main__":
    main()
