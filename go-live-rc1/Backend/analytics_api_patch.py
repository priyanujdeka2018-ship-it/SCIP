"""
Optional API integration snippet for Batch 18.

Do not auto-import this in production without RBAC/JWT review. To expose a route,
mount get_batch18_analytics_payload from Backend/main.py after auth checks.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict

from analytics_engine import AnalyticsTransformationEngine, build_default_report_file_map


def get_batch18_analytics_payload(data_dir: str | Path, role: str = "Board/CXO") -> Dict:
    engine = AnalyticsTransformationEngine()
    report_files = build_default_report_file_map(data_dir)
    return engine.run(report_files, role=role).to_dict()


# Example FastAPI route to copy into main.py after JWT/RBAC gates:
#
# @app.get("/api/batch18/analytics")
# def batch18_analytics(role_context = Depends(require_role_context)):
#     if role_context.role == "Entity Head":
#         raise HTTPException(status_code=403, detail="Entity Head role is blocked")
#     return get_batch18_analytics_payload(DATA_DIR, role=role_context.role)
