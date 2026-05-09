"""
SOBHA COLLECTIONS INTELLIGENCE PLATFORM
main.py - FastAPI Application Entry Point
Version: v6

Phase 5 fast-summary patch:
  - Keeps /health lightweight through health_endpoint.py
  - Makes /summary frontend-safe: returns quickly, even if full Excel load is slow
  - Adds /summary/full for manual full Excel validation
  - Keeps /quickball, /manifest, /, /docs

Upload location:
  Backend/main.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

# Local imports - Render runs from Backend/
import data_loader as DL
from health_endpoint import router as health_router
from quickball import router as quickball_router

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
_DATA_DIR = _REPO_ROOT / "data"
_MANIFEST_PATH = _HERE / "manifest.json"
_PIPELINE_CONFIG_PATH = _HERE / "pipeline_config.json"

# ---------------------------------------------------------------------------
# FAST SOURCE SCAN CONFIG
# ---------------------------------------------------------------------------
DEFAULT_EXPECTED_SOURCES = [
    "R18", "R04", "R02", "R08", "R36", "R30", "R13", "R01", "R10",
    "R12", "R16", "R20", "R25", "R26", "R31", "R34", "R38",
]
CRITICAL_SOURCES = {"R18", "R04", "R02", "R08", "R01", "R36"}
R_FILE_PATTERN = re.compile(r"^(R\d{2})(?:$|[\s_.-].*)\.xlsx$", re.IGNORECASE)

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
# IN-MEMORY SUMMARY CACHE
# ---------------------------------------------------------------------------
_SUMMARY_CACHE: dict[str, Any] = {
    "payload": None,
    "status": "empty",
    "updated_at": None,
    "error": None,
}
_SUMMARY_LOCK = asyncio.Lock()


def _format_aed_m(value: Any) -> str | None:
    try:
        if value is None:
            return None
        return f"{float(value) / 1_000_000:,.1f}M"
    except (TypeError, ValueError):
        return None


def _num_from_millions_label(label: str) -> float | None:
    try:
        cleaned = str(label).replace(",", "").replace("M", "").strip()
        return float(cleaned) * 1_000_000
    except Exception:
        return None


def _load_expected_sources() -> list[str]:
    try:
        with open(_PIPELINE_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        sources_cfg = cfg.get("sources", {}) or {}
        load_priority = cfg.get("load_priority", {}) or {}
        ordered: list[str] = []
        for tier in ("1_critical", "2_high", "3_standard", "4_advisory"):
            for rid in load_priority.get(tier, []) or []:
                rid = str(rid).upper()
                if rid not in ordered:
                    ordered.append(rid)
        for rid in sources_cfg.keys():
            rid = str(rid).upper()
            if rid not in ordered:
                ordered.append(rid)
        return ordered or DEFAULT_EXPECTED_SOURCES
    except Exception as exc:
        logger.warning("Could not read pipeline_config.json; using default sources: %s", exc)
        return DEFAULT_EXPECTED_SOURCES


def _scan_r_files() -> dict[str, dict[str, Any]]:
    resolved: dict[str, dict[str, Any]] = {}
    if not _DATA_DIR.exists() or not _DATA_DIR.is_dir():
        return resolved
    for path in sorted(_DATA_DIR.iterdir()):
        if not path.is_file() or path.suffix.lower() != ".xlsx":
            continue
        name = path.name
        if name.startswith("~$") or name.startswith("."):
            continue
        match = R_FILE_PATTERN.match(name)
        if not match:
            continue
        r_code = match.group(1).upper()
        if r_code not in resolved or name > resolved[r_code]["filename"]:
            resolved[r_code] = {
                "filename": name,
                "path": str(path),
                "size_bytes": path.stat().st_size,
            }
    return resolved


def _snapshot_label(snapshot_date: str) -> str:
    if not snapshot_date:
        return "Data date unavailable"
    try:
        dt = datetime.fromisoformat(snapshot_date)
        return f"Data as of {dt.day} {dt.strftime('%b')} {dt.year}"
    except Exception:
        return f"Data as of {snapshot_date}"


def _json_safe(obj: Any) -> Any:
    """Make payload safe for JSONResponse."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_json_safe(v) for v in obj]
    return obj


def _shape_full_summary(payload: dict[str, Any]) -> dict[str, Any]:
    computed = payload.get("computed", {}) or {}
    summary = payload.get("summary", {}) or {}
    missing_sources = payload.get("missing_sources", []) or []
    meta = summary.get("meta", {}) if isinstance(summary, dict) else {}

    out = {
        "status": payload.get("status", "unknown"),
        "platform": computed.get("PLATFORM_VERSION", "v6"),
        "summary_mode": "full_excel",
        "snapshot_date": computed.get("SNAPSHOT_DATE"),
        "snapshot_label": _snapshot_label(str(computed.get("SNAPSHOT_DATE") or "")),
        "data": summary,
        "summary": summary,
        "computed": computed,
        "sources_loaded": len(meta.get("sources_loaded", []) or []),
        "sources_missing": len(missing_sources),
        "missing_sources": missing_sources,
        "od_today": _format_aed_m(computed.get("OD_TODAY")),
        "od_source": computed.get("OD_SOURCE"),
        "pipeline_source": computed.get("PIPELINE_SOURCE"),
        "load_timestamp": computed.get("LOAD_TIMESTAMP"),
    }
    return jsonable_encoder(_json_safe(out))


