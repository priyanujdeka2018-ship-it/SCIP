"""
SCIP Batch 11 - RBAC, authenticated actor identity, row-level visibility,
and denied-attempt audit logging.

Patch-pack authentication contract:
- Uses signed/validated identity headers in this sandbox pack.
- Production should replace header trust with SSO/JWT verification at the gateway
  or identity provider middleware while preserving the Actor and RBAC policy model.

Guardrails preserved:
- Entity Head is not a valid role.
- Role visibility is enforced before action/workflow/notification/audit rows leave the API.
- Denied access attempts are stored durably for audit.
- No business computations are performed here.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

try:
    from fastapi import APIRouter, Depends, HTTPException, Request, Response
    from fastapi.responses import JSONResponse
except Exception:  # pragma: no cover
    APIRouter = None
    Depends = None
    HTTPException = Exception
    Request = object
    Response = object
    JSONResponse = None

try:
    import persistence
except Exception:  # pragma: no cover
    persistence = None

try:
    import identity
except Exception:  # pragma: no cover
    identity = None

RBAC_CONTRACT_VERSION = "rbac.v2.batch13"
HERE = Path(__file__).resolve().parent
DEFAULT_DB_PATH = Path(os.environ.get("SCIP_AUDIT_DB", str(HERE / "scip_batch11_security.sqlite")))

ROLE_MODEL = ["board_cxo", "cco_gm_agm", "finance", "mis_qcg_admin", "collector_rm"]
REMOVED_ROLES = {"entity_head", "entity head", "entity-head", "entity_head_user"}
ROLE_LABELS = {
    "board_cxo": "Board/CXO",
    "cco_gm_agm": "CCO/GM/AGM",
    "finance": "Finance",
    "mis_qcg_admin": "MIS/QCG/Admin",
    "collector_rm": "Collector/RM",
}

PERMISSIONS: Dict[str, Set[str]] = {
    "board_cxo": {
        "read:command_centres",
        "read:forecast",
        "read:quickball",
        "read:notifications_digest",
        "read:audit_summary",
        "read:health",
    },
    "cco_gm_agm": {
        "read:command_centres",
        "read:forecast",
        "read:quickball",
        "read:action_queues",
        "read:workflows",
        "write:workflows_assign",
        "write:workflows_update",
        "read:notifications",
        "read:notifications_digest",
        "read:audit_export_management",
        "read:audit_summary",
        "read:health",
    },
    "finance": {
        "read:command_centres",
        "read:forecast",
        "read:quickball",
        "read:action_queues",
        "read:workflows",
        "write:workflows_assign_finance",
        "write:workflows_update_finance",
        "read:notifications",
        "read:notifications_digest",
        "read:audit_export_finance",
        "read:audit_summary",
        "read:health",
    },
    "mis_qcg_admin": {
        "read:command_centres",
        "read:forecast",
        "read:quickball",
        "read:action_queues",
        "read:workflows",
        "write:workflows_assign",
        "write:workflows_update",
        "read:notifications",
        "read:notifications_digest",
        "read:audit_export_all",
        "read:audit_summary",
        "run:migrations",
        "run:backup_restore_check",
        "read:security_audit",
        "read:deployment_health",
        "read:health",
    },
    "collector_rm": {
        "read:command_centres",
        "read:quickball",
        "read:action_queues_own",
        "read:workflows_own",
        "write:workflows_update_own",
        "read:notifications_own",
        "read:notifications_digest",
        "read:health",
    },
}

# URL-level mapping. Fine-grain row filtering is handled separately.
PATH_PERMISSIONS = [
    ("GET", "/command-centres", "read:command_centres"),
    ("GET", "/forecast", "read:forecast"),
    ("GET", "/quickball", "read:quickball"),
    ("GET", "/action-queues", "read:action_queues"),
    ("GET", "/workflows", "read:workflows"),
    ("POST", "/workflows/assign", "write:workflows_assign"),
    ("POST", "/workflows/reassign", "write:workflows_assign"),
    ("POST", "/workflows/due-date", "write:workflows_update"),
    ("POST", "/workflows/disposition", "write:workflows_update"),
    ("POST", "/workflows/evidence", "write:workflows_update"),
    ("POST", "/workflows/close", "write:workflows_update"),
    ("POST", "/workflows/stale", "write:workflows_update"),
    ("GET", "/notifications/digests", "read:notifications_digest"),
    ("GET", "/notifications", "read:notifications"),
    ("GET", "/persistence/summary", "read:audit_summary"),
    ("POST", "/persistence/seed", "run:migrations"),
    ("GET", "/audit/export", "read:audit_export_all"),
    ("GET", "/security/me", "read:health"),
    ("GET", "/identity/me", "read:health"),
    ("GET", "/identity/policy", "read:health"),
    ("GET", "/identity/provisioning", "read:security_audit"),
    ("POST", "/identity/deactivate", "read:security_audit"),
    ("GET", "/security", "read:security_audit"),
    ("GET", "/deployment", "read:deployment_health"),
    ("POST", "/deployment/migrate", "run:migrations"),
    ("POST", "/deployment/backup-check", "run:backup_restore_check"),
]

PUBLIC_PATH_PREFIXES = (
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
    "/manifest",
    "/favicon.ico",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, sort_keys=True, default=str)


def _loads(text: Optional[str], fallback: Any) -> Any:
    if not text:
        return fallback
    try:
        return json.loads(text)
    except Exception:
        return fallback


def canonical_role(value: str | None) -> str:
    raw = (value or "").strip().lower().replace("/", "_").replace(" ", "_").replace("-", "_")
    aliases = {
        "board": "board_cxo",
        "cxo": "board_cxo",
        "board_cxo": "board_cxo",
        "cco": "cco_gm_agm",
        "gm": "cco_gm_agm",
        "agm": "cco_gm_agm",
        "cco_gm_agm": "cco_gm_agm",
        "mis": "mis_qcg_admin",
        "qcg": "mis_qcg_admin",
        "admin": "mis_qcg_admin",
        "mis_qcg_admin": "mis_qcg_admin",
        "collector": "collector_rm",
        "rm": "collector_rm",
        "collector_rm": "collector_rm",
        "finance": "finance",
    }
    if raw in REMOVED_ROLES:
        raise ValueError("entity_head_role_removed")
    role = aliases.get(raw)
    if role not in ROLE_MODEL:
        raise ValueError(f"unknown_role:{value}")
    return role


def _split_scope(value: str | None, default: Optional[List[str]] = None) -> List[str]:
    if not value:
        return default or ["Group"]
    return [item.strip() for item in value.split(",") if item.strip()] or (default or ["Group"])


@dataclass(frozen=True)
class Actor:
    actor_id: str
    actor_name: str
    role: str
    role_label: str
    entity_scope: List[str]
    collector_id: Optional[str]
    environment: str
    permissions: List[str]

    def has(self, permission: str) -> bool:
        if permission in self.permissions:
            return True
        # Own-action permissions satisfy read/write checks only after row filtering.
        own_equivalents = {
            "read:action_queues": "read:action_queues_own",
            "read:workflows": "read:workflows_own",
            "read:notifications": "read:notifications_own",
            "write:workflows_update": "write:workflows_update_own",
            "write:workflows_assign": "write:workflows_assign_finance",
        }
        return own_equivalents.get(permission) in self.permissions

    def is_own_limited(self, permission: str) -> bool:
        own_equivalents = {
            "read:action_queues": "read:action_queues_own",
            "read:workflows": "read:workflows_own",
            "read:notifications": "read:notifications_own",
            "write:workflows_update": "write:workflows_update_own",
            "write:workflows_assign": "write:workflows_assign_finance",
        }
        own_perm = own_equivalents.get(permission)
        return bool(own_perm and own_perm in self.permissions and permission not in self.permissions)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def legacy_actor_from_headers(headers: Dict[str, str]) -> Actor:
    """Batch 11 development identity fallback. Batch 13 allows this only via identity local-dev bypass."""
    normalized = {str(k).lower(): str(v) for k, v in headers.items()}
    role = canonical_role(normalized.get("x-scip-role", os.environ.get("SCIP_DEFAULT_ROLE", "mis_qcg_admin")))
    actor_id = normalized.get("x-scip-actor-id") or os.environ.get("SCIP_DEFAULT_ACTOR_ID", "system_admin")
    actor_name = normalized.get("x-scip-actor-name") or os.environ.get("SCIP_DEFAULT_ACTOR_NAME", actor_id)
    entity_scope = _split_scope(normalized.get("x-scip-entity-scope"), ["Group"])
    collector_id = normalized.get("x-scip-collector-id")
    environment = normalized.get("x-scip-environment") or os.environ.get("SCIP_ENV", "local")
    permissions = sorted(PERMISSIONS[role])
    return Actor(
        actor_id=actor_id,
        actor_name=actor_name,
        role=role,
        role_label=ROLE_LABELS[role],
        entity_scope=entity_scope,
        collector_id=collector_id,
        environment=environment,
        permissions=permissions,
    )


def actor_from_headers(headers: Dict[str, str], *, path: str = "", method: str = "GET") -> Actor:
    """Batch 13 identity entrypoint. JWT/SSO is default; header identity only works with explicit local-dev bypass."""
    if identity is not None and hasattr(identity, "actor_from_request_headers"):
        return identity.actor_from_request_headers(headers, path=path, method=method)  # type: ignore[no-any-return,attr-defined]
    # Fallback keeps older smoke harnesses importable but should not be used in production.
    return legacy_actor_from_headers(headers)


def get_actor(request: Request) -> Actor:
    try:
        return actor_from_headers(dict(request.headers), path=getattr(getattr(request, "url", None), "path", "unknown"), method=getattr(request, "method", "GET"))
    except ValueError as exc:
        log_denied_attempt(None, "authenticate", str(exc), path=getattr(getattr(request, "url", None), "path", "unknown"), method=getattr(request, "method", "GET"))
        raise HTTPException(status_code=401, detail={"status": "denied", "reason": str(exc)})


def required_permission(method: str, path: str) -> Optional[str]:
    method = method.upper()
    for expected_method, prefix, permission in PATH_PERMISSIONS:
        if method == expected_method and path.startswith(prefix):
            return permission
    return None


def is_public_path(path: str, method: str = "GET") -> bool:
    # Root is public only as exact path; other prefixes are explicit.
    if path == "/":
        return True
    return any(path == prefix or path.startswith(prefix + "/") for prefix in PUBLIC_PATH_PREFIXES if prefix != "/")


def authorize(actor: Actor, permission: Optional[str], *, path: str = "", method: str = "GET", row_context: Optional[Dict[str, Any]] = None) -> bool:
    if permission is None:
        return True
    if actor.has(permission):
        return True
    log_denied_attempt(actor, permission, "missing_permission", path=path, method=method, row_context=row_context)
    return False


def _ensure_security_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS actors (
            actor_id TEXT PRIMARY KEY,
            actor_name TEXT NOT NULL,
            role TEXT NOT NULL,
            entity_scope_json TEXT NOT NULL,
            collector_id TEXT,
            environment TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS rbac_policies (
            role TEXT NOT NULL,
            permission TEXT NOT NULL,
            effect TEXT NOT NULL DEFAULT 'allow',
            created_at TEXT NOT NULL,
            PRIMARY KEY(role, permission)
        );
        CREATE TABLE IF NOT EXISTS access_denials (
            denial_id TEXT PRIMARY KEY,
            actor_id TEXT,
            actor_role TEXT,
            permission TEXT NOT NULL,
            reason TEXT NOT NULL,
            path TEXT,
            method TEXT,
            row_context_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )


def _connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    if persistence is not None and hasattr(persistence, "_connect"):
        conn = persistence._connect(db_path)  # type: ignore[attr-defined]
    else:
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
    _ensure_security_tables(conn)
    return conn


def seed_rbac_policies(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    with _connect(db_path) as conn:
        for role, perms in PERMISSIONS.items():
            for perm in perms:
                conn.execute(
                    "INSERT OR IGNORE INTO rbac_policies(role, permission, effect, created_at) VALUES (?, ?, 'allow', ?)",
                    (role, perm, _now()),
                )
        conn.commit()


def upsert_actor(actor: Actor, db_path: Path | str = DEFAULT_DB_PATH) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO actors(actor_id, actor_name, role, entity_scope_json, collector_id, environment, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(actor_id) DO UPDATE SET
                actor_name=excluded.actor_name,
                role=excluded.role,
                entity_scope_json=excluded.entity_scope_json,
                collector_id=excluded.collector_id,
                environment=excluded.environment,
                updated_at=excluded.updated_at
            """,
            (actor.actor_id, actor.actor_name, actor.role, _json(actor.entity_scope), actor.collector_id, actor.environment, _now(), _now()),
        )
        conn.commit()


