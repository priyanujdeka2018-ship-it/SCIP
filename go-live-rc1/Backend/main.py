"""
SOBHA COLLECTIONS INTELLIGENCE PLATFORM
main.py - FastAPI Application Entry Point
Version: v8.13 Batch 13
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

try:
    from health_endpoint import router as health_router
except Exception:
    health_router = None

try:
    import data_loader
except Exception as exc:  # cache endpoints disclose unavailability; platform stays bootable.
    data_loader = None
    _data_loader_import_error = str(exc)
else:
    _data_loader_import_error = None

try:
    import warmup_state
except Exception as exc:  # W1 concurrent boot unavailable; flag-off behavior unaffected.
    warmup_state = None
    _warmup_state_import_error = str(exc)
else:
    _warmup_state_import_error = None

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
    import identity
    from identity import router as identity_router
except Exception as exc:
    identity = None
    identity_router = None
    _identity_import_error = str(exc)
else:
    _identity_import_error = None

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

try:
    import observability
    from observability import router as observability_router
except Exception as exc:
    observability = None
    observability_router = None
    _observability_import_error = str(exc)
else:
    _observability_import_error = None

# Batch 18 analytics integration.  Importing the router is optional so
# that the platform can boot even if the analytics patch is not
# applied.  When present, the router exposes `/analytics/batch18` and
# `/analytics/batch18/summary` endpoints.  Any import errors are
# captured in `_analytics_import_error` for diagnostics.
try:
    from analytics import router as analytics_router  # type: ignore
except Exception as exc:
    analytics_router = None  # type: ignore
    _analytics_import_error = str(exc)
else:
    _analytics_import_error = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger(__name__)

_HERE = Path(__file__).resolve().parent
MANIFEST_PATH = _HERE / "manifest.json"

app = FastAPI(
    title="Sobha Collections Intelligence Platform",
    version="8.13.0-batch13",
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

_allowed_headers = ["authorization", "content-type", "x-scip-correlation-id", "x-request-id"]
if os.environ.get("SCIP_AUTH_MODE", "jwt").lower() == "local_dev" and os.environ.get("SCIP_LOCAL_DEV_BYPASS", "false").lower() == "true":
    _allowed_headers += ["x-scip-actor-id", "x-scip-actor-name", "x-scip-role", "x-scip-entity-scope", "x-scip-collector-id", "x-scip-environment"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=_allowed_headers,
)

# W0 instrumentation: request-duration log line per core endpoint.
# Path + method + status + ms + role slug only — no bodies, no PII.
_CORE_TIMING_PREFIXES = (
    "/command-centres",
    "/forecast",
    "/action-queues",
    "/workflows",
    "/quickball",
    "/health",
    "/cache",
    "/bootstrap",
)


@app.middleware("http")
async def request_timing_middleware(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    path = request.url.path
    if path.startswith(_CORE_TIMING_PREFIXES):
        duration_ms = (time.perf_counter() - start) * 1000
        role = request.headers.get("x-scip-role", "-")
        logger.info(
            "SCIP request timing: path=%s method=%s status=%s ms=%.1f role=%s",
            path, request.method, getattr(response, "status_code", "?"), duration_ms, role,
        )
    return response


if observability is not None:
    app.middleware("http")(observability.correlation_middleware)

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
if identity_router is not None:
    app.include_router(identity_router)
if deployment_router is not None:
    app.include_router(deployment_router)
if observability_router is not None:
    app.include_router(observability_router)
if analytics_router is not None:
    app.include_router(analytics_router)


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


@app.get("/cache/status", tags=["platform"])
async def cache_status() -> dict:
    data_cache = data_loader.get_cache_status() if data_loader is not None and hasattr(data_loader, "get_cache_status") else {"status": "unavailable"}
    action_cache = {"status": "unavailable"}
    try:
        import account_action_queues
        if hasattr(account_action_queues, "get_action_queue_cache_status"):
            action_cache = account_action_queues.get_action_queue_cache_status()
    except Exception as exc:
        action_cache = {"status": "error", "message": str(exc)}
    return {
        "status": "ok",
        "data_loader": data_cache,
        "action_queues": action_cache,
        "guardrails": {
            "lineage_preserved": True,
            "no_frontend_business_computation": True,
            "no_silent_fallback": True,
        },
    }


@app.post("/cache/refresh", tags=["platform"])
async def cache_refresh() -> dict:
    if data_loader is not None and hasattr(data_loader, "invalidate_cache"):
        data_loader.invalidate_cache()
    try:
        import account_action_queues
        if hasattr(account_action_queues, "invalidate_action_queue_cache"):
            account_action_queues.invalidate_action_queue_cache()
    except Exception:
        pass
    return {"status": "cache_invalidated", "next_request": "will_reload_sources"}


@app.get("/", tags=["platform"])
async def root() -> dict:
    return {
        "platform": "Sobha Collections Intelligence Platform",
        "version": "v8.13 Batch 13",
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
        "identity": "/identity/me",
        "identity_policy": "/identity/policy",
        "identity_provisioning": "/identity/provisioning",
        "rbac_policy_matrix": "/security/policy-matrix",
        "deployment_health": "/deployment/health",
        "observability_summary": "/observability/summary",
        "observability_dashboards": "/observability/dashboards",
        "observability_alerts": "/observability/alerts",
        "quickball_import_error": _quickball_import_error,
        "forecast_import_error": _forecast_import_error,
        "action_queues_import_error": _action_queues_import_error,
        "workflow_import_error": _workflow_import_error,
        "notifications_import_error": _notifications_import_error,
        "persistence_import_error": _persistence_import_error,
        "auth_import_error": _auth_import_error,
        "identity_import_error": _identity_import_error,
        "deployment_import_error": _deployment_import_error,
        "observability_import_error": _observability_import_error,
        "cors_allowed_origins": _allowed_origins,
        "environment": _env,
    }


def _run_concurrent_boot() -> None:
    """W1 background boot: bootstrap sources, warm the cache, update warmup_state.

    Any failure lands in an explicit warmup_failed state with the reason; no
    figures are served and a restart retries from a clean cold state.
    """
    try:
        warmup_state.set_state(warmup_state.STATE_DOWNLOADING)
        import bootstrap_rseries_google_drive_folder as _bootstrap
        _bootstrap.run_bootstrap()
        warmup_state.set_state(warmup_state.STATE_PARSING)
        if data_loader is None or not hasattr(data_loader, "get_cached_payload"):
            raise RuntimeError(f"data_loader cache entry point unavailable: {_data_loader_import_error}")
        data_loader.get_cached_payload(force_refresh=True)
        warmup_state.set_state(warmup_state.STATE_WARM)
        logger.info("SCIP concurrent boot complete: sources warm")
    except Exception as exc:
        logger.exception("SCIP concurrent boot failed")
        if warmup_state is not None:
            warmup_state.set_state(warmup_state.STATE_FAILED, reason=str(exc))


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Sobha Collections Intelligence Platform v8.13 Batch 13 starting")
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
    logger.info("Observability router loaded: %s", observability_router is not None)
    logger.info("SCIP_ENV: %s", _env)
    logger.info("CORS origins: %s", _allowed_origins)
    if warmup_state is not None and warmup_state.is_concurrent_boot_enabled():
        # W1 concurrent boot: accept connections immediately; bootstrap + parse
        # run in a daemon thread. Exactly one load path per boot — the
        # synchronous SCIP_WARM_DATA_CACHE_ON_STARTUP warm below must not also run.
        logger.info("SCIP concurrent boot enabled (SCIP_CONCURRENT_BOOT=true); background source load starting")
        threading.Thread(target=_run_concurrent_boot, name="scip-concurrent-boot", daemon=True).start()
        return
    if data_loader is not None and hasattr(data_loader, "get_cached_payload"):
        if os.environ.get("SCIP_WARM_DATA_CACHE_ON_STARTUP", "true").lower() == "true":
            try:
                data_loader.get_cached_payload()
                logger.info("SCIP data cache warmed on startup")
            except Exception as exc:
                logger.warning("SCIP data cache warmup failed; first request will retry: %s", exc)
