from __future__ import annotations

import os
from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "scip-backend",
        "version": "v8.13-batch13-rc1",
        "environment": os.environ.get("SCIP_ENV", "unknown"),
        "auth_mode": os.environ.get("SCIP_AUTH_MODE", "unknown"),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
