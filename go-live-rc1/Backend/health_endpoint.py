from __future__ import annotations

import os
from datetime import datetime, timezone
from fastapi import APIRouter

try:  # W1 warmup reporting; /health stays serveable even if the module is absent.
    import warmup_state as _warmup_state
except Exception:  # pragma: no cover
    _warmup_state = None

router = APIRouter(tags=["health"])

@router.get("/health")
async def health():
    body = {
        "status": "ok",
        "service": "scip-backend",
        "version": "v8.13-batch13-rc1",
        "environment": os.environ.get("SCIP_ENV", "unknown"),
        "auth_mode": os.environ.get("SCIP_AUTH_MODE", "unknown"),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    if _warmup_state is not None:
        # Body-only boot progress; {"state": "disabled", ...} when the
        # SCIP_CONCURRENT_BOOT flag is off.
        body["warmup"] = _warmup_state.snapshot()
    return body
