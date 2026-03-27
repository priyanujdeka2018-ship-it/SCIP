"""
SOBHA COLLECTIONS INTELLIGENCE PLATFORM
quickball.py — Claude API Relay Endpoint
Version: v6
Authority: MASTER_ARCHITECTURE_v9.1.md

Location: /backend/quickball.py

Responsibilities:
  - Single POST /quickball endpoint
  - Receives question + conversation history from React frontend
  - Loads manifest.json + computed dict from data_loader
  - Calls Claude API (claude-sonnet-4-20250514) via ANTHROPIC_API_KEY env var
  - Returns: annotation (AI text) + route (submodule) + actions (up to 3 buttons)
  - 1-hour response cache for identical questions (reduces API cost)
  - Usage logging: every query logged with timestamp, question_hash, tokens_used
  - Graceful degradation: if Claude API fails → returns structured offline response

Dependency rule (non-negotiable):
  quickball.py  →  imports: data_loader, utils, FastAPI, httpx, json, hashlib
  quickball.py  →  NEVER imports: endpoints/context, endpoints/pulse, endpoints/tools
  quickball.py  →  ZERO computation. ZERO business logic.
  quickball.py  →  API key ONLY from env var. Never in any file or response.

Architecture rules:
  - Cache key = SHA256 hash of (question.strip().lower() + entity_filter)
  - Cache TTL = 3600 seconds (1 hour)
  - Usage log = append-only JSONL file at /backend/usage_log.jsonl
  - Claude model: claude-sonnet-4-20250514 (always Sonnet 4 — never Haiku in prod)
  - System prompt: includes manifest + computed summary. Never raw row data.
  - Response always returns HTTP 200 — even in error state
  - Token budget: max_tokens=1000 (sufficient for annotation + route + 3 actions)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import data_loader as DL

# ---------------------------------------------------------------------------
# ROUTER
# ---------------------------------------------------------------------------
router = APIRouter()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
_HERE = Path(__file__).parent
MANIFEST_PATH  = _HERE / "manifest.json"
USAGE_LOG_PATH = _HERE / "usage_log.jsonl"

# ---------------------------------------------------------------------------
# CACHE
# ---------------------------------------------------------------------------
# Simple in-memory dict cache. TTL: 3600 seconds (1 hour).
# Key: SHA256(question_lower + entity_filter). Value: { "response": dict, "ts": float }
_CACHE: dict[str, dict] = {}
_CACHE_TTL_SECONDS = 3600

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL   = "claude-sonnet-4-20250514"
MAX_TOKENS     = 1000
MAX_HISTORY    = 10   # Cap conversation history sent to API (cost control)

# ---------------------------------------------------------------------------
# REQUEST / RESPONSE MODELS
# ---------------------------------------------------------------------------

class QuickballRequest(BaseModel):
    """
    Incoming request from React Quickball panel.

    Fields:
        question:    User's natural language question
        history:     Prior conversation turns (role: user|assistant, content: str)
        entity:      Active entity filter — "Group" | "Sobha" | "Siniya" | "DT"
        mode:        Active app mode — "ops" | "board"
    """
    question: str
    history:  list[dict] = []
    entity:   str = "Group"
    mode:     str = "ops"


class QuickballResponse(BaseModel):
    """
    Response sent to React Quickball panel.

    Fields:
        status:       "ok" | "cached" | "offline" | "error"
        annotation:   2–3 sentence Claude-generated interpretation
        route:        Submodule ID to surface (e.g. "S04_SM1") or None
        route_label:  Human label for the routed submodule
        actions:      Up to 3 action buttons with label + type + target
        tokens_used:  Tokens consumed (0 if cached/offline)
        cached:       True if served from cache
        ping_ts:      ISO timestamp of this call
    """
    status:       str
    annotation:   str
    route:        Optional[str]
    route_label:  Optional[str]
    actions:      list[dict]
    tokens_used:  int
    cached:       bool
    ping_ts:      str


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _cache_key(question: str, entity: str) -> str:
    """SHA256 hash of normalised question + entity for cache lookup."""
    raw = f"{question.strip().lower()}|{entity.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _cache_get(key: str) -> Optional[dict]:
    """Return cached response if present and not expired. Else None."""
    entry = _CACHE.get(key)
    if not entry:
        return None
    if time.time() - entry["ts"] > _CACHE_TTL_SECONDS:
        del _CACHE[key]
        return None
    return entry["response"]


def _cache_set(key: str, response: dict) -> None:
    """Store response in cache with current timestamp."""
    _CACHE[key] = {"response": response, "ts": time.time()}


def _log_usage(question_hash: str, tokens: int, cached: bool, status: str) -> None:
    """Append a usage record to usage_log.jsonl (append-only)."""
    record = {
        "ts":            datetime.now(timezone.utc).isoformat(),
        "question_hash": question_hash,
        "tokens_used":   tokens,
        "cached":        cached,
        "status":        status,
    }
    try:
        with open(USAGE_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as exc:
        logger.warning("Usage log write failed: %s", exc)


def _load_manifest() -> dict:
    """Load manifest.json. Returns empty submodules dict on failure."""
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Could not load manifest.json: %s", exc)
        return {"submodules": {}, "workflows": {}}


def _build_system_prompt(manifest: dict, computed: dict, entity: str, mode: str) -> str:
    """
    Build the system prompt for Claude.
    Includes: platform context, key computed metrics, manifest summary, response rules.
    Never includes raw row data — only pre-aggregated computed values.
    """
    # Format key metrics for the prompt
    od_today   = computed.get("OD_TODAY")
    od_fmt     = f"AED {od_today/1e6:,.1f}M" if od_today else "data pending"
    snap_date  = computed.get("SNAPSHOT_DATE", "")
    pipeline   = computed.get("PIPELINE_GROSS")
    pipe_fmt   = f"AED {pipeline/1e9:,.1f}B" if pipeline else "data pending"
    cy_mix     = computed.get("CY_ADV_MIX_YTD")
    cy_fmt     = f"{cy_mix:.1f}%" if cy_mix else "data pending"
    fy_dues    = computed.get("FY_DUES_TARGET")
    fy_fmt     = f"AED {fy_dues/1e9:,.1f}B" if fy_dues else "data pending"
    od_source  = computed.get("OD_SOURCE", "unknown")
    platform_v = computed.get("PLATFORM_VERSION", "v6")

    # Compact submodule index for routing intelligence
    submodule_index = []
    for sm_id, sm in manifest.get("submodules", {}).items():
        submodule_index.append(
            f"{sm_id} | {sm.get('label', '')} | answers: {', '.join(sm.get('answers', [])[:2])}"
        )
    sm_index_text = "\n".join(submodule_index) if submodule_index else "No submodules confirmed yet."

    prompt = f"""You are the AI assistant embedded in the Sobha Collections Intelligence Platform (v{platform_v}).