def log_denied_attempt(
    actor: Optional[Actor],
    permission: str,
    reason: str,
    *,
    path: str = "",
    method: str = "GET",
    row_context: Optional[Dict[str, Any]] = None,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    import hashlib

    created_at = _now()
    enriched_row_context = dict(row_context or {})
    enriched_row_context.setdefault("correlation_id", os.environ.get("SCIP_CORRELATION_ID", f"scip-{uuid.uuid4().hex}"))
    enriched_row_context.setdefault("audit_lineage", {
        "contract_version": RBAC_CONTRACT_VERSION,
        "permission": permission,
        "reason": reason,
        "created_at": created_at,
        "actor_id": actor.actor_id if actor else None,
        "actor_role": actor.role if actor else None,
    })
    payload = {
        "actor_id": actor.actor_id if actor else None,
        "actor_role": actor.role if actor else None,
        "permission": permission,
        "reason": reason,
        "path": path,
        "method": method,
        "row_context": enriched_row_context,
        "created_at": created_at,
    }
    denial_id = "deny_" + hashlib.sha256(_json(payload).encode("utf-8")).hexdigest()[:20]
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO access_denials(denial_id, actor_id, actor_role, permission, reason, path, method, row_context_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                denial_id,
                payload["actor_id"],
                payload["actor_role"],
                permission,
                reason,
                path,
                method,
                _json(payload["row_context"]),
                created_at,
            ),
        )
        conn.commit()
    payload["denial_id"] = denial_id
    return payload


