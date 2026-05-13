"""
SOBHA COLLECTIONS INTELLIGENCE PLATFORM
metric_loader.py — dynamic metric catalogue loader

This module provides a helper for loading metric definitions from an
external JSON configuration file.  Moving the metric catalogue into a
data file enables non‑developers (governance teams, analysts) to
contribute new definitions without changing Python code.  It also
supports runtime patching and experimentation in staging environments.

The default path resolves to ``metric_catalog.json`` in the same
directory as this module.  Callers may override the path via the
``catalog_path`` argument.

Returns a dictionary keyed by the canonical metric identifier; each
value is the raw dictionary loaded from JSON.  Conversion to
``MetricSpec`` objects remains the responsibility of the caller to
avoid circular imports.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Optional

def load_metric_catalog(catalog_path: Optional[str | Path] = None) -> Dict[str, Dict[str, Any]]:
    """Load the metric catalogue from a JSON file.

    Args:
        catalog_path: Optional override path to the catalogue file. If
            not provided, the loader looks for ``metric_catalog.json``
            in the same directory as this module.

    Returns:
        A dictionary mapping canonical metric keys to the raw metric
        definitions loaded from JSON.  If the file cannot be found
        this returns an empty dictionary.
    """
    path: Path
    if catalog_path:
        path = Path(catalog_path)
    else:
        path = Path(__file__).resolve().parent / "metric_catalog.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Ensure the top-level object is a dict
    if isinstance(data, dict):
        return data
    return {}
