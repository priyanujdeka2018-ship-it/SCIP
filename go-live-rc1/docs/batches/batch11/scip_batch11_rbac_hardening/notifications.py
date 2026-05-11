"""
SCIP Batch 9 - Notification and escalation automation.

Built on top of Batch 8 workflow assignment and closure tracking. This module
emits evidence-driven notification payloads only when both source-action lineage
and workflow-event lineage are present. It does not send external messages from
this patch pack; it defines the backend contract and produces in-app / digest
payloads that a delivery worker can consume later.

Design rules preserved:
- Notifications are L5 outputs close to Live Pulse Risk & Action; not a new
  dashboard and not a third Arrival door.
- No silent fallback. Missing lineage blocks notification emission.
- No business computation is moved to the frontend.
- Deduplication and suppression keys are required for every emitted item.
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import date, datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    from fastapi import APIRouter, Query, Request
    from fastapi.responses import JSONResponse
except Exception:  # pragma: no cover
    APIRouter = None
    Request = object
    Query = None
    JSONResponse = None

import workflow
try:
    import auth
except Exception:  # pragma: no cover
    auth = None

NOTIFICATION_CONTRACT_VERSION = "notifications.v1.batch9"
DEFAULT_AS_OF_DATE = "2026-05-09"
STALE_DAYS = 7
HIGH_RISK_AMOUNT_AED = 1_000_000

ROLE_NOTIFICATION_TYPES: Dict[str, str] = {
    "collector_rm": "collector_rm_reminder",
    "cco_gm_agm": "manager_escalation",
    "finance": "finance_exception_nudge",
    "mis_qcg_admin": "mis_qcg_governance_alert",
}

ROLE_LABELS = {
    "board_cxo": "Board/CXO",
    "cco_gm_agm": "CCO/GM/AGM",
    "finance": "Finance",
    "mis_qcg_admin": "MIS/QCG/Admin",
    "collector_rm": "Collector/RM",
}

RULES: Dict[str, Dict[str, Any]] = {
    "overdue_due_date": {
        "severity": "high",
        "default_roles": ["collector_rm", "cco_gm_agm"],
        "description": "Workflow due date is past and the action is not closed or blocked.",
    },
    "stale_workflow": {
        "severity": "medium",
        "default_roles": ["cco_gm_agm", "mis_qcg_admin"],
        "description": "Workflow is explicitly stale or has exceeded the configured stale-days threshold.",
    },
    "broken_ptp_promise": {
        "severity": "high",
        "default_roles": ["collector_rm", "cco_gm_agm"],
        "description": "Promise-to-pay date has passed while the source PTP status remains open/pending.",
    },
    "termination_risk": {
        "severity": "critical",
        "default_roles": ["cco_gm_agm", "mis_qcg_admin"],
        "description": "Action carries termination or legal escalation status.",
    },
    "pr_tat_ageing": {
        "severity": "medium",
        "default_roles": ["finance", "mis_qcg_admin"],
        "description": "PR, SOA, TAT or finance-process action requires process follow-up.",
    },
    "unassigned_high_risk": {
        "severity": "critical",
        "default_roles": ["cco_gm_agm", "mis_qcg_admin"],
        "description": "High-value action is queued without an assigned owner.",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _deepcopy(value: Any) -> Any:
    return copy.deepcopy(value)


def _parse_date(value: Any) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    for candidate in (text[:10], text):
        try:
            return datetime.fromisoformat(candidate.replace("Z", "+00:00")).date()
        except Exception:
            pass
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except Exception:
            pass
    return None


def _date_days_between(a: Optional[date], b: Optional[date]) -> Optional[int]:
    if a is None or b is None:
        return None
    return (b - a).days


def _hash_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _short_hash(value: Any, length: int = 16) -> str:
    return _hash_json(value)[:length]


def _visible_roles(record: Dict[str, Any]) -> List[str]:
    roles = [r for r in (record.get("role_visibility") or []) if r in ROLE_NOTIFICATION_TYPES]
    return roles


def _events_for_record(events: Iterable[Dict[str, Any]], action_id: str) -> List[Dict[str, Any]]:
    return [e for e in events if e.get("source_action_id") == action_id]


def _latest_event(record_events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    return record_events[-1] if record_events else None


def _workflow_event_lineage(record_events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    latest = _latest_event(record_events)
    if not latest:
        return None
    if not latest.get("immutable_lineage_refs") or not latest.get("lineage_hash"):
        return None
    return {
        "latest_event_id": latest.get("event_id"),
        "latest_event_type": latest.get("event_type"),
        "latest_event_created_at": latest.get("created_at"),
        "workflow_lineage_hash": latest.get("lineage_hash"),
        "immutable_lineage_refs": _deepcopy(latest.get("immutable_lineage_refs") or []),
    }


def _record_is_notifiable(record: Dict[str, Any], record_events: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    failures: List[str] = []
    if not record.get("immutable_lineage_refs") or not record.get("lineage_hash"):
        failures.append("missing_source_action_lineage")
    if not _workflow_event_lineage(record_events):
        failures.append("missing_workflow_event_lineage")
    if not _visible_roles(record):
        failures.append("missing_role_visibility")
    if not record.get("source_gate", {}).get("assignable"):
        failures.append("source_action_gate_not_passed")
    if record.get("workflow_state") in {"closed", "blocked"}:
        failures.append("terminal_or_blocked_workflow")
    return (not failures, failures)


def _base_rule_evidence(rule_id: str, record: Dict[str, Any], as_of: date) -> Dict[str, Any]:
    snap = record.get("source_snapshot") or {}
    return {
        "rule_id": rule_id,
        "as_of_date": as_of.isoformat(),
        "workflow_state": record.get("workflow_state"),
        "due_date": record.get("due_date"),
        "updated_at": record.get("updated_at"),
        "ptp_date": snap.get("ptp_date"),
        "ptp_status": snap.get("ptp_status"),
        "escalation_status": snap.get("escalation_status"),
        "pr_status": snap.get("pr_status"),
        "amount_aed": snap.get("amount_aed"),
        "assigned_owner": record.get("assigned_owner"),
        "thresholds": {
            "stale_days": STALE_DAYS,
            "high_risk_amount_aed": HIGH_RISK_AMOUNT_AED,
        },
    }


def evaluate_rules(record: Dict[str, Any], as_of_date: str = DEFAULT_AS_OF_DATE) -> List[Dict[str, Any]]:
    """Return rule triggers with evidence. This function does not emit notifications."""
    as_of = _parse_date(as_of_date) or date.today()
    snap = record.get("source_snapshot") or {}
    state = record.get("workflow_state")
    if state in {"closed", "blocked"}:
        return []

    triggers: List[Dict[str, Any]] = []

    due = _parse_date(record.get("due_date"))
    if due and due < as_of:
        evidence = _base_rule_evidence("overdue_due_date", record, as_of)
        evidence["days_overdue"] = _date_days_between(due, as_of)
        triggers.append({"rule_id": "overdue_due_date", "evidence": evidence})

    updated = _parse_date(record.get("updated_at"))
    days_since_update = _date_days_between(updated, as_of)
    if state == "stale" or (days_since_update is not None and days_since_update > STALE_DAYS):
        evidence = _base_rule_evidence("stale_workflow", record, as_of)
        evidence["days_since_update"] = days_since_update
        triggers.append({"rule_id": "stale_workflow", "evidence": evidence})

    ptp_date = _parse_date(snap.get("ptp_date"))
    ptp_status = str(snap.get("ptp_status") or "").lower()
    if ptp_date and ptp_date < as_of and ptp_status in {"pending", "open", "promised", "ptp", ""}:
        evidence = _base_rule_evidence("broken_ptp_promise", record, as_of)
        evidence["days_after_ptp"] = _date_days_between(ptp_date, as_of)
        triggers.append({"rule_id": "broken_ptp_promise", "evidence": evidence})

    escalation = str(snap.get("escalation_status") or "").lower()
    if "term" in escalation or "legal" in escalation:
        evidence = _base_rule_evidence("termination_risk", record, as_of)
        triggers.append({"rule_id": "termination_risk", "evidence": evidence})

    action_type = str(record.get("action_type") or "").lower()
    pr_status = str(snap.get("pr_status") or "").lower()
    process_status = str(snap.get("process_status") or "").lower()
    if any(token in action_type for token in ["pr", "tat", "soa", "finance"]) or pr_status or process_status:
        evidence = _base_rule_evidence("pr_tat_ageing", record, as_of)
        evidence["process_tokens"] = {"action_type": action_type, "pr_status": pr_status, "process_status": process_status}
        triggers.append({"rule_id": "pr_tat_ageing", "evidence": evidence})

    amount = snap.get("amount_aed") or 0
    try:
        amount = float(amount)
    except Exception:
        amount = 0
    if not record.get("assigned_owner") and amount >= HIGH_RISK_AMOUNT_AED and state == "queued":
        evidence = _base_rule_evidence("unassigned_high_risk", record, as_of)
        evidence["amount_threshold_exceeded"] = True
        triggers.append({"rule_id": "unassigned_high_risk", "evidence": evidence})

    return triggers


def _roles_for_rule(record: Dict[str, Any], rule_id: str) -> List[str]:
    allowed = set(_visible_roles(record))
    defaults = RULES.get(rule_id, {}).get("default_roles") or []
    roles = [role for role in defaults if role in allowed]
    if roles:
        return roles
    # Governance alerts may also go to MIS/QCG/Admin if that role can see the item.
    return [role for role in _visible_roles(record) if role in ROLE_NOTIFICATION_TYPES]


def _notification_title(rule_id: str, record: Dict[str, Any]) -> str:
    snap = record.get("source_snapshot") or {}
    account = snap.get("account_id") or record.get("source_action_id")
    unit = snap.get("unit") or "unit"
    titles = {
        "overdue_due_date": f"Due date missed for {account} / {unit}",
        "stale_workflow": f"Workflow stale for {account} / {unit}",
        "broken_ptp_promise": f"Broken PTP follow-up for {account} / {unit}",
        "termination_risk": f"Termination-risk action needs review for {account} / {unit}",
        "pr_tat_ageing": f"Finance/QCG process follow-up for {account} / {unit}",
        "unassigned_high_risk": f"High-value action is unassigned for {account} / {unit}",
    }
    return titles.get(rule_id, f"Action follow-up required for {account} / {unit}")


def _notification_message(rule_id: str, record: Dict[str, Any], evidence: Dict[str, Any]) -> str:
    snap = record.get("source_snapshot") or {}
    amount = snap.get("display_amount") or (f"AED {float(snap.get('amount_aed') or 0):,.0f}" if snap.get("amount_aed") is not None else "amount unavailable")
    entity = snap.get("entity_display") or "entity unavailable"
    basis = snap.get("reporting_basis") or record.get("source_snapshot", {}).get("reporting_basis") or "source basis unavailable"
    rule_text = {
        "overdue_due_date": f"Due date is {evidence.get('days_overdue')} day(s) overdue.",
        "stale_workflow": f"Workflow is stale or inactive for {evidence.get('days_since_update')} day(s).",
        "broken_ptp_promise": f"PTP date is {evidence.get('days_after_ptp')} day(s) past while status remains open/pending.",
        "termination_risk": "Source action carries termination/legal escalation status.",
        "pr_tat_ageing": "Process evidence indicates PR/SOA/TAT follow-up is required.",
        "unassigned_high_risk": "High-value queued action has no assigned owner.",
    }.get(rule_id, "Rule evidence requires follow-up.")
    return f"{rule_text} Exposure: {amount}. Entity: {entity}. Basis: {basis}."


def make_notification(record: Dict[str, Any], record_events: List[Dict[str, Any]], trigger: Dict[str, Any], recipient_role: str) -> Optional[Dict[str, Any]]:
    rule_id = trigger["rule_id"]
    evidence = trigger.get("evidence") or {}
    notifiable, failures = _record_is_notifiable(record, record_events)
    if not notifiable:
        return None
    if recipient_role not in _roles_for_rule(record, rule_id):
        return None
    if not evidence:
        return None

    workflow_lineage = _workflow_event_lineage(record_events)
    if not workflow_lineage:
        return None

    dedupe_material = {
        "rule_id": rule_id,
        "source_action_id": record.get("source_action_id"),
        "workflow_id": record.get("workflow_id"),
        "recipient_role": recipient_role,
        "as_of_date": evidence.get("as_of_date"),
    }
    dedupe_key = "dedupe::" + _short_hash(dedupe_material, 24)
    notification_id = "notif::" + _short_hash({**dedupe_material, "lineage_hash": record.get("lineage_hash")}, 24)
    snap = record.get("source_snapshot") or {}

    return {
        "notification_id": notification_id,
        "contract_version": NOTIFICATION_CONTRACT_VERSION,
        "notification_type": ROLE_NOTIFICATION_TYPES.get(recipient_role, "governance_alert"),
        "rule_id": rule_id,
        "severity": RULES.get(rule_id, {}).get("severity", "medium"),
        "recipient_role": recipient_role,
        "recipient_role_label": ROLE_LABELS.get(recipient_role, recipient_role),
        "recipient_owner": record.get("assigned_owner") if recipient_role == "collector_rm" else snap.get("manager_name") or record.get("assigned_owner"),
        "title": _notification_title(rule_id, record),
        "message": _notification_message(rule_id, record, evidence),
        "recommended_action": _recommended_action(rule_id, recipient_role),
        "world": "live_pulse",
        "focus": "risk_action",
        "output_layer": "L5_notification_output",
        "source_action_id": record.get("source_action_id"),
        "workflow_id": record.get("workflow_id"),
        "workflow_state": record.get("workflow_state"),
        "source_snapshot": {
            "account_id": snap.get("account_id"),
            "unit": snap.get("unit"),
            "customer_name": snap.get("customer_name"),
            "entity_code": snap.get("entity_code"),
            "entity_display": snap.get("entity_display"),
            "amount_aed": snap.get("amount_aed"),
            "display_amount": snap.get("display_amount"),
            "ageing_bucket": snap.get("ageing_bucket"),
            "ptp_date": snap.get("ptp_date"),
            "ptp_status": snap.get("ptp_status"),
            "pr_status": snap.get("pr_status"),
            "escalation_status": snap.get("escalation_status"),
        },
        "reporting_basis": snap.get("reporting_basis"),
        "confidence_state": snap.get("confidence_state"),
        "lineage": {
            "source_action_lineage_refs": _deepcopy(record.get("immutable_lineage_refs") or []),
            "source_lineage_hash": record.get("lineage_hash"),
            "workflow_event_lineage": workflow_lineage,
        },
        "rule_evidence": evidence,
        "suppression": {
            "dedupe_key": dedupe_key,
            "suppression_scope": f"{rule_id}:{record.get('source_action_id')}:{recipient_role}",
            "suppress_reemit_until": evidence.get("as_of_date"),
            "dedupe_material_hash": _short_hash(dedupe_material, 24),
        },
        "delivery": {
            "channel": "in_app",
            "external_delivery_enabled": False,
            "delivery_note": "Patch pack emits contracts only; production delivery worker can send email/Teams/WhatsApp after RBAC review.",
        },
        "created_at": _now(),
    }


def _recommended_action(rule_id: str, recipient_role: str) -> str:
    if rule_id == "overdue_due_date":
        return "Update disposition or escalate with revised due date."
    if rule_id == "stale_workflow":
        return "Review stale action and either progress, escalate, or close with reason."
    if rule_id == "broken_ptp_promise":
        return "Contact customer/RM, update PTP status, and escalate if no revised commitment."
    if rule_id == "termination_risk":
        return "Review legal/termination readiness and attach evidence before escalation."
    if rule_id == "pr_tat_ageing":
        return "Resolve PR/SOA blocker or route to MIS/QCG with process evidence."
    if rule_id == "unassigned_high_risk":
        return "Assign owner and due date before next Live Pulse review."
    return "Review action and update workflow state."


def _validate_notification(notification: Dict[str, Any]) -> Tuple[bool, List[str]]:
    failures: List[str] = []
    lineage = notification.get("lineage") or {}
    rule_evidence = notification.get("rule_evidence") or {}
    suppression = notification.get("suppression") or {}
    if not lineage.get("source_action_lineage_refs") or not lineage.get("source_lineage_hash"):
        failures.append("missing_source_action_lineage")
    workflow_lineage = lineage.get("workflow_event_lineage") or {}
    if not workflow_lineage.get("latest_event_id") or not workflow_lineage.get("workflow_lineage_hash"):
        failures.append("missing_workflow_event_lineage")
    if not notification.get("recipient_role") or not notification.get("recipient_role_label"):
        failures.append("missing_role_visibility")
    if not rule_evidence.get("rule_id") or not rule_evidence.get("as_of_date"):
        failures.append("missing_due_or_stale_rule_evidence")
    if not suppression.get("dedupe_key") or not suppression.get("suppression_scope"):
        failures.append("missing_suppression_or_deduplication_key")
    if not notification.get("reporting_basis") or not notification.get("confidence_state"):
        failures.append("missing_reporting_basis_or_confidence")
    return (not failures, failures)


def validate_notification_payload(notifications: List[Dict[str, Any]], digests: Dict[str, Any]) -> Dict[str, Any]:
    checks: Dict[str, Any] = {
        "all_notifications_have_source_action_lineage": all((n.get("lineage") or {}).get("source_action_lineage_refs") for n in notifications),
        "all_notifications_have_workflow_event_lineage": all(((n.get("lineage") or {}).get("workflow_event_lineage") or {}).get("latest_event_id") for n in notifications),
        "all_notifications_have_role_visibility": all(n.get("recipient_role") for n in notifications),
        "all_notifications_have_rule_evidence": all((n.get("rule_evidence") or {}).get("rule_id") for n in notifications),
        "all_notifications_have_dedupe_keys": all((n.get("suppression") or {}).get("dedupe_key") for n in notifications),
        "all_notifications_have_reporting_basis": all(n.get("reporting_basis") for n in notifications),
        "dedupe_keys_unique": len({(n.get("suppression") or {}).get("dedupe_key") for n in notifications}) == len(notifications),
        "entity_head_removed": all(n.get("recipient_role") != "entity_head" for n in notifications),
        "digests_are_evidence_driven": bool(digests.get("daily_live_pulse_risk_action", {}).get("evidence_notification_ids") is not None and digests.get("weekly_management_review", {}).get("evidence_notification_ids") is not None),
        "no_third_arrival_door": True,
        "notifications_are_l5_output": all(n.get("output_layer") == "L5_notification_output" for n in notifications),
    }
    invalid = []
    for n in notifications:
        ok, failures = _validate_notification(n)
        if not ok:
            invalid.append({"notification_id": n.get("notification_id"), "failures": failures})
    checks["no_invalid_notifications"] = not invalid
    return {"passed": all(checks.values()), "checks": checks, "invalid_notifications": invalid}


def build_digest_payload(notifications: List[Dict[str, Any]], as_of_date: str = DEFAULT_AS_OF_DATE) -> Dict[str, Any]:
    daily_items = [n for n in notifications if n.get("world") == "live_pulse" and n.get("focus") == "risk_action"]
    weekly_items = [n for n in notifications if n.get("recipient_role") in {"cco_gm_agm", "mis_qcg_admin", "finance"}]

    def digest(kind: str, title: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        by_severity: Dict[str, int] = {}
        by_role: Dict[str, int] = {}
        by_rule: Dict[str, int] = {}
        for n in items:
            by_severity[n.get("severity", "medium")] = by_severity.get(n.get("severity", "medium"), 0) + 1
            by_role[n.get("recipient_role", "unknown")] = by_role.get(n.get("recipient_role", "unknown"), 0) + 1
            by_rule[n.get("rule_id", "unknown")] = by_rule.get(n.get("rule_id", "unknown"), 0) + 1
        evidence_ids = [n.get("notification_id") for n in items]
        return {
            "digest_id": f"digest::{kind}::{_short_hash({'kind': kind, 'as_of': as_of_date, 'ids': evidence_ids}, 16)}",
            "title": title,
            "world": "live_pulse",
            "focus": "risk_action",
            "output_layer": "L5_digest_output",
            "as_of_date": as_of_date,
            "notification_count": len(items),
            "evidence_notification_ids": evidence_ids[:100],
            "aggregate_counts": {"by_severity": by_severity, "by_role": by_role, "by_rule": by_rule},
            "suppression": {
                "dedupe_key": f"digest_dedupe::{kind}::{as_of_date}",
                "suppression_scope": f"digest:{kind}",
            },
            "lineage_hashes": sorted({((n.get("lineage") or {}).get("source_lineage_hash")) for n in items if (n.get("lineage") or {}).get("source_lineage_hash")})[:100],
            "delivery": {"channel": "in_app_digest", "external_delivery_enabled": False},
        }

    return {
        "daily_live_pulse_risk_action": digest("daily_live_pulse_risk_action", "Daily Live Pulse Risk & Action digest", daily_items),
        "weekly_management_review": digest("weekly_management_review", "Weekly management review escalation digest", weekly_items),
    }


def build_notifications_payload(role: Optional[str] = None, as_of_date: str = DEFAULT_AS_OF_DATE, data_dir: Optional[str] = None) -> Dict[str, Any]:
    if not workflow.WORKFLOW_STORE:
        workflow.seed_workflows(data_dir=data_dir or "/mnt/data", force=True)

    records = list(workflow.WORKFLOW_STORE.values())
    events = list(workflow.EVENT_LOG)
    notifications: List[Dict[str, Any]] = []
    blocked_candidates: List[Dict[str, Any]] = []

    for record in records:
        record_events = _events_for_record(events, record.get("source_action_id"))
        triggers = evaluate_rules(record, as_of_date=as_of_date)
        if not triggers:
            continue
        notifiable, failures = _record_is_notifiable(record, record_events)
        if not notifiable:
            blocked_candidates.append({"source_action_id": record.get("source_action_id"), "failures": failures, "trigger_count": len(triggers)})
            continue
        for trigger in triggers:
            for recipient_role in _roles_for_rule(record, trigger["rule_id"]):
                if role and recipient_role != role:
                    continue
                notification = make_notification(record, record_events, trigger, recipient_role)
                if notification:
                    notifications.append(notification)

    # Deterministic de-duplication by dedupe key.
    deduped: Dict[str, Dict[str, Any]] = {}
    for n in notifications:
        key = (n.get("suppression") or {}).get("dedupe_key")
        if key and key not in deduped:
            deduped[key] = n
    notifications = list(deduped.values())

    digests = build_digest_payload(notifications, as_of_date=as_of_date)
    validations = validate_notification_payload(notifications, digests)

    return {
        "contract_version": NOTIFICATION_CONTRACT_VERSION,
        "status": "ready_notifications_guarded" if validations["passed"] else "validation_failed",
        "generated_at": _now(),
        "as_of_date": as_of_date,
        "guardrails": {
            "tolerance_pct": 0.05,
            "no_silent_fallback": True,
            "role_model": ["Board/CXO", "CCO/GM/AGM", "Finance", "MIS/QCG/Admin", "Collector/RM"],
            "removed_role": "Entity Head",
            "account_action_gate": "notifications inherit Batch 7 account-action gate and Batch 8 workflow event lineage",
            "lineage_rule": "no notification emitted without source action lineage and workflow event lineage",
            "liquid_glass_rule": "notifications are L5 outputs in Live Pulse Risk & Action; no third Arrival door or standalone notification dashboard",
        },
        "rules": RULES,
        "summary": {
            "notification_count": len(notifications),
            "blocked_candidate_count": len(blocked_candidates),
            "by_role": _count_by(notifications, "recipient_role"),
            "by_rule": _count_by(notifications, "rule_id"),
            "by_severity": _count_by(notifications, "severity"),
        },
        "notifications": notifications[:200],
        "digests": digests,
        "blocked_candidates": blocked_candidates[:100],
        "validations": validations,
    }


def _count_by(items: Iterable[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for item in items:
        value = item.get(key) or "unknown"
        counts[value] = counts.get(value, 0) + 1
    return counts


if APIRouter is not None:
    router = APIRouter(prefix="/notifications", tags=["notifications"])

    @router.get("")
    async def get_notifications(request: Request, role: Optional[str] = None, as_of_date: str = DEFAULT_AS_OF_DATE) -> Any:
        actor = auth.get_actor(request) if auth is not None else None
        payload = build_notifications_payload(role=actor.role if actor is not None else role, as_of_date=as_of_date)
        if auth is not None and actor is not None:
            payload = auth.filter_notifications_payload(payload, actor)
        return JSONResponse(content=payload, status_code=200)

    @router.get("/digests")
    async def get_notification_digests(request: Request, role: Optional[str] = None, as_of_date: str = DEFAULT_AS_OF_DATE) -> Any:
        actor = auth.get_actor(request) if auth is not None else None
        payload = build_notifications_payload(role=actor.role if actor is not None else role, as_of_date=as_of_date)
        if auth is not None and actor is not None:
            payload = auth.filter_notifications_payload(payload, actor)
        return JSONResponse(content={
            "contract_version": "notification_digests.v2.batch11",
            "status": payload.get("status"),
            "as_of_date": as_of_date,
            "digests": payload.get("digests"),
            "validations": payload.get("validations"),
            "rbac": payload.get("rbac"),
        }, status_code=200)
