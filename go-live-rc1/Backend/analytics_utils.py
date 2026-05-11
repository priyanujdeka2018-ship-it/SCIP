"""SCIP Batch 18 runtime utilities."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def utc_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def norm(value: Any) -> str:
    return str(value or "").strip()


def norm_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", norm(value).lower()).strip("_")


def to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        text = str(value).replace(",", "").replace("AED", "").strip()
        try:
            return float(text)
        except (TypeError, ValueError):
            return default


def safe_div(numerator: Any, denominator: Any) -> Optional[float]:
    n = to_float(numerator)
    d = to_float(denominator)
    if n is None or d in (None, 0):
        return None
    return n / d


def first_non_empty(values: Iterable[Any]) -> Optional[Any]:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def parse_date(value: Any) -> Optional[str]:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if value is None:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d-%m-%y", "%d/%m/%Y", "%d/%m/%y", "%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    return None


def date_from_filename(path: str | Path) -> Optional[str]:
    name = Path(path).name
    patterns = [
        r"(\d{2})-(\d{2})-(\d{4})",
        r"(\d{2})-(\d{2})-(\d{2})",
        r"(\d{2})\.(\d{2})\.(\d{4})",
        r"(\d{2})(\d{2})(\d{4})",
    ]
    for pat in patterns:
        m = re.search(pat, name)
        if not m:
            continue
        parts = m.groups()
        if len(parts) == 3:
            day, month, year = parts
            if len(year) == 2:
                year = "20" + year
            try:
                return datetime(int(year), int(month), int(day)).date().isoformat()
            except ValueError:
                continue
    return None


def make_hash(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def find_header_index(headers: List[Any], *names: str) -> Optional[int]:
    wanted = {norm_key(n) for n in names}
    for idx, header in enumerate(headers):
        if norm_key(header) in wanted:
            return idx
    return None


def header_map(headers: List[Any]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for i, h in enumerate(headers):
        key = norm_key(h)
        if key and key not in out:
            out[key] = i
    return out


def row_value(row: List[Any] | tuple, index: Optional[int], default: Any = None) -> Any:
    if index is None or index < 0 or index >= len(row):
        return default
    value = row[index]
    return default if value is None else value
