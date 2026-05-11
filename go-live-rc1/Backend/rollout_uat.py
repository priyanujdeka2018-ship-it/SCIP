"""
SCIP Batch 14 - Rollout and UAT read-only router.
This module exposes rollout/UAT artifacts as governance endpoints.
It performs no financial computation and does not change RBAC/identity rules.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import APIRouter

router = APIRouter(prefix="/rollout", tags=["rollout-uat"])

ROLES = ["Board/CXO", "CCO/GM/AGM", "Finance", "MIS/QCG/Admin", "Collector/RM"]
STAGES = ["dev", "staging", "pilot", "uat", "production", "rollback", "break_glass"]

GUARDRAILS = {
    "liquid_glass_two_door": True,
    "no_silent_fallback": True,
    "locked_hierarchy": "Group > Sobha/Sobha Dubai/Sobha AUH + UAQ/Siniya/Downtown UAQ",
    "tolerance_pct": 0.05,
    "entity_head_removed": True,
    "jwt_sso_default": True,
    "row_level_visibility": True,
    "audit_export_required": True,
    "observability_correlation_required": True,
}

@router.get("/plan")
async def rollout_plan() -> Dict[str, Any]:
    return {
        "contract": "rollout_uat_signoff.v1.batch14",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stages": STAGES,
        "roles": ROLES,
        "guardrails": GUARDRAILS,
        "promotion_rule": "no stage promotion if identity, RBAC, lineage, no-silent-fallback, audit, notification dedupe, workflow closure, or observability checks fail",
    }

@router.get("/uat-scripts")
async def uat_scripts() -> Dict[str, Any]:
    return {
        "roles": ROLES,
        "scripts": {
            "Board/CXO": ["Verify Arrival has Live Pulse/Narratives only", "Open Narratives journey", "Ask Quickball to explain a board metric", "Confirm account queues are denied"],
            "CCO/GM/AGM": ["Open Risk & Action", "Assign permitted action", "Review manager escalation digest"],
            "Finance": ["Review PR/TAT exceptions", "Attempt collector-only workflow and confirm denial", "Export scoped audit"],
            "MIS/QCG/Admin": ["Run migration/backup/health checks", "Review denials", "Review alert dashboard"],
            "Collector/RM": ["Open own action queue", "Update disposition/evidence", "Confirm other-owner rows are hidden"],
        }
    }

@router.get("/checklists")
async def checklists() -> Dict[str, Any]:
    return {
        "production_readiness": ["build", "backend boot", "JWT", "CORS", "migrations", "lineage", "audit", "observability", "rollback", "break_glass"],
        "data_cutover": ["critical sources", "account sources", "lineage coverage", "reconciliations", "cache invalidation"],
        "identity_provisioning": ["user", "groups", "roles", "entity scope", "collector mappings", "deactivation"],
        "rbac_verification": ["role visibility", "denied audit", "own-row collector scope", "no Entity Head"],
        "dashboard_alert_signoff": ["stale source", "missing lineage", "migration failure", "backup failure", "high denials", "slow endpoint", "failed export"],
    }

@router.get("/signoff-matrix")
async def signoff_matrix() -> Dict[str, Any]:
    return {
        "contract": "rollout_uat_signoff.v1.batch14",
        "status": "pending_business_signoff",
        "items": [
            {"area": "Product / Liquid Glass", "owner_role": "Board/CXO", "status": "pending"},
            {"area": "Operational Management", "owner_role": "CCO/GM/AGM", "status": "pending"},
            {"area": "Finance", "owner_role": "Finance", "status": "pending"},
            {"area": "Governance / Data Ops", "owner_role": "MIS/QCG/Admin", "status": "pending"},
            {"area": "Collector workflow", "owner_role": "Collector/RM", "status": "pending"},
            {"area": "Security", "owner_role": "MIS/QCG/Admin", "status": "pending"},
            {"area": "Executive go-live", "owner_role": "Board/CXO", "status": "pending"},
        ],
    }

@router.get("/final-smoke-manifest")
async def final_smoke_manifest() -> Dict[str, Any]:
    return {
        "contract": "final_deployment_smoke.v1.batch14",
        "checks": [
            "liquid_glass_two_door_navigation",
            "no_silent_fallback",
            "identity_enforcement",
            "row_level_visibility",
            "audit_export",
            "workflow_closure",
            "notification_dedupe",
            "observability_correlation",
            "critical_lineage",
        ],
    }
