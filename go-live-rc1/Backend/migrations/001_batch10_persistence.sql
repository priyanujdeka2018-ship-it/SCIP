-- SCIP Batch 10 durable persistence and audit export schema
-- SQLite-compatible, migration-ready. Production can port this schema to Postgres.
-- Preserve lineage hashes immutably; application code should reject updates that change them.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS source_actions (
    source_action_id TEXT PRIMARY KEY,
    action_type TEXT,
    grain TEXT,
    title TEXT,
    role_visibility_json TEXT NOT NULL,
    source_snapshot_json TEXT NOT NULL,
    source_action_lineage_json TEXT NOT NULL,
    source_lineage_hash TEXT NOT NULL,
    reporting_basis TEXT,
    confidence_state TEXT,
    source_gate_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workflow_records (
    workflow_id TEXT PRIMARY KEY,
    source_action_id TEXT NOT NULL REFERENCES source_actions(source_action_id),
    workflow_state TEXT NOT NULL CHECK(workflow_state IN ('queued','assigned','in_progress','promised','escalated','closed','stale','blocked')),
    assigned_owner TEXT,
    original_owner TEXT,
    due_date TEXT,
    disposition TEXT,
    closure_reason TEXT,
    closed_at TEXT,
    stale_reason TEXT,
    blocked_reason TEXT,
    evidence_attachments_json TEXT NOT NULL DEFAULT '[]',
    role_visibility_json TEXT NOT NULL,
    source_snapshot_json TEXT NOT NULL,
    immutable_lineage_refs_json TEXT NOT NULL,
    lineage_hash TEXT NOT NULL,
    source_gate_json TEXT NOT NULL,
    event_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workflow_events (
    event_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL REFERENCES workflow_records(workflow_id),
    source_action_id TEXT NOT NULL REFERENCES source_actions(source_action_id),
    event_type TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    actor TEXT NOT NULL,
    from_state TEXT,
    to_state TEXT,
    event_payload_json TEXT NOT NULL DEFAULT '{}',
    immutable_lineage_refs_json TEXT NOT NULL,
    lineage_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notification_eligibility (
    eligibility_id TEXT PRIMARY KEY,
    source_action_id TEXT NOT NULL REFERENCES source_actions(source_action_id),
    workflow_id TEXT NOT NULL REFERENCES workflow_records(workflow_id),
    rule_id TEXT NOT NULL,
    rule_evidence_json TEXT NOT NULL,
    eligible INTEGER NOT NULL CHECK(eligible IN (0,1)),
    blocked_reasons_json TEXT NOT NULL DEFAULT '[]',
    source_lineage_hash TEXT NOT NULL,
    workflow_lineage_hash TEXT NOT NULL,
    evaluated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notification_emissions (
    notification_id TEXT PRIMARY KEY,
    source_action_id TEXT NOT NULL REFERENCES source_actions(source_action_id),
    workflow_id TEXT NOT NULL REFERENCES workflow_records(workflow_id),
    rule_id TEXT NOT NULL,
    notification_type TEXT NOT NULL,
    recipient_role TEXT NOT NULL,
    severity TEXT,
    title TEXT,
    body TEXT,
    reporting_basis TEXT,
    confidence_state TEXT,
    source_action_lineage_json TEXT NOT NULL,
    workflow_event_lineage_json TEXT NOT NULL,
    notification_lineage_json TEXT NOT NULL,
    source_lineage_hash TEXT NOT NULL,
    workflow_lineage_hash TEXT NOT NULL,
    dedupe_key TEXT NOT NULL UNIQUE,
    suppression_scope TEXT NOT NULL,
    rule_evidence_json TEXT NOT NULL,
    delivery_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS suppression_state (
    dedupe_key TEXT PRIMARY KEY,
    suppression_scope TEXT NOT NULL,
    source_action_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    recipient_role TEXT NOT NULL,
    suppress_reemit_until TEXT,
    first_emitted_at TEXT NOT NULL,
    last_emitted_at TEXT NOT NULL,
    emission_count INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS delivery_status (
    delivery_id TEXT PRIMARY KEY,
    notification_id TEXT NOT NULL REFERENCES notification_emissions(notification_id),
    channel TEXT NOT NULL,
    external_delivery_enabled INTEGER NOT NULL CHECK(external_delivery_enabled IN (0,1)),
    delivery_state TEXT NOT NULL CHECK(delivery_state IN ('pending','suppressed','delivered','failed','disabled')),
    attempt_count INTEGER NOT NULL DEFAULT 0,
    last_attempt_at TEXT,
    last_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_exports (
    export_id TEXT PRIMARY KEY,
    export_format TEXT NOT NULL CHECK(export_format IN ('json','csv')),
    export_path TEXT NOT NULL,
    record_count INTEGER NOT NULL,
    filter_json TEXT NOT NULL DEFAULT '{}',
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    export_hash TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_workflow_records_source_action ON workflow_records(source_action_id);
CREATE INDEX IF NOT EXISTS idx_workflow_events_source_action ON workflow_events(source_action_id);
CREATE INDEX IF NOT EXISTS idx_notification_emissions_role_rule ON notification_emissions(recipient_role, rule_id);
CREATE INDEX IF NOT EXISTS idx_notification_emissions_source_action ON notification_emissions(source_action_id);
CREATE INDEX IF NOT EXISTS idx_delivery_status_notification ON delivery_status(notification_id);

CREATE TRIGGER IF NOT EXISTS trg_source_actions_lineage_immutable
BEFORE UPDATE OF source_lineage_hash, source_action_lineage_json ON source_actions
FOR EACH ROW
WHEN OLD.source_lineage_hash != NEW.source_lineage_hash OR OLD.source_action_lineage_json != NEW.source_action_lineage_json
BEGIN
    SELECT RAISE(ABORT, 'source action lineage is immutable');
END;

CREATE TRIGGER IF NOT EXISTS trg_workflow_records_lineage_immutable
BEFORE UPDATE OF lineage_hash, immutable_lineage_refs_json ON workflow_records
FOR EACH ROW
WHEN OLD.lineage_hash != NEW.lineage_hash OR OLD.immutable_lineage_refs_json != NEW.immutable_lineage_refs_json
BEGIN
    SELECT RAISE(ABORT, 'workflow record lineage is immutable');
END;

CREATE TRIGGER IF NOT EXISTS trg_workflow_events_lineage_immutable
BEFORE UPDATE OF lineage_hash, immutable_lineage_refs_json ON workflow_events
FOR EACH ROW
WHEN OLD.lineage_hash != NEW.lineage_hash OR OLD.immutable_lineage_refs_json != NEW.immutable_lineage_refs_json
BEGIN
    SELECT RAISE(ABORT, 'workflow event lineage is immutable');
END;

CREATE TRIGGER IF NOT EXISTS trg_notification_emissions_dedupe_immutable
BEFORE UPDATE OF dedupe_key, source_lineage_hash, workflow_lineage_hash ON notification_emissions
FOR EACH ROW
WHEN OLD.dedupe_key != NEW.dedupe_key OR OLD.source_lineage_hash != NEW.source_lineage_hash OR OLD.workflow_lineage_hash != NEW.workflow_lineage_hash
BEGIN
    SELECT RAISE(ABORT, 'notification dedupe and lineage are immutable');
END;
