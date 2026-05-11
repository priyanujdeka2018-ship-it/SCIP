"""SCIP Batch 18 metric registry loader."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class MetricRegistry:
    def __init__(self, registry_path: str | Path | None = None):
        self.registry_path = Path(registry_path) if registry_path else self._default_path()
        self.raw = self._load()
        self.metrics = self.raw.get("metrics", []) if isinstance(self.raw, dict) else []
        self.by_id = {m.get("metric_id"): m for m in self.metrics if m.get("metric_id")}

    def _default_path(self) -> Path:
        here = Path(__file__).resolve().parent
        candidates = [
            here.parent / "config" / "metric_registry_v1.json",
            here / "metric_registry_v1.json",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]

    def _load(self) -> Dict[str, Any]:
        if not self.registry_path.exists():
            return {"version": "runtime_empty", "metrics": []}
        with open(self.registry_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get(self, metric_id: str) -> Optional[Dict[str, Any]]:
        return self.by_id.get(metric_id)

    def all(self) -> List[Dict[str, Any]]:
        return list(self.metrics)

    def by_family(self, family: str) -> List[Dict[str, Any]]:
        return [m for m in self.metrics if m.get("family") == family]
