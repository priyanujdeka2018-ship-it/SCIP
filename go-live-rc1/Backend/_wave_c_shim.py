"""
SCIP _wave_c_shim.py - LOCAL TEST FALLBACK ONLY

constrained_editorial.py imports the real `quickball_provider_gate` and
`llm_providers` when they are present (on the deployment). When they are not
(local dev / this environment), it falls back to this shim. The gate logic here
is a faithful transcription of the real quickball_provider_gate so that the
lineage-block behaviour under test matches production. Do not deploy this file
as the provider implementation; it exists so the Wave C smoke can run anywhere.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any, Mapping

REQUIRED_CRITICAL_LINEAGE_FIELDS = (
    "source_file", "report_code", "sheet", "snapshot_date",
    "reporting_basis", "validation_status", "confidence_state", "lineage_hash",
)


def missing_lineage_fields(lineage: Mapping[str, Any] | None) -> list:
    if not lineage:
        return list(REQUIRED_CRITICAL_LINEAGE_FIELDS)
    return [n for n in REQUIRED_CRITICAL_LINEAGE_FIELDS if not lineage.get(n)]


def should_block_quickball_answer(*, is_critical: bool, lineage: Mapping[str, Any] | None):
    missing = missing_lineage_fields(lineage)
    if is_critical and missing:
        return True, "blocked_lineage_missing", missing
    return False, None, []


def blocked_response(*, correlation_id: str, missing_fields: list) -> dict:
    return {
        "status": "blocked",
        "blocked_reason": "blocked_lineage_missing",
        "message": "I cannot answer this as trusted because required lineage is missing.",
        "missing_lineage_fields": missing_fields,
        "correlation_id": correlation_id,
    }


@dataclass
class LLMRequest:
    system_prompt: str
    user_prompt: str
    correlation_id: str
    metadata: dict


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    latency_ms: int
    prompt_policy_version: str
    response_hash: str


def build_llm_request(*, system_prompt, user_prompt, correlation_id, metadata):
    return LLMRequest(system_prompt, user_prompt, correlation_id, metadata or {})


class _MockProvider:
    provider = "mock"
    model = "mock-1"

    def complete(self, request: LLMRequest) -> LLMResponse:
        # The mock echoes the facts it was given - it never invents a number.
        text = request.metadata.get("_mock_echo", "Source-backed summary unavailable.")
        return LLMResponse(text, self.provider, self.model, 1,
                           "quickball-prompt-policy-v1",
                           hashlib.sha256(text.encode()).hexdigest())


def get_llm_provider():
    return _MockProvider()


def provider_health() -> dict:
    return {"provider": "mock", "model": "mock-1"}
