"""
SOBHA COLLECTIONS INTELLIGENCE PLATFORM
data_loader.py — R-Series Data Pipeline
Version: v6
Authority: FINAL_ARCHITECTURE.md

Responsibilities:
  - Read all active R-series xlsx files from /data directory
  - Apply column mappings from pipeline_config.json
  - Compute all derived constants (OD_TODAY, PIPELINE_GROSS, etc.)
  - Return { "dataframes": dict, "computed": dict }
  - Pre-aggregate lean summary JSON for frontend (~100KB)
  - Graceful degradation on missing or malformed files
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, date
from pathlib import Path
from typing import Any, Optional

import openpyxl

import constants as C
import utils as U

logger = logging.getLogger(__name__)

_HERE = Path(__file__).parent
DATA_DIR = (_HERE.parent / "data").resolve()
PIPELINE_CONFIG_PATH = (_HERE / "pipeline_config.json").resolve()


# ---------------------------------------------------------------------------
# SECTION 1 — CONFIG LOADER
# ---------------------------------------------------------------------------

def _load_pipeline_config() -> dict:
    with open(PIPELINE_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# SECTION 2 — OPENPYXL SHEET READER
# ---------------------------------------------------------------------------

def _read_sheet(file_path: Path, sheet_name: Any) -> Optional[list[dict]]:
    try:
        wb = openpyxl.load_workbook(str(file_path), read_only=True, data_only=True)
        if isinstance(sheet_name, int):
            ws = wb.worksheets[sheet_name]
        elif isinstance(sheet_name, str):
            if sheet_name not in wb.sheetnames:
                logger.warning("Sheet '%s' not found in %s. Available: %s",
                               sheet_name, file_path.name, wb.sheetnames)
                wb.close()
                return None
            ws = wb[sheet_name]
        else:
            ws = wb.active

        rows = list(ws.iter_rows(values_only=True))
        wb.close()

        if not rows:
            return []

        headers = [str(h).strip() if h is not None else f"col_{i}"
                   for i, h in enumerate(rows[0])]
        result = []
        for row in rows[1:]:
            if all(v is None for v in row):
                continue
            result.append(dict(zip(headers, row)))
        return result

    except FileNotFoundError:
        logger.info("File not found (graceful skip): %s", file_path.name)
        return None
    except Exception as exc:
        logger.warning("Failed to read %s sheet=%s: %s", file_path.name, sheet_name, exc)
        return None


# ---------------------------------------------------------------------------
# SECTION 3 — COLUMN MAPPER & TYPE COERCER
# ---------------------------------------------------------------------------

def _apply_column_map(rows: list[dict], col_map: dict, col_types: dict) -> list[dict]:
    mapped = []
    for row in rows:
        new_row: dict = {}
        for src_col, dest_col in col_map.items():
            raw = row.get(src_col)
            coerced = _coerce(raw, col_types.get(dest_col, "str"))
            new_row[dest_col] = coerced
        if any(v is not None for v in new_row.values()):
            mapped.append(new_row)
    return mapped


def _coerce(value: Any, type_str: str) -> Any:
    if value is None:
        return None
    try:
        if type_str == "int":
            return int(float(value))
        if type_str == "float":
            return float(value)
        if type_str == "bool":
            if isinstance(value, bool):
                return value
            return str(value).strip().lower() in ("true", "yes", "1")
        if type_str == "datetime":
            if isinstance(value, (datetime, date)):
                return value
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d %b %Y"):
                try:
                    return datetime.strptime(str(value).strip(), fmt)
                except ValueError:
                    continue
            return None
        return str(value).strip() if value is not None else None
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# SECTION 4 — AGGREGATION ENGINE
# ---------------------------------------------------------------------------

def _run_aggregations(rows: list[dict], agg_cfg: dict) -> dict:
    results: dict = {}

    for agg_name, agg_def in agg_cfg.items():
        op = agg_def.get("op")
        col = agg_def.get("col")
        filt = agg_def.get("filter", {})

        try:
            filtered = _filter_rows(rows, filt) if filt else rows

            if op == "sum":
                results[agg_name] = _safe_sum(filtered, col)
            elif op == "filter_sum":
                results[agg_name] = _safe_sum(filtered, col)
            elif op == "mean":
                vals = [r[col] for r in filtered if r.get(col) is not None]
                results[agg_name] = sum(vals) / len(vals) if vals else None
            elif op == "filter_mean":
                vals = [r[col] for r in filtered if r.get(col) is not None]
                results[agg_name] = sum(vals) / len(vals) if vals else None
            elif op in ("filter_count", "count_filter"):
                results[agg_name] = sum(1 for r in filtered if r.get(col) is not None)
            elif op == "last":
                vals = [r[col] for r in filtered if r.get(col) is not None]
                results[agg_name] = vals[-1] if vals else None
            elif op == "extract_list":
                fmt = agg_def.get("format", "raw")
                vals = []
                for r in filtered:
                    v = r.get(col)
                    if v is None:
                        continue
                    if fmt == "DD MMM" and isinstance(v, (datetime, date)):
                        vals.append(v.strftime("%d %b"))
                    else:
                        vals.append(v)
                results[agg_name] = vals
            elif op == "weighted_avg":
                num_col = agg_def.get("numerator")
                den_col = agg_def.get("denominator")
                multiply = agg_def.get("multiply_100", False)
                total_num = _safe_sum(filtered, num_col)
                total_den = _safe_sum(filtered, den_col)
                if total_den and total_den > 0:
                    ratio = total_num / total_den
                    results[agg_name] = ratio * 100 if multiply else ratio
                else:
                    results[agg_name] = None
            elif op == "derived":
                results[agg_name] = {"__deferred__": agg_def.get("formula")}
            elif op == "read_metadata":
                results[agg_name] = {"__metadata__": agg_def.get("field")}
            elif op == "read_header_cell":
                results[agg_name] = {"__metadata__": "snapshot_date"}

        except Exception as exc:
            logger.warning("Aggregation '%s' failed: %s", agg_name, exc)
            results[agg_name] = None

    return results


def _filter_rows(rows: list[dict], filt: dict) -> list[dict]:
    result = []
    for row in rows:
        match = True
        for key, val in filt.items():
            if key == "entity_section":
                entity = row.get("entity", "")
                section_map = {
                    "A-E": lambda e: str(e).strip().upper() in ("A","B","C","D","E","SOBHA"),
                    "F":   lambda e: str(e).strip().upper() in ("F","SINIYA"),
                    "G":   lambda e: str(e).strip().upper() in ("G","DT","DOWNTOWN"),
                }
                checker = section_map.get(val)
                if checker and not checker(entity):
                    match = False
            elif key.endswith("_in"):
                col = key[:-3]
                cell = row.get(col)
                if cell is None:
                    match = False
                else:
                    cell_str = str(cell)[:7]
                    if cell_str not in [str(v)[:7] for v in val]:
                        match = False
            elif key.endswith("_ne"):
                col = key[:-3]
                cell = row.get(col)
                if cell is not None and str(cell).strip().lower() == str(val).lower():
                    match = False
            elif key == "year":
                for yr_col in ("year", "month", "collection_date", "acd_year"):
                    cell = row.get(yr_col)
                    if cell is not None:
                        extracted = _extract_year(cell)
                        if extracted is not None and extracted != int(val):
                            match = False
                        break
            else:
                cell = row.get(key)
                if cell is None:
                    match = False
                elif str(cell).strip().lower() != str(val).strip().lower():
                    match = False
        if match:
            result.append(row)
    return result


def _extract_year(value: Any) -> Optional[int]:
    if isinstance(value, (datetime, date)):
        return value.year
    if isinstance(value, int):
        return value if 2000 <= value <= 2100 else None
    try:
        s = str(value)
        if len(s) >= 4:
            yr = int(s[:4])
            if 2000 <= yr <= 2100:
                return yr
    except (ValueError, TypeError):
        pass
    return None


def _safe_sum(rows: list[dict], col: str) -> float:
    return sum(r[col] for r in rows if r.get(col) is not None)


# ---------------------------------------------------------------------------
# SECTION 5 — SINGLE SOURCE LOADER
# ---------------------------------------------------------------------------

def _load_source(source_id: str, source_cfg: dict, data_dir: Path) -> dict:
    fname = source_cfg["file"]
    candidates = [data_dir / fname, data_dir / fname.lower(), data_dir / fname.upper()]
    file_path = next((p for p in candidates if p.exists()), data_dir / fname)
    sheet_name = source_cfg.get("sheet_name", 0)
    col_map = source_cfg.get("column_map", {})
    col_types = source_cfg.get("column_types", {})
    agg_cfg = source_cfg.get("aggregations", {})

    raw_rows = _read_sheet(file_path, sheet_name)

    if raw_rows is None:
        logger.info("Source %s not available — graceful degradation", source_id)
        return {
            "id": source_id,
            "status": "missing",
            "rows": [],
            "aggs": {},
            "data_date": source_cfg.get("data_date", None),
        }

    mapped_rows = _apply_column_map(raw_rows, col_map, col_types) if col_map else []

    fixed_entity = source_cfg.get("fixed_entity")
    if fixed_entity:
        for row in mapped_rows:
            row["entity"] = fixed_entity

    post_load = source_cfg.get("post_load", {})
    if "sort" in post_load:
        sort_col = post_load["sort"]["col"]
        sort_desc = post_load["sort"]["order"] == "desc"
        mapped_rows.sort(
            key=lambda r: r.get(sort_col) if r.get(sort_col) is not None else -999,
            reverse=sort_desc,
        )

    aggs = _run_aggregations(mapped_rows, agg_cfg)
    data_date = source_cfg.get("data_date")

    return {
        "id": source_id,
        "status": "ok",
        "rows": mapped_rows,
        "aggs": aggs,
        "data_date": data_date,
    }


# ---------------------------------------------------------------------------
# SECTION 6 — DERIVED CONSTANT RESOLVER
# ---------------------------------------------------------------------------

def _resolve_derived_constants(computed: dict) -> dict:
    pg = computed.get("PIPELINE_GROSS")
    if pg is not None:
        computed["PIPELINE_ADV_DENOM"] = pg - C.PIPELINE_ADV_DENOM_OFFSET_AED

    computed["PIPELINE_FORWARD_BOOK"] = 40_000_000_000
    return computed


# ---------------------------------------------------------------------------
# SECTION 7 — COMPUTED DICT BUILDER
# ---------------------------------------------------------------------------

def _build_computed(sources: dict) -> dict:
    computed: dict = {}

    # R18: OD constants
    r18 = sources.get("R18", {})
    r18_aggs = r18.get("aggs", {})
    computed["OD_TODAY"]  = r18_aggs.get("OD_TODAY")
    computed["OD_SOBHA"]  = r18_aggs.get("OD_SOBHA")
    computed["OD_SINIYA"] = r18_aggs.get("OD_SINIYA")
    computed["OD_DT"]     = r18_aggs.get("OD_DT")

    if computed["OD_TODAY"] is None:
        computed["OD_TODAY"]  = sum(C.OD_AGEING_REF_AED.values())
        computed["OD_SOBHA"]  = 1_472_700_000
        computed["OD_SINIYA"] = 166_400_000
        computed["OD_DT"]     = 11_000_000
        computed["OD_SOURCE"] = "fallback_reference"
        logger.warning("R18 unavailable — OD constants using reference fallback values")
    else:
        computed["OD_SOURCE"] = "R18_live"

    computed["SNAPSHOT_DATE"] = r18.get("data_date") or "2026-03-15"
    computed["OD_AGEING"] = {
        "0-30d":    r18_aggs.get("ageing_0_30"),
        "31-60d":   r18_aggs.get("ageing_31_60"),
        "61-90d":   r18_aggs.get("ageing_61_90"),
        "91-120d":  r18_aggs.get("ageing_91_120"),
        "121-180d": r18_aggs.get("ageing_121_180"),
        "180+d":    r18_aggs.get("ageing_180plus"),
    }
    for band, ref_key in [
        ("0-30d", "0–30d"), ("31-60d", "31–60d"), ("61-90d", "61–90d"),
        ("91-120d", "91–120d"), ("121-180d", "121–180d"), ("180+d", "180d+")
    ]:
        if computed["OD_AGEING"][band] is None:
            computed["OD_AGEING"][band] = C.OD_AGEING_REF_AED.get(ref_key)

    # R36: Pipeline constants
    r36 = sources.get("R36", {})
    r36_aggs = r36.get("aggs", {})
    computed["PIPELINE_GROSS"] = r36_aggs.get("PIPELINE_GROSS")
    if computed["PIPELINE_GROSS"] is None:
        computed["PIPELINE_GROSS"] = 43_500_000_000
        computed["PIPELINE_SOURCE"] = "fallback_reference"
    else:
        computed["PIPELINE_SOURCE"] = "R36_live"

    computed["PIPELINE_GROSS_LABEL"]        = C.PIPELINE_GROSS_LABEL
    computed["PIPELINE_ADV_DENOM_LABEL"]    = C.PIPELINE_ADV_DENOM_LABEL
    computed["PIPELINE_FORWARD_BOOK_LABEL"] = C.PIPELINE_FORWARD_BOOK_LABEL

    # R08: Advance constants
    r08 = sources.get("R08", {})
    r08_aggs = r08.get("aggs", {})
    computed["CY_ADV_MIX_YTD"] = r08_aggs.get("CY_ADV_MIX_YTD")
    if computed["CY_ADV_MIX_YTD"] is None:
        computed["CY_ADV_MIX_YTD"] = 81.1
    computed["AVG_ADVANCE_LEAD_DAYS"] = r08_aggs.get("AVG_ADVANCE_LEAD_DAYS") or C.AVG_ADVANCE_LEAD_DAYS
    computed["ADVANCE_2025_TOTAL"]    = r08_aggs.get("advance_2025_total")
    computed["YTD_2026_REBATE"]       = r08_aggs.get("ytd_2026_rebate")
    computed["YTD_2026_ADVANCE"]      = r08_aggs.get("ytd_2026_advance")

    # R04: Daily arrays
    r04 = sources.get("R04", {})
    r04_aggs = r04.get("aggs", {})
    computed["DAILY_DAYS"]    = r04_aggs.get("DAILY_DAYS") or []
    computed["MTD_DA_TOTAL"]  = r04_aggs.get("mtd_da_total")
    computed["MTD_DUES_TOTAL"]= r04_aggs.get("mtd_dues_total")
    computed["MTD_ADV_TOTAL"] = r04_aggs.get("mtd_advance_total")
    computed["MTD_NS_TOTAL"]  = r04_aggs.get("mtd_ns_total")

    # R02: MDO targets
    r02 = sources.get("R02", {})
    r02_aggs = r02.get("aggs", {})
    computed["FY_DUES_TARGET"] = r02_aggs.get("fy_dues_target_group") or C.MDO_DUES_FY_2026_AED
    computed["FY_ADV_TARGET"]  = r02_aggs.get("fy_advance_target_group") or C.MDO_ADV_FY_2026_AED
    computed["Q1_DUES_ACTUAL"] = r02_aggs.get("q1_dues_actual_group")
    computed["Q1_ADV_ACTUAL"]  = r02_aggs.get("q1_advance_actual_group")

    # R13: ITD portfolio
    r13 = sources.get("R13", {})
    r13_aggs = r13.get("aggs", {})
    computed["GROUP_SALE_VALUE_ITD"] = r13_aggs.get("group_sale_value_itd") or C.GROUP_SALE_VALUE_ITD_AED
    computed["GROUP_COLLECTED_ITD"]  = r13_aggs.get("group_collected_itd") or C.GROUP_COLLECTED_ITD_AED

    # R10: Coverage
    r10 = sources.get("R10", {})
    r10_aggs = r10.get("aggs", {})
    computed["SINIYA_UNWORKED_POOL"] = r10_aggs.get("siniya_unworked_pool_aed") or C.SINIYA_UNWORKED_POOL_AED

    # R30: Collector metrics
    r30 = sources.get("R30", {})
    r30_aggs = r30.get("aggs", {})
    computed["COLLECTOR_TEAM_AVG_ACH"] = r30_aggs.get("team_avg_achievement")
    computed["COLLECTOR_TOTAL_ACTUAL"] = r30_aggs.get("total_actual")
    computed["COLLECTOR_TOTAL_TARGET"] = r30_aggs.get("total_target")

    # R26: LP / charges
    r26 = sources.get("R26", {})
    r26_aggs = r26.get("aggs", {})
    computed["LP_2021"]      = r26_aggs.get("lp_2021")
    computed["LP_2025"]      = r26_aggs.get("lp_2025")
    computed["DLD_2026_YTD"] = r26_aggs.get("dld_2026_ytd")

    # R34: Termination gap
    r34 = sources.get("R34", {})
    r34_aggs = r34.get("aggs", {})
    computed["TERM_NOT_IN_SYSTEM"] = r34_aggs.get("latest_not_in_system") or C.TERMINATION_GAP_UNITS
    computed["TERM_GAP_EXPOSURE"]  = r34_aggs.get("latest_gap_exposure") or C.TERMINATION_GAP_EXPOSURE_AED

    # R38: Risk / IC threshold
    r38 = sources.get("R38", {})
    r38_aggs = r38.get("aggs", {})
    computed["IC_BAND_0_10_UNITS"]    = r38_aggs.get("ic_band_0_10_units") or C.IC_THRESHOLD_UNITS
    computed["IC_BAND_0_10_EXPOSURE"] = r38_aggs.get("ic_band_0_10_exposure") or C.IC_THRESHOLD_EXPOSURE_AED

    computed = _resolve_derived_constants(computed)
    computed["LOAD_TIMESTAMP"]  = datetime.utcnow().isoformat()
    computed["PLATFORM_VERSION"] = C.PLATFORM_VERSION

    return computed


# ---------------------------------------------------------------------------
# SECTION 8 — LEAN SUMMARY BUILDER
# ---------------------------------------------------------------------------

def _build_collector_summary(sources: dict) -> dict:
    r30 = sources.get("R30", {})
    rows = r30.get("rows", [])
    if not rows:
        return {"top": [], "bottom": [], "count": C.COLLECTOR_COUNT}

    formatted = [
        {
            "name":           r.get("collector_name"),
            "achievement_pct": r.get("achievement_pct"),
            "actual_aed":     r.get("actual_aed"),
            "target_aed":     r.get("target_aed"),
        }
        for r in rows if r.get("collector_name")
    ]
    return {
        "top":    formatted[:3],
        "bottom": formatted[-3:] if len(formatted) >= 3 else formatted,
        "count":  len(formatted),
        "data_currency": C.SNAPSHOT_LABEL,
    }


def _build_summary(sources: dict, computed: dict) -> dict:
    return {
        "meta": {
            "snapshot_date":   computed.get("SNAPSHOT_DATE"),
            "load_timestamp":  computed.get("LOAD_TIMESTAMP"),
            "platform_version": computed.get("PLATFORM_VERSION"),
            "sources_loaded":  [rid for rid, s in sources.items() if s.get("status") == "ok"],
            "sources_missing": [rid for rid, s in sources.items() if s.get("status") == "missing"],
        },
        "portfolio": {
            "group_sale_value_itd":    computed.get("GROUP_SALE_VALUE_ITD"),
            "group_collected_itd":     computed.get("GROUP_COLLECTED_ITD"),
            "group_collected_itd_pct": U.safe_divide(
                computed.get("GROUP_COLLECTED_ITD") or 0,
                computed.get("GROUP_SALE_VALUE_ITD") or 1
            ) * 100,
            "od_today":  computed.get("OD_TODAY"),
            "od_sobha":  computed.get("OD_SOBHA"),
            "od_siniya": computed.get("OD_SINIYA"),
            "od_dt":     computed.get("OD_DT"),
            "od_source": computed.get("OD_SOURCE"),
            "od_ageing": computed.get("OD_AGEING"),
            "pipeline_gross":           computed.get("PIPELINE_GROSS"),
            "pipeline_gross_label":     computed.get("PIPELINE_GROSS_LABEL"),
            "pipeline_adv_denom":       computed.get("PIPELINE_ADV_DENOM"),
            "pipeline_adv_denom_label": computed.get("PIPELINE_ADV_DENOM_LABEL"),
            "pipeline_forward_book":       computed.get("PIPELINE_FORWARD_BOOK"),
            "pipeline_forward_book_label": computed.get("PIPELINE_FORWARD_BOOK_LABEL"),
        },
        "advance": {
            "cy_adv_mix_ytd":        computed.get("CY_ADV_MIX_YTD"),
            "avg_advance_lead_days": computed.get("AVG_ADVANCE_LEAD_DAYS"),
            "advance_2025_total":    computed.get("ADVANCE_2025_TOTAL"),
            "ytd_2026_rebate":       computed.get("YTD_2026_REBATE"),
            "ytd_2026_advance":      computed.get("YTD_2026_ADVANCE"),
        },
        "targets": {
            "fy_dues_target": computed.get("FY_DUES_TARGET"),
            "fy_adv_target":  computed.get("FY_ADV_TARGET"),
            "q1_dues_actual": computed.get("Q1_DUES_ACTUAL"),
            "q1_adv_actual":  computed.get("Q1_ADV_ACTUAL"),
        },
        "daily": {
            "days":        computed.get("DAILY_DAYS"),
            "mtd_da":      computed.get("MTD_DA_TOTAL"),
            "mtd_dues":    computed.get("MTD_DUES_TOTAL"),
            "mtd_advance": computed.get("MTD_ADV_TOTAL"),
            "mtd_ns":      computed.get("MTD_NS_TOTAL"),
        },
        "ops": {
            "collector_team_avg_ach": computed.get("COLLECTOR_TEAM_AVG_ACH"),
            "siniya_unworked_pool":   computed.get("SINIYA_UNWORKED_POOL"),
            "term_not_in_system":     computed.get("TERM_NOT_IN_SYSTEM"),
            "term_gap_exposure":      computed.get("TERM_GAP_EXPOSURE"),
            "ic_band_0_10_units":     computed.get("IC_BAND_0_10_UNITS"),
            "ic_band_0_10_exposure":  computed.get("IC_BAND_0_10_EXPOSURE"),
        },
        "charges": {
            "lp_2021":      computed.get("LP_2021"),
            "lp_2025":      computed.get("LP_2025"),
            "dld_2026_ytd": computed.get("DLD_2026_YTD"),
        },
        "collectors": _build_collector_summary(sources),
    }


# ---------------------------------------------------------------------------
# SECTION 9 — MAIN ENTRY POINT
# ---------------------------------------------------------------------------

def load_all(data_dir: Optional[Path] = None) -> dict:
    """
    Main entry point. Load all active R-series sources, build computed dict,
    build lean summary. Called by FastAPI on startup and on health-check refresh.
    """
    global DATA_DIR
    if data_dir:
        DATA_DIR = data_dir

    active_data_dir = data_dir if data_dir else DATA_DIR
    cfg = _load_pipeline_config()
    sources_cfg = cfg.get("sources", {})
    load_priority = cfg.get("load_priority", {})

    ordered_ids: list[str] = []
    for tier in ("1_critical", "2_high", "3_standard", "4_advisory"):
        ordered_ids.extend(load_priority.get(tier, []))
    for rid in sources_cfg:
        if rid not in ordered_ids:
            ordered_ids.append(rid)

    sources: dict = {}
    for rid in ordered_ids:
        if rid not in sources_cfg:
            continue
        logger.debug("Loading %s ...", rid)
        sources[rid] = _load_source(rid, sources_cfg[rid], data_dir=active_data_dir)

    computed = _build_computed(sources)
    summary  = _build_summary(sources, computed)

    missing = [rid for rid, s in sources.items() if s.get("status") == "missing"]
    critical = set(load_priority.get("1_critical", []))
    critical_missing = [rid for rid in missing if rid in critical]

    if critical_missing:
        status = "degraded"
    elif missing:
        status = "partial"
    else:
        status = "ok"

    logger.info("Data load complete. Status=%s. Sources: %d ok / %d missing.",
                status, len(sources) - len(missing), len(missing))

    return {
        "dataframes":      sources,
        "computed":        computed,
        "summary":         summary,
        "status":          status,
        "missing_sources": missing,
    }


def get_source_rows(payload: dict, source_id: str) -> list[dict]:
    return payload.get("dataframes", {}).get(source_id, {}).get("rows", [])


def get_computed(payload: dict, key: str, fallback: Any = None) -> Any:
    return payload.get("computed", {}).get(key, fallback)
