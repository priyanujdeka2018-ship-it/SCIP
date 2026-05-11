"""
SCIP Batch 10 - Durable persistence and audit export.

This module replaces the Batch 8/9 in-memory workflow + notification runtime with
an SQLite-backed repository contract. It is intentionally dependency-light for the
patch pack and migration-ready for Postgres/SQLAlchemy later.

Guardrails preserved:
- No workflow/action/notification row is stored without source lineage.
- Lineage hashes are immutable through DB triggers and repository checks.
- Notification dedupe/suppression is persisted and survives process restart.
- Closed workflow records remain auditable.
- Audit exports include source action lineage, workflow event lineage,
  notification lineage, actor, timestamp, role, state, and closure/escalation evidence.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    from fastapi import APIRouter, HTTPException, Query, Request
    from fastapi.responses import FileResponse, JSONResponse
except Exception:  # pragma: no cover
    APIRouter = None
    Request = object
    HTTPException = Exception
    Query = None
    FileResponse = None
    JSONResponse = None

import workflow
import notifications
try:
    import auth
except Exception:  # pragma: no cover
    auth = None

PERSISTENCE_CONTRACT_VERSION = "persistence_audit.v1.batch10"
HERE = Path(__file__).resolve().parent
MIGRATION_PATH = HERE / "migrations" / "001_batch10_persistence.sql"
DEFAULT_DB_PATH = Path(os.environ.get("SCIP_AUDIT_DB", str(HERE / "scip_batch10_audit.sqlite")))
DEFAULT_EXPORT_DIR = HERE / "audit_exports"
DEFAULT_AS_OF_DATE = "2026-05-09"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, sort_keys=True, default=str)


def _json_list(value: Any) -> str:
    return json.dumps(value if value is not None else [], sort_keys=True, default=str)


def _loads(text: Optional[str], fallback: Any) -> Any:
    if not text:
        return fallback
    try:
        return json.loads(text)
    except Exception:
        return fallback


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _short_hash(value: Any, length: int = 16) -> str:
    return _hash(value)[:length]


def _connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path | str = DEFAULT_DB_PATH) -> Path:
    db_path = Path(db_path)
    with _connect(db_path) as conn:
        conn.executescript(MIGRATION_PATH.read_text(encoding="utf-8"))
        conn.commit()
    return db_path


def reset_db(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    db_path = Path(db_path)
    init_db(db_path)
    tables = [
        "audit_exports",
        "delivery_status",
        "suppression_state",
        "notification_emissions",
        "notification_eligibility",
        "workflow_events",
        "workflow_records",
        "source_actions",
    ]
    with _connect(db_path) as conn:
        for table in tables:
            conn.execute(f"DELETE FROM {table}")
        conn.commit()


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def _source_snapshot(record: Dict[str, Any]) -> Dict[str, Any]:
    return record.get("source_snapshot") or {}


def _insert_or_ignore_source_action(conn: sqlite3.Connection, record: Dict[str, Any]) -> None:
    snap = _source_snapshot(record)
    refs = record.get("immutable_lineage_refs") or []
    source_action_id = record.get("source_action_id")
    if not source_action_id or not refs or not record.get("lineage_hash"):
        raise ValueError(f"cannot_persist_unlineaged_source_action:{source_action_id}")
    conn.execute(
        """
        INSERT OR IGNORE INTO source_actions (
            source_action_id, action_type, grain, title, role_visibility_json,
            source_snapshot_json, source_action_lineage_json, source_lineage_hash,
            reporting_basis, confidence_state, source_gate_json, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source_action_id,
            record.get("action_type"),
            record.get("grain"),
            record.get("title"),
            _json_list(record.get("role_visibility") or []),
            _json(snap),
            _json_list(refs),
            record.get("lineage_hash"),
            snap.get("reporting_basis"),
            snap.get("confidence_state"),
            _json(record.get("source_gate") or {}),
            record.get("created_at") or _now(),
            record.get("updated_at") or _now(),
        ),
    )