def _role_list(row: Dict[str, Any]) -> List[str]:
    for key in ["role_visibility", "roles", "visible_to", "target_roles"]:
        value = row.get(key)
        if isinstance(value, list):
            return [str(x) for x in value]
        if isinstance(value, str):
            loaded = _loads(value, None)
            if isinstance(loaded, list):
                return [str(x) for x in loaded]
    snap = row.get("source_snapshot") or {}
    if isinstance(snap, dict):
        value = snap.get("role_visibility") or snap.get("roles")
        if isinstance(value, list):
            return [str(x) for x in value]
    return []


def _entity_value(row: Dict[str, Any]) -> Optional[str]:
    for key in ["entity", "entity_key", "entity_display", "entity_scope"]:
        if row.get(key):
            return str(row.get(key))
    snap = row.get("source_snapshot") or {}
    if isinstance(snap, dict):
        for key in ["entity", "entity_key", "entity_display"]:
            if snap.get(key):
                return str(snap.get(key))
    return None


def _owner_value(row: Dict[str, Any]) -> Optional[str]:
    for key in ["owner", "assigned_owner", "collector", "collector_id", "rm_owner", "original_owner"]:
        if row.get(key):
            return str(row.get(key))
    snap = row.get("source_snapshot") or {}
    if isinstance(snap, dict):
        for key in ["owner", "collector", "collector_id", "rm_owner"]:
            if snap.get(key):
                return str(snap.get(key))
    return None


