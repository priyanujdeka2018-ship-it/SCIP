"""
SCIP Batch 8 - Workflow assignment and closure tracking.

Built on top of Batch 7 account-level action queues. This module is intentionally
lightweight and auditable: it stores workflow state in memory for the patch pack,
keeps immutable lineage references to the source action, and blocks assignment or
closure if the Batch 7 account-action gate is not satisfied.

Production note: replace the in-memory WORKFLOW_STORE / EVENT_LOG with a durable
DB table using the same contract. Do not mutate source lineage in workflow rows.
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    from fastapi import APIRouter, Body, HTTPException
    from fastapi.responses import JSONResponse
except Exception:  # pragma: no cover
    APIRouter = None
    Body = None
    HTTPException = Exception
    JSONResponse = None

from account_action_queues import build_action_queue_payload

WORKFLOW_STATES = [
    "queued",
    "assigned",
    "in_progress",
    "promised",
    "escalated",
    "closed",
    "stale",
    "blocked",
]

TERMINAL_STATES = {"closed", "blocked"}

ROLE_PERMISSIONS: Dict[str, Dict[str, Any]] = {
    "collector_rm": {
        "can_assign": False,
        "can_reassign": False,
        "can_set_due_date": True,
        "can_update_disposition": True,
        "can_attach_evidence": True,
        "can_close": True,
        "allowed_action_visibility": {"collector_rm"},
        "closure_requires_evidence": False,
    },
    "cco_gm_agm": {
        "can_assign": True,
        "can_reassign": True,
        "can_set_due_date": True,
        "can_update_disposition": True,
        "can_attach_evidence": True,
        "can_close": True,
        "allowed_action_visibility": {"cco_gm_agm", "collector_rm"},
        "closure_requires_evidence": False,
    },
    "finance": {
        "can_assign": True,
        "can_reassign": True,
        "can_set_due_date": True,
        "can_update_disposition": True,
        "can_attach_evidence": True,
        "can_close": True,
        "allowed_action_visibility": {"finance"},
        "closure_requires_evidence": False,
    },
    "mis_qcg_admin": {
        "can_assign": True,
        "can_reassign": True,
        "can_set_due_date": True,
        "can_update_disposition": True,
        "can_attach_evidence": True,
        "can_close": True,
        "allowed_action_visibility": {"mis_qcg_admin", "finance", "cco_gm_agm", "collector_rm"},
        "closure_requires_evidence": False,
    },
}

WORKFLOW_STORE: Dict[str, Dict[str, Any]] = {}
EVENT_LOG: List[Dict[str, Any]] = []
_SEEDED = False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _deepcopy(value: Any) -> Any:
    return copy.deepcopy(value)


def _lineage_hash(lineage_refs: Iterable[Dict[str, Any]]) -> str:
    canonical = json.dumps(list(lineage_refs or []), sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _has_lineage(action: Dict[str, Any]) -> bool:
    refs = action.get("lineage_refs") or []
    required = ["source_code", "source_file", "sheet", "cell_or_range", "validation_status", "confidence_state", "reporting_basis"]
    return bool(refs) and all(all(ref.get(k) for k in required) for ref in refs)


def _has_owner_entity_amount_or_status(action: Dict[str, Any]) -> bool:
    has_identity = bool(action.get("action_id") and action.get("account_id") and action.get("unit"))
    has_owner = bool(action.get("collector_rm_owner") or action.get("owner") or action.get("assigned_owner"))
    has_entity = bool(action.get("entity_code") and action.get("entity_display"))
    has_amount_or_status = action.get("amount_aed") is not None or bool(action.get("pr_status") or action.get("process_status"))
    has_ageing_or_process = bool(action.get("ageing_bucket") or action.get("process_ageing") or action.get("pr_status"))
    return has_identity and has_owner and has_entity and has_amount_or_status and has_ageing_or_process


def source_action_is_assignable(action: Dict[str, Any]) -> Tuple[bool, List[str]]:
    failures: List[str] = []
    if not _has_lineage(action):
        failures.append("missing_or_incomplete_source_lineage")
    if not _has_owner_entity_amount_or_status(action):
        failures.append("missing_owner_entity_amount_or_ageing_status")
    if not action.get("role_visibility"):
        failures.append("missing_role_visibility")
    if not action.get("reporting_basis"):
        failures.append("missing_reporting_basis")
    if not action.get("confidence_state"):
        failures.append("missing_confidence_state")
    return (not failures, failures)


def _workflow_id(action_id: str) -> str:
    return "wf::" + str(action_id).replace(" ", "_")


def _event_id(action_id: str, event_type: str) -> str:
    raw = f"{action_id}|{event_type}|{len(EVENT_LOG)+1}|{_now()}"
    return "evt_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _role_can_see(action: Dict[str, Any], role: str) -> bool:
    role = role or "mis_qcg_admin"
    perms = ROLE_PERMISSIONS.get(role)
    if not perms:
        return False
    visible = set(action.get("role_visibility") or [])
    return bool(visible.intersection(perms["allowed_action_visibility"]))


def _ensure_role_permission(role: str, permission: str, action: Optional[Dict[str, Any]] = None) -> None:
    perms = ROLE_PERMISSIONS.get(role)
    if not perms:
        raise PermissionError(f"unknown_role:{role}")
    if not perms.get(permission):
        raise PermissionError(f"role_not_allowed:{role}:{permission}")
    if action is not None and not _role_can_see(action, role):
        raise PermissionError(f"role_not_visible_for_action:{role}:{action.get('action_id')}")


def _flatten_actions(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    actions: Dict[str, Dict[str, Any]] = {}
    for role_payload in (payload.get("roles") or {}).values():
        for bucket in ("account_actions", "process_actions", "management_actions"):
            for action in role_payload.get(bucket) or []:
                aid = action.get("action_id")
                if aid and aid not in actions:
                    actions[aid] = action
    return list(actions.values())


def _make_initial_record(action: Dict[str, Any]) -> Dict[str, Any]:
    assignable, failures = source_action_is_assignable(action)
    state = "queued" if assignable else "blocked"
    refs = _deepcopy(action.get("lineage_refs") or [])
    assigned_owner = action.get("collector_rm_owner") or action.get("owner") or None
    return {
        "workflow_id": _workflow_id(action.get("action_id")),
        "source_action_id": action.get("action_id"),
        "action_type": action.get("action_type"),
        "grain": action.get("grain"),
        "title": action.get("title"),
        "summary": action.get("summary"),
        "recommended_action": action.get("recommended_action"),
        "role_visibility": action.get("role_visibility") or [],
        "workflow_state": state,
        "assigned_owner": assigned_owner,
        "original_owner": assigned_owner,
        "due_date": None,
        "disposition": None,
        "closure_reason": None,
        "closed_at": None,
        "stale_reason": None,
        "blocked_reason": ";".join(failures) if failures else None,
        "evidence_attachments": [],
        "event_count": 0,
        "source_snapshot": _deepcopy({
            "account_id": action.get("account_id"),
            "unit": action.get("unit"),
            "customer_name": action.get("customer_name"),
            "project": action.get("project"),
            "sub_project": action.get("sub_project"),
            "collector_rm_owner": action.get("collector_rm_owner"),
            "manager_name": action.get("manager_name"),
            "entity_code": action.get("entity_code"),
            "entity_display": action.get("entity_display"),
            "parent_entity_code": action.get("parent_entity_code"),
            "parent_entity_display": action.get("parent_entity_display"),
            "amount_aed": action.get("amount_aed"),
            "display_amount": action.get("display_amount"),
            "ageing_bucket": action.get("ageing_bucket"),
            "ptp_date": action.get("ptp_date"),
            "ptp_amount_aed": action.get("ptp_amount_aed"),
            "ptp_status": action.get("ptp_status"),
            "pr_status": action.get("pr_status"),
            "escalation_status": action.get("escalation_status"),
            "reporting_basis": action.get("reporting_basis"),
            "confidence_state": action.get("confidence_state"),
        }),
        "immutable_lineage_refs": refs,
        "lineage_hash": _lineage_hash(refs),
        "source_gate": {
            "assignable": assignable,
            "failures": failures,
            "rule": "assignment requires lineage + owner + entity + amount/status + ageing/process status + role visibility",
        },
        "created_at": _now(),
        "updated_at": _now(),
    }


def _append_event(record: Dict[str, Any], event_type: str, actor_role: str, actor: str, from_state: str, to_state: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    event = {
        "event_id": _event_id(record["source_action_id"], event_type),
        "workflow_id": record["workflow_id"],
        "source_action_id": record["source_action_id"],
        "event_type": event_type,
        "actor_role": actor_role,
        "actor": actor,
        "from_state": from_state,
        "to_state": to_state,
        "event_payload": payload or {},
        "immutable_lineage_refs": _deepcopy(record.get("immutable_lineage_refs") or []),
        "lineage_hash": record.get("lineage_hash"),
        "created_at": _now(),
    }
    EVENT_LOG.append(event)
    record["event_count"] = int(record.get("event_count") or 0) + 1
    record["updated_at"] = event["created_at"]
    return event


def reset_workflow_store() -> None:
    global _SEEDED
    WORKFLOW_STORE.clear()
    EVENT_LOG.clear()
    _SEEDED = False


def seed_workflows(data_dir: Optional[Path | str] = None, force: bool = False) -> Dict[str, Any]:
    global _SEEDED
    if _SEEDED and not force:
        return build_workflow_payload(role=None)
    if force:
        reset_workflow_store()
    payload = build_action_queue_payload(data_dir=data_dir)
    actions = _flatten_actions(payload)
    for action in actions:
        record = _make_initial_record(action)
        WORKFLOW_STORE[record["source_action_id"]] = record
        _append_event(record, "queued" if record["workflow_state"] == "queued" else "blocked", "system", "batch8_seed", "none", record["workflow_state"], {"source_action_title": action.get("title")})
    _SEEDED = True
    return build_workflow_payload(role=None)


def _get_record(action_id: str) -> Dict[str, Any]:
    if not _SEEDED:
        seed_workflows()
    record = WORKFLOW_STORE.get(action_id)
    if not record:
        raise KeyError(f"action_not_found:{action_id}")
    return record


def _source_action_for_record(record: Dict[str, Any]) -> Dict[str, Any]:
    snap = record.get("source_snapshot") or {}
    return {
        "action_id": record.get("source_action_id"),
        "role_visibility": record.get("role_visibility") or [],
        "lineage_refs": record.get("immutable_lineage_refs") or [],
        "account_id": snap.get("account_id"),
        "unit": snap.get("unit"),
        "collector_rm_owner": snap.get("collector_rm_owner"),
        "entity_code": snap.get("entity_code"),
        "entity_display": snap.get("entity_display"),
        "amount_aed": snap.get("amount_aed"),
        "ageing_bucket": snap.get("ageing_bucket"),
        "pr_status": snap.get("pr_status"),
        "process_status": snap.get("process_status"),
        "reporting_basis": snap.get("reporting_basis"),
        "confidence_state": snap.get("confidence_state"),
    }


def assign_action(action_id: str, assignee: str, actor: str, actor_role: str, due_date: Optional[str] = None, note: Optional[str] = None) -> Dict[str, Any]:
    record = _get_record(action_id)
    _ensure_role_permission(actor_role, "can_assign", _source_action_for_record(record))
    if record.get("workflow_state") in TERMINAL_STATES:
        raise ValueError("cannot_assign_terminal_or_blocked_action")
    if not record.get("source_gate", {}).get("assignable"):
        raise ValueError("cannot_assign_untrusted_source_action")
    from_state = record["workflow_state"]
    record["workflow_state"] = "assigned"
    record["assigned_owner"] = assignee
    if due_date:
        record["due_date"] = due_date
    event = _append_event(record, "assigned", actor_role, actor, from_state, "assigned", {"assignee": assignee, "due_date": due_date, "note": note})
    return {"status": "ok", "record": _deepcopy(record), "event": event}


def reassign_action(action_id: str, assignee: str, actor: str, actor_role: str, note: Optional[str] = None) -> Dict[str, Any]:
    record = _get_record(action_id)
    _ensure_role_permission(actor_role, "can_reassign", _source_action_for_record(record))
    if record.get("workflow_state") in TERMINAL_STATES:
        raise ValueError("cannot_reassign_terminal_or_blocked_action")
    previous_owner = record.get("assigned_owner")
    from_state = record["workflow_state"]
    record["workflow_state"] = "assigned"
    record["assigned_owner"] = assignee
    event = _append_event(record, "reassigned", actor_role, actor, from_state, "assigned", {"previous_owner": previous_owner, "assignee": assignee, "note": note})
    return {"status": "ok", "record": _deepcopy(record), "event": event}


def set_due_date(action_id: str, due_date: str, actor: str, actor_role: str, note: Optional[str] = None) -> Dict[str, Any]:
    record = _get_record(action_id)
    _ensure_role_permission(actor_role, "can_set_due_date", _source_action_for_record(record))
    if record.get("workflow_state") in TERMINAL_STATES:
        raise ValueError("cannot_set_due_date_on_terminal_or_blocked_action")
    old_due = record.get("due_date")
    record["due_date"] = due_date
    event = _append_event(record, "due_date_set", actor_role, actor, record["workflow_state"], record["workflow_state"], {"old_due_date": old_due, "due_date": due_date, "note": note})
    return {"status": "ok", "record": _deepcopy(record), "event": event}


def update_disposition(action_id: str, disposition: str, actor: str, actor_role: str, next_state: Optional[str] = None, note: Optional[str] = None) -> Dict[str, Any]:
    record = _get_record(action_id)
    _ensure_role_permission(actor_role, "can_update_disposition", _source_action_for_record(record))
    if record.get("workflow_state") in TERMINAL_STATES:
        raise ValueError("cannot_update_terminal_or_blocked_action")
    if next_state and next_state not in WORKFLOW_STATES:
        raise ValueError("invalid_next_state")
    if next_state in {"closed", "blocked"}:
        raise ValueError("use_close_or_block_endpoint_for_terminal_state")
    from_state = record["workflow_state"]
    to_state = next_state or "in_progress"
    record["workflow_state"] = to_state
    record["disposition"] = disposition
    event = _append_event(record, "disposition_updated", actor_role, actor, from_state, to_state, {"disposition": disposition, "note": note})
    return {"status": "ok", "record": _deepcopy(record), "event": event}


def attach_evidence(action_id: str, evidence_type: str, evidence_ref: str, actor: str, actor_role: str, note: Optional[str] = None) -> Dict[str, Any]:
    record = _get_record(action_id)
    _ensure_role_permission(actor_role, "can_attach_evidence", _source_action_for_record(record))
    if record.get("workflow_state") == "blocked":
        raise ValueError("cannot_attach_evidence_to_blocked_action")
    attachment = {
        "evidence_id": "ev_" + hashlib.sha1(f"{action_id}|{evidence_ref}|{_now()}".encode("utf-8")).hexdigest()[:12],
        "evidence_type": evidence_type,
        "evidence_ref": evidence_ref,
        "note": note,
        "attached_by": actor,
        "attached_by_role": actor_role,
        "attached_at": _now(),
    }
    record.setdefault("evidence_attachments", []).append(attachment)
    event = _append_event(record, "evidence_attached", actor_role, actor, record["workflow_state"], record["workflow_state"], attachment)
    return {"status": "ok", "record": _deepcopy(record), "event": event}


def close_action(action_id: str, closure_reason: str, actor: str, actor_role: str, evidence_ref: Optional[str] = None, note: Optional[str] = None) -> Dict[str, Any]:
    record = _get_record(action_id)
    _ensure_role_permission(actor_role, "can_close", _source_action_for_record(record))
    if record.get("workflow_state") == "blocked":
        raise ValueError("cannot_close_blocked_action")
    if record.get("workflow_state") == "closed":
        raise ValueError("action_already_closed")
    if not closure_reason:
        raise ValueError("closure_reason_required")
    from_state = record["workflow_state"]
    if evidence_ref:
        record.setdefault("evidence_attachments", []).append({
            "evidence_id": "ev_" + hashlib.sha1(f"{action_id}|{evidence_ref}|close|{_now()}".encode("utf-8")).hexdigest()[:12],
            "evidence_type": "closure_evidence",
            "evidence_ref": evidence_ref,
            "note": note,
            "attached_by": actor,
            "attached_by_role": actor_role,
            "attached_at": _now(),
        })
    record["workflow_state"] = "closed"
    record["closure_reason"] = closure_reason
    record["closed_at"] = _now()
    event = _append_event(record, "closed", actor_role, actor, from_state, "closed", {"closure_reason": closure_reason, "evidence_ref": evidence_ref, "note": note})
    return {"status": "ok", "record": _deepcopy(record), "event": event}


def mark_stale(action_id: str, stale_reason: str, actor: str, actor_role: str) -> Dict[str, Any]:
    record = _get_record(action_id)
    _ensure_role_permission(actor_role, "can_update_disposition", _source_action_for_record(record))
    if record.get("workflow_state") in TERMINAL_STATES:
        raise ValueError("cannot_mark_terminal_or_blocked_action_stale")
    from_state = record["workflow_state"]
    record["workflow_state"] = "stale"
    record["stale_reason"] = stale_reason
    event = _append_event(record, "stale", actor_role, actor, from_state, "stale", {"stale_reason": stale_reason})
    return {"status": "ok", "record": _deepcopy(record), "event": event}


def build_workflow_payload(role: Optional[str] = None) -> Dict[str, Any]:
    if not _SEEDED:
        seed_workflows()
    records = list(WORKFLOW_STORE.values())
    if role:
        records = [r for r in records if _role_can_see(_source_action_for_record(r), role)]
    state_counts = {state: 0 for state in WORKFLOW_STATES}
    for r in records:
        state_counts[r.get("workflow_state", "queued")] = state_counts.get(r.get("workflow_state", "queued"), 0) + 1
    events = EVENT_LOG
    if role:
        visible_ids = {r["source_action_id"] for r in records}
        events = [e for e in events if e.get("source_action_id") in visible_ids]
    validations = validate_workflow_store(records, events)
    return {
        "contract_version": "workflow.v1.batch8",
        "status": "ready_workflow_tracking_guarded" if validations["passed"] else "validation_failed",
        "generated_at": _now(),
        "workflow_states": WORKFLOW_STATES,
        "guardrails": {
            "tolerance_pct": 0.05,
            "no_silent_fallback": True,
            "role_model": ["Board/CXO", "CCO/GM/AGM", "Finance", "MIS/QCG/Admin", "Collector/RM"],
            "removed_role": "Entity Head",
            "account_action_gate": "workflow records inherit Batch 7 gate; no assignment without lineage, owner, entity, amount/status and ageing/process status",
            "lineage_rule": "workflow events copy immutable source lineage refs and hash; events never mutate source facts",
            "liquid_glass_rule": "workflow drawer is L5 glass action output; evidence timeline is solid trust surface",
        },
        "permission_model": ROLE_PERMISSIONS,
        "summary": {
            "workflow_count": len(records),
            "event_count": len(events),
            "state_counts": state_counts,
            "lineaged_event_count": len([e for e in events if e.get("immutable_lineage_refs") and e.get("lineage_hash")]),
        },
        "records": [_deepcopy(r) for r in records[:80]],
        "event_log": [_deepcopy(e) for e in events[-120:]],
        "validations": validations,
    }


def validate_workflow_store(records: List[Dict[str, Any]], events: List[Dict[str, Any]]) -> Dict[str, Any]:
    checks = {
        "all_records_have_immutable_lineage": all(r.get("immutable_lineage_refs") and r.get("lineage_hash") for r in records),
        "all_assignable_records_pass_source_gate": all((not r.get("source_gate", {}).get("assignable")) or r.get("workflow_state") != "blocked" for r in records),
        "all_queued_or_active_records_have_owner_entity_amount_status": all(
            r.get("workflow_state") == "blocked" or _has_owner_entity_amount_or_status(_source_action_for_record(r)) for r in records
        ),
        "all_events_have_immutable_lineage_hash": all(e.get("immutable_lineage_refs") and e.get("lineage_hash") for e in events),
        "all_states_are_allowed": all(r.get("workflow_state") in WORKFLOW_STATES for r in records),
        "entity_head_removed": all("entity_head" not in (r.get("role_visibility") or []) for r in records),
        "closed_records_have_closure_reason": all(r.get("workflow_state") != "closed" or bool(r.get("closure_reason")) for r in records),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "checked_record_count": len(records),
        "checked_event_count": len(events),
    }


def _api_guard(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except PermissionError as exc:
        if HTTPException is Exception:
            raise
        raise HTTPException(status_code=403, detail=str(exc))
    except KeyError as exc:
        if HTTPException is Exception:
            raise
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        if HTTPException is Exception:
            raise
        raise HTTPException(status_code=422, detail=str(exc))


if APIRouter is not None:
    router = APIRouter(prefix="/workflows", tags=["workflows"])

    @router.get("")
    async def get_workflows(role: Optional[str] = None) -> Any:
        return JSONResponse(content=build_workflow_payload(role=role), status_code=200)

    @router.get("/{action_id}")
    async def get_workflow(action_id: str) -> Any:
        record = _api_guard(_get_record, action_id)
        events = [e for e in EVENT_LOG if e.get("source_action_id") == action_id]
        return JSONResponse(content={"contract_version": "workflow_record.v1.batch8", "record": record, "event_log": events}, status_code=200)

    @router.post("/assign")
    async def api_assign(payload: Dict[str, Any] = Body(...)) -> Any:
        result = _api_guard(assign_action, payload.get("action_id"), payload.get("assignee"), payload.get("actor", "unknown"), payload.get("actor_role"), payload.get("due_date"), payload.get("note"))
        return JSONResponse(content=result, status_code=200)

    @router.post("/reassign")
    async def api_reassign(payload: Dict[str, Any] = Body(...)) -> Any:
        result = _api_guard(reassign_action, payload.get("action_id"), payload.get("assignee"), payload.get("actor", "unknown"), payload.get("actor_role"), payload.get("note"))
        return JSONResponse(content=result, status_code=200)

    @router.post("/due-date")
    async def api_due_date(payload: Dict[str, Any] = Body(...)) -> Any:
        result = _api_guard(set_due_date, payload.get("action_id"), payload.get("due_date"), payload.get("actor", "unknown"), payload.get("actor_role"), payload.get("note"))
        return JSONResponse(content=result, status_code=200)

    @router.post("/disposition")
    async def api_disposition(payload: Dict[str, Any] = Body(...)) -> Any:
        result = _api_guard(update_disposition, payload.get("action_id"), payload.get("disposition"), payload.get("actor", "unknown"), payload.get("actor_role"), payload.get("next_state"), payload.get("note"))
        return JSONResponse(content=result, status_code=200)

    @router.post("/evidence")
    async def api_evidence(payload: Dict[str, Any] = Body(...)) -> Any:
        result = _api_guard(attach_evidence, payload.get("action_id"), payload.get("evidence_type"), payload.get("evidence_ref"), payload.get("actor", "unknown"), payload.get("actor_role"), payload.get("note"))
        return JSONResponse(content=result, status_code=200)

    @router.post("/close")
    async def api_close(payload: Dict[str, Any] = Body(...)) -> Any:
        result = _api_guard(close_action, payload.get("action_id"), payload.get("closure_reason"), payload.get("actor", "unknown"), payload.get("actor_role"), payload.get("evidence_ref"), payload.get("note"))
        return JSONResponse(content=result, status_code=200)

    @router.post("/stale")
    async def api_stale(payload: Dict[str, Any] = Body(...)) -> Any:
        result = _api_guard(mark_stale, payload.get("action_id"), payload.get("stale_reason"), payload.get("actor", "unknown"), payload.get("actor_role"))
        return JSONResponse(content=result, status_code=200)