def _insert_or_update_workflow_record(conn: sqlite3.Connection, record: Dict[str, Any]) -> None:
    _insert_or_ignore_source_action(conn, record)
    conn.execute(
        """
        INSERT INTO workflow_records (
            workflow_id, source_action_id, workflow_state, assigned_owner, original_owner,
            due_date, disposition, closure_reason, closed_at, stale_reason, blocked_reason,
            evidence_attachments_json, role_visibility_json, source_snapshot_json,
            immutable_lineage_refs_json, lineage_hash, source_gate_json, event_count,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(workflow_id) DO UPDATE SET
            workflow_state=excluded.workflow_state,
            assigned_owner=excluded.assigned_owner,
            due_date=excluded.due_date,
            disposition=excluded.disposition,
            closure_reason=excluded.closure_reason,
            closed_at=excluded.closed_at,
            stale_reason=excluded.stale_reason,
            blocked_reason=excluded.blocked_reason,
            evidence_attachments_json=excluded.evidence_attachments_json,
            event_count=excluded.event_count,
            updated_at=excluded.updated_at
        """,
        (
            record.get("workflow_id"),
            record.get("source_action_id"),
            record.get("workflow_state"),
            record.get("assigned_owner"),
            record.get("original_owner"),
            record.get("due_date"),
            record.get("disposition"),
            record.get("closure_reason"),
            record.get("closed_at"),
            record.get("stale_reason"),
            record.get("blocked_reason"),
            _json_list(record.get("evidence_attachments") or []),
            _json_list(record.get("role_visibility") or []),
            _json(record.get("source_snapshot") or {}),
            _json_list(record.get("immutable_lineage_refs") or []),
            record.get("lineage_hash"),
            _json(record.get("source_gate") or {}),
            int(record.get("event_count") or 0),
            record.get("created_at") or _now(),
            record.get("updated_at") or _now(),
        ),
    )


