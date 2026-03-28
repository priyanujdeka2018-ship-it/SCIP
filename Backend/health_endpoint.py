"""
SOBHA COLLECTIONS INTELLIGENCE PLATFORM
health_endpoint.py — Platform Health Endpoint
Version: v6
(Renamed from endpoints/health.py to avoid subpackage import issues on Render)
"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter

import data_loader as DL
import utils as U

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check() -> dict:
    ping_ts = datetime.utcnow().isoformat() + "Z"

    try:
        payload = DL.load_all()

        status          = payload.get("status", "unknown")
        summary_meta    = payload.get("summary", {}).get("meta", {})
        sources_loaded  = summary_meta.get("sources_loaded", [])
        sources_missing = summary_meta.get("sources_missing", [])

        od_today_raw = DL.get_computed(payload, "OD_TODAY")
        od_today_fmt = U.fmt_aed_millions(od_today_raw) if od_today_raw is not None else "—"
        od_source    = DL.get_computed(payload, "OD_SOURCE", "unknown")

        snapshot_date  = DL.get_computed(payload, "SNAPSHOT_DATE", "")
        snapshot_label = U.fmt_snapshot_label(snapshot_date)
        platform       = DL.get_computed(payload, "PLATFORM_VERSION", "v6")
        load_timestamp = DL.get_computed(payload, "LOAD_TIMESTAMP", ping_ts)

        logger.info("Health check OK. status=%s od_today=%s sources=%d/%d",
                    status, od_today_fmt, len(sources_loaded),
                    len(sources_loaded) + len(sources_missing))

        return {
            "status":          status,
            "platform":        platform,
            "od_today":        od_today_fmt,
            "od_source":       od_source,
            "snapshot_date":   snapshot_date,
            "snapshot_label":  snapshot_label,
            "sources_loaded":  len(sources_loaded),
            "sources_missing": len(sources_missing),
            "missing_sources": sources_missing,
            "load_timestamp":  load_timestamp,
            "ping_ts":         ping_ts,
        }

    except Exception as exc:
        logger.error("Health check error: %s", exc, exc_info=True)
        return {
            "status":          "error",
            "platform":        "v6",
            "od_today":        "—",
            "od_source":       "unavailable",
            "snapshot_date":   "",
            "snapshot_label":  "Data unavailable",
            "sources_loaded":  0,
            "sources_missing": 0,
            "missing_sources": [],
            "load_timestamp":  "",
            "ping_ts":         ping_ts,
            "error_detail":    str(exc),
        }
