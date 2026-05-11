"""
SCIP Batch 13 - SSO/JWT actor identity and user provisioning.

Purpose
- Replace trusted X-SCIP-* development headers with verified JWT actor identity.
- Preserve the Batch 11 Actor/RBAC contract so existing row-level visibility continues to work.
- Add provisioning stores for users, groups, roles, entity scopes, collector mappings, sessions, and deactivation.
- Keep a safe local-development bypass behind explicit environment flags only.

Security posture
- Production default is SCIP_AUTH_MODE=jwt.
- JWTs must be signed, unexpired, issued by the configured issuer, and intended for the configured audience.
- alg=none is rejected.
- Header-based identity is accepted only when SCIP_AUTH_MODE=local_dev and SCIP_LOCAL_DEV_BYPASS=true.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

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

IDENTITY_CONTRACT_VERSION = "identity_sso_jwt.v1.batch13"
HERE = Path(__file__).resolve().parent
DEFAULT_DB_PATH = Path(os.environ.get("SCIP_AUDIT_DB", str(HERE / "scip_batch13_identity.sqlite")))

DEFAULT_JWT_ISSUER = os.environ.get("SCIP_JWT_ISSUER", "https://identity.sobha.example/scip")
DEFAULT_JWT_AUDIENCE = os.environ.get("SCIP_JWT_AUDIENCE", "scip-platform")
DEFAULT_JWT_SECRET = os.environ.get("SCIP_JWT_SECRET", "scip-local-dev-secret-change-me")
AUTH_MODE = os.environ.get("SCIP_AUTH_MODE", "jwt").strip().lower()
LOCAL_DEV_BYPASS = os.environ.get("SCIP_LOCAL_DEV_BYPASS", "false").strip().lower() == "true"

ROLE_MODEL = ["board_cxo", "cco_gm_agm", "finance", "mis_qcg_admin", "collector_rm"]
REMOVED_ROLES = {"entity_head", "entity head", "entity-head", "entity_head_user"}
GROUP_ROLE_MAP = {
    "scip-board": "board_cxo",
    "scip-cxo": "board_cxo",
    "scip-management": "cco_gm_agm",
    "scip-cco-gm-agm": "cco_gm_agm",
    "scip-finance": "finance",
    "scip-mis-qcg-admin": "mis_qcg_admin",
    "scip-admin": "mis_qcg_admin",
    "scip-collector-rm": "collector_rm",
    "scip-collector": "collector_rm",
}
ROLE_PRIORITY = ["mis_qcg_admin", "cco_gm_agm", "finance", "collector_rm", "board_cxo"]

SENSITIVE_CLAIMS = {"email", "phone", "mobile", "address", "token", "access_token", "refresh_token"}


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


def _b64url_decode(segment: str) -> bytes:
    padding = "=" * ((4 - len(segment) % 4) % 4)
    return base64.urlsafe_b64decode((segment + padding).encode("ascii"))


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _redact_claims(claims: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, value in claims.items():
        if key.lower() in SENSITIVE_CLAIMS:
            out[key] = "[REDACTED]"
        else:
            out[key] = value
    return out


def canonical_role(value: Optional[str]) -> str:
    if auth is not None and hasattr(auth, "canonical_role"):
        return auth.canonical_role(value)  # type: ignore[attr-defined]
    raw = (value or "").strip().lower().replace("/", "_").replace(" ", "_").replace("-", "_")
    aliases = {
        "board": "board_cxo", "cxo": "board_cxo", "board_cxo": "board_cxo",
        "cco": "cco_gm_agm", "gm": "cco_gm_agm", "agm": "cco_gm_agm", "cco_gm_agm": "cco_gm_agm",
        "finance": "finance",
        "mis": "mis_qcg_admin", "qcg": "mis_qcg_admin", "admin": "mis_qcg_admin", "mis_qcg_admin": "mis_qcg_admin",
        "collector": "collector_rm", "rm": "collector_rm", "collector_rm": "collector_rm",
    }
    if raw in REMOVED_ROLES:
        raise ValueError("entity_head_role_removed")
    role = aliases.get(raw)
    if role not in ROLE_MODEL:
        raise ValueError(f"unknown_role:{value}")
    return role


def _split_scope(value: Optional[str], default: Optional[List[str]] = None) -> List[str]:
    if not value:
        return default or ["Group"]
    if value.strip().startswith("["):
        loaded = _loads(value, [])
        if isinstance(loaded, list):
            return [str(item) for item in loaded if str(item).strip()] or (default or ["Group"])
    return [item.strip() for item in value.split(",") if item.strip()] or (default or ["Group"])


def _connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    ensure_identity_tables(conn)
    return conn


def ensure_identity_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS provisioned_users (
            user_id TEXT PRIMARY KEY,
            subject TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            email_hash TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            source_idp TEXT NOT NULL DEFAULT 'jwt',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            deactivated_at TEXT,
            deactivation_reason TEXT
        );
        CREATE TABLE IF NOT EXISTS provisioned_groups (
            group_id TEXT PRIMARY KEY,
            group_name TEXT NOT NULL UNIQUE,
            scip_role TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS user_group_memberships (
            user_id TEXT NOT NULL,
            group_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY(user_id, group_id)
        );
        CREATE TABLE IF NOT EXISTS role_assignments (
            assignment_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            scip_role TEXT NOT NULL,
            source TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS entity_scope_assignments (
            assignment_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            entity_scope_json TEXT NOT NULL,
            source TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS collector_mappings (
            mapping_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            collector_id TEXT NOT NULL,
            collector_name TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sso_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            issued_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            refresh_expires_at TEXT,
            status TEXT NOT NULL,
            token_hash TEXT NOT NULL,
            correlation_id TEXT
        );
        CREATE TABLE IF NOT EXISTS identity_denials (
            denial_id TEXT PRIMARY KEY,
            subject TEXT,
            reason TEXT NOT NULL,
            path TEXT,
            method TEXT,
            correlation_id TEXT NOT NULL,
            audit_lineage_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_identity_denials_created ON identity_denials(created_at);
        CREATE INDEX IF NOT EXISTS idx_role_assignments_user ON role_assignments(user_id, active);
        CREATE INDEX IF NOT EXISTS idx_entity_scope_user ON entity_scope_assignments(user_id, active);
        CREATE INDEX IF NOT EXISTS idx_collector_user ON collector_mappings(user_id, active);
        CREATE INDEX IF NOT EXISTS idx_sso_sessions_user ON sso_sessions(user_id, status);
        """
    )


