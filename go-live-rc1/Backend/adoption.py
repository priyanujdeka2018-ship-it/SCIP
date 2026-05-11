"""
SCIP Batch 15 - post-launch optimization and adoption analytics.

Guardrails preserved:
- Two-door Liquid Glass model: Live Pulse and Narratives only.
- Analytics are governance/evidence outputs, not a third Arrival door.
- No frontend business computation; frontend only displays server-provided aggregates.
- Redaction and correlation rules from Batch 12 remain mandatory.
- RBAC row-level scope is respected by role-filtered analytics.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    from fastapi import APIRouter, Depends, HTTPException, Request
    from fastapi.responses import JSONResponse
except Exception:  # pragma: no cover
    APIRouter = None
    Depends = None
    HTTPException = Exception
    Request = Any
    JSONResponse = None

try:
    import auth
except Exception:  # pragma: no cover
    auth = None

try:
    import observability
except Exception:  # pragma: no cover
    observability = None

ADOPTION_CONTRACT_VERSION = "adoption_optimization.v1.batch15"
HERE = Path(__file__).resolve().parent
DEFAULT_DB_PATH = Path(os.environ.get("SCIP_AUDIT_DB", str(HERE / "scip_batch15_adoption.sqlite")))

ROLE_ORDER = ["board_cxo", "cco_gm_agm", "finance", "mis_qcg_admin", "collector_rm"]
ROLE_LABELS = {
    "board_cxo": "Board/CXO",
    "cco_gm_agm": "CCO/GM/AGM",
    "finance": "Finance",
    "mis_qcg_admin": "MIS/QCG/Admin",
    "collector_rm": "Collector/RM",
}
ALLOWED_WORLDS = {"live_pulse", "narratives"}
ALLOWED_FOCUS = {
    "current_signal", "month_movement", "risk_action",
    "story", "portfolio", "dues", "advance", "roadmap",
    "target_track",
}
ALLOWED_DEPTH = {"summary", "detailed", "executive", "evidence", "action"}
SENSITIVE_KEYS = {
    "password", "passwd", "pwd", "secret", "token", "authorization", "cookie",
    "email", "mobile", "phone", "customer", "customer_name", "account_number",
    "passport", "emirates_id", "national_id", "iban", "card", "jwt",
}

EVENT_CATALOG = [
    "world_open",
    "focus_open",
    "depth_change",
    "quickball_explain",
    "quickball_blocked",
    "evidence_open",
    "action_queue_open",
    "action_queue_converted",
    "workflow_closed",
    "workflow_stale",
    "notification_seen",
    "notification_acted",
    "notification_suppressed",
    "forecast_review",
    "stale_source_impact",
    "uat_defect_logged",
    "production_defect_logged",
]

METRIC_CATALOG = [
    "world_focus_depth_usage",
    "quickball_explanation_usage",
    "evidence_path_opens",
    "action_queue_conversion_rate",
    "workflow_closure_rate",
    "notification_effectiveness",
    "forecast_review_frequency",
    "role_level_engagement",
    "stale_source_impact",
    "uat_to_production_defect_trends",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_key(key: str) -> str:
    return key.strip().lower().replace("-", "_").replace(" ", "_")


def looks_sensitive(key: str) -> bool:
    lower = canonical_key(key)
    return any(token in lower for token in SENSITIVE_KEYS)


def redact(value: Any, parent_key: str = "") -> Any:
    if looks_sensitive(parent_key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(k): redact(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v, parent_key) for v in value]
    return value


def stable_hash(value: str) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:24]


def connect(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path or DEFAULT_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS adoption_events (
            event_id TEXT PRIMARY KEY,
            event_ts TEXT NOT NULL,
            correlation_id TEXT NOT NULL,
            actor_hash TEXT NOT NULL,
            session_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            world TEXT NOT NULL,
            focus TEXT,
            depth TEXT,
            event_type TEXT NOT NULL,
            output_type TEXT,
            source_contract TEXT,
            properties_json TEXT NOT NULL,
            redaction_applied INTEGER NOT NULL DEFAULT 1
        );
        CREATE INDEX IF NOT EXISTS idx_adoption_role_ts ON adoption_events(role, event_ts);
        CREATE INDEX IF NOT EXISTS idx_adoption_world_focus ON adoption_events(world, focus);
        CREATE INDEX IF NOT EXISTS idx_adoption_event_type ON adoption_events(event_type);

        CREATE TABLE IF NOT EXISTS adoption_recommendations (
            recommendation_id TEXT PRIMARY KEY,
            created_ts TEXT NOT NULL,
            priority TEXT NOT NULL,
            theme TEXT NOT NULL,
            title TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            liquid_glass_guardrail TEXT NOT NULL,
            owner_role TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'proposed'
        );
        """
    )
    conn.commit()


