"""
SOBHA COLLECTIONS INTELLIGENCE PLATFORM
health_endpoint.py - Phase 5 safe health endpoint

Purpose:
  - Keep GET /health from hanging forever on Render/Swagger
  - Run data_loader.load_all() in a worker thread
  - Return HTTP 200 even if data loading errors or times out
  - Preserve the existing Phase 5 response shape

Upload location:
  Backend/health_endpoint.py
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter

import data_loader as DL
import utils as U

router = APIRouter()
logger = logging.getLogger(__name__)

HEALTH_TIMEOUT_SECONDS = float(os.environ.get("HEALTH_TIMEOUT_SECONDS", "25"))


def _fmt_od(value: Any) -> str:
    try:
        if value is None:
            return "—"
        return U.fmt_aed_millions(value)
    except Exception:
        return "—"


async def _load_payload_with_timeout() -> dict:
    """Run the Excel/data load outside the event loop and cap wait time."""
    return await asyncio.wait_for(
        asyncio.to_thread(DL.load_all),
        timeout=HEALTH_TIMEOUT_SECONDS,
    )


@router.get("/health")
async def health_check() -> dict:
    """
    Platform health + warm-up endpoint.

    Always returns HTTP 200. The JSON `status` field carries the real state:
      ok | partial | degraded | error
    """
    ping_ts = datetime.utcnow().isoformat() + "Z"

    try:
        payload = await _load_payload_with_timeout()

        status = payload.get("status", "unknown")
        summary = payload.get("summary", {}) or {}
        summary_meta = summary.get("meta", {}) or {}

        sources_loaded = summary_meta.get("sources_loaded", []) or []
        sources_missing = summary_meta.get("sources_missing", []) or payload.get("missing_sources", []) or []

        od_today_raw = DL.get_computed(payload, "OD_TODAY")
        od_today_fmt = _fmt_od(od_today_raw)
        od_source = DL.get_computed(payload, "OD_SOURCE", "unknown")

        snapshot_date = DL.get_computed(payload, "SNAPSHOT_DATE", "")
        snapshot_label = U.fmt_snapshot_label(snapshot_date) if snapshot_date else "Data unavailable"
        platform = DL.get_computed(payload, "PLATFORM_VERSION", "v6")
        load_timestamp = DL.get_computed(payload, "LOAD_TIMESTAMP", ping_ts)
        pipeline_source = DL.get_computed(payload, "PIPELINE_SOURCE", "unknown")

        logger.info(
            "Health check OK. status=%s od_today=%s od_source=%s pipeline_source=%s sources=%d/%d",
            status,
            od_today_fmt,
            od_source,
            pipeline_source,
            len(sources_loaded),
            len(sources_loaded) + len(sources_missing),
        )

        return {
            "status": status,
            "platform": platform,
            "od_today": od_today_fmt,
            "od_source": od_source,
            "pipeline_source": pipeline_source,
            "snapshot_date": snapshot_date,
            "snapshot_label": snapshot_label,
            "sources_loaded": len(sources_loaded),
            "sources_missing": len(sources_missing),
            "missing_sources": sources_missing,
            "load_timestamp": load_timestamp,
            "ping_ts": ping_ts,
        }

    except asyncio.TimeoutError:
        logger.error("Health check timed out after %.1fs", HEALTH_TIMEOUT_SECONDS)
        return {
            "status": "degraded",
            "platform": "v6",
            "od_today": "—",
            "od_source": "health_timeout",
            "pipeline_source": "health_timeout",
            "snapshot_date": "",
            "snapshot_label": "Data load timed out",
            "sources_loaded": 0,
            "sources_missing": 0,
            "missing_sources": [],
            "load_timestamp": "",
            "ping_ts": ping_ts,
            "error_detail": f"health_timeout_after_{HEALTH_TIMEOUT_SECONDS:.0f}s",
        }

    except Exception as exc:
        logger.error("Health check error: %s", exc, exc_info=True)
        return {
            "status": "error",
            "platform": "v6",
            "od_today": "—",
            "od_source": "unavailable",
            "pipeline_source": "unavailable",
            "snapshot_date": "",
            "snapshot_label": "Data unavailable",
            "sources_loaded": 0,
            "sources_missing": 0,
            "missing_sources": [],
            "load_timestamp": "",
            "ping_ts": ping_ts,
            "error_detail": str(exc),
        }
