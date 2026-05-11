"""
SOBHA COLLECTIONS INTELLIGENCE PLATFORM
main.py - FastAPI Application Entry Point
Version: v8.11 Batch 11
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

try:
    from forecast import router as forecast_router
except Exception as exc:
    forecast_router = None
    _forecast_import_error = str(exc)
else:
    _forecast_import_error = None

try:
    from account_action_queues import router as action_queues_router
except Exception as exc:
    action_queues_router = None
    _action_queues_import_error = str(exc)
else:
    _action_queues_import_error = None

try:
    from workflow import router as workflow_router
except Exception as exc:
    workflow_router = None
    _workflow_import_error = str(exc)
else:
    _workflow_import_error = None

try:
    from notifications import router as notifications_router
except Exception as exc:
    notifications_router = None
    _notifications_import_error = str(exc)
else:
    _notifications_import_error = None

try:
    from persistence import router as persistence_router
except Exception as exc:
    persistence_router = None
    _persistence_import_error = str(exc)
else:
    _persistence_import_error = None

try:
    import auth
    from auth import router as auth_router
except Exception as exc:
    auth = None
    auth_router = None
    _auth_import_error = str(exc)
else:
    _auth_import_error = None

try:
    from deployment import router as deployment_router
except Exception as exc:
    deployment_router = None
    _deployment_import_error = str(exc)
else:
    _deployment_import_error = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger(__name__)

_HERE = Path(__file__).resolve().parent
MANIFEST_PATH = _HERE / "manifest.json"

app = FastAPI(
    title="Sobha Collections Intelligence Platform",
    version="8.11.0-batch11",
    docs_url="/docs",
    redoc_url="/redoc",
)

_frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
_env = os.environ.get("SCIP_ENV", "local")
_raw_origins = os.environ.get("CORS_ALLOWED_ORIGINS", _frontend_url)
_allowed_origins = sorted({origin.strip().rstrip("/") for origin in _raw_origins.split(",") if origin.strip()})
if _env == "local":
    _allowed_origins = sorted(set(_allowed_origins) | {
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    })
if _env != "local" and "*" in _allowed_origins:
    raise RuntimeError("Wildcard CORS is not allowed outside local development")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["authorization", "content-type", "x-scip-actor-id", "x-scip-actor-name", "x-scip-role", "x-scip-entity-scope", "x-scip-collector-id", "x-scip-environment"],
)

if auth is not None:
    app.middleware("http")(auth.rbac_middleware)

if health_router is not None:
    app.include_router(health_router)
if quickball_router is not None:
    app.include_router(quickball_router)
if forecast_router is not None:
    app.include_router(forecast_router)
if action_queues_router is not None:
    app.include_router(action_queues_router)
if workflow_router is not None:
    app.include_router(workflow_router)
if notifications_router is not None:
    app.include_router(notifications_router)
if persistence_router is not None:
    app.include_router(persistence_router)
if auth_router is not None:
    app.include_router(auth_router)
if deployment_router is not None:
    app.include_router(deployment_router)


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
        "version": "v8.11 Batch 11",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
        "manifest": "/manifest",
        "quickball": "/quickball",
        "command_centres": "/command-centres",
        "month_end_forecast": "/forecast/month-end",
        "action_queues": "/action-queues",
        "collector_drilldown": "/action-queues/collector-drilldown",
        "workflows": "/workflows",
        "notifications": "/notifications",
        "notification_digests": "/notifications/digests",
        "persistence_summary": "/persistence/summary",
        "audit_export": "/audit/export",
        "security": "/security/me",
        "rbac_policy_matrix": "/security/policy-matrix",
        "deployment_health": "/deployment/health",
        "quickball_import_error": _quickball_import_error,
        "forecast_import_error": _forecast_import_error,
        "action_queues_import_error": _action_queues_import_error,
        "workflow_import_error": _workflow_import_error,
        "notifications_import_error": _notifications_import_error,
        "persistence_import_error": _persistence_import_error,
        "auth_import_error": _auth_import_error,
        "deployment_import_error": _deployment_import_error,
        "cors_allowed_origins": _allowed_origins,
        "environment": _env,
    }


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Sobha Collections Intelligence Platform v8.11 Batch 11 starting")
    logger.info("Backend dir: %s", _HERE)
    logger.info("FRONTEND_URL: %s", _frontend_url)
    logger.info("Quickball router loaded: %s", quickball_router is not None)
    logger.info("Forecast router loaded: %s", forecast_router is not None)
    logger.info("Action queues router loaded: %s", action_queues_router is not None)
    logger.info("Workflow router loaded: %s", workflow_router is not None)
    logger.info("Notifications router loaded: %s", notifications_router is not None)
    logger.info("Persistence router loaded: %s", persistence_router is not None)
    logger.info("Auth router loaded: %s", auth_router is not None)
    logger.info("Deployment router loaded: %s", deployment_router is not None)
    logger.info("SCIP_ENV: %s", _env)
    logger.info("CORS origins: %s", _allowed_origins)