def row_visible_to_actor(row: Dict[str, Any], actor: Actor, required_read_permission: str = "read:action_queues") -> bool:
    roles = _role_list(row)
    if roles and actor.role not in roles:
        return False
    entity = _entity_value(row)
    if entity and "Group" not in actor.entity_scope and entity not in actor.entity_scope:
        return False
    if actor.is_own_limited(required_read_permission):
        owner = _owner_value(row)
        # Collector/RM visibility requires explicit owner match. If collector_id is absent,
        # actor_id is used as the source of truth.
        allowed_owner_ids = {actor.actor_id}
        if actor.collector_id:
            allowed_owner_ids.add(actor.collector_id)
        return owner in allowed_owner_ids
    return True


def filter_rows_for_actor(rows: Iterable[Dict[str, Any]], actor: Actor, required_read_permission: str = "read:action_queues") -> List[Dict[str, Any]]:
    return [row for row in rows if row_visible_to_actor(row, actor, required_read_permission)]


def filter_action_queue_payload(payload: Dict[str, Any], actor: Actor) -> Dict[str, Any]:
    """Return a role-filtered action queue payload without mutating source data."""
    if actor.role == "collector_rm":
        visible_roles = ["collector_rm"]
    elif actor.role == "finance":
        visible_roles = ["finance"]
    elif actor.role == "mis_qcg_admin":
        visible_roles = ["mis_qcg_admin", "finance", "cco_gm_agm", "collector_rm"]
    elif actor.role == "cco_gm_agm":
        visible_roles = ["cco_gm_agm", "collector_rm"]
    else:
        visible_roles = []

    out = json.loads(json.dumps(payload, default=str))
    roles = out.get("roles") or {}
    out["roles"] = {role: roles.get(role, {}) for role in visible_roles if role in roles}
    out["rbac"] = {"actor": actor.to_dict(), "filtered": True, "visible_roles": visible_roles}
    return out


def filter_workflow_payload(payload: Dict[str, Any], actor: Actor) -> Dict[str, Any]:
    out = json.loads(json.dumps(payload, default=str))
    records = out.get("records") or []
    out["records"] = filter_rows_for_actor(records, actor, "read:workflows")
    event_log = out.get("event_log") or []
    visible_workflow_ids = {row.get("workflow_id") for row in out["records"]}
    out["event_log"] = [event for event in event_log if event.get("workflow_id") in visible_workflow_ids]
    out["rbac"] = {"actor": actor.to_dict(), "filtered": True, "visible_workflow_count": len(out["records"])}
    return out