@dataclass(frozen=True)
class VerifiedToken:
    header: Dict[str, Any]
    claims: Dict[str, Any]
    token_hash: str


class JWTValidationError(ValueError):
    pass


class JWTVerifier:
    def __init__(self, issuer: str = DEFAULT_JWT_ISSUER, audience: str = DEFAULT_JWT_AUDIENCE, secret: str = DEFAULT_JWT_SECRET) -> None:
        self.issuer = issuer
        self.audience = audience
        self.secret = secret

    def verify(self, token: str, *, now_ts: Optional[int] = None) -> VerifiedToken:
        token = (token or "").strip()
        parts = token.split(".")
        if len(parts) != 3:
            raise JWTValidationError("malformed_token")
        try:
            header = json.loads(_b64url_decode(parts[0]).decode("utf-8"))
            claims = json.loads(_b64url_decode(parts[1]).decode("utf-8"))
        except Exception as exc:
            raise JWTValidationError(f"invalid_token_encoding:{exc}") from exc
        alg = str(header.get("alg", "")).upper()
        if alg in {"", "NONE"}:
            raise JWTValidationError("unsigned_tokens_rejected")
        if alg != "HS256":
            raise JWTValidationError("unsupported_alg_for_patch_pack_use_gateway_or_jwks")
        signing_input = f"{parts[0]}.{parts[1]}".encode("ascii")
        expected = hmac.new(self.secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
        provided = _b64url_decode(parts[2])
        if not hmac.compare_digest(expected, provided):
            raise JWTValidationError("invalid_signature")
        now_ts = int(now_ts or time.time())
        exp = int(claims.get("exp", 0) or 0)
        if not exp or exp <= now_ts:
            raise JWTValidationError("token_expired")
        nbf = int(claims.get("nbf", 0) or 0)
        if nbf and nbf > now_ts:
            raise JWTValidationError("token_not_yet_valid")
        iss = claims.get("iss")
        if self.issuer and iss != self.issuer:
            raise JWTValidationError("issuer_mismatch")
        aud = claims.get("aud")
        aud_values = aud if isinstance(aud, list) else [aud]
        if self.audience and self.audience not in aud_values:
            raise JWTValidationError("audience_mismatch")
        if not claims.get("sub"):
            raise JWTValidationError("missing_subject")
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        return VerifiedToken(header=header, claims=claims, token_hash=token_hash)


def create_test_jwt(claims: Dict[str, Any], *, secret: str = DEFAULT_JWT_SECRET, issuer: str = DEFAULT_JWT_ISSUER, audience: str = DEFAULT_JWT_AUDIENCE, lifetime_seconds: int = 3600) -> str:
    now_ts = int(time.time())
    full_claims = dict(claims)
    full_claims.setdefault("iss", issuer)
    full_claims.setdefault("aud", audience)
    full_claims.setdefault("iat", now_ts)
    full_claims.setdefault("exp", now_ts + lifetime_seconds)
    header = {"alg": "HS256", "typ": "JWT"}
    h = _b64url_encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    p = _b64url_encode(json.dumps(full_claims, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    sig = hmac.new(secret.encode("utf-8"), f"{h}.{p}".encode("ascii"), hashlib.sha256).digest()
    return f"{h}.{p}.{_b64url_encode(sig)}"


def _groups_from_claims(claims: Dict[str, Any]) -> List[str]:
    raw = claims.get("groups") or claims.get("roles") or claims.get("scp_groups") or []
    if isinstance(raw, str):
        return [item.strip() for item in raw.split(",") if item.strip()]
    if isinstance(raw, list):
        return [str(item) for item in raw]
    return []


def role_from_claims(claims: Dict[str, Any]) -> str:
    direct = claims.get("scip_role") or claims.get("role")
    if direct:
        return canonical_role(str(direct))
    groups = {g.strip().lower() for g in _groups_from_claims(claims)}
    mapped_roles = [role for group, role in GROUP_ROLE_MAP.items() if group.lower() in groups]
    if not mapped_roles:
        raise ValueError("no_scip_role_claim_or_group")
    for role in ROLE_PRIORITY:
        if role in mapped_roles:
            return role
    return mapped_roles[0]


def _email_hash(email: Optional[str]) -> Optional[str]:
    if not email:
        return None
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


def upsert_user_from_claims(claims: Dict[str, Any], db_path: Path | str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    subject = str(claims.get("sub"))
    user_id = str(claims.get("scip_user_id") or subject)
    display_name = str(claims.get("name") or claims.get("preferred_username") or subject)
    email_hash = _email_hash(claims.get("email"))
    source_idp = str(claims.get("idp") or claims.get("iss") or "jwt")
    now = _now()
    role = role_from_claims(claims)
    entity_scope = claims.get("scip_entity_scope") or claims.get("entity_scope") or ["Group"]
    if isinstance(entity_scope, str):
        entity_scope = _split_scope(entity_scope, ["Group"])
    collector_id = claims.get("scip_collector_id") or claims.get("collector_id")

    with _connect(db_path) as conn:
        existing = conn.execute("SELECT active, deactivated_at FROM provisioned_users WHERE user_id = ?", (user_id,)).fetchone()
        if existing and int(existing["active"]) == 0:
            raise ValueError("user_deactivated")
        conn.execute(
            """
            INSERT INTO provisioned_users(user_id, subject, display_name, email_hash, active, source_idp, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET display_name=excluded.display_name, email_hash=excluded.email_hash,
                source_idp=excluded.source_idp, updated_at=excluded.updated_at
            """,
            (user_id, subject, display_name, email_hash, source_idp, now, now),
        )
        assignment_id = hashlib.sha256(f"role:{user_id}:{role}".encode("utf-8")).hexdigest()[:24]
        conn.execute(
            """
            INSERT INTO role_assignments(assignment_id, user_id, scip_role, source, active, created_at, updated_at)
            VALUES (?, ?, ?, 'jwt_claims', 1, ?, ?)
            ON CONFLICT(assignment_id) DO UPDATE SET active=1, updated_at=excluded.updated_at
            """,
            (assignment_id, user_id, role, now, now),
        )
        scope_id = hashlib.sha256(f"scope:{user_id}:{_json(entity_scope)}".encode("utf-8")).hexdigest()[:24]
        conn.execute(
            """
            INSERT INTO entity_scope_assignments(assignment_id, user_id, entity_scope_json, source, active, created_at, updated_at)
            VALUES (?, ?, ?, 'jwt_claims', 1, ?, ?)
            ON CONFLICT(assignment_id) DO UPDATE SET active=1, updated_at=excluded.updated_at
            """,
            (scope_id, user_id, _json(entity_scope), now, now),
        )
        if collector_id:
            mapping_id = hashlib.sha256(f"collector:{user_id}:{collector_id}".encode("utf-8")).hexdigest()[:24]
            conn.execute(
                """
                INSERT INTO collector_mappings(mapping_id, user_id, collector_id, collector_name, active, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, ?, ?)
                ON CONFLICT(mapping_id) DO UPDATE SET active=1, collector_name=excluded.collector_name, updated_at=excluded.updated_at
                """,
                (mapping_id, user_id, str(collector_id), display_name, now, now),
            )
        conn.commit()
    return {
        "user_id": user_id,
        "subject": subject,
        "display_name": display_name,
        "role": role,
        "entity_scope": list(entity_scope),
        "collector_id": str(collector_id) if collector_id else None,
    }


def load_user_provisioning(user_id: str, db_path: Path | str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    with _connect(db_path) as conn:
        user = conn.execute("SELECT * FROM provisioned_users WHERE user_id = ?", (user_id,)).fetchone()
        if not user:
            raise ValueError("user_not_provisioned")
        if int(user["active"]) == 0:
            raise ValueError("user_deactivated")
        role_row = conn.execute("SELECT scip_role FROM role_assignments WHERE user_id = ? AND active = 1 ORDER BY updated_at DESC LIMIT 1", (user_id,)).fetchone()
        scope_row = conn.execute("SELECT entity_scope_json FROM entity_scope_assignments WHERE user_id = ? AND active = 1 ORDER BY updated_at DESC LIMIT 1", (user_id,)).fetchone()
        collector_row = conn.execute("SELECT collector_id FROM collector_mappings WHERE user_id = ? AND active = 1 ORDER BY updated_at DESC LIMIT 1", (user_id,)).fetchone()
        role = canonical_role(role_row["scip_role"] if role_row else "board_cxo")
        scope = _loads(scope_row["entity_scope_json"], ["Group"]) if scope_row else ["Group"]
        return {
            "user_id": user_id,
            "subject": user["subject"],
            "display_name": user["display_name"],
            "role": role,
            "entity_scope": scope,
            "collector_id": collector_row["collector_id"] if collector_row else None,
            "active": bool(user["active"]),
        }


def actor_from_verified_token(verified: VerifiedToken, db_path: Path | str = DEFAULT_DB_PATH) -> Any:
    if auth is None:
        raise RuntimeError("auth_module_required")
    upserted = upsert_user_from_claims(verified.claims, db_path)
    provisioned = load_user_provisioning(upserted["user_id"], db_path)
    role = canonical_role(provisioned["role"])
    return auth.Actor(
        actor_id=provisioned["user_id"],
        actor_name=provisioned["display_name"],
        role=role,
        role_label=auth.ROLE_LABELS[role],
        entity_scope=list(provisioned["entity_scope"] or ["Group"]),
        collector_id=provisioned.get("collector_id"),
        environment=os.environ.get("SCIP_ENV", "local"),
        permissions=sorted(auth.PERMISSIONS[role]),
    )


def _correlation_id(headers: Dict[str, str]) -> str:
    if observability is not None and hasattr(observability, "CORRELATION_ID_CTX"):
        try:
            existing = observability.CORRELATION_ID_CTX.get()  # type: ignore[attr-defined]
            if existing:
                return existing
        except Exception:
            pass
    normalized = {str(k).lower(): str(v) for k, v in headers.items()}
    return normalized.get("x-scip-correlation-id") or normalized.get("x-request-id") or f"scip-{uuid.uuid4().hex}"


def log_identity_denial(reason: str, *, subject: Optional[str] = None, path: str = "", method: str = "GET", headers: Optional[Dict[str, str]] = None, claims: Optional[Dict[str, Any]] = None, db_path: Path | str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    correlation_id = _correlation_id(headers or {})
    created_at = _now()
    audit_lineage = {
        "contract_version": IDENTITY_CONTRACT_VERSION,
        "reason": reason,
        "subject": subject,
        "claim_fingerprint": hashlib.sha256(_json(_redact_claims(claims or {})).encode("utf-8")).hexdigest() if claims else None,
        "correlation_id": correlation_id,
        "created_at": created_at,
    }
    denial_id = "ideny_" + hashlib.sha256(_json(audit_lineage).encode("utf-8")).hexdigest()[:20]
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO identity_denials(denial_id, subject, reason, path, method, correlation_id, audit_lineage_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (denial_id, subject, reason, path, method, correlation_id, _json(audit_lineage), created_at),
        )
        conn.commit()
    if auth is not None and hasattr(auth, "log_denied_attempt"):
        try:
            auth.log_denied_attempt(None, "authenticate:jwt", reason, path=path, method=method, row_context={"correlation_id": correlation_id, "identity_denial_id": denial_id})
        except Exception:
            pass
    return {"denial_id": denial_id, "correlation_id": correlation_id, "audit_lineage": audit_lineage}


def actor_from_local_dev_headers(headers: Dict[str, str]) -> Any:
    if not (AUTH_MODE == "local_dev" and LOCAL_DEV_BYPASS):
        raise JWTValidationError("local_dev_bypass_disabled")
    if auth is None:
        raise RuntimeError("auth_module_required")
    return auth.legacy_actor_from_headers(headers) if hasattr(auth, "legacy_actor_from_headers") else auth.actor_from_headers(headers)


def actor_from_request_headers(headers: Dict[str, str], *, path: str = "", method: str = "GET", db_path: Path | str = DEFAULT_DB_PATH) -> Any:
    normalized = {str(k).lower(): str(v) for k, v in headers.items()}
    if AUTH_MODE == "local_dev" and LOCAL_DEV_BYPASS:
        return actor_from_local_dev_headers(normalized)
    auth_header = normalized.get("authorization", "")
    if not auth_header.lower().startswith("bearer "):
        log_identity_denial("missing_bearer_token", path=path, method=method, headers=normalized, db_path=db_path)
        raise JWTValidationError("missing_bearer_token")
    token = auth_header.split(" ", 1)[1].strip()
    claims: Dict[str, Any] = {}
    try:
        verified = JWTVerifier().verify(token)
        claims = verified.claims
        actor = actor_from_verified_token(verified, db_path)
        record_session(actor.actor_id, verified, headers=normalized, db_path=db_path)
        return actor
    except Exception as exc:
        subject = claims.get("sub") if isinstance(claims, dict) else None
        log_identity_denial(str(exc), subject=subject, path=path, method=method, headers=normalized, claims=claims, db_path=db_path)
        raise


def record_session(user_id: str, verified: VerifiedToken, *, headers: Optional[Dict[str, str]] = None, db_path: Path | str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    claims = verified.claims
    issued_ts = int(claims.get("iat") or time.time())
    exp_ts = int(claims.get("exp") or time.time())
    issued_at = datetime.fromtimestamp(issued_ts, timezone.utc).isoformat().replace("+00:00", "Z")
    expires_at = datetime.fromtimestamp(exp_ts, timezone.utc).isoformat().replace("+00:00", "Z")
    refresh_expires_at = datetime.fromtimestamp(exp_ts + 3600, timezone.utc).isoformat().replace("+00:00", "Z")
    session_id = "sess_" + verified.token_hash[:24]
    correlation_id = _correlation_id(headers or {})
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO sso_sessions(session_id, user_id, subject, issued_at, expires_at, refresh_expires_at, status, token_hash, correlation_id)
            VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
            """,
            (session_id, user_id, str(claims.get("sub")), issued_at, expires_at, refresh_expires_at, verified.token_hash, correlation_id),
        )
        conn.commit()
    return {"session_id": session_id, "expires_at": expires_at, "refresh_expires_at": refresh_expires_at, "correlation_id": correlation_id}


def deactivate_user(user_id: str, reason: str, db_path: Path | str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    now = _now()
    with _connect(db_path) as conn:
        conn.execute("UPDATE provisioned_users SET active = 0, deactivated_at = ?, deactivation_reason = ?, updated_at = ? WHERE user_id = ?", (now, reason, now, user_id))
        conn.execute("UPDATE role_assignments SET active = 0, updated_at = ? WHERE user_id = ?", (now, user_id))
        conn.execute("UPDATE entity_scope_assignments SET active = 0, updated_at = ? WHERE user_id = ?", (now, user_id))
        conn.execute("UPDATE collector_mappings SET active = 0, updated_at = ? WHERE user_id = ?", (now, user_id))
        conn.execute("UPDATE sso_sessions SET status = 'revoked' WHERE user_id = ?", (user_id,))
        conn.commit()
    return {"status": "deactivated", "user_id": user_id, "reason": reason, "deactivated_at": now}


def provisioning_summary(db_path: Path | str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    with _connect(db_path) as conn:
        def count(table: str, where: str = "") -> int:
            return int(conn.execute(f"SELECT COUNT(*) AS c FROM {table} {where}").fetchone()["c"])
        users = [dict(row) for row in conn.execute("SELECT user_id, subject, display_name, active, source_idp, updated_at FROM provisioned_users ORDER BY updated_at DESC LIMIT 50").fetchall()]
        return {
            "contract_version": IDENTITY_CONTRACT_VERSION,
            "auth_mode": AUTH_MODE,
            "local_dev_bypass_enabled": LOCAL_DEV_BYPASS,
            "counts": {
                "users": count("provisioned_users"),
                "active_users": count("provisioned_users", "WHERE active = 1"),
                "groups": count("provisioned_groups"),
                "role_assignments": count("role_assignments", "WHERE active = 1"),
                "entity_scope_assignments": count("entity_scope_assignments", "WHERE active = 1"),
                "collector_mappings": count("collector_mappings", "WHERE active = 1"),
                "sessions": count("sso_sessions"),
                "identity_denials": count("identity_denials"),
            },
            "users": users,
        }



def get_identity_actor(request: Request) -> Any:
    return actor_from_request_headers(dict(request.headers), path=getattr(getattr(request, "url", None), "path", "unknown"), method=getattr(request, "method", "GET"))

def identity_policy() -> Dict[str, Any]:
    return {
        "contract_version": IDENTITY_CONTRACT_VERSION,
        "default_auth_mode": "jwt",
        "local_dev_bypass": "SCIP_AUTH_MODE=local_dev and SCIP_LOCAL_DEV_BYPASS=true only",
        "accepted_token": {
            "authorization_header": "Bearer <JWT>",
            "algorithms": ["HS256 in patch pack", "RS256/ES256 via production gateway or JWKS verifier"],
            "required_claims": ["sub", "iss", "aud", "exp", "scip_role or mapped groups"],
            "recommended_claims": ["name", "email", "scip_entity_scope", "scip_collector_id"],
        },
        "group_role_map": GROUP_ROLE_MAP,
        "role_model": ROLE_MODEL,
        "removed_roles": sorted(REMOVED_ROLES),
        "provisioning_models": [
            "provisioned_users", "provisioned_groups", "user_group_memberships", "role_assignments",
            "entity_scope_assignments", "collector_mappings", "sso_sessions", "identity_denials",
        ],
        "denied_attempts": "Identity denials include correlation_id and audit_lineage_json; RBAC denials continue in access_denials.",
    }


if APIRouter is not None:
    router = APIRouter(prefix="/identity", tags=["identity-sso-jwt"])

    @router.get("/me")
    async def identity_me(request: Request) -> Any:
        actor = actor_from_request_headers(dict(request.headers), path="/identity/me", method="GET")
        return {"contract_version": IDENTITY_CONTRACT_VERSION, "actor": actor.to_dict(), "auth_mode": AUTH_MODE}

    @router.get("/policy")
    async def identity_policy_route() -> Any:
        return identity_policy()

    @router.get("/provisioning")
    async def identity_provisioning(actor: Any = Depends(get_identity_actor)) -> Any:
        if auth is not None and not auth.authorize(actor, "read:security_audit", path="/identity/provisioning"):
            raise HTTPException(status_code=403, detail={"status": "denied", "reason": "missing_permission"})
        return provisioning_summary()

    @router.post("/deactivate/{user_id}")
    async def deactivate_user_route(user_id: str, reason: str = "admin_deactivation", actor: Any = Depends(get_identity_actor)) -> Any:
        if auth is not None and not auth.authorize(actor, "read:security_audit", path="/identity/deactivate", method="POST"):
            raise HTTPException(status_code=403, detail={"status": "denied", "reason": "missing_permission"})
        return deactivate_user(user_id, reason)

    @router.post("/test-token")
    async def issue_test_token(claims: Dict[str, Any]) -> Any:
        if AUTH_MODE != "local_dev":
            raise HTTPException(status_code=403, detail={"status": "denied", "reason": "test_token_only_in_local_dev"})
        return {"token": create_test_jwt(claims), "contract_version": IDENTITY_CONTRACT_VERSION}
else:  # pragma: no cover
    router = None
