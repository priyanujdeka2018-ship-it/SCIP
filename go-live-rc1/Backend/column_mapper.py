"""
SOBHA COLLECTIONS INTELLIGENCE PLATFORM
column_mapper.py — column mapping and type coercion utilities

This module encapsulates the logic for renaming columns according to
``pipeline_config.json`` and coercing raw spreadsheet values into
explicit Python types.  Separating these functions from
``data_loader.py`` improves readability and allows the mapping logic
to be reused by other components (such as analytics engines or
testing harnesses) without dragging along the entire loader.

Functions:

* ``apply_column_map(rows, col_map, col_types)`` — Rename and
  selectively copy columns from a list of row dictionaries, applying
  type coercion to each value.  Rows that have no mapped values are
  skipped.
* ``coerce(value, type_str)`` — Convert a raw cell value into the
  declared type.  Supported types include ``int``, ``float``,
  ``bool``, ``datetime`` and the default ``str``.  Returns ``None``
  on conversion failure and never raises exceptions.
"""

from __future__ import annotations

import logging
from datetime import datetime, date
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def coerce(value: Any, type_str: str) -> Any:
    """Coerce a raw cell value to the declared type.

    If the value is ``None`` it is returned unchanged.  Supported
    ``type_str`` values are ``"int"``, ``"float"``, ``"bool"``,
    ``"datetime"`` and the default ``"str"``.  Datetimes are parsed
    using a small set of common formats.  On conversion errors
    (``ValueError`` or ``TypeError``), ``None`` is returned.
    """
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
            # Pass through existing datetime/date values
            if isinstance(value, (datetime, date)):
                return value
            # Attempt to parse common date formats
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d %b %Y"):
                try:
                    return datetime.strptime(str(value).strip(), fmt)
                except ValueError:
                    continue
            return None
        # Default: return a stripped string representation
        return str(value).strip() if value is not None else None
    except (ValueError, TypeError):
        return None


def apply_column_map(rows: List[Dict[str, Any]], col_map: Dict[str, str], col_types: Dict[str, str]) -> List[Dict[str, Any]]:
    """Rename columns per the ``pipeline_config`` and coerce types.

    Iterates over each source row, selects the columns declared in
    ``col_map``, renames them according to the mapping, and applies
    type coercion via ``coerce``.  Rows that have no non‑null values
    after mapping are dropped.  This behaviour mirrors the
    implementation originally embedded in ``data_loader.py`` but is
    decoupled for reuse.

    Args:
        rows: List of row dictionaries as produced by ``excel_reader.read_sheet``.
        col_map: Mapping of source column names (keys) to destination names (values).
        col_types: Mapping of destination column names to type strings (see ``coerce``).

    Returns:
        A new list of dictionaries containing only the mapped and coerced columns.
    """
    mapped: List[Dict[str, Any]] = []
    for row in rows:
        new_row: Dict[str, Any] = {}
        for src_col, dest_col in col_map.items():
            raw = row.get(src_col)
            coerced_val = coerce(raw, col_types.get(dest_col, "str"))
            new_row[dest_col] = coerced_val
        # Skip rows with no non‑null values
        if any(v is not None for v in new_row.values()):
            mapped.append(new_row)
    return mapped
