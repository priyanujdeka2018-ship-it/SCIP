"""
SOBHA COLLECTIONS INTELLIGENCE PLATFORM
main.py — FastAPI Application Entry Point
Version: v6
Authority: MASTER_ARCHITECTURE_v9.1.md

Location: /backend/main.py

Responsibilities:
  - Instantiate FastAPI app
  - Register routers from endpoints/ and quickball.py
  - Serve manifest.json at GET /manifest
  - Configure CORS (frontend URL only)
  - Zero business logic — routes only

Dependency rule (non-negotiable):
  main.py  →  imports: FastAPI, CORS, endpoint routers, quickball router ONLY
  main.py  →  NEVER imports: data_loader, constants, utils, any section submodule
  main.py  →  ZERO business logic, ZERO data reads, ZERO computation

Architecture rules:
  - All computation lives in data_loader.py + endpoint functions
  - This file is a wiring harness only
  - /health route registered from endpoints/health.py
  - /quickball route registered from quickball.py
  - /manifest route serves manifest.json directly (static)
  - CORS origin = FRONTEND_URL env var (falls back to localhost for dev)
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import sys

# Ensure the directory containing main.py is on sys.path
# This fixes the Render deployment where uvicorn runs from repo root
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ---------------------------------------------------------------------------
# ENDPOINT ROUTERS
# ---------------------------------------------------------------------------
# Import routers only. No business logic imported here.
# Each router file owns its own endpoint logic.

from endpoints.health import router as health_router

# Placeholder imports for Phase 6+ routers.
# Uncomment each as the corresponding endpoint file is built and smoke-tested.
# from endpoints.context import router as context_router
# from endpoints.pulse   import router as pulse_router
# from endpoints.tools   import router as tools_router

from quickball import router as quickball_router

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
_HERE = Path(__file__).parent
MANIFEST_PATH = _HERE / "manifest.json"

# ---------------------------------------------------------------------------
# APP INSTANTIATION
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Sobha Collections Intelligence Platform",
    description=(
        "Backend API for the Sobha Collections Intelligence Platform. "
        "Serves pre-aggregated R-series data, health status, Quickball AI relay, "
        "and submodule manifest to the React frontend."
    ),
    version="6.0.0",
    docs_url="/docs",        # Swagger UI — remove in production if needed
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — Frontend URL only
# ---------------------------------------------------------------------------
# FRONTEND_URL must be set as an environment variable in Render.
# Falls back to localhost:3000 for local development.
# Rule: never use wildcard "*" in CORS — security requirement.
_frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")

# Allow both bare domain and trailing-slash variants
_allowed_origins = [_frontend_url.rstrip("/")]

# Also permit localhost variants for local dev regardless of env var
_dev_origins = [
    "http://localhost:3000",
    "http://localhost:5173",  # Vite default
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

_all_origins = list(set(_allowed_origins + _dev_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_all_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

logger.info("CORS configured for origins: %s", _all_origins)

# ---------------------------------------------------------------------------
# ROUTER REGISTRATION
# ---------------------------------------------------------------------------
# health router — active Phase 5
app.include_router(health_router)

# quickball router — active Phase 5
app.include_router(quickball_router)

# Context, Pulse, Tools routers — uncomment as each phase completes
# app.include_router(context_router, prefix="/context", tags=["context"])
# app.include_router(pulse_router,   prefix="/pulse",   tags=["pulse"])
# app.include_router(tools_router,   prefix="/tools",   tags=["tools"])

# ---------------------------------------------------------------------------
# MANIFEST ENDPOINT — serves submodule manifest to frontend + Quickball
# ---------------------------------------------------------------------------

@app.get("/manifest", tags=["platform"])
async def get_manifest() -> JSONResponse:
    """
    Serve the SUBMODULE_MANIFEST to the React frontend.

    Called:
      - On React app initialisation (App.jsx useEffect on mount)
      - By Quickball at query time for routing intelligence
      - During Phase 6+ development to confirm submodule registration

    Returns HTTP 200 always.
    Returns degraded payload if manifest.json is missing or malformed.
    """
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        return JSONResponse(content=manifest, status_code=200)
    except FileNotFoundError:
        logger.warning("manifest.json not found at %s — returning empty manifest", MANIFEST_PATH)
        return JSONResponse(
            content={
                "status": "manifest_missing",
                "message": "manifest.json not found. Platform routing degraded.",
                "submodules": {},
                "workflows": {},
            },
            status_code=200,
        )
    except json.JSONDecodeError as exc:
        logger.error("manifest.json parse error: %s", exc)
        return JSONResponse(
            content={
                "status": "manifest_error",
                "message": f"manifest.json parse error: {exc}",
                "submodules": {},
                "workflows": {},
            },
            status_code=200,
        )


# ---------------------------------------------------------------------------
# ROOT ENDPOINT — deployment confirmation ping
# ---------------------------------------------------------------------------

@app.get("/", tags=["platform"])
async def root() -> dict:
    """
    Root endpoint. Confirms backend is deployed and reachable.
    Used by Render health check and initial deployment verification.
    Not used by React frontend — /health is the operational ping.
    """
    return {
        "platform":  "Sobha Collections Intelligence Platform",
        "version":   "v6",
        "status":    "ok",
        "docs":      "/docs",
        "health":    "/health",
        "manifest":  "/manifest",
        "quickball": "/quickball",
    }


# ---------------------------------------------------------------------------
# STARTUP EVENT — log configuration on boot
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def on_startup() -> None:
    """Log configuration on startup for Render log confirmation (Smoke Test #11)."""
    logger.info("=" * 60)
    logger.info("Sobha Collections Intelligence Platform — v6 Starting")
    logger.info("CORS origins: %s", _all_origins)
    logger.info("Manifest path: %s  exists=%s", MANIFEST_PATH, MANIFEST_PATH.exists())
    logger.info("ANTHROPIC_API_KEY set: %s", bool(os.environ.get("ANTHROPIC_API_KEY")))
    logger.info("FRONTEND_URL: %s", _frontend_url)
    logger.info("=" * 60)
    logger.info("Routes registered: / | /health | /manifest | /quickball | /docs | /redoc")
    logger.info("Phase 6 context/pulse/tools routers: pending build")
    logger.info("Platform startup complete.")