def _insert_workflow_event(conn: sqlite3.Connection, event: Dict[str, Any]) -> None:
    if not event.get("immutable_lineage_refs") or not event.get("lineage_hash"):
        raise ValueError(f"cannot_persist_unlineaged_workflow_event:{event.get('event_id')}")
    conn.execute(
        """
        INSERT OR IGNORE INTO workflow_events (
            event_id, workflow_id, source_action_id, event_type, actor_role, actor,
            from_state, to_state, event_payload_json, immutable_lineage_refs_json,
            lineage_hash, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.get("event_id"),
            event.get("workflow_id"),
            event.get("source_action_id"),
            event.get("event_type"),
            event.get("actor_role"),
            event.get("actor"),
            event.get("from_state"),
            event.get("to_state"),
            _json(event.get("event_payload") or {}),
            _json_list(event.get("immutable_lineage_refs") or []),
            event.get("lineage_hash"),
            event.get("created_at") or _now(),
        ),
    )


def persist_workflow_runtime(db_path: Path | str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    init_db(db_path)
    with _connect(db_path) as conn:
        for record in workflow.WORKFLOW_STORE.values():
            _insert_or_update_workflow_record(conn, record)
        for event in workflow.EVENT_LOG:
            _insert_workflow_event(conn, event)
        conn.commit()
    return table_counts(db_path)


def _extract_workflow_lineage(notification: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    workflow_lineage = ((notification.get("lineage") or {}).get("workflow_event_lineage") or {})
    return workflow_lineage.get("workflow_lineage_hash"), workflow_lineage


def _insert_notification(conn: sqlite3.Connection, notification: Dict[str, Any]) -> Tuple[bool, str]:
    lineage = notification.get("lineage") or {}
    suppression = notification.get("suppression") or {}
    source_hash = lineage.get("source_lineage_hash")
    workflow_hash, workflow_lineage = _extract_workflow_lineage(notification)
    dedupe_key = suppression.get("dedupe_key")
    if not (lineage.get("source_action_lineage_refs") and source_hash and workflow_lineage and workflow_hash and dedupe_key):
        raise ValueError(f"cannot_persist_unlineaged_notification:{notification.get('notification_id')}")

    conn.execute(
        """
        INSERT OR IGNORE INTO notification_eligibility (
            eligibility_id, source_action_id, workflow_id, rule_id, rule_evidence_json,
            eligible, blocked_reasons_json, source_lineage_hash, workflow_lineage_hash, evaluated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "elig::" + _short_hash({"notification": notification.get("notification_id"), "rule": notification.get("rule_id")}, 18),
            notification.get("source_action_id"),
            notification.get("workflow_id"),
            notification.get("rule_id"),
            _json(notification.get("rule_evidence") or {}),
            1,
            _json_list([]),
            source_hash,
            workflow_hash,
            notification.get("created_at") or _now(),
        ),
    )

    cursor = conn.execute(
        """
        INSERT OR IGNORE INTO notification_emissions (
            notification_id, source_action_id, workflow_id, rule_id, notification_type,
            recipient_role, severity, title, body, reporting_basis, confidence_state,
            source_action_lineage_json, workflow_event_lineage_json, notification_lineage_json,
            source_lineage_hash, workflow_lineage_hash, dedupe_key, suppression_scope,
            rule_evidence_json, delivery_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            notification.get("notification_id"),
            notification.get("source_action_id"),
            notification.get("workflow_id"),
            notification.get("rule_id"),
            notification.get("notification_type"),
            notification.get("recipient_role"),
            notification.get("severity"),
            notification.get("title"),
            notification.get("message"),
            notification.get("reporting_basis"),
            notification.get("confidence_state"),
            _json_list(lineage.get("source_action_lineage_refs") or []),
            _json(workflow_lineage),
            _json({
                "notification_id": notification.get("notification_id"),
                "rule_id": notification.get("rule_id"),
                "dedupe_key": dedupe_key,
                "suppression_scope": suppression.get("suppression_scope"),
            }),
            source_hash,
            workflow_hash,
            dedupe_key,
            suppression.get("suppression_scope"),
            _json(notification.get("rule_evidence") or {}),
            _json(notification.get("delivery") or {}),
            notification.get("created_at") or _now(),
        ),
    )
    inserted = cursor.rowcount > 0

    if inserted:
        conn.execute(
            """
            INSERT INTO suppression_state (
                dedupe_key, suppression_scope, source_action_id, rule_id, recipient_role,
                suppress_reemit_until, first_emitted_at, last_emitted_at, emission_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            ON CONFLICT(dedupe_key) DO UPDATE SET
                last_emitted_at=excluded.last_emitted_at,
                emission_count=suppression_state.emission_count + 1
            """,
            (
                dedupe_key,
                suppression.get("suppression_scope"),
                notification.get("source_action_id"),
                notification.get("rule_id"),
                notification.get("recipient_role"),
                suppression.get("suppress_reemit_until"),
                notification.get("created_at") or _now(),
                notification.get("created_at") or _now(),
            ),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO delivery_status (
                delivery_id, notification_id, channel, external_delivery_enabled,
                delivery_state, attempt_count, last_attempt_at, last_error, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 0, NULL, NULL, ?, ?)
            """,
            (
                "deliv::" + _short_hash(notification.get("notification_id"), 18),
                notification.get("notification_id"),
                (notification.get("delivery") or {}).get("channel") or "in_app",
                1 if (notification.get("delivery") or {}).get("external_delivery_enabled") else 0,
                "disabled" if not (notification.get("delivery") or {}).get("external_delivery_enabled") else "pending",
                _now(),
                _now(),
            ),
        )
    return inserted, dedupe_key


def persist_notifications_payload(payload: Dict[str, Any], db_path: Path | str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    init_db(db_path)
    inserted = 0
    suppressed_duplicate = 0
    with _connect(db_path) as conn:
        for notification in payload.get("notifications") or []:
            ok, _key = _insert_notification(conn, notification)
            if ok:
                inserted += 1
            else:
                suppressed_duplicate += 1
        conn.commit()
    counts = table_counts(db_path)
    return {"inserted": inserted, "suppressed_duplicate": suppressed_duplicate, "table_counts": counts}


def prepare_demo_runtime(as_of_date: str = DEFAULT_AS_OF_DATE, data_dir: Path | str = "/mnt/data") -> Dict[str, Any]:
    """Seed workflows and representative Batch 9 notification triggers."""
    workflow.reset_workflow_store()
    workflow.seed_workflows(data_dir=data_dir, force=True)

    def pick(predicate):
        for record in workflow.WORKFLOW_STORE.values():
            if predicate(record):
                return record
        raise RuntimeError("required_demo_record_not_found")

    collector_1 = pick(lambda r: r.get("workflow_state") == "queued" and "collector_rm" in (r.get("role_visibility") or []))
    workflow.assign_action(collector_1["source_action_id"], collector_1.get("assigned_owner") or "RM Owner", "batch10_seed_manager", "cco_gm_agm", due_date="2026-05-01", note="Batch 10 persistence overdue seed")

    collector_2 = pick(lambda r: r.get("source_action_id") != collector_1.get("source_action_id") and r.get("workflow_state") == "queued" and "collector_rm" in (r.get("role_visibility") or []))
    workflow.mark_stale(collector_2["source_action_id"], "Batch 10 persistence stale seed", "batch10_seed_manager", "cco_gm_agm")

    collector_3 = pick(lambda r: r.get("source_action_id") not in {collector_1.get("source_action_id"), collector_2.get("source_action_id")} and r.get("workflow_state") == "queued" and "collector_rm" in (r.get("role_visibility") or []))
    collector_3["assigned_owner"] = None
    workflow._append_event(collector_3, "owner_removed_for_unassigned_high_risk_persistence_seed", "system", "batch10_seed", collector_3["workflow_state"], collector_3["workflow_state"], {"reason": "Batch 10 unassigned high-risk seed"})

    # Close one auditable workflow to prove closed records stay in audit exports.
    collector_4 = pick(lambda r: r.get("source_action_id") not in {collector_1.get("source_action_id"), collector_2.get("source_action_id"), collector_3.get("source_action_id")} and r.get("workflow_state") == "queued" and "collector_rm" in (r.get("role_visibility") or []))
    workflow.assign_action(collector_4["source_action_id"], collector_4.get("assigned_owner") or "RM Owner", "batch10_seed_manager", "cco_gm_agm", due_date="2026-05-10", note="Batch 10 closure seed")
    workflow.close_action(collector_4["source_action_id"], "customer_paid_or_resolved", "batch10_seed_manager", "cco_gm_agm", evidence_ref="receipt://batch10-smoke", note="Batch 10 closed workflow audit seed")

    notification_payload = notifications.build_notifications_payload(as_of_date=as_of_date, data_dir=str(data_dir))
    return {"notifications": notification_payload, "workflow_count": len(workflow.WORKFLOW_STORE), "event_count": len(workflow.EVENT_LOG)}


def seed_persistent_store(db_path: Path | str = DEFAULT_DB_PATH, as_of_date: str = DEFAULT_AS_OF_DATE, reset: bool = True, data_dir: Path | str = "/mnt/data") -> Dict[str, Any]:
    if reset:
        reset_db(db_path)
    else:
        init_db(db_path)
    runtime = prepare_demo_runtime(as_of_date=as_of_date, data_dir=data_dir)
    workflow_counts = persist_workflow_runtime(db_path)
    notification_counts = persist_notifications_payload(runtime["notifications"], db_path)
    return {
        "contract_version": PERSISTENCE_CONTRACT_VERSION,
        "status": "seeded",
        "db_path": str(db_path),
        "runtime": {"workflow_count": runtime["workflow_count"], "event_count": runtime["event_count"], "notification_count": len(runtime["notifications"].get("notifications") or [])},
        "workflow_counts": workflow_counts,
        "notification_counts": notification_counts,
        "table_counts": table_counts(db_path),
    }


def table_counts(db_path: Path | str = DEFAULT_DB_PATH) -> Dict[str, int]:
    init_db(db_path)
    tables = [
        "source_actions",
        "workflow_records",
        "workflow_events",
        "notification_eligibility",
        "notification_emissions",
        "suppression_state",
        "delivery_status",
        "audit_exports",
    ]
    with _connect(db_path) as conn:
        return {table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]) for table in tables}