Owner: Priyanuj Deka — AGM Dues, Sobha Realty Dubai.
Platform: Real estate collections analytics covering Sobha, Siniya, and Downtown UAQ entities.

CURRENT SESSION CONTEXT:
- Active entity filter: {entity}
- Active mode: {mode.upper()} MODE
- OD Today (Group): {od_fmt} (source: {od_source}, as of {snap_date})
- Forward Pipeline: {pipe_fmt} (Total Forward Pipeline, R36)
- 2026 MDO Dues FY Target: {fy_fmt} (Dues only)
- CY Advance Mix YTD 2026: {cy_fmt}

KEY BUSINESS RULES (never violate):
- OD% = OD ÷ MS Due ITD (never ÷ purchase price)
- 30-Day Efficiency = Dues ÷ Booksize BOM (avg 34.8%, not 18%)
- Finance Dues = D+A combined. MDO Dues = Dues only. Always label which.
- Pipeline: 43.5B (gross) ≠ ~40B (narrative book) ≠ 37.8B (advance denom). Label each.
- CY_ADV_MIX_YTD = 81.1% (computed from R08 — never hardcoded)
- App payment share: COUNT basis only. 2026 YTD = 25.9%.
- NPV figures always labelled [PROJECTED] — never Actual.
- IC threshold (907.7M / 251 units at 0–10% paid) is read-only data — policy decision is a separate board business case.
- Org chart: Priyanuj → QCG (Garima, 12) | MIS (Asjad, 15) | Mathews team (38) | 12 RMs direct | 12 via Rohan→Akkad.

SUBMODULE INDEX (use for routing):
{sm_index_text}

RESPONSE FORMAT — you MUST return valid JSON only. No markdown. No preamble.
{{
  "annotation": "2-3 sentences interpreting the question with specific metrics. Reference actual numbers.",
  "route": "SUBMODULE_ID or null if no single submodule fits",
  "route_label": "Human label for the routed submodule or null",
  "actions": [
    {{"label": "Button label", "type": "scroll_to|tool_open|mode_switch", "target": "section_id or tool_id or mode"}}
  ]
}}