def filter_notifications_payload(payload: Dict[str, Any], actor: Actor) -> Dict[str, Any]:
    out = json.loads(json.dumps(payload, default=str))
    notifications = out.get("notifications") or []
    out["notifications"] = filter_rows_for_actor(notifications, actor, "read:notifications")
    out["digests"] = [d for d in out.get("digests", []) if actor.role in (d.get("target_roles") or d.get("role_visibility") or [actor.role])]
    out["rbac"] = {"actor": actor.to_dict(), "filtered": True, "visible_notification_count": len(out["notifications"])}
    return out


def audit_rows_allowed_for_actor(rows: Iterable[Dict[str, Any]], actor: Actor) -> List[Dict[str, Any]]:
    if "read:audit_export_all" in actor.permissions:
        return list(rows)
    if "read:audit_export_management" in actor.permissions:
        return [row for row in rows if row.get("role") in {"cco_gm_agm", "collector_rm"} or row.get("actor_role") in {"cco_gm_agm", "collector_rm"}]
    if "read:audit_export_finance" in actor.permissions:
        return [row for row in rows if row.get("role") == "finance" or row.get("actor_role") == "finance" or str(row.get("notification_type", "")).startswith("finance")]
    log_denied_attempt(actor, "read:audit_export", "missing_audit_export_permission")
    return []


async def rbac_middleware(request: Request, call_next):
    path = request.url.path
    method = request.method.upper()
    if is_public_path(path, method):
        return await call_next(request)
    try:
        actor = get_actor(request)
        upsert_actor(actor)
        permission = required_permission(method, path)
        if permission and not authorize(actor, permission, path=path, method=method):
            return JSONResponse(status_code=403, content={"status": "denied", "reason": "missing_permission", "required_permission": permission})
        request.state.actor = actor
        request.state.required_permission = permission
        response = await call_next(request)
        response.headers["X-SCIP-RBAC"] = RBAC_CONTRACT_VERSION
        response.headers["X-SCIP-Actor-Role"] = actor.role
        return response
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    except Exception as exc:
        log_denied_attempt(None, "authenticate", f"auth_error:{exc}", path=path, method=method)
        return JSONResponse(status_code=401, content={"status": "denied", "reason": "authentication_failed"})


def build_policy_matrix() -> Dict[str, Any]:
    return {
        "contract_version": RBAC_CONTRACT_VERSION,
        "identity_contract": "identity_sso_jwt.v1.batch13",
        "role_model": ROLE_MODEL,
        "removed_roles": sorted(REMOVED_ROLES),
        "permissions": {role: sorted(perms) for role, perms in PERMISSIONS.items()},
        "row_level_rules": {
            "entity_scope": "Rows are visible only when actor scope contains Group or the row entity.",
            "role_visibility": "Rows are visible only when actor role is included in row role_visibility.",
            "collector_rm_own": "Collector/RM rows require owner match to actor_id or collector_id.",
            "audit_export": "Audit export is all for MIS/QCG/Admin, management-only for CCO/GM/AGM, finance-only for Finance, denied for Collector/RM and Board/CXO.",
        },
    }


def get_denied_attempts(limit: int = 100, db_path: Path | str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    with _connect(db_path) as conn:
        rows = conn.execute("SELECT * FROM access_denials ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) | {"row_context": _loads(row["row_context_json"], {})} for row in rows]


if APIRouter is not None:
    router = APIRouter(prefix="/security", tags=["security-rbac"])

    @router.get("/me")
    async def security_me(request: Request) -> Any:
        actor = get_actor(request)
        upsert_actor(actor)
        return {"contract_version": RBAC_CONTRACT_VERSION, "actor": actor.to_dict()}

    @router.get("/policy-matrix")
    async def policy_matrix(actor: Actor = Depends(get_actor)) -> Any:
        if not authorize(actor, "read:security_audit", path="/security/policy-matrix") and actor.role != "board_cxo":
            raise HTTPException(status_code=403, detail={"status": "denied", "reason": "missing_permission"})
        return build_policy_matrix()

    @router.get("/denied-attempts")
    async def denied_attempts(limit: int = 100, actor: Actor = Depends(get_actor)) -> Any:
        if not authorize(actor, "read:security_audit", path="/security/denied-attempts"):
            raise HTTPException(status_code=403, detail={"status": "denied", "reason": "missing_permission"})
        return {"contract_version": RBAC_CONTRACT_VERSION, "items": get_denied_attempts(limit)}
else:  # pragma: no cover
    router = None