def build_audit_rows(db_path: Path | str = DEFAULT_DB_PATH, include_closed: bool = True) -> List[Dict[str, Any]]:
    init_db(db_path)
    with _connect(db_path) as conn:
        sql = """
        SELECT
            wr.workflow_id,
            wr.source_action_id,
            wr.workflow_state,
            wr.assigned_owner,
            wr.due_date,
            wr.disposition,
            wr.closure_reason,
            wr.closed_at,
            wr.stale_reason,
            wr.blocked_reason,
            wr.role_visibility_json,
            wr.source_snapshot_json,
            wr.immutable_lineage_refs_json,
            wr.lineage_hash AS workflow_record_lineage_hash,
            wr.source_gate_json,
            we.event_id,
            we.event_type,
            we.actor_role,
            we.actor,
            we.from_state,
            we.to_state,
            we.event_payload_json,
            we.lineage_hash AS workflow_event_lineage_hash,
            we.created_at AS event_created_at,
            ne.notification_id,
            ne.rule_id,
            ne.notification_type,
            ne.recipient_role,
            ne.severity,
            ne.dedupe_key,
            ne.suppression_scope,
            ne.rule_evidence_json,
            ne.source_lineage_hash AS notification_source_lineage_hash,
            ne.workflow_lineage_hash AS notification_workflow_lineage_hash,
            ne.notification_lineage_json,
            ne.created_at AS notification_created_at,
            ds.delivery_state,
            ds.channel
        FROM workflow_records wr
        LEFT JOIN workflow_events we ON we.workflow_id = wr.workflow_id
        LEFT JOIN notification_emissions ne ON ne.workflow_id = wr.workflow_id
        LEFT JOIN delivery_status ds ON ds.notification_id = ne.notification_id
        WHERE (? = 1 OR wr.workflow_state != 'closed')
        ORDER BY wr.source_action_id, we.created_at, ne.created_at
        """
        rows = []
        for row in conn.execute(sql, (1 if include_closed else 0,)).fetchall():
            d = _row_to_dict(row)
            snap = _loads(d.pop("source_snapshot_json", None), {})
            d["account_id"] = snap.get("account_id")
            d["unit"] = snap.get("unit")
            d["entity_code"] = snap.get("entity_code")
            d["entity_display"] = snap.get("entity_display")
            d["amount_aed"] = snap.get("amount_aed")
            d["ageing_bucket"] = snap.get("ageing_bucket")
            d["reporting_basis"] = snap.get("reporting_basis")
            d["confidence_state"] = snap.get("confidence_state")
            d["role_visibility"] = _loads(d.pop("role_visibility_json", None), [])
            d["source_action_lineage"] = _loads(d.pop("immutable_lineage_refs_json", None), [])
            d["source_gate"] = _loads(d.pop("source_gate_json", None), {})
            d["workflow_event_payload"] = _loads(d.pop("event_payload_json", None), {})
            d["notification_rule_evidence"] = _loads(d.pop("rule_evidence_json", None), {})
            d["notification_lineage"] = _loads(d.pop("notification_lineage_json", None), {})
            rows.append(d)
        return rows


