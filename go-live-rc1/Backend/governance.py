"""
SCIP Batch 16 - continuous improvement governance.

Purpose
- Convert Batch 15 adoption analytics into controlled improvement governance.
- Preserve the Liquid Glass two-door model: governance is an L5 evidence/output layer,
  not a third Arrival door or a dashboard-first product area.
- Require every improvement item to map to evidence, owner, decision, expected impact,
  rollout gate, and rollback criteria.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from fastapi import APIRouter, Depends, HTTPException, Request
except Exception:  # pragma: no cover
    APIRouter = None
    Depends = None
    HTTPException = Exception
    Request = Any

try:
    import auth
except Exception:  # pragma: no cover
    auth = None

GOVERNANCE_CONTRACT_VERSION = "continuous_improvement_governance.v1.batch16"
HERE = Path(__file__).resolve().parent
DEFAULT_DB_PATH = Path(os.environ.get("SCIP_AUDIT_DB", str(HERE / "scip_batch16_governance.sqlite")))

ROLE_LABELS = {
    "board_cxo": "Board/CXO",
    "cco_gm_agm": "CCO/GM/AGM",
    "finance": "Finance",
    "mis_qcg_admin": "MIS/QCG/Admin",
    "collector_rm": "Collector/RM",
}
ALLOWED_OWNER_ROLES = set(ROLE_LABELS) | {"platform_owner", "data_owner", "source_owner", "quickball_owner", "ux_owner"}
ALLOWED_DECISIONS = {"proposed", "approved", "rejected", "deferred", "released", "rolled_back"}
ALLOWED_GATES = {"dev", "staging", "pilot", "uat", "production", "break_glass", "blocked"}
REQUIRED_ITEM_FIELDS = [
    "evidence_refs",
    "owner",
    "decision",
    "expected_impact",
    "rollout_gate",
    "rollback_criteria",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def connect(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path or DEFAULT_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS improvement_items (
            item_id TEXT PRIMARY KEY,
            created_ts TEXT NOT NULL,
            theme TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            evidence_refs_json TEXT NOT NULL,
            owner TEXT NOT NULL,
            decision TEXT NOT NULL,
            expected_impact TEXT NOT NULL,
            rollout_gate TEXT NOT NULL,
            rollback_criteria TEXT NOT NULL,
            score_json TEXT NOT NULL,
            priority TEXT NOT NULL,
            liquid_glass_guardrail TEXT NOT NULL,
            status TEXT NOT NULL,
            evidence_hash TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_improvement_status ON improvement_items(status);
        CREATE INDEX IF NOT EXISTS idx_improvement_priority ON improvement_items(priority);

        CREATE TABLE IF NOT EXISTS change_control_decisions (
            decision_id TEXT PRIMARY KEY,
            item_id TEXT NOT NULL,
            decision_ts TEXT NOT NULL,
            decision TEXT NOT NULL,
            decision_owner TEXT NOT NULL,
            rationale TEXT NOT NULL,
            rollout_gate TEXT NOT NULL,
            rollback_criteria TEXT NOT NULL,
            evidence_hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS metric_definition_change_log (
            change_id TEXT PRIMARY KEY,
            metric_key TEXT NOT NULL,
            requested_ts TEXT NOT NULL,
            requested_by_role TEXT NOT NULL,
            change_type TEXT NOT NULL,
            old_definition TEXT,
            new_definition TEXT NOT NULL,
            source_reports_json TEXT NOT NULL,
            approval_status TEXT NOT NULL,
            rollout_gate TEXT NOT NULL,
            rollback_criteria TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS source_owner_sla_reviews (
            review_id TEXT PRIMARY KEY,
            review_ts TEXT NOT NULL,
            source_code TEXT NOT NULL,
            source_owner TEXT NOT NULL,
            sla_status TEXT NOT NULL,
            latest_snapshot_date TEXT,
            stale_count INTEGER NOT NULL DEFAULT 0,
            missing_lineage_count INTEGER NOT NULL DEFAULT 0,
            decision TEXT NOT NULL,
            corrective_action TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS quickball_answer_reviews (
            review_id TEXT PRIMARY KEY,
            review_ts TEXT NOT NULL,
            metric_key TEXT NOT NULL,
            sample_question TEXT NOT NULL,
            answer_status TEXT NOT NULL,
            lineage_present INTEGER NOT NULL,
            blocked_when_untrusted INTEGER NOT NULL,
            reviewer_role TEXT NOT NULL,
            decision TEXT NOT NULL,
            notes TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ux_simplification_reviews (
            review_id TEXT PRIMARY KEY,
            review_ts TEXT NOT NULL,
            world TEXT NOT NULL,
            focus TEXT NOT NULL,
            finding TEXT NOT NULL,
            simplification_decision TEXT NOT NULL,
            liquid_glass_guardrail TEXT NOT NULL,
            evidence_refs_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS release_notes_governance (
            release_id TEXT PRIMARY KEY,
            release_ts TEXT NOT NULL,
            version_label TEXT NOT NULL,
            change_summary TEXT NOT NULL,
            included_item_ids_json TEXT NOT NULL,
            rollout_gate TEXT NOT NULL,
            rollback_criteria TEXT NOT NULL,
            signoff_roles_json TEXT NOT NULL
        );
        """
    )
    conn.commit()


