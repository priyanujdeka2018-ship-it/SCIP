-- SCIP Batch 16 continuous improvement governance
-- Migration-ready SQL. Compatible with SQLite; adapt types for Postgres if needed.

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