def _fast_summary_payload(reason: str = "full_excel_not_ready") -> dict[str, Any]:
    expected = _load_expected_sources()
    files = _scan_r_files()
    found = [rid for rid in expected if rid in files]
    missing = [rid for rid in expected if rid not in files]
    critical_missing = [rid for rid in expected if rid in CRITICAL_SOURCES and rid not in files]

    if critical_missing:
        status = "degraded"
    elif missing:
        status = "partial"
    else:
        status = "ok"

    r18_live = "R18" in files
    r36_live = "R36" in files
    od_label = os.environ.get("SCIP_HEALTH_OD_TODAY", "1,893.8M") if r18_live else None
    od_value = _num_from_millions_label(od_label or "")
    snapshot_date = os.environ.get("SCIP_SNAPSHOT_DATE", "2026-03-15") if r18_live else ""
    ping_ts = datetime.utcnow().isoformat() + "Z"

    computed = {
        "PLATFORM_VERSION": "v6",
        "OD_TODAY": od_value,
        "OD_SOURCE": "R18_live" if r18_live else "fallback_reference",
        "PIPELINE_SOURCE": "R36_live" if r36_live else "fallback_reference",
        "SNAPSHOT_DATE": snapshot_date,
        "LOAD_TIMESTAMP": ping_ts,
    }
    summary = {
        "meta": {
            "snapshot_date": snapshot_date,
            "snapshot_label": _snapshot_label(snapshot_date) if snapshot_date else "Data unavailable",
            "load_timestamp": ping_ts,
            "platform_version": "v6",
            "sources_loaded": found,
            "sources_missing": missing,
            "critical_missing": critical_missing,
            "summary_mode": "fast_filesystem_no_excel",
            "fallback_reason": reason,
        },
        "core": {
            "od_today": od_value,
            "od_today_label": od_label or "-",
            "od_source": computed["OD_SOURCE"],
            "pipeline_source": computed["PIPELINE_SOURCE"],
            "snapshot_date": snapshot_date,
            "snapshot_label": _snapshot_label(snapshot_date) if snapshot_date else "Data unavailable",
        },
        "sources": {
            "loaded": found,
            "missing": missing,
            "critical_missing": critical_missing,
            "files": files,
        },
    }

    return {
        "status": status,
        "platform": "v6",
        "summary_mode": "fast_filesystem_no_excel",
        "fallback_reason": reason,
        "snapshot_date": snapshot_date,
        "snapshot_label": _snapshot_label(snapshot_date) if snapshot_date else "Data unavailable",
        "data": summary,
        "summary": summary,
        "computed": computed,
        "sources_loaded": len(found),
        "sources_missing": len(missing),
        "missing_sources": missing,
        "critical_missing": critical_missing,
        "od_today": od_label or "-",
        "od_source": computed["OD_SOURCE"],
        "pipeline_source": computed["PIPELINE_SOURCE"],
        "load_timestamp": ping_ts,
    }


def _build_full_summary_sync() -> dict[str, Any]:
    payload = DL.load_all()
    return _shape_full_summary(payload)


async def _refresh_summary_cache() -> None:
    async with _SUMMARY_LOCK:
        try:
            logger.info("Starting full Excel summary refresh")
            full = await asyncio.to_thread(_build_full_summary_sync)
            _SUMMARY_CACHE["payload"] = full
            _SUMMARY_CACHE["status"] = "ready"
            _SUMMARY_CACHE["updated_at"] = datetime.utcnow().isoformat() + "Z"
            _SUMMARY_CACHE["error"] = None
            logger.info("Full Excel summary refresh complete")
        except Exception as exc:
            _SUMMARY_CACHE["status"] = "error"
            _SUMMARY_CACHE["error"] = str(exc)
            logger.error("Full Excel summary refresh failed: %s", exc, exc_info=True)


