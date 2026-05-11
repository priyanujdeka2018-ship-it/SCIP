"""
SOBHA COLLECTIONS INTELLIGENCE PLATFORM
main.py - FastAPI Application Entry Point
Version: v8.4 Batch 4
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

try:
    from health_endpoint import router as health_router
except Exception:
    health_router = None

try:
    from quickball import router as quickball_router
except Exception as exc:  # keep platform bootable; health will disclose missing router.
    quickball_router = None
    _quickball_import_error = str(exc)
else:
    _quickball_import_error = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger(__name__)

_HERE = Path(__file__).resolve().parent
MANIFEST_PATH = _HERE / "manifest.json"

app = FastAPI(
    title="Sobha Collections Intelligence Platform",
    version="8.4.0-batch4",
    docs_url="/docs",
    redoc_url="/redoc",
)

_frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
_allowed_origins = list({
    _frontend_url.rstrip("/"),
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
})

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

if health_router is not None:
    app.include_router(health_router)
if quickball_router is not None:
    app.include_router(quickball_router)


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


@app.get("/", tags=["platform"])
async def root() -> dict:
    return {
        "platform": "Sobha Collections Intelligence Platform",
        "version": "v8.4 Batch 4",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
        "manifest": "/manifest",
        "quickball": "/quickball",
        "quickball_import_error": _quickball_import_error,
    }


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Sobha Collections Intelligence Platform v8.4 Batch 4 starting")
    logger.info("Backend dir: %s", _HERE)
    logger.info("FRONTEND_URL: %s", _frontend_url)
    logger.info("Quickball router loaded: %s", quickball_router is not None)
