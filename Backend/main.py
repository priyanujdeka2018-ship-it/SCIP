"""
SOBHA COLLECTIONS INTELLIGENCE PLATFORM
main.py — FastAPI Application Entry Point
Version: v6
Authority: MASTER_ARCHITECTURE_v9.1.md

Phase 5 patch:
  - Adds /summary endpoint for frontend data load
  - Keeps /health and /quickball routers
  - Keeps manifest/root endpoints
  - Adds HEAD / so Render health probes do not show 405
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

# ---------------------------------------------------------------------------
# LOCAL IMPORTS — imported directly because Render runs from Backend/
# ---------------------------------------------------------------------------
import data_loader as DL
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
# Set FRONTEND_URL in Render after Netlify deploys, for example:
# FRONTEND_URL=https://your-site-name.netlify.app
_frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
_allowed_origins = [_frontend_url.rstrip("/")]
_dev_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]
_all_origins = sorted(set(_allowed_origins + _dev_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_all_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# ROUTERS
# ---------------------------------------------------------------------------
app.include_router(health_router)
app.include_router(quickball_router)

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def _format_aed_m(value: Any) -> str | None:
    """Format AED base-unit numeric values as 1-decimal millions for smoke checks/UI."""
    try:
        if value is None:
            return None
        return f"{float(value) / 1_000_000:,.1f}M"
    except (TypeError, ValueError):
        return None


def _summary_payload() -> dict:
    """
    Load data once and shape it for frontend consumption.

    data_loader.load_all() already returns:
      - computed: authoritative constants
      - summary: lean frontend JSON
      - status: ok | partial | degraded
      - missing_sources: source ids not present
    """
    payload = DL.load_all()
    computed = payload.get("computed", {}) or {}
    summary = payload.get("summary", {}) or {}
    missing_sources = payload.get("missing_sources", []) or []

    return {
        "status": payload.get("status", "unknown"),
        "platform": "v6",
        "snapshot_date": computed.get("SNAPSHOT_DATE"),
        "snapshot_label": "Data as of 15 Mar 2026",
        "data": summary,
        "summary": summary,
        "computed": computed,
        "sources_loaded": len(summary.get("meta", {}).get("sources_loaded", [])),
        "sources_missing": len(missing_sources),
        "missing_sources": missing_sources,
        "od_today": _format_aed_m(computed.get("OD_TODAY")),
        "od_source": computed.get("OD_SOURCE"),
        "pipeline_source": computed.get("PIPELINE_SOURCE"),
        "load_timestamp": computed.get("LOAD_TIMESTAMP"),
    }


# ---------------------------------------------------------------------------
# SUMMARY — REQUIRED BY FRONTEND
# ---------------------------------------------------------------------------
@app.get("/summary", tags=["data"])
async def get_summary() -> JSONResponse:
    """
    Frontend data endpoint.

    This must return HTTP 200 even when the platform is partial/degraded, because
    the frontend should show available data and the missing-source list instead
    of crashing.
    """
    try:
        return JSONResponse(content=_summary_payload(), status_code=200)
    except Exception as exc:
        logger.error("Summary endpoint error: %s", exc, exc_info=True)
        return JSONResponse(
            content={
                "status": "error",
                "platform": "v6",
                "data": {},
                "summary": {},
                "computed": {},
                "sources_loaded": 0,
                "sources_missing": 0,
                "missing_sources": [],
                "error_detail": str(exc),
            },
            status_code=200,
        )


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
        return JSONResponse(
            content={"status": "manifest_missing", "submodules": {}, "workflows": {}},
            status_code=200,
        )
    except json.JSONDecodeError as exc:
        return JSONResponse(
            content={"status": "manifest_error", "message": str(exc), "submodules": {}, "workflows": {}},
            status_code=200,
        )


# ---------------------------------------------------------------------------
# ROOT
# ---------------------------------------------------------------------------
@app.get("/", tags=["platform"])
async def root() -> dict:
    return {
        "platform": "Sobha Collections Intelligence Platform",
        "version": "v6",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
        "summary": "/summary",
        "manifest": "/manifest",
        "quickball": "/quickball",
    }


@app.head("/", include_in_schema=False)
async def root_head() -> Response:
    return Response(status_code=200)


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
    logger.info("Allowed CORS origins: %s", _all_origins)
    logger.info("=" * 60)
    logger.info("Platform startup complete.")