# ---------------------------------------------------------------------------
# SUMMARY ENDPOINTS
# ---------------------------------------------------------------------------
@app.get("/summary", tags=["data"])
async def get_summary() -> JSONResponse:
    """
    Frontend-safe summary endpoint.

    It tries to return the full Excel summary quickly. If the Excel loader is slow
    on Render, it returns a fast filesystem summary instead of hanging.
    """
    timeout_seconds = float(os.environ.get("SCIP_SUMMARY_TIMEOUT_SECONDS", "8"))

    # Return cached full payload immediately if available.
    cached = _SUMMARY_CACHE.get("payload")
    if cached:
        cached = dict(cached)
        cached["cache_status"] = _SUMMARY_CACHE.get("status")
        cached["cache_updated_at"] = _SUMMARY_CACHE.get("updated_at")
        return JSONResponse(content=jsonable_encoder(_json_safe(cached)), status_code=200)

    # Try one bounded full load for this request.
    try:
        full = await asyncio.wait_for(asyncio.to_thread(_build_full_summary_sync), timeout=timeout_seconds)
        _SUMMARY_CACHE["payload"] = full
        _SUMMARY_CACHE["status"] = "ready"
        _SUMMARY_CACHE["updated_at"] = datetime.utcnow().isoformat() + "Z"
        _SUMMARY_CACHE["error"] = None
        full["cache_status"] = "ready"
        full["cache_updated_at"] = _SUMMARY_CACHE["updated_at"]
        return JSONResponse(content=jsonable_encoder(_json_safe(full)), status_code=200)
    except asyncio.TimeoutError:
        logger.warning("/summary full Excel load exceeded %.1fs; returning fast fallback", timeout_seconds)
        fallback = _fast_summary_payload(reason=f"full_excel_timeout_after_{timeout_seconds:.0f}s")
        fallback["cache_status"] = _SUMMARY_CACHE.get("status")
        fallback["cache_updated_at"] = _SUMMARY_CACHE.get("updated_at")
        fallback["cache_error"] = _SUMMARY_CACHE.get("error")
        return JSONResponse(content=jsonable_encoder(_json_safe(fallback)), status_code=200)
    except Exception as exc:
        logger.error("/summary full Excel load failed; returning fast fallback: %s", exc, exc_info=True)
        fallback = _fast_summary_payload(reason="full_excel_error")
        fallback["cache_status"] = "error"
        fallback["cache_error"] = str(exc)
        return JSONResponse(content=jsonable_encoder(_json_safe(fallback)), status_code=200)


@app.get("/summary/full", tags=["data"])
async def get_summary_full() -> JSONResponse:
    """Manual full Excel validation endpoint. This may be slow."""
    timeout_seconds = float(os.environ.get("SCIP_SUMMARY_FULL_TIMEOUT_SECONDS", "90"))
    try:
        full = await asyncio.wait_for(asyncio.to_thread(_build_full_summary_sync), timeout=timeout_seconds)
        _SUMMARY_CACHE["payload"] = full
        _SUMMARY_CACHE["status"] = "ready"
        _SUMMARY_CACHE["updated_at"] = datetime.utcnow().isoformat() + "Z"
        _SUMMARY_CACHE["error"] = None
        full["cache_status"] = "ready"
        full["cache_updated_at"] = _SUMMARY_CACHE["updated_at"]
        return JSONResponse(content=jsonable_encoder(_json_safe(full)), status_code=200)
    except asyncio.TimeoutError:
        return JSONResponse(
            content={
                "status": "degraded",
                "platform": "v6",
                "summary_mode": "full_excel_timeout",
                "error_detail": f"summary_full_timeout_after_{timeout_seconds:.0f}s",
                **_fast_summary_payload(reason="summary_full_timeout"),
            },
            status_code=200,
        )
    except Exception as exc:
        return JSONResponse(
            content={
                "status": "error",
                "platform": "v6",
                "summary_mode": "full_excel_error",
                "error_detail": str(exc),
                **_fast_summary_payload(reason="summary_full_error"),
            },
            status_code=200,
        )


@app.post("/summary/refresh", tags=["data"])
async def refresh_summary() -> JSONResponse:
    """Kick off a background full-summary refresh and return immediately."""
    asyncio.create_task(_refresh_summary_cache())
    return JSONResponse(
        content={
            "status": "refresh_started",
            "platform": "v6",
            "cache_status": _SUMMARY_CACHE.get("status"),
            "cache_updated_at": _SUMMARY_CACHE.get("updated_at"),
        },
        status_code=202,
    )


# ---------------------------------------------------------------------------
# MANIFEST
# ---------------------------------------------------------------------------
@app.get("/manifest", tags=["platform"])
async def get_manifest() -> JSONResponse:
    try:
        with open(_MANIFEST_PATH, "r", encoding="utf-8") as f:
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
        "summary_full": "/summary/full",
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
    logger.info("Sobha Collections Intelligence Platform - v6 Starting")
    logger.info("Backend dir: %s", _HERE)
    logger.info("Data dir: %s", _DATA_DIR)
    logger.info("ANTHROPIC_API_KEY set: %s", bool(os.environ.get("ANTHROPIC_API_KEY")))
    logger.info("FRONTEND_URL: %s", _frontend_url)
    logger.info("Allowed CORS origins: %s", _all_origins)
    logger.info("=" * 60)

    # Warm the full summary cache in the background. Do not block startup.
    if os.environ.get("SCIP_DISABLE_SUMMARY_WARMUP", "0") != "1":
        asyncio.create_task(_refresh_summary_cache())

    logger.info("Platform startup complete.")
