"""
SCIP warmup_state.py — W1 concurrent-boot state machine (additive).

Single source of truth for boot progress when SCIP_CONCURRENT_BOOT=true:

    cold -> downloading_sources -> parsing_sources -> warm
                                |-> warmup_failed (reason)

State lives in process memory only — never persisted — so a restart always
recovers to a clean cold boot (no poisoned state).

Trust rules honored here:
- Warming/warmup_failed envelopes are body-only (no new X-SCIP-* headers).
- confidence_state is "unavailable"; no figures, no partial values, ever.
- When SCIP_CONCURRENT_BOOT is false (default), gate_response() is always
  None and every endpoint behaves exactly as before this wave.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

STATE_COLD = "cold"
STATE_DOWNLOADING = "downloading_sources"
STATE_PARSING = "parsing_sources"
STATE_WARM = "warm"
STATE_FAILED = "warmup_failed"

VALID_STATES = (STATE_COLD, STATE_DOWNLOADING, STATE_PARSING, STATE_WARM, STATE_FAILED)

WARMING_DETAIL = (
    "R-series sources are loading. No figures are served until the "
    "lineage-backed payload is ready."
)
FAILED_DETAIL = (
    "R-series source warmup failed. No figures are served; a service restart "
    "retries the bootstrap from a clean state."
)
RETRY_AFTER_SECONDS = 4

_LOCK = threading.RLock()
_STATE = STATE_COLD
_REASON: Optional[str] = None
_BOOT_STARTED_AT_EPOCH: Optional[float] = None
_BOOT_STARTED_AT_ISO: Optional[str] = None
_STAGE_STARTED_AT_EPOCH: Optional[float] = None
_STAGE_STARTED_AT_ISO: Optional[str] = None


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def is_concurrent_boot_enabled() -> bool:
    return os.environ.get("SCIP_CONCURRENT_BOOT", "false").strip().lower() == "true"


def set_state(state: str, reason: Optional[str] = None) -> None:
    """Advance the boot state machine. Thread-safe; logs every transition."""
    global _STATE, _REASON, _BOOT_STARTED_AT_EPOCH, _BOOT_STARTED_AT_ISO
    global _STAGE_STARTED_AT_EPOCH, _STAGE_STARTED_AT_ISO
    if state not in VALID_STATES:
        raise ValueError(f"unknown warmup state: {state}")
    with _LOCK:
        previous = _STATE
        _STATE = state
        _REASON = reason if state == STATE_FAILED else None
        now_epoch = time.time()
        now_iso = _iso_now()
        if _BOOT_STARTED_AT_EPOCH is None or state == STATE_DOWNLOADING:
            _BOOT_STARTED_AT_EPOCH = now_epoch
            _BOOT_STARTED_AT_ISO = now_iso
        _STAGE_STARTED_AT_EPOCH = now_epoch
        _STAGE_STARTED_AT_ISO = now_iso
    logger.info("SCIP warmup state: %s -> %s%s", previous, state, f" (reason: {reason})" if reason else "")


def get_state() -> str:
    with _LOCK:
        return _STATE


def get_reason() -> Optional[str]:
    with _LOCK:
        return _REASON


def snapshot() -> Dict[str, Any]:
    """Warmup block for /health. Body-only, no values, no headers."""
    with _LOCK:
        state = _STATE
        reason = _REASON
        stage_started_iso = _STAGE_STARTED_AT_ISO
        stage_started_epoch = _STAGE_STARTED_AT_EPOCH
    if not is_concurrent_boot_enabled():
        return {"state": "disabled", "stage_started_at": None, "elapsed_seconds": None}
    elapsed = None if stage_started_epoch is None else round(time.time() - stage_started_epoch, 1)
    block: Dict[str, Any] = {
        "state": state,
        "stage_started_at": stage_started_iso,
        "elapsed_seconds": elapsed,
    }
    if state == STATE_FAILED and reason:
        block["reason"] = reason
    return block


def warming_envelope() -> Dict[str, Any]:
    """Warming/warmup_failed response body per the W1 contract (HTTP 200)."""
    with _LOCK:
        state = _STATE
        reason = _REASON
        started_iso = _BOOT_STARTED_AT_ISO or _iso_now()
    if state == STATE_FAILED:
        envelope: Dict[str, Any] = {
            "scip_state": "warmup_failed",
            "stage": STATE_FAILED,
            "started_at": started_iso,
            "confidence_state": "unavailable",
            "detail": FAILED_DETAIL,
            "retry_after_seconds": RETRY_AFTER_SECONDS,
        }
        if reason:
            envelope["reason"] = reason
        return envelope
    # cold means the boot thread has not transitioned yet; report the first
    # contract stage rather than inventing a new one.
    stage = state if state in (STATE_DOWNLOADING, STATE_PARSING) else STATE_DOWNLOADING
    return {
        "scip_state": "warming",
        "stage": stage,
        "started_at": started_iso,
        "confidence_state": "unavailable",
        "detail": WARMING_DETAIL,
        "retry_after_seconds": RETRY_AFTER_SECONDS,
    }


def gate_response() -> Optional[Dict[str, Any]]:
    """Return the warming envelope if a core endpoint must not serve figures.

    None when concurrent boot is disabled (default — existing behavior) or
    when the boot reached warm. Never raises.
    """
    if not is_concurrent_boot_enabled():
        return None
    if get_state() == STATE_WARM:
        return None
    return warming_envelope()


def reset_for_tests() -> None:
    """Smoke-test helper; never called by runtime code."""
    global _STATE, _REASON, _BOOT_STARTED_AT_EPOCH, _BOOT_STARTED_AT_ISO
    global _STAGE_STARTED_AT_EPOCH, _STAGE_STARTED_AT_ISO
    with _LOCK:
        _STATE = STATE_COLD
        _REASON = None
        _BOOT_STARTED_AT_EPOCH = None
        _BOOT_STARTED_AT_ISO = None
        _STAGE_STARTED_AT_EPOCH = None
        _STAGE_STARTED_AT_ISO = None
