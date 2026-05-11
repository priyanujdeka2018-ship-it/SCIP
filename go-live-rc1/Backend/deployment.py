"""
SCIP Batch 11 - production deployment hardening, environment config,
migration runner, backup/restore checks and deployment health endpoints.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from fastapi import APIRouter, Depends, HTTPException
except Exception:  # pragma: no cover
    APIRouter = None
    Depends = None
    HTTPException = Exception

import auth

DEPLOYMENT_CONTRACT_VERSION = "deployment_hardening.v1.batch11"
HERE = Path(__file__).resolve().parent
MIGRATIONS_DIR = HERE / "migrations"
DEFAULT_DB_PATH = Path(os.environ.get("SCIP_AUDIT_DB", str(HERE / "scip_batch11_security.sqlite")))
BACKUP_DIR = Path(os.environ.get("SCIP_BACKUP_DIR", str(HERE / "backups")))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, sort_keys=True, default=str)


@dataclass(frozen=True)
class EnvironmentConfig:
    environment: str
    frontend_url: str
    backend_url: str
    audit_db: str
    backup_dir: str
    cors_allowed_origins: List[str]
    auth_mode: str
    secrets_expected: List[str]
    secrets_present: List[str]
    secrets_missing: List[str]
    debug_enabled: bool


def load_environment_config() -> EnvironmentConfig:
    env = os.environ.get("SCIP_ENV", "local")
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
    origins = [x.strip().rstrip("/") for x in os.environ.get("CORS_ALLOWED_ORIGINS", frontend_url).split(",") if x.strip()]
    auth_mode = os.environ.get("SCIP_AUTH_MODE", "header-dev")
    expected = ["SCIP_SECRET_KEY", "SCIP_AUDIT_DB"] if env != "local" else ["SCIP_AUDIT_DB"]
    present = [name for name in expected if os.environ.get(name)]
    missing = [name for name in expected if not os.environ.get(name)]
    debug_enabled = os.environ.get("DEBUG", "false").lower() in {"1", "true", "yes"}
    return EnvironmentConfig(
        environment=env,
        frontend_url=frontend_url,
        backend_url=backend_url,
        audit_db=str(DEFAULT_DB_PATH),
        backup_dir=str(BACKUP_DIR),
        cors_allowed_origins=origins,
        auth_mode=auth_mode,
        secrets_expected=expected,
        secrets_present=present,
        secrets_missing=missing,
        debug_enabled=debug_enabled,
    )


def _connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_deployment_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS migration_history (
            migration_id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            checksum TEXT NOT NULL,
            applied_at TEXT NOT NULL,
            status TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS backup_checks (
            check_id TEXT PRIMARY KEY,
            db_path TEXT NOT NULL,
            backup_path TEXT NOT NULL,
            restore_path TEXT NOT NULL,
            source_count INTEGER NOT NULL,
            restored_count INTEGER NOT NULL,
            status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS deployment_health_checks (
            check_id TEXT PRIMARY KEY,
            environment TEXT NOT NULL,
            status TEXT NOT NULL,
            checks_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )


def _sha256(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run_migrations(db_path: Path | str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    applied: List[Dict[str, Any]] = []
    with _connect(db_path) as conn:
        ensure_deployment_tables(conn)
        auth._ensure_security_tables(conn)
        for sql_path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            migration_id = sql_path.stem
            checksum = _sha256(sql_path)
            existing = conn.execute("SELECT checksum FROM migration_history WHERE migration_id=?", (migration_id,)).fetchone()
            if existing and existing["checksum"] == checksum:
                applied.append({"migration_id": migration_id, "status": "already_applied", "checksum": checksum})
                continue
            if existing and existing["checksum"] != checksum:
                raise RuntimeError(f"migration_checksum_changed:{migration_id}")
            conn.executescript(sql_path.read_text(encoding="utf-8"))
            conn.execute(
                "INSERT INTO migration_history(migration_id, filename, checksum, applied_at, status) VALUES (?, ?, ?, ?, 'applied')",
                (migration_id, sql_path.name, checksum, _now()),
            )
            applied.append({"migration_id": migration_id, "status": "applied", "checksum": checksum})
        conn.commit()
    auth.seed_rbac_policies(db_path)
    return {"contract_version": DEPLOYMENT_CONTRACT_VERSION, "db_path": str(db_path), "applied": applied}


def backup_restore_check(db_path: Path | str = DEFAULT_DB_PATH, backup_dir: Path | str = BACKUP_DIR) -> Dict[str, Any]:
    db_path = Path(db_path)
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    if not db_path.exists():
        run_migrations(db_path)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"scip_audit_backup_{stamp}.sqlite"
    restore_path = backup_dir / f"scip_audit_restore_check_{stamp}.sqlite"
    shutil.copy2(db_path, backup_path)
    shutil.copy2(backup_path, restore_path)

    with _connect(db_path) as conn:
        ensure_deployment_tables(conn)
        source_count = sum(row[0] for row in conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchall())
    with _connect(restore_path) as conn:
        restored_count = sum(row[0] for row in conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchall())

    status = "passed" if source_count == restored_count and restored_count > 0 else "failed"
    evidence = {"source_table_count": source_count, "restored_table_count": restored_count}
    check_id = f"backup_{stamp}"
    with _connect(db_path) as conn:
        ensure_deployment_tables(conn)
        conn.execute(
            "INSERT OR REPLACE INTO backup_checks(check_id, db_path, backup_path, restore_path, source_count, restored_count, status, evidence_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (check_id, str(db_path), str(backup_path), str(restore_path), source_count, restored_count, status, _json(evidence), _now()),
        )
        conn.commit()
    return {
        "contract_version": DEPLOYMENT_CONTRACT_VERSION,
        "check_id": check_id,
        "status": status,
        "db_path": str(db_path),
        "backup_path": str(backup_path),
        "restore_path": str(restore_path),
        "evidence": evidence,
    }


def build_deployment_health(db_path: Path | str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    cfg = load_environment_config()
    db_path = Path(db_path)
    migration_status = "not_checked"
    table_count = 0
    denial_count = 0
    try:
        run_migrations(db_path)
        with _connect(db_path) as conn:
            table_count = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
            denial_count = conn.execute("SELECT COUNT(*) FROM access_denials").fetchone()[0]
        migration_status = "ok"
    except Exception as exc:
        migration_status = f"failed:{exc}"

    checks = {
        "environment_named": bool(cfg.environment),
        "cors_origins_configured": bool(cfg.cors_allowed_origins),
        "no_wildcard_cors_in_nonlocal": cfg.environment == "local" or "*" not in cfg.cors_allowed_origins,
        "auth_mode_declared": bool(cfg.auth_mode),
        "required_secrets_present": len(cfg.secrets_missing) == 0,
        "debug_disabled_for_nonlocal": cfg.environment == "local" or not cfg.debug_enabled,
        "migrations_ok": migration_status == "ok",
        "security_tables_exist": table_count >= 3,
        "denial_audit_accessible": denial_count >= 0,
        "backup_dir_configured": bool(cfg.backup_dir),
    }
    status = "ok" if all(checks.values()) else "needs_attention"
    payload = {
        "contract_version": DEPLOYMENT_CONTRACT_VERSION,
        "status": status,
        "generated_at": _now(),
        "environment_config": asdict(cfg),
        "checks": checks,
        "migration_status": migration_status,
        "table_count": table_count,
        "denial_count": denial_count,
        "hardening_notes": [
            "Header identity is acceptable for this patch pack; production should switch SCIP_AUTH_MODE to SSO/JWT validation.",
            "CORS is environment-driven and must not use wildcard origins outside local development.",
            "Secrets are checked by name only and are never returned in payloads.",
        ],
    }
    with _connect(db_path) as conn:
        ensure_deployment_tables(conn)
        conn.execute(
            "INSERT OR REPLACE INTO deployment_health_checks(check_id, environment, status, checks_json, created_at) VALUES (?, ?, ?, ?, ?)",
            ("deployment_health_latest", cfg.environment, status, _json(checks), _now()),
        )
        conn.commit()
    return payload


if APIRouter is not None:
    router = APIRouter(prefix="/deployment", tags=["deployment-hardening"])

    @router.get("/health")
    async def deployment_health(actor: auth.Actor = Depends(auth.get_actor)) -> Any:
        if not auth.authorize(actor, "read:deployment_health", path="/deployment/health"):
            raise HTTPException(status_code=403, detail={"status": "denied", "reason": "missing_permission"})
        return build_deployment_health()

    @router.post("/migrate")
    async def deployment_migrate(actor: auth.Actor = Depends(auth.get_actor)) -> Any:
        if not auth.authorize(actor, "run:migrations", path="/deployment/migrate", method="POST"):
            raise HTTPException(status_code=403, detail={"status": "denied", "reason": "missing_permission"})
        return run_migrations()

    @router.post("/backup-check")
    async def deployment_backup_check(actor: auth.Actor = Depends(auth.get_actor)) -> Any:
        if not auth.authorize(actor, "run:backup_restore_check", path="/deployment/backup-check", method="POST"):
            raise HTTPException(status_code=403, detail={"status": "denied", "reason": "missing_permission"})
        return backup_restore_check()
else:  # pragma: no cover
    router = None