Rules for actions (maximum 3):
- type=scroll_to: target = section ID e.g. "S04"
- type=tool_open: target = tool ID e.g. "ToolRunRate"
- type=mode_switch: target = "board" or "ops"
- Only include actions that are genuinely useful for this question.

If data is unavailable or the question is outside platform scope, say so clearly in annotation. Route to null. No invented metrics."""

    return prompt


def _offline_response(ping_ts: str, reason: str = "Claude API unavailable") -> dict:
    """Return a structured offline/error response — always HTTP 200."""
    return {
        "status":      "offline",
        "annotation":  f"AI assistant temporarily unavailable: {reason}. Platform data and navigation are unaffected.",
        "route":       None,
        "route_label": None,
        "actions":     [],
        "tokens_used": 0,
        "cached":      False,
        "ping_ts":     ping_ts,
    }


# ---------------------------------------------------------------------------
# QUICKBALL ENDPOINT
# ---------------------------------------------------------------------------

@router.post("/quickball", tags=["quickball"])
async def quickball(request: QuickballRequest) -> JSONResponse:
    """
    Quickball AI relay endpoint.

    Flow:
      1. Check cache (1-hour TTL)
      2. Load manifest + computed dict from data_loader
      3. Build system prompt with live computed metrics
      4. Call Claude API via ANTHROPIC_API_KEY
      5. Parse response → annotation + route + actions
      6. Store in cache + log usage
      7. Return HTTP 200 always

    Request body: { question, history, entity, mode }
    Response:     { status, annotation, route, route_label, actions, tokens_used, cached, ping_ts }
    """
    ping_ts = datetime.now(timezone.utc).isoformat() + "Z"
    question = request.question.strip()

    if not question:
        return JSONResponse(content=_offline_response(ping_ts, "Empty question"), status_code=200)

    # ── Cache check ────────────────────────────────────────────────────────
    cache_key = _cache_key(question, request.entity)
    cached = _cache_get(cache_key)
    if cached:
        _log_usage(cache_key[:12], 0, cached=True, status="cached")
        logger.info("Quickball cache HIT for key=%s...", cache_key[:12])
        result = dict(cached)
        result["cached"]  = True
        result["ping_ts"] = ping_ts
        result["status"]  = "cached"
        return JSONResponse(content=result, status_code=200)

    # ── API key check ──────────────────────────────────────────────────────
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set — Quickball offline")
        _log_usage(cache_key[:12], 0, cached=False, status="no_api_key")
        return JSONResponse(
            content=_offline_response(ping_ts, "ANTHROPIC_API_KEY not configured"),
            status_code=200,
        )

    # ── Load manifest + computed ───────────────────────────────────────────
    try:
        manifest = _load_manifest()
        payload  = DL.load_all()
        computed = payload.get("computed", {})
    except Exception as exc:
        logger.error("Data load failed in quickball: %s", exc)
        return JSONResponse(
            content=_offline_response(ping_ts, "Data pipeline error"),
            status_code=200,
        )

    # ── Build messages ─────────────────────────────────────────────────────
    system_prompt = _build_system_prompt(manifest, computed, request.entity, request.mode)

    # Truncate history to MAX_HISTORY turns (cost control)
    history = request.history[-MAX_HISTORY:] if len(request.history) > MAX_HISTORY else request.history

    messages: list[dict] = []
    for turn in history:
        role    = turn.get("role", "user")
        content = turn.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    # Add current question
    messages.append({"role": "user", "content": question})

    # ── Claude API call ────────────────────────────────────────────────────
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                CLAUDE_API_URL,
                headers={
                    "Content-Type":      "application/json",
                    "x-api-key":         api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model":      CLAUDE_MODEL,
                    "max_tokens": MAX_TOKENS,
                    "system":     system_prompt,
                    "messages":   messages,
                },
            )

        if response.status_code != 200:
            logger.error("Claude API returned %s: %s", response.status_code, response.text[:300])
            _log_usage(cache_key[:12], 0, cached=False, status=f"api_error_{response.status_code}")
            return JSONResponse(
                content=_offline_response(ping_ts, f"Claude API error {response.status_code}"),
                status_code=200,
            )

        api_data    = response.json()
        raw_text    = api_data.get("content", [{}])[0].get("text", "")
        tokens_used = api_data.get("usage", {}).get("output_tokens", 0)

    except httpx.TimeoutException:
        logger.warning("Claude API timeout for question=%s...", question[:40])
        _log_usage(cache_key[:12], 0, cached=False, status="timeout")
        return JSONResponse(
            content=_offline_response(ping_ts, "Claude API request timed out"),
            status_code=200,
        )
    except Exception as exc:
        logger.error("Claude API call failed: %s", exc)
        _log_usage(cache_key[:12], 0, cached=False, status="exception")
        return JSONResponse(
            content=_offline_response(ping_ts, str(exc)),
            status_code=200,
        )

    # ── Parse Claude JSON response ─────────────────────────────────────────
    try:
        # Strip markdown fences if present (defensive)
        clean = raw_text.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        clean = clean.strip()

        parsed: dict[str, Any] = json.loads(clean)

        annotation   = str(parsed.get("annotation", "See platform sections for details."))
        route        = parsed.get("route")          # may be None
        route_label  = parsed.get("route_label")    # may be None
        actions_raw  = parsed.get("actions", [])

        # Validate and cap actions at 3
        actions: list[dict] = []
        for action in actions_raw[:3]:
            if isinstance(action, dict) and action.get("label") and action.get("type"):
                actions.append({
                    "label":  str(action["label"]),
                    "type":   str(action["type"]),
                    "target": str(action.get("target", "")),
                })

    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        # Parsing failed — treat entire response as annotation
        logger.warning("Quickball response parse error: %s | raw=%s...", exc, raw_text[:100])
        annotation  = raw_text[:500] if raw_text else "Unable to parse AI response."
        route       = None
        route_label = None
        actions     = []

    # ── Lookup route label from manifest if not provided by Claude ─────────
    if route and not route_label:
        sm = manifest.get("submodules", {}).get(route, {})
        route_label = sm.get("label")

    # ── Build final response ───────────────────────────────────────────────
    result = {
        "status":      "ok",
        "annotation":  annotation,
        "route":       route,
        "route_label": route_label,
        "actions":     actions,
        "tokens_used": tokens_used,
        "cached":      False,
        "ping_ts":     ping_ts,
    }

    # ── Cache + log ────────────────────────────────────────────────────────
    _cache_set(cache_key, result)
    _log_usage(cache_key[:12], tokens_used, cached=False, status="ok")

    logger.info(
        "Quickball OK. question=%s... route=%s tokens=%d",
        question[:30], route, tokens_used
    )

    return JSONResponse(content=result, status_code=200)


# ---------------------------------------------------------------------------
# USAGE LOG ENDPOINT — for monitoring and cost tracking
# ---------------------------------------------------------------------------

@router.get("/quickball/usage", tags=["quickball"])
async def get_usage_log(limit: int = 50) -> JSONResponse:
    """
    Return the last N usage log entries.
    Used for monitoring Claude API cost trajectory.
    Priyanuj-only endpoint — not called by frontend.

    Query params:
        limit: Number of most-recent entries to return (default 50, max 500)
    """
    limit = min(max(1, limit), 500)
    try:
        with open(USAGE_LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        recent = lines[-limit:] if len(lines) >= limit else lines
        records = [json.loads(line) for line in recent if line.strip()]
        total_tokens = sum(r.get("tokens_used", 0) for r in records if not r.get("cached"))
        return JSONResponse(content={
            "count":        len(records),
            "total_tokens": total_tokens,
            "records":      records,
        }, status_code=200)
    except FileNotFoundError:
        return JSONResponse(content={"count": 0, "total_tokens": 0, "records": []}, status_code=200)
    except Exception as exc:
        logger.error("Usage log read failed: %s", exc)
        return JSONResponse(content={"error": str(exc)}, status_code=200)


# ---------------------------------------------------------------------------
# CACHE CLEAR ENDPOINT — for development / stale data refresh
# ---------------------------------------------------------------------------

@router.post("/quickball/cache/clear", tags=["quickball"])
async def clear_cache() -> JSONResponse:
    """
    Clear the in-memory Quickball response cache.
    Use after a data push to ensure fresh responses.
    Development/admin endpoint — not called by frontend.
    """
    count = len(_CACHE)
    _CACHE.clear()
    logger.info("Quickball cache cleared. %d entries removed.", count)
    return JSONResponse(content={
        "status":  "cleared",
        "removed": count,
        "ping_ts": datetime.now(timezone.utc).isoformat() + "Z",
    }, status_code=200)
