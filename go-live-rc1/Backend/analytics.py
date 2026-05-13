"""
SOBHA COLLECTIONS INTELLIGENCE PLATFORM
analytics.py — Batch 18 analytics API integration

This module exposes FastAPI routes for the Batch 18 Analytics Transformation
Engine.  It wraps the runtime engine from the Batch 18 patch pack and
provides a simple GET endpoint that accepts a user role and returns a
full analytics payload.  Roles that are explicitly removed in the
RBAC model (e.g. ``entity head``) are blocked with HTTP 403.  For
other roles, the engine will run against the current R-series report
files found in ``data_loader.DATA_DIR``.

To enable this API in the platform, import the router in
``main.py`` and mount it behind existing authentication and RBAC
middleware.  See ``analytics_api_patch.py`` in the Batch 18 runtime
patch for a reference implementation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

try:
    from fastapi import APIRouter, Depends, HTTPException, Query
except Exception:  # pragma: no cover - import optional in non-FastAPI contexts
    APIRouter = None  # type: ignore
    Depends = None  # type: ignore
    HTTPException = Exception  # type: ignore
    Query = lambda *args, **kwargs: None  # type: ignore

# Import the Batch 18 analytics engine components.  The patch pack
# installs these modules alongside this file.  If the import fails the
# router will not be mounted.
try:
    from analytics_engine import AnalyticsTransformationEngine, build_default_report_file_map  # type: ignore
except Exception:
    AnalyticsTransformationEngine = None  # type: ignore
    build_default_report_file_map = None  # type: ignore

try:
    import data_loader  # type: ignore
except Exception:
    data_loader = None  # type: ignore

try:
    import auth  # type: ignore
except Exception:
    auth = None  # type: ignore


def _canonical_role(role: str) -> str:
    """Canonicalise the role string to a normalized identifier.

    Falls back to the raw role if the auth module is unavailable.
    """
    if auth is not None and hasattr(auth, "canonical_role"):
        return auth.canonical_role(role)
    return role.strip().lower().replace("/", "_").replace(" ", "_").replace("-", "_")


def _is_role_blocked(role: str) -> bool:
    """Return True if the canonical role is removed in the RBAC model."""
    can = _canonical_role(role)
    if auth is not None and hasattr(auth, "REMOVED_ROLES"):
        return can in {r.replace(" ", "_") for r in auth.REMOVED_ROLES}
    # Default: block entity head roles even without auth module
    return can in {"entity_head", "entity_head_user", "entity-head", "entity head"}


def _default_data_dir() -> Path:
    """Determine the base directory for R-series data files."""
    # Prefer data_loader.DATA_DIR if available; fallback to current directory
    if data_loader is not None and hasattr(data_loader, "DATA_DIR"):
        return Path(getattr(data_loader, "DATA_DIR"))
    return Path.cwd() / "data"


router: Any
if APIRouter is not None and AnalyticsTransformationEngine is not None and build_default_report_file_map is not None:
    router = APIRouter(prefix="/analytics", tags=["analytics"])

    @router.get("/batch18")
    async def batch18_analytics(role: str = Query("Board/CXO", description="User role, e.g. Board/CXO")) -> Dict:
        """Run the Batch 18 analytics engine and return a full payload.

        This endpoint runs the analytics transformation engine against the
        latest available R-series files.  A role must be provided to
        tailor the chart specification; if the role is blocked by the
        RBAC model a 403 is returned.
        """
        if _is_role_blocked(role):
            raise HTTPException(status_code=403, detail=f"Role '{role}' is blocked")
        engine = AnalyticsTransformationEngine()
        data_dir = _default_data_dir()
        report_files: Dict[str, Path] = build_default_report_file_map(data_dir)
        result = engine.run(report_files, role=role)
        return result.to_dict()

    @router.get("/batch18/summary")
    async def batch18_analytics_summary(role: str = Query("Board/CXO", description="User role, e.g. Board/CXO")) -> Dict:
        """Return a lightweight summary of the analytics run.

        The summary includes counts of profiles, facts, metrics, links,
        candidates, charts, and a count of blocked metrics.  Use this
        endpoint for health checks or dashboards where the full payload is
        unnecessary.
        """
        if _is_role_blocked(role):
            raise HTTPException(status_code=403, detail=f"Role '{role}' is blocked")
        engine = AnalyticsTransformationEngine()
        data_dir = _default_data_dir()
        report_files: Dict[str, Path] = build_default_report_file_map(data_dir)
        return engine.quick_summary(report_files, role=role)
else:
    # Provide a dummy router when dependencies are missing to avoid import errors
    router = None  # type: ignore