def export_audit_json(db_path: Path | str = DEFAULT_DB_PATH, export_dir: Path | str = DEFAULT_EXPORT_DIR, created_by: str = "system") -> Path:
    export_dir = Path(export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    rows = build_audit_rows(db_path=db_path, include_closed=True)
    payload = {
        "contract_version": PERSISTENCE_CONTRACT_VERSION,
        "export_type": "audit_json",
        "created_at": _now(),
        "created_by": created_by,
        "record_count": len(rows),
        "guardrails": {
            "locked_hierarchy": "Group > Sobha(Sobha Dubai,Sobha AUH), UAQ(Siniya,Downtown UAQ)",
            "tolerance_pct": 0.05,
            "no_silent_fallback": True,
            "role_model_without_entity_head": True,
            "immutable_lineage_required": True,
        },
        "rows": rows,
    }
    path = export_dir / "scip_batch10_audit_export.json"
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    _register_export(db_path, path, "json", len(rows), created_by)
    return path


def export_audit_csv(db_path: Path | str = DEFAULT_DB_PATH, export_dir: Path | str = DEFAULT_EXPORT_DIR, created_by: str = "system") -> Path:
    export_dir = Path(export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    rows = build_audit_rows(db_path=db_path, include_closed=True)
    path = export_dir / "scip_batch10_audit_export.csv"
    fields = [
        "workflow_id", "source_action_id", "workflow_state", "assigned_owner", "due_date",
        "disposition", "closure_reason", "closed_at", "event_id", "event_type",
        "actor_role", "actor", "from_state", "to_state", "event_created_at",
        "notification_id", "rule_id", "notification_type", "recipient_role", "severity",
        "dedupe_key", "suppression_scope", "notification_created_at", "delivery_state", "channel",
        "account_id", "unit", "entity_code", "entity_display", "amount_aed", "ageing_bucket",
        "reporting_basis", "confidence_state", "workflow_record_lineage_hash",
        "workflow_event_lineage_hash", "notification_source_lineage_hash", "notification_workflow_lineage_hash",
        "source_action_lineage", "workflow_event_payload", "notification_rule_evidence", "notification_lineage",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            serial = dict(row)
            for key in ("source_action_lineage", "workflow_event_payload", "notification_rule_evidence", "notification_lineage"):
                serial[key] = json.dumps(serial.get(key), sort_keys=True, default=str)
            writer.writerow(serial)
    _register_export(db_path, path, "csv", len(rows), created_by)
    return path


def _register_export(db_path: Path | str, path: Path, fmt: str, record_count: int, created_by: str) -> None:
    content = path.read_bytes()
    export_hash = hashlib.sha256(content).hexdigest()
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO audit_exports (
                export_id, export_format, export_path, record_count, filter_json,
                created_by, created_at, export_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"audit_export::{fmt}::{_short_hash(str(path), 12)}",
                fmt,
                str(path),
                record_count,
                _json({"include_closed": True}),
                created_by,
                _now(),
                export_hash,
            ),
        )
        conn.commit()


def validate_persistence(db_path: Path | str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    init_db(db_path)
    counts = table_counts(db_path)
    with _connect(db_path) as conn:
        workflow_hashes = [r[0] for r in conn.execute("SELECT lineage_hash FROM workflow_records").fetchall()]
        event_hashes = [r[0] for r in conn.execute("SELECT lineage_hash FROM workflow_events").fetchall()]
        notification_keys = [r[0] for r in conn.execute("SELECT dedupe_key FROM notification_emissions").fetchall()]
        closed_count = int(conn.execute("SELECT COUNT(*) FROM workflow_records WHERE workflow_state='closed'").fetchone()[0])
        closed_audit_count = int(conn.execute("SELECT COUNT(*) FROM workflow_events we JOIN workflow_records wr ON wr.workflow_id = we.workflow_id WHERE wr.workflow_state='closed'").fetchone()[0])
        sample_workflow = conn.execute("SELECT workflow_id, lineage_hash FROM workflow_records LIMIT 1").fetchone()
        trigger_blocked_update = False
        if sample_workflow:
            try:
                conn.execute("UPDATE workflow_records SET lineage_hash = ? WHERE workflow_id = ?", ("tampered", sample_workflow["workflow_id"]))
                conn.commit()
            except sqlite3.DatabaseError:
                trigger_blocked_update = True
                conn.rollback()
    audit_rows = build_audit_rows(db_path)
    checks = {
        "source_actions_persisted": counts["source_actions"] > 0,
        "workflow_records_persisted": counts["workflow_records"] > 0,
        "workflow_events_persisted": counts["workflow_events"] > 0,
        "notifications_persisted": counts["notification_emissions"] > 0,
        "suppression_state_persisted": counts["suppression_state"] == counts["notification_emissions"],
        "delivery_status_persisted": counts["delivery_status"] == counts["notification_emissions"],
        "workflow_lineage_hashes_present": all(bool(h) for h in workflow_hashes),
        "event_lineage_hashes_present": all(bool(h) for h in event_hashes),
        "notification_dedupe_keys_unique": len(notification_keys) == len(set(notification_keys)),
        "lineage_triggers_block_tampering": trigger_blocked_update,
        "closed_records_remain_auditable": closed_count > 0 and closed_audit_count > 0,
        "audit_rows_have_source_action_lineage": all(row.get("source_action_lineage") for row in audit_rows if row.get("source_action_id")),
        "audit_rows_have_workflow_event_lineage": any(row.get("workflow_event_lineage_hash") for row in audit_rows),
        "audit_rows_include_actor_timestamp_role_state": all(row.get("actor_role") is not None and row.get("event_created_at") is not None and row.get("workflow_state") is not None for row in audit_rows if row.get("event_id")),
        "audit_rows_include_closure_or_escalation_evidence": any(row.get("closure_reason") or (row.get("notification_rule_evidence") or {}).get("rule_id") for row in audit_rows),
        "role_model_without_entity_head": not any("entity_head" in (row.get("role_visibility") or []) for row in audit_rows),
    }
    return {"passed": all(checks.values()), "checks": checks, "counts": counts, "audit_row_count": len(audit_rows)}


def run_dedupe_restart_check(db_path: Path | str = DEFAULT_DB_PATH, as_of_date: str = DEFAULT_AS_OF_DATE) -> Dict[str, Any]:
    # First pass assumes runtime already prepared and persisted. Rebuild notifications from the same runtime and persist again.
    before = table_counts(db_path)
    payload_again = notifications.build_notifications_payload(as_of_date=as_of_date, data_dir="/mnt/data")
    second = persist_notifications_payload(payload_again, db_path)
    after = table_counts(db_path)
    return {
        "before_notification_count": before["notification_emissions"],
        "after_notification_count": after["notification_emissions"],
        "second_pass_inserted": second["inserted"],
        "second_pass_suppressed_duplicate": second["suppressed_duplicate"],
        "dedupe_survived_restart": before["notification_emissions"] == after["notification_emissions"] and second["inserted"] == 0,
    }


def build_persistence_payload(db_path: Path | str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    init_db(db_path)
    validation = validate_persistence(db_path)
    return {
        "contract_version": PERSISTENCE_CONTRACT_VERSION,
        "status": "ready_persistence_audit_guarded" if validation["passed"] else "validation_failed",
        "generated_at": _now(),
        "db_path": str(db_path),
        "table_counts": table_counts(db_path),
        "validations": validation,
        "routes": [
            "POST /persistence/seed",
            "GET /persistence/summary",
            "GET /audit/export?format=json",
            "GET /audit/export?format=csv",
        ],
    }


if APIRouter is not None:
    router = APIRouter(tags=["persistence-audit"])

    @router.post("/persistence/seed")
    async def api_seed_persistence(reset: bool = True, as_of_date: str = DEFAULT_AS_OF_DATE) -> JSONResponse:
        try:
            result = seed_persistent_store(DEFAULT_DB_PATH, as_of_date=as_of_date, reset=reset, data_dir="/mnt/data")
            return JSONResponse(content=result, status_code=200)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    @router.get("/persistence/summary")
    async def api_persistence_summary(request: Request) -> JSONResponse:
        try:
            if table_counts(DEFAULT_DB_PATH)["workflow_records"] == 0:
                seed_persistent_store(DEFAULT_DB_PATH, reset=True, data_dir="/mnt/data")
            return JSONResponse(content=build_persistence_payload(DEFAULT_DB_PATH), status_code=200)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    @router.get("/audit/export")
    async def api_audit_export(request: Request, format: str = Query("json", pattern="^(json|csv)$")):
        try:
            actor = auth.get_actor(request) if auth is not None else None
            if table_counts(DEFAULT_DB_PATH)["workflow_records"] == 0:
                seed_persistent_store(DEFAULT_DB_PATH, reset=True, data_dir="/mnt/data")
            rows = build_audit_rows(DEFAULT_DB_PATH)
            if auth is not None and actor is not None:
                rows = auth.audit_rows_allowed_for_actor(rows, actor)
                if not rows and actor.role not in {"mis_qcg_admin", "cco_gm_agm", "finance"}:
                    raise HTTPException(status_code=403, detail={"status": "denied", "reason": "missing_audit_export_permission"})
            DEFAULT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            actor_id = actor.actor_id if actor is not None else "api"
            if format == "csv":
                path = DEFAULT_EXPORT_DIR / f"scip_batch11_audit_export_{actor_id}.csv"
                if rows:
                    keys = sorted({key for row in rows for key in row.keys()})
                    with path.open("w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=keys)
                        writer.writeheader(); writer.writerows(rows)
                else:
                    path.write_text("status\nno_visible_rows\n", encoding="utf-8")
                return FileResponse(str(path), media_type="text/csv", filename=path.name)
            path = DEFAULT_EXPORT_DIR / f"scip_batch11_audit_export_{actor_id}.json"
            path.write_text(json.dumps({"contract_version":"audit_export.v2.batch11","actor": actor.to_dict() if actor is not None else None,"rows": rows}, indent=2, default=str), encoding="utf-8")
            return FileResponse(str(path), media_type="application/json", filename=path.name)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))
else:  # pragma: no cover
    router = None
