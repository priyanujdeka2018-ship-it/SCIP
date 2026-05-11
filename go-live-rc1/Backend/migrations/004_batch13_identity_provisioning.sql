-- SCIP Batch 13 - SSO/JWT identity and provisioning schema
-- Migration-ready SQL for durable identity, provisioning, sessions, and identity denied-attempt audit.

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
    scip_role TEXT NOT NULL CHECK (scip_role IN ('board_cxo','cco_gm_agm','finance','mis_qcg_admin','collector_rm')),
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
    scip_role TEXT NOT NULL CHECK (scip_role IN ('board_cxo','cco_gm_agm','finance','mis_qcg_admin','collector_rm')),
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
    status TEXT NOT NULL CHECK (status IN ('active','expired','revoked','refresh_required')),
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

CREATE INDEX IF NOT EXISTS idx_identity_users_subject ON provisioned_users(subject);
CREATE INDEX IF NOT EXISTS idx_identity_role_user ON role_assignments(user_id, active);
CREATE INDEX IF NOT EXISTS idx_identity_entity_user ON entity_scope_assignments(user_id, active);
CREATE INDEX IF NOT EXISTS idx_identity_collector_user ON collector_mappings(user_id, active);
CREATE INDEX IF NOT EXISTS idx_identity_sessions_user ON sso_sessions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_identity_denials_created ON identity_denials(created_at);

INSERT OR IGNORE INTO migration_history(migration_id, description, applied_at, status, evidence_json)
VALUES ('004_batch13_identity_provisioning', 'SSO/JWT identity and provisioning schema', datetime('now'), 'applied', '{"contract":"identity_sso_jwt.v1.batch13"}');