@dataclass
class AdoptionEvent:
    event_id: str
    event_ts: str
    correlation_id: str
    actor_hash: str
    session_hash: str
    role: str
    world: str
    focus: Optional[str]
    depth: Optional[str]
    event_type: str
    output_type: Optional[str]
    source_contract: str
    properties: Dict[str, Any] = field(default_factory=dict)
    redaction_applied: bool = True

    def to_row(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["properties_json"] = json.dumps(redact(self.properties), sort_keys=True)
        payload["redaction_applied"] = 1 if self.redaction_applied else 0
        payload.pop("properties")
        return payload


def validate_event_payload(event: AdoptionEvent) -> List[str]:
    errors: List[str] = []
    if not event.correlation_id:
        errors.append("missing_correlation_id")
    if event.role not in ROLE_ORDER:
        errors.append("invalid_role")
    if event.role == "entity_head":
        errors.append("entity_head_removed")
    if event.world not in ALLOWED_WORLDS:
        errors.append("invalid_world_third_door_blocked")
    if event.focus and event.focus not in ALLOWED_FOCUS:
        errors.append("invalid_focus")
    if event.depth and event.depth not in ALLOWED_DEPTH:
        errors.append("invalid_depth")
    if event.event_type not in EVENT_CATALOG:
        errors.append("invalid_event_type")
    return errors


def record_event(
    conn: sqlite3.Connection,
    *,
    role: str,
    world: str,
    event_type: str,
    correlation_id: str,
    actor_id: str = "anonymous",
    session_id: str = "session",
    focus: Optional[str] = None,
    depth: Optional[str] = None,
    output_type: Optional[str] = None,
    source_contract: str = ADOPTION_CONTRACT_VERSION,
    properties: Optional[Dict[str, Any]] = None,
    event_ts: Optional[str] = None,
) -> AdoptionEvent:
    event = AdoptionEvent(
        event_id=f"adopt_{uuid.uuid4().hex[:20]}",
        event_ts=event_ts or now_utc(),
        correlation_id=correlation_id,
        actor_hash=stable_hash(actor_id),
        session_hash=stable_hash(session_id),
        role=role,
        world=world,
        focus=focus,
        depth=depth,
        event_type=event_type,
        output_type=output_type,
        source_contract=source_contract,
        properties=properties or {},
    )
    errors = validate_event_payload(event)
    if errors:
        raise ValueError(",".join(errors))
    row = event.to_row()
    conn.execute(
        """
        INSERT INTO adoption_events (
            event_id, event_ts, correlation_id, actor_hash, session_hash, role, world,
            focus, depth, event_type, output_type, source_contract, properties_json,
            redaction_applied
        ) VALUES (
            :event_id, :event_ts, :correlation_id, :actor_hash, :session_hash, :role, :world,
            :focus, :depth, :event_type, :output_type, :source_contract, :properties_json,
            :redaction_applied
        )
        """,
        row,
    )
    conn.commit()
    if observability is not None and hasattr(observability, "emit_event"):
        try:
            observability.emit_event(
                "adoption_event_recorded",
                correlation_id=correlation_id,
                metric_name="adoption_event_total",
                value=1,
                properties={"role": role, "world": world, "focus": focus, "event_type": event_type},
            )
        except Exception:
            pass
    return event


def fetch_events(conn: sqlite3.Connection, role: Optional[str] = None, limit: int = 500) -> List[Dict[str, Any]]:
    if role:
        rows = conn.execute(
            "SELECT * FROM adoption_events WHERE role = ? ORDER BY event_ts DESC LIMIT ?", (role, limit)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM adoption_events ORDER BY event_ts DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in rows]


def count_by(conn: sqlite3.Connection, column: str, where: str = "1=1") -> Dict[str, int]:
    rows = conn.execute(f"SELECT {column} AS k, COUNT(*) AS c FROM adoption_events WHERE {where} GROUP BY {column}").fetchall()
    return {str(row["k"]): int(row["c"]) for row in rows if row["k"] is not None}


def pct(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


def adoption_summary(conn: sqlite3.Connection, role: Optional[str] = None) -> Dict[str, Any]:
    role_filter = f"role = '{role}'" if role in ROLE_ORDER else "1=1"
    total_events = conn.execute(f"SELECT COUNT(*) c FROM adoption_events WHERE {role_filter}").fetchone()["c"]
    active_sessions = conn.execute(f"SELECT COUNT(DISTINCT session_hash) c FROM adoption_events WHERE {role_filter}").fetchone()["c"]
    world_usage = count_by(conn, "world", role_filter)
    focus_usage = count_by(conn, "focus", role_filter)
    depth_usage = count_by(conn, "depth", role_filter)
    role_usage = count_by(conn, "role", "1=1")
    event_usage = count_by(conn, "event_type", role_filter)

    action_open = event_usage.get("action_queue_open", 0)
    action_converted = event_usage.get("action_queue_converted", 0)
    workflow_closed = event_usage.get("workflow_closed", 0)
    workflow_stale = event_usage.get("workflow_stale", 0)
    notification_seen = event_usage.get("notification_seen", 0)
    notification_acted = event_usage.get("notification_acted", 0)
    forecast_review = event_usage.get("forecast_review", 0)
    quickball_explain = event_usage.get("quickball_explain", 0)
    quickball_blocked = event_usage.get("quickball_blocked", 0)
    evidence_open = event_usage.get("evidence_open", 0)
    stale_source = event_usage.get("stale_source_impact", 0)
    uat_defects = event_usage.get("uat_defect_logged", 0)
    prod_defects = event_usage.get("production_defect_logged", 0)

    return {
        "contract_version": ADOPTION_CONTRACT_VERSION,
        "status": "ready_adoption_analytics_guarded",
        "role_filter": role or "all_roles",
        "total_events": int(total_events),
        "active_sessions": int(active_sessions),
        "world_usage": world_usage,
        "focus_usage": focus_usage,
        "depth_usage": depth_usage,
        "role_level_engagement": role_usage,
        "event_usage": event_usage,
        "metrics": {
            "world_focus_depth_usage": {"worlds": world_usage, "focus": focus_usage, "depth": depth_usage},
            "quickball_explanation_usage": {
                "explanations": quickball_explain,
                "blocked_answers": quickball_blocked,
                "blocked_rate_pct": pct(quickball_blocked, quickball_explain + quickball_blocked),
            },
            "evidence_path_opens": {"opens": evidence_open, "per_100_sessions": pct(evidence_open, max(active_sessions, 1))},
            "action_queue_conversion_rate": pct(action_converted, action_open),
            "workflow_closure_rate": pct(workflow_closed, workflow_closed + workflow_stale),
            "notification_effectiveness": pct(notification_acted, notification_seen),
            "forecast_review_frequency": {"reviews": forecast_review, "per_session": round(forecast_review / max(active_sessions, 1), 2)},
            "role_level_engagement": role_usage,
            "stale_source_impact": {"events": stale_source, "sessions_affected_estimate": stale_source},
            "uat_to_production_defect_trends": {
                "uat_defects": uat_defects,
                "production_defects": prod_defects,
                "prod_escape_rate_pct": pct(prod_defects, uat_defects + prod_defects),
            },
        },
        "guardrails": {
            "arrival_doors": ["live_pulse", "narratives"],
            "third_door_allowed": False,
            "entity_head_removed": True,
            "frontend_business_computation_allowed": False,
            "analytics_surface": "L5 governance evidence/output only",
        },
    }


def dashboard_specs(summary: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    summary = summary or {}
    return {
        "contract_version": ADOPTION_CONTRACT_VERSION,
        "dashboards": [
            {
                "dashboard_id": "adoption_experience_brief",
                "title": "Adoption Experience Brief",
                "surface": "Live Pulse > Risk & Action > L5 governance evidence",
                "not_arrival_door": True,
                "cards": [
                    "world_focus_depth_usage",
                    "quickball_explanation_usage",
                    "evidence_path_opens",
                    "forecast_review_frequency",
                ],
            },
            {
                "dashboard_id": "operational_conversion_brief",
                "title": "Operational Conversion Brief",
                "surface": "L5 management review output",
                "not_arrival_door": True,
                "cards": [
                    "action_queue_conversion_rate",
                    "workflow_closure_rate",
                    "notification_effectiveness",
                    "role_level_engagement",
                ],
            },
            {
                "dashboard_id": "rollout_quality_brief",
                "title": "Rollout Quality Brief",
                "surface": "MIS/QCG/Admin governance evidence",
                "not_arrival_door": True,
                "cards": [
                    "stale_source_impact",
                    "uat_to_production_defect_trends",
                    "blocked_quickball_answers",
                    "source_freshness_impact",
                ],
            },
        ],
        "sample_summary": summary,
    }


def build_recommendations(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    metrics = summary.get("metrics", {})
    event_usage = summary.get("event_usage", {})
    recommendations: List[Dict[str, Any]] = []

    def add(priority: str, theme: str, title: str, evidence: Dict[str, Any], recommendation: str, owner_role: str = "mis_qcg_admin") -> None:
        recommendations.append({
            "recommendation_id": f"opt_{stable_hash(title + json.dumps(evidence, sort_keys=True))}",
            "created_ts": now_utc(),
            "priority": priority,
            "theme": theme,
            "title": title,
            "evidence": evidence,
            "recommendation": recommendation,
            "owner_role": owner_role,
            "liquid_glass_guardrail": "Preserve two doors. Do not add dashboard-first navigation or a third Arrival option.",
            "status": "proposed",
        })

    worlds = summary.get("world_usage", {})
    total_worlds = sum(worlds.values()) or 1
    narratives_share = pct(worlds.get("narratives", 0), total_worlds)
    if narratives_share < 30:
        add(
            "P1", "experience", "Improve Narratives entry clarity",
            {"narratives_share_pct": narratives_share, "world_usage": worlds},
            "Tune Arrival copy and Quickball arrival suggestions so users understand when to choose Narratives. Do not add more entry doors.",
            "board_cxo",
        )

    qb = metrics.get("quickball_explanation_usage", {})
    if qb.get("blocked_rate_pct", 0) > 10:
        add(
            "P0", "trust", "Reduce Quickball blocked-answer rate",
            qb,
            "Prioritize missing lineage fixes for the metrics causing blocked Quickball answers. Do not let Quickball answer from unlineaged values.",
        )

    conversion = metrics.get("action_queue_conversion_rate", 0)
    if conversion < 40 and event_usage.get("action_queue_open", 0):
        add(
            "P1", "operations", "Improve action queue conversion",
            {"action_queue_conversion_rate": conversion},
            "Review queue ranking, default owner filters, and workflow drawer microcopy. Keep action queues as L5 output, not a homepage dashboard.",
            "cco_gm_agm",
        )

    closure = metrics.get("workflow_closure_rate", 0)
    if closure < 60:
        add(
            "P1", "workflow", "Increase workflow closure discipline",
            {"workflow_closure_rate": closure},
            "Add manager review rhythm and stale workflow coaching. Preserve immutable closure evidence and source lineage.",
            "cco_gm_agm",
        )

    notification_effectiveness = metrics.get("notification_effectiveness", 0)
    if notification_effectiveness < 35 and event_usage.get("notification_seen", 0):
        add(
            "P2", "notifications", "Tune notification targeting",
            {"notification_effectiveness": notification_effectiveness},
            "Adjust suppression windows and escalation thresholds to reduce noise while keeping lineage-backed evidence in every notification.",
        )

    stale = metrics.get("stale_source_impact", {}).get("events", 0)
    if stale:
        add(
            "P0", "data_trust", "Reduce stale-source impact",
            {"stale_source_events": stale},
            "Move impacted R-series refreshes into a daily source-owner checklist. Keep no-silent-fallback warnings visible.",
        )

    defects = metrics.get("uat_to_production_defect_trends", {})
    if defects.get("prod_escape_rate_pct", 0) > 10:
        add(
            "P0", "rollout_quality", "Tighten UAT regression before production",
            defects,
            "Add defect classes that escaped UAT into the production smoke manifest and UAT role scripts.",
            "mis_qcg_admin",
        )

    if not recommendations:
        add(
            "P2", "continuous_improvement", "Continue instrumented optimization review",
            {"status": "healthy_adoption_signal"},
            "Keep weekly adoption review focused on one question, one answer, and one optimization decision at a time.",
        )
    return recommendations


def upsert_recommendations(conn: sqlite3.Connection, recommendations: List[Dict[str, Any]]) -> None:
    for rec in recommendations:
        conn.execute(
            """
            INSERT OR REPLACE INTO adoption_recommendations (
                recommendation_id, created_ts, priority, theme, title, evidence_json,
                recommendation, liquid_glass_guardrail, owner_role, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rec["recommendation_id"], rec["created_ts"], rec["priority"], rec["theme"], rec["title"],
                json.dumps(rec["evidence"], sort_keys=True), rec["recommendation"],
                rec["liquid_glass_guardrail"], rec["owner_role"], rec.get("status", "proposed"),
            ),
        )
    conn.commit()


def get_recommendations(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows = conn.execute("SELECT * FROM adoption_recommendations ORDER BY CASE priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 ELSE 2 END, created_ts DESC").fetchall()
    output = []
    for row in rows:
        item = dict(row)
        item["evidence"] = json.loads(item.pop("evidence_json") or "{}")
        output.append(item)
    return output


def seed_sample_data(conn: sqlite3.Connection) -> Dict[str, Any]:
    initialize_db(conn)
    existing = conn.execute("SELECT COUNT(*) c FROM adoption_events").fetchone()["c"]
    if existing:
        return {"status": "already_seeded", "event_count": existing}

    base = datetime(2026, 5, 9, tzinfo=timezone.utc)
    event_count = 0
    sessions = {
        "board_cxo": 8,
        "cco_gm_agm": 14,
        "finance": 9,
        "mis_qcg_admin": 7,
        "collector_rm": 22,
    }
    for role, count in sessions.items():
        for idx in range(count):
            session_id = f"{role}_session_{idx}"
            actor_id = f"{role}_user_{idx % 5}"
            ts = base + timedelta(minutes=(idx * 7))
            world = "live_pulse" if role != "board_cxo" or idx % 3 else "narratives"
            focus = "risk_action" if role in {"collector_rm", "cco_gm_agm", "mis_qcg_admin"} else "month_movement"
            if world == "narratives":
                focus = ["story", "portfolio", "dues", "advance"][idx % 4]
            depth = "summary" if world == "live_pulse" else "executive"
            corr = f"corr_{role}_{idx}"
            for ev_type in ["world_open", "focus_open", "depth_change"]:
                record_event(conn, role=role, world=world, focus=focus, depth=depth, event_type=ev_type,
                             correlation_id=f"{corr}_{ev_type}", actor_id=actor_id, session_id=session_id,
                             event_ts=(ts + timedelta(seconds=event_count)).isoformat().replace("+00:00", "Z"),
                             properties={"source": "batch15_seed", "email": f"{actor_id}@example.com"})
                event_count += 1
            if idx % 2 == 0:
                record_event(conn, role=role, world=world, focus=focus, depth="evidence", event_type="evidence_open",
                             output_type="source_basis", correlation_id=f"{corr}_evidence", actor_id=actor_id,
                             session_id=session_id, event_ts=(ts + timedelta(seconds=event_count)).isoformat().replace("+00:00", "Z"),
                             properties={"evidence_path": "lineage_drawer", "customer_name": "redacted_seed"})
                event_count += 1
            if idx % 3 != 0:
                record_event(conn, role=role, world=world, focus=focus, depth=depth, event_type="quickball_explain",
                             correlation_id=f"{corr}_qb", actor_id=actor_id, session_id=session_id,
                             event_ts=(ts + timedelta(seconds=event_count)).isoformat().replace("+00:00", "Z"),
                             properties={"metric": "OD_TODAY", "result": "answered"})
                event_count += 1
            if idx % 11 == 0:
                record_event(conn, role=role, world=world, focus=focus, depth=depth, event_type="quickball_blocked",
                             correlation_id=f"{corr}_qb_blocked", actor_id=actor_id, session_id=session_id,
                             event_ts=(ts + timedelta(seconds=event_count)).isoformat().replace("+00:00", "Z"),
                             properties={"metric": "UNLINEAGED_METRIC", "reason": "missing_lineage"})
                event_count += 1
            if focus == "risk_action":
                record_event(conn, role=role, world="live_pulse", focus="risk_action", depth="action", event_type="action_queue_open",
                             correlation_id=f"{corr}_queue", actor_id=actor_id, session_id=session_id,
                             event_ts=(ts + timedelta(seconds=event_count)).isoformat().replace("+00:00", "Z"),
                             properties={"queue": "role_default"})
                event_count += 1
                if idx % 2 == 0:
                    record_event(conn, role=role, world="live_pulse", focus="risk_action", depth="action", event_type="action_queue_converted",
                                 correlation_id=f"{corr}_queue_convert", actor_id=actor_id, session_id=session_id,
                                 event_ts=(ts + timedelta(seconds=event_count)).isoformat().replace("+00:00", "Z"),
                                 properties={"action_id": stable_hash(session_id), "disposition": "assigned"})
                    event_count += 1
                if idx % 3 == 0:
                    record_event(conn, role=role, world="live_pulse", focus="risk_action", depth="action", event_type="workflow_closed",
                                 correlation_id=f"{corr}_workflow_closed", actor_id=actor_id, session_id=session_id,
                                 event_ts=(ts + timedelta(seconds=event_count)).isoformat().replace("+00:00", "Z"),
                                 properties={"closure_reason": "resolved"})
                    event_count += 1
                if idx % 7 == 0:
                    record_event(conn, role=role, world="live_pulse", focus="risk_action", depth="action", event_type="workflow_stale",
                                 correlation_id=f"{corr}_workflow_stale", actor_id=actor_id, session_id=session_id,
                                 event_ts=(ts + timedelta(seconds=event_count)).isoformat().replace("+00:00", "Z"),
                                 properties={"days_since_update": 5})
                    event_count += 1
            if role in {"collector_rm", "finance", "mis_qcg_admin", "cco_gm_agm"}:
                record_event(conn, role=role, world="live_pulse", focus="risk_action", depth="action", event_type="notification_seen",
                             correlation_id=f"{corr}_notif_seen", actor_id=actor_id, session_id=session_id,
                             event_ts=(ts + timedelta(seconds=event_count)).isoformat().replace("+00:00", "Z"),
                             properties={"notification_type": "role_digest"})
                event_count += 1
                if idx % 2:
                    record_event(conn, role=role, world="live_pulse", focus="risk_action", depth="action", event_type="notification_acted",
                                 correlation_id=f"{corr}_notif_acted", actor_id=actor_id, session_id=session_id,
                                 event_ts=(ts + timedelta(seconds=event_count)).isoformat().replace("+00:00", "Z"),
                                 properties={"notification_type": "role_digest"})
                    event_count += 1
                if idx % 10 == 0:
                    record_event(conn, role=role, world="live_pulse", focus="risk_action", depth="action", event_type="notification_suppressed",
                                 correlation_id=f"{corr}_notif_suppressed", actor_id=actor_id, session_id=session_id,
                                 event_ts=(ts + timedelta(seconds=event_count)).isoformat().replace("+00:00", "Z"),
                                 properties={"dedupe_key": stable_hash(session_id)})
                    event_count += 1
            if role in {"board_cxo", "cco_gm_agm", "finance"} and idx % 2 == 0:
                record_event(conn, role=role, world="live_pulse", focus="month_movement", depth="summary", event_type="forecast_review",
                             correlation_id=f"{corr}_forecast", actor_id=actor_id, session_id=session_id,
                             event_ts=(ts + timedelta(seconds=event_count)).isoformat().replace("+00:00", "Z"),
                             properties={"forecast": "month_end", "basis": "R04 Finance actuals vs R02 MDO target"})
                event_count += 1
    # rollout quality signals
    for i in range(4):
        record_event(conn, role="mis_qcg_admin", world="live_pulse", focus="risk_action", depth="evidence", event_type="stale_source_impact",
                     correlation_id=f"corr_stale_{i}", actor_id="mis_admin", session_id=f"stale_{i}",
                     event_ts=(base + timedelta(hours=i)).isoformat().replace("+00:00", "Z"),
                     properties={"source_code": "R32" if i % 2 else "R18", "impact": "blocked_queue_or_warning"})
    for i in range(7):
        record_event(conn, role="mis_qcg_admin", world="live_pulse", focus="risk_action", depth="evidence", event_type="uat_defect_logged",
                     correlation_id=f"corr_uat_defect_{i}", actor_id="uat_admin", session_id=f"uat_defect_{i}",
                     properties={"defect_class": "lineage_label" if i % 2 else "rbac_scope"})
    for i in range(1):
        record_event(conn, role="mis_qcg_admin", world="live_pulse", focus="risk_action", depth="evidence", event_type="production_defect_logged",
                     correlation_id=f"corr_prod_defect_{i}", actor_id="prod_admin", session_id=f"prod_defect_{i}",
                     properties={"defect_class": "copy_issue"})

    summary = adoption_summary(conn)
    recs = build_recommendations(summary)
    upsert_recommendations(conn, recs)
    return {"status": "seeded", "event_count": conn.execute("SELECT COUNT(*) c FROM adoption_events").fetchone()["c"], "recommendation_count": len(recs)}


def actor_from_request(request: Any) -> Dict[str, Any]:
    if auth is not None and hasattr(auth, "actor_from_request"):
        try:
            actor = auth.actor_from_request(request)
            if hasattr(actor, "__dict__"):
                return actor.__dict__
            if isinstance(actor, dict):
                return actor
        except Exception:
            pass
    return {
        "actor_id": request.headers.get("x-scip-actor-id", "anonymous") if hasattr(request, "headers") else "anonymous",
        "role": request.headers.get("x-scip-role", "mis_qcg_admin") if hasattr(request, "headers") else "mis_qcg_admin",
    }


def get_connection() -> sqlite3.Connection:
    conn = connect()
    initialize_db(conn)
    return conn


if APIRouter is not None:
    router = APIRouter(prefix="/adoption", tags=["adoption"])

    @router.post("/seed")
    async def seed_adoption() -> Dict[str, Any]:
        conn = get_connection()
        try:
            return seed_sample_data(conn)
        finally:
            conn.close()

    @router.post("/record")
    async def record_adoption_event(request: Request) -> JSONResponse:
        body = await request.json()
        conn = get_connection()
        actor = actor_from_request(request)
        try:
            event = record_event(
                conn,
                role=body.get("role") or actor.get("role") or "mis_qcg_admin",
                world=body.get("world"),
                focus=body.get("focus"),
                depth=body.get("depth"),
                event_type=body.get("event_type"),
                output_type=body.get("output_type"),
                correlation_id=request.headers.get("x-scip-correlation-id") or body.get("correlation_id") or f"adoption_{uuid.uuid4().hex}",
                actor_id=actor.get("actor_id", "anonymous"),
                session_id=body.get("session_id", "browser_session"),
                properties=body.get("properties") or {},
            )
            return JSONResponse({"status": "recorded", "event_id": event.event_id, "contract_version": ADOPTION_CONTRACT_VERSION})
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        finally:
            conn.close()

    @router.get("/summary")
    async def get_adoption_summary(role: Optional[str] = None) -> Dict[str, Any]:
        conn = get_connection()
        try:
            if not conn.execute("SELECT COUNT(*) c FROM adoption_events").fetchone()["c"]:
                seed_sample_data(conn)
            return adoption_summary(conn, role=role)
        finally:
            conn.close()

    @router.get("/events")
    async def get_adoption_events(role: Optional[str] = None, limit: int = 200) -> Dict[str, Any]:
        conn = get_connection()
        try:
            rows = fetch_events(conn, role=role, limit=min(max(limit, 1), 1000))
            return {"contract_version": ADOPTION_CONTRACT_VERSION, "events": rows, "count": len(rows)}
        finally:
            conn.close()

    @router.get("/dashboards")
    async def get_adoption_dashboards(role: Optional[str] = None) -> Dict[str, Any]:
        conn = get_connection()
        try:
            if not conn.execute("SELECT COUNT(*) c FROM adoption_events").fetchone()["c"]:
                seed_sample_data(conn)
            summary = adoption_summary(conn, role=role)
            return dashboard_specs(summary)
        finally:
            conn.close()

    @router.get("/backlog")
    async def get_optimization_backlog(role: Optional[str] = None) -> Dict[str, Any]:
        conn = get_connection()
        try:
            if not conn.execute("SELECT COUNT(*) c FROM adoption_events").fetchone()["c"]:
                seed_sample_data(conn)
            summary = adoption_summary(conn, role=role)
            recs = build_recommendations(summary)
            upsert_recommendations(conn, recs)
            return {"contract_version": ADOPTION_CONTRACT_VERSION, "recommendations": get_recommendations(conn), "count": len(get_recommendations(conn))}
        finally:
            conn.close()
else:  # pragma: no cover
    router = None
