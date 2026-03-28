"""
SOBHA COLLECTIONS INTELLIGENCE PLATFORM
main.py — FastAPI Application Entry Point
Version: v6
Authority: MASTER_ARCHITECTURE_v9.1.md

Location: /backend/main.py
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# CRITICAL — sys.path fix must come before ANY local imports
# Render's uvicorn runs from repo root, not from Backend/.
# This ensures endpoints/ and quickball.py are always found.
# ---------------------------------------------------------------------------
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

# ---------------------------------------------------------------------------
# STANDARD IMPORTS
# ---------------------------------------------------------------------------
import json
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ---------------------------------------------------------------------------
# ENDPOINT ROUTERS
# ---------------------------------------------------------------------------
from endpoints.health import router as health_router

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
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — Frontend URL only
# ---------------------------------------------------------------------------
_frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
_allowed_origins = [_frontend_url.rstrip("/")]
_dev_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
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
app.include_router(health_router)
app.include_router(quickball_router)

# app.include_router(context_router, prefix="/context", tags=["context"])
# app.include_router(pulse_router,   prefix="/pulse",   tags=["pulse"])
# app.include_router(tools_router,   prefix="/tools",   tags=["tools"])

# ---------------------------------------------------------------------------
# MANIFEST ENDPOINT
# ---------------------------------------------------------------------------

@app.get("/manifest", tags=["platform"])
async def get_manifest() -> JSONResponse:
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
# ROOT ENDPOINT
# ---------------------------------------------------------------------------

@app.get("/", tags=["platform"])
async def root() -> dict:
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
# STARTUP EVENT
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def on_startup() -> None:
    logger.info("=" * 60)
    logger.info("Sobha Collections Intelligence Platform — v6 Starting")
    logger.info("sys.path[0]: %s", sys.path[0])
    logger.info("Backend dir: %s", _HERE)
    logger.info("CORS origins: %s", _all_origins)
    logger.info("Manifest path: %s  exists=%s", MANIFEST_PATH, MANIFEST_PATH.exists())
    logger.info("ANTHROPIC_API_KEY set: %s", bool(os.environ.get("ANTHROPIC_API_KEY")))
    logger.info("FRONTEND_URL: %s", _frontend_url)
    logger.info("=" * 60)
    logger.info("Routes registered: / | /health | /manifest | /quickball | /docs | /redoc")
    logger.info("Phase 6 context/pulse/tools routers: pending build")
    logger.info("Platform startup complete.")
