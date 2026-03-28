"""
SOBHA COLLECTIONS INTELLIGENCE PLATFORM
main.py — FastAPI Application Entry Point
Version: v6
Authority: MASTER_ARCHITECTURE_v9.1.md
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ---------------------------------------------------------------------------
# ROUTERS — imported directly, no subpackage
# ---------------------------------------------------------------------------
from health_endpoint import router as health_router
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
_HERE = Path(__file__).resolve().parent
MANIFEST_PATH = _HERE / "manifest.json"

# ---------------------------------------------------------------------------
# APP
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Sobha Collections Intelligence Platform",
    version="6.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS
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

# ---------------------------------------------------------------------------
# ROUTERS
# ---------------------------------------------------------------------------
app.include_router(health_router)
app.include_router(quickball_router)

# ---------------------------------------------------------------------------
# MANIFEST
# ---------------------------------------------------------------------------
@app.get("/manifest", tags=["platform"])
async def get_manifest() -> JSONResponse:
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        return JSONResponse(content=manifest, status_code=200)
    except FileNotFoundError:
        return JSONResponse(content={"status": "manifest_missing", "submodules": {}, "workflows": {}}, status_code=200)
    except json.JSONDecodeError as exc:
        return JSONResponse(content={"status": "manifest_error", "message": str(exc), "submodules": {}, "workflows": {}}, status_code=200)


# ---------------------------------------------------------------------------
# ROOT
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
# STARTUP
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup() -> None:
    logger.info("=" * 60)
    logger.info("Sobha Collections Intelligence Platform — v6 Starting")
    logger.info("Backend dir: %s", _HERE)
    logger.info("ANTHROPIC_API_KEY set: %s", bool(os.environ.get("ANTHROPIC_API_KEY")))
    logger.info("FRONTEND_URL: %s", _frontend_url)
    logger.info("=" * 60)
    logger.info("Platform startup complete.")
