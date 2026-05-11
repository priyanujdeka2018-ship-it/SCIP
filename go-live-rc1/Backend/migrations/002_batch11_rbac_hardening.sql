-- SCIP Batch 11 - RBAC and deployment hardening migration
-- Migration-ready SQL for SQLite patch pack; compatible concepts map to Postgres.

CREATE TABLE IF NOT EXISTS actors (
    actor_id TEXT PRIMARY KEY,
    actor_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('board_cxo','cco_gm_agm','finance','mis_qcg_admin','collector_rm')),
    entity_scope_json TEXT NOT NULL,
    collector_id TEXT,
    environment TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rbac_policies (
    role TEXT NOT NULL CHECK (role IN ('board_cxo','cco_gm_agm','finance','mis_qcg_admin','collector_rm')),
    permission TEXT NOT NULL,
    effect TEXT NOT NULL CHECK (effect IN ('allow','deny')) DEFAULT 'allow',
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

CREATE TABLE IF NOT EXISTS migration_history (
    migration_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    checksum TEXT NOT NULL,
    applied_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('applied','failed','rolled_back','already_applied'))
);

CREATE TABLE IF NOT EXISTS backup_checks (
    check_id TEXT PRIMARY KEY,
    db_path TEXT NOT NULL,
    backup_path TEXT NOT NULL,
    restore_path TEXT NOT NULL,
    source_count INTEGER NOT NULL,
    restored_count INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('passed','failed')),
    evidence_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS deployment_health_checks (
    check_id TEXT PRIMARY KEY,
    environment TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ok','needs_attention','failed')),
    checks_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_access_denials_actor_created ON access_denials(actor_id, created_at);
CREATE INDEX IF NOT EXISTS idx_access_denials_permission ON access_denials(permission);
CREATE INDEX IF NOT EXISTS idx_actors_role ON actors(role);
CREATE INDEX IF NOT EXISTS idx_rbac_policies_role ON rbac_policies(role);
