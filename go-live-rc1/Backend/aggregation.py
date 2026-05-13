"""
SOBHA COLLECTIONS INTELLIGENCE PLATFORM
aggregation.py — aggregation and filtering utilities

This module contains pure functions used by the R‑series data pipeline to
aggregate and filter mapped rows.  Extracting these helpers from
``data_loader.py`` improves modularity and allows the aggregation logic
to be tested in isolation.

Functions provided:
  * ``run_aggregations`` — compute aggregations as declared in
    ``pipeline_config.json``.  Supports a variety of operations
    including sums, means, counts, weighted averages and derived
    metrics.
  * ``filter_rows`` — apply basic filtering predicates to a list of
    dictionaries.  Handles exact matching, membership tests and
    year/month filters.
  * ``extract_year`` — helper to pull a four‑digit year from a date,
    integer or string.
  * ``safe_sum`` — sum a numeric column while skipping ``None`` values.

None of these functions mutate their input.  On encountering errors
within a specific aggregation, the error is logged and the result
defaults to ``None`` rather than raising.
"""

from __future__ import annotations

import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def safe_sum(rows: List[Dict[str, Any]], col: str) -> float:
    """Sum a numeric column, skipping ``None`` values."""
    return sum(r[col] for r in rows if r.get(col) is not None)


def extract_year(value: Any) -> Optional[int]:
    """Extract a 4‑digit year from a datetime, int or string value.

    Returns the year as an int if it falls within [2000, 2100], or
    ``None`` otherwise.
    """
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


def filter_rows(rows: List[Dict[str, Any]], filt: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Apply filter conditions to a list of row dictionaries.

    Supported filter keys:
      * ``col_name: value`` — exact match (string comparison, case‑insensitive)
      * ``col_name_in: [v1, v2]`` — membership test on string prefixes
      * ``col_name_ne: value`` — not equal comparison
      * ``entity_section`` — special mapping for Sobha section codes
      * ``year`` — filter rows where any year‑like column equals the given value
      * ``month_in`` — filter datetime values by month membership

    Unknown keys are interpreted as exact matches.  If any predicate
    fails for a row, the row is excluded.
    """
    result: List[Dict[str, Any]] = []
    for row in rows:
        match = True
        for key, val in filt.items():
            if key == "entity_section":
                entity = row.get("entity", "")
                section_map = {
                    "A-E": lambda e: str(e).strip().upper() in ("A", "B", "C", "D", "E", "SOBHA"),
                    "F":   lambda e: str(e).strip().upper() in ("F", "SINIYA"),
                    "G":   lambda e: str(e).strip().upper() in ("G", "DT", "DOWNTOWN"),
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
                # Filter by year extracted from one of several possible date columns
                for yr_col in ("year", "month", "collection_date", "acd_year"):
                    cell = row.get(yr_col)
                    if cell is not None:
                        extracted = extract_year(cell)
                        if extracted is not None and extracted != int(val):
                            match = False
                        break
            else:
                # Exact match
                cell = row.get(key)
                if cell is None:
                    match = False
                elif str(cell).strip().lower() != str(val).strip().lower():
                    match = False
        if match:
            result.append(row)
    return result


def run_aggregations(rows: List[Dict[str, Any]], agg_cfg: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Execute aggregation operations declared in ``pipeline_config``.

    Supported operations:
      * ``sum`` — sum a column
      * ``mean`` — mean of a column
      * ``filter_sum`` — sum after applying filters
      * ``filter_mean`` — mean after applying filters
      * ``filter_count`` / ``count_filter`` — count rows after filtering
      * ``last`` — last non‑null value
      * ``extract_list`` — extract a column as a list, with optional formatting
      * ``weighted_avg`` — weighted average computed as sum(numerator) / sum(denominator)
      * ``derived`` — deferred formula evaluation handled elsewhere
      * ``read_metadata`` — copy metadata fields from source configuration

    For any aggregation that raises an exception, the error is logged and
    the result is set to ``None``.
    """
    results: Dict[str, Any] = {}
    for agg_name, agg_def in agg_cfg.items():
        op = agg_def.get("op")
        col = agg_def.get("col")
        filt = agg_def.get("filter", {})
        try:
            filtered = filter_rows(rows, filt) if filt else rows
            if op == "sum":
                results[agg_name] = safe_sum(filtered, col)
            elif op == "filter_sum":
                results[agg_name] = safe_sum(filtered, col)
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
                vals: List[Any] = []
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
                total_num = safe_sum(filtered, num_col)
                total_den = safe_sum(filtered, den_col)
                if total_den and total_den > 0:
                    ratio = total_num / total_den
                    results[agg_name] = ratio * 100 if multiply else ratio
                else:
                    results[agg_name] = None
            elif op == "derived":
                # Deferred formula evaluation; store the formula placeholder
                results[agg_name] = {"__deferred__": agg_def.get("formula")}
            elif op == "read_metadata":
                # Copy metadata fields; actual resolution performed in _load_source
                results[agg_name] = {"__metadata__": agg_def.get("field")}
            else:
                # Unknown operation: log and set None
                logger.warning("Unknown aggregation op '%s' for %s", op, agg_name)
                results[agg_name] = None
        except Exception as exc:
            logger.warning("Aggregation '%s' failed: %s", agg_name, exc)
            results[agg_name] = None
    return results