@dataclass
class ImprovementItem:
    item_id: str
    created_ts: str
    theme: str
    title: str
    description: str
    evidence_refs: List[Dict[str, Any]]
    owner: str
    decision: str
    expected_impact: str
    rollout_gate: str
    rollback_criteria: str
    score: Dict[str, Any]
    priority: str
    liquid_glass_guardrail: str
    status: str
    evidence_hash: str

    @staticmethod
    def from_payload(payload: Dict[str, Any]) -> "ImprovementItem":
        evidence = payload.get("evidence_refs") or []
        score = compute_backlog_score(payload)
        return ImprovementItem(
            item_id=payload.get("item_id") or f"CI-{uuid.uuid4().hex[:10].upper()}",
            created_ts=payload.get("created_ts") or now_utc(),
            theme=payload.get("theme", "adoption_optimization"),
            title=payload["title"],
            description=payload.get("description", payload["title"]),
            evidence_refs=evidence,
            owner=payload["owner"],
            decision=payload.get("decision", "proposed"),
            expected_impact=payload["expected_impact"],
            rollout_gate=payload.get("rollout_gate", "pilot"),
            rollback_criteria=payload["rollback_criteria"],
            score=score,
            priority=score["priority"],
            liquid_glass_guardrail=payload.get(
                "liquid_glass_guardrail",
                "Do not add a third Arrival door; keep changes inside Live Pulse/Narratives progressive depth.",
            ),
            status=payload.get("status", "open"),
            evidence_hash=stable_hash(evidence),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def validate_improvement_item(payload: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for field in REQUIRED_ITEM_FIELDS:
        if not payload.get(field):
            errors.append(f"missing_required_field:{field}")
    if payload.get("decision") and payload["decision"] not in ALLOWED_DECISIONS:
        errors.append("invalid_decision")
    if payload.get("rollout_gate") and payload["rollout_gate"] not in ALLOWED_GATES:
        errors.append("invalid_rollout_gate")
    if payload.get("owner") not in ALLOWED_OWNER_ROLES:
        errors.append("invalid_owner_role")
    if not isinstance(payload.get("evidence_refs", []), list) or len(payload.get("evidence_refs", [])) == 0:
        errors.append("evidence_required")
    if "Entity Head" in json.dumps(payload, default=str):
        errors.append("entity_head_role_forbidden")
    return errors


def compute_backlog_score(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Weighted RICE-like scoring, tuned for SCIP governance rather than product vanity.
    reach = int(payload.get("reach", 3))
    impact = int(payload.get("impact", 3))
    confidence = int(payload.get("confidence", 3))
    effort = max(1, int(payload.get("effort", 3)))
    trust_risk_reduction = int(payload.get("trust_risk_reduction", 3))
    adoption_lift = int(payload.get("adoption_lift", 3))
    operational_value = int(payload.get("operational_value", 3))
    score = round(((reach * impact * confidence) / effort) + trust_risk_reduction + adoption_lift + operational_value, 2)
    if score >= 30:
        priority = "P0"
    elif score >= 20:
        priority = "P1"
    elif score >= 12:
        priority = "P2"
    else:
        priority = "P3"
    return {
        "method": "SCIP weighted RICE + trust/adoption/operations uplift",
        "reach": reach,
        "impact": impact,
        "confidence": confidence,
        "effort": effort,
        "trust_risk_reduction": trust_risk_reduction,
        "adoption_lift": adoption_lift,
        "operational_value": operational_value,
        "score": score,
        "priority": priority,
    }


def insert_item(conn: sqlite3.Connection, item: ImprovementItem) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO improvement_items (
            item_id, created_ts, theme, title, description, evidence_refs_json,
            owner, decision, expected_impact, rollout_gate, rollback_criteria,
            score_json, priority, liquid_glass_guardrail, status, evidence_hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item.item_id, item.created_ts, item.theme, item.title, item.description,
            json.dumps(item.evidence_refs, sort_keys=True), item.owner, item.decision,
            item.expected_impact, item.rollout_gate, item.rollback_criteria,
            json.dumps(item.score, sort_keys=True), item.priority, item.liquid_glass_guardrail,
            item.status, item.evidence_hash,
        ),
    )
    conn.commit()


def row_to_item(row: sqlite3.Row) -> Dict[str, Any]:
    d = dict(row)
    d["evidence_refs"] = json.loads(d.pop("evidence_refs_json"))
    d["score"] = json.loads(d.pop("score_json"))
    return d


def sample_improvement_payloads() -> List[Dict[str, Any]]:
    return [
        {
            "theme": "quickball_trust",
            "title": "Reduce blocked Quickball explanations for validated metrics",
            "description": "Review top blocked-answer patterns and add missing metric synonyms only where lineage already exists.",
            "evidence_refs": [
                {"source": "adoption", "metric": "quickball_blocked_rate", "value": "observed in Batch 15 analytics"},
                {"source": "observability", "metric": "quickball_blocked_answers_total"},
            ],
            "owner": "quickball_owner",
            "decision": "proposed",
            "expected_impact": "Improve explain-this-number success without weakening lineage gate.",
            "rollout_gate": "pilot",
            "rollback_criteria": "Rollback if any Quickball answer uses a critical metric without lineage or confidence state.",
            "reach": 4, "impact": 4, "confidence": 4, "effort": 2,
            "trust_risk_reduction": 5, "adoption_lift": 4, "operational_value": 3,
        },
        {
            "theme": "source_sla",
            "title": "Tighten stale-source SLA for critical R-series reports",
            "description": "Run monthly source-owner SLA review for R18/R04/R02/R08/R36/R10/R32/R34 and block stale critical cards.",
            "evidence_refs": [
                {"source": "observability", "metric": "stale_source_alerts"},
                {"source": "adoption", "metric": "stale_source_impact"},
            ],
            "owner": "source_owner",
            "decision": "proposed",
            "expected_impact": "Reduce trust erosion caused by stale data and reinforce no-silent-fallback rule.",
            "rollout_gate": "uat",
            "rollback_criteria": "Rollback if source blocks prevent approved fallback-labelled Board/CXO cards from rendering.",
            "reach": 5, "impact": 5, "confidence": 4, "effort": 3,
            "trust_risk_reduction": 5, "adoption_lift": 3, "operational_value": 4,
        },
        {
            "theme": "ux_simplification",
            "title": "Simplify Risk & Action evidence path for managers",
            "description": "Reduce first-click choices by grouping action queues, workflows, and notifications under one 'Act on risk' path.",
            "evidence_refs": [
                {"source": "adoption", "metric": "evidence_path_opens"},
                {"source": "adoption", "metric": "action_queue_conversion_rate"},
            ],
            "owner": "ux_owner",
            "decision": "proposed",
            "expected_impact": "Increase action conversion while preserving two-door, three-choice Liquid Glass constraints.",
            "rollout_gate": "staging",
            "rollback_criteria": "Rollback if users require more than three visible choices on an L2 screen or if action discovery drops in pilot.",
            "reach": 4, "impact": 3, "confidence": 3, "effort": 2,
            "trust_risk_reduction": 2, "adoption_lift": 5, "operational_value": 4,
        },
        {
            "theme": "metric_definition",
            "title": "Formalize Finance vs MDO target wording in all release notes",
            "description": "Add metric-definition governance check for all cards that compare R04 Finance actuals to R02 MDO targets.",
            "evidence_refs": [
                {"source": "lineage", "metric": "reporting_basis_label_coverage"},
                {"source": "uat", "metric": "target_basis_confusion_defects"},
            ],
            "owner": "data_owner",
            "decision": "proposed",
            "expected_impact": "Prevent interpretation drift in executive discussions and audit exports.",
            "rollout_gate": "dev",
            "rollback_criteria": "Rollback if wording change causes mismatch with approved metric definitions or source lineage labels.",
            "reach": 3, "impact": 4, "confidence": 5, "effort": 1,
            "trust_risk_reduction": 5, "adoption_lift": 2, "operational_value": 3,
        },
    ]


def seed_governance(conn: sqlite3.Connection) -> Dict[str, Any]:
    initialize_db(conn)
    items = []
    for payload in sample_improvement_payloads():
        errs = validate_improvement_item(payload)
        if errs:
            raise ValueError(f"invalid sample item {payload.get('title')}: {errs}")
        item = ImprovementItem.from_payload(payload)
        insert_item(conn, item)
        items.append(item.to_dict())
    # sample dependent logs
    conn.execute("""
        INSERT OR REPLACE INTO metric_definition_change_log VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "MDCL-R04-R02-001", "MAY_TOTAL_COLLECTIONS_TARGET", now_utc(), "data_owner",
        "wording_clarification", "May target", "May MDO total collections target; R04 actuals remain Finance basis.",
        json.dumps(["R02", "R04"]), "proposed", "dev", "Rollback to previous label only if approved by data owner."
    ))
    conn.execute("""
        INSERT OR REPLACE INTO source_owner_sla_reviews VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "SLA-R18-001", now_utc(), "R18", "source_owner", "green", "2026-05-01", 0, 0,
        "continue", "Maintain current refresh cadence and lineage checks."
    ))
    conn.execute("""
        INSERT OR REPLACE INTO quickball_answer_reviews VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "QB-OD-001", now_utc(), "OD_TODAY", "Explain OD today", "passed", 1, 1,
        "quickball_owner", "continue", "Answer included source file, sheet/range, validation, and confidence."
    ))
    conn.execute("""
        INSERT OR REPLACE INTO ux_simplification_reviews VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "UX-RISK-001", now_utc(), "live_pulse", "risk_action",
        "Managers open action queues but underuse workflow drawer.", "test_one_act_on_risk_path",
        "Keep within Live Pulse/Risk & Action; do not add a new dashboard or fourth L1 choice.",
        json.dumps([{"source":"adoption", "metric":"action_queue_conversion_rate"}])
    ))
    conn.execute("""
        INSERT OR REPLACE INTO release_notes_governance VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "REL-B16-001", now_utc(), "batch16-governance",
        "Introduces monthly optimization review and change-control governance without changing user navigation.",
        json.dumps([i["item_id"] for i in items]), "pilot",
        "Rollback governance routes if they expose raw dashboards at Arrival or bypass signoff gates.",
        json.dumps(["platform_owner", "data_owner", "mis_qcg_admin"])
    ))
    conn.commit()
    return {"seeded_items": len(items), "items": items}


def monthly_review_pack(conn: sqlite3.Connection) -> Dict[str, Any]:
    initialize_db(conn)
    rows = [row_to_item(r) for r in conn.execute("SELECT * FROM improvement_items ORDER BY priority, created_ts DESC").fetchall()]
    return {
        "contract_version": GOVERNANCE_CONTRACT_VERSION,
        "status": "ready_monthly_review_governed",
        "review_cadence": "monthly",
        "review_name": "SCIP Monthly Optimization Review",
        "liquid_glass_positioning": "L5 governance/evidence output inside Live Pulse/Risk & Action or admin governance, not a third Arrival door.",
        "required_review_sections": [
            "adoption evidence summary",
            "source-owner SLA review",
            "metric-definition change log",
            "Quickball answer review",
            "UX simplification review",
            "change-control board decisions",
            "release notes and rollout gates",
        ],
        "improvement_items": rows,
        "decision_rules": {
            "may_release": "approved item + evidence + owner + expected impact + rollout gate + rollback criteria",
            "must_block": "missing lineage, forbidden removed role, third Arrival door, silent fallback, or missing rollback criteria",
        },
    }


def backlog_scoring_model() -> Dict[str, Any]:
    return {
        "contract_version": GOVERNANCE_CONTRACT_VERSION,
        "method": "SCIP weighted RICE + trust/adoption/operations uplift",
        "inputs": {
            "reach": "1-5; number of roles/users affected",
            "impact": "1-5; expected business/decision value",
            "confidence": "1-5; strength of evidence",
            "effort": "1-5; delivery complexity, lower is better",
            "trust_risk_reduction": "1-5; reduces lineage/fallback/source-risk exposure",
            "adoption_lift": "1-5; likely improvement in meaningful usage",
            "operational_value": "1-5; improves collection/action outcomes",
        },
        "formula": "((reach * impact * confidence) / effort) + trust_risk_reduction + adoption_lift + operational_value",
        "priority_bands": {"P0": ">= 30", "P1": ">= 20", "P2": ">= 12", "P3": "< 12"},
        "hard_blocks": [
            "No evidence references",
            "No owner",
            "No rollback criteria",
            "Weakens no-silent-fallback rule",
            "Moves business computation into frontend",
            "Adds third Arrival door or >3 L1 choices",
            "Uses forbidden Entity Head role",
        ],
    }


def templates() -> Dict[str, str]:
    return {
        "monthly_optimization_review": "governance/SCIP_Batch16_Monthly_Optimization_Review_Template.md",
        "change_control_board": "governance/SCIP_Batch16_Change_Control_Board_Charter.md",
        "metric_definition_change_log": "governance/SCIP_Batch16_Metric_Definition_Change_Log_Template.md",
        "source_owner_sla_review": "governance/SCIP_Batch16_Source_Owner_SLA_Review_Template.md",
        "quickball_answer_review": "governance/SCIP_Batch16_Quickball_Answer_Review_Template.md",
        "ux_simplification_review": "governance/SCIP_Batch16_UX_Simplification_Review_Template.md",
        "release_notes_governance": "governance/SCIP_Batch16_Release_Notes_Governance.md",
    }


if APIRouter is not None:
    router = APIRouter(prefix="/governance", tags=["continuous-improvement-governance"])

    def _actor_dependency(request: Request):
        if auth and hasattr(auth, "get_actor"):
            return auth.get_actor(request)
        return {"actor_id": "local-dev", "role": "mis_qcg_admin"}

    @router.get("/continuous-improvement")
    def get_continuous_improvement(actor: Any = Depends(_actor_dependency)):
        if isinstance(actor, dict) and actor.get("role") not in {"mis_qcg_admin", "cco_gm_agm", "board_cxo"}:
            raise HTTPException(status_code=403, detail="governance_view_forbidden")
        with connect() as conn:
            if conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='improvement_items'").fetchone()[0] == 0:
                seed_governance(conn)
            return monthly_review_pack(conn)

    @router.post("/continuous-improvement/seed")
    def seed(actor: Any = Depends(_actor_dependency)):
        if isinstance(actor, dict) and actor.get("role") not in {"mis_qcg_admin"}:
            raise HTTPException(status_code=403, detail="seed_governance_forbidden")
        with connect() as conn:
            return seed_governance(conn)

    @router.get("/monthly-review-pack")
    def get_monthly_review_pack(actor: Any = Depends(_actor_dependency)):
        with connect() as conn:
            if conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='improvement_items'").fetchone()[0] == 0:
                seed_governance(conn)
            return monthly_review_pack(conn)

    @router.post("/improvement-items")
    def create_improvement_item(payload: Dict[str, Any], actor: Any = Depends(_actor_dependency)):
        if isinstance(actor, dict) and actor.get("role") not in {"mis_qcg_admin", "cco_gm_agm"}:
            raise HTTPException(status_code=403, detail="create_improvement_forbidden")
        errors = validate_improvement_item(payload)
        if errors:
            raise HTTPException(status_code=422, detail={"errors": errors})
        item = ImprovementItem.from_payload(payload)
        with connect() as conn:
            initialize_db(conn)
            insert_item(conn, item)
        return {"status": "created", "item": item.to_dict()}

    @router.get("/backlog-scoring-model")
    def get_backlog_scoring_model():
        return backlog_scoring_model()

    @router.get("/templates")
    def get_templates():
        return {"contract_version": GOVERNANCE_CONTRACT_VERSION, "templates": templates()}
else:
    router = None
