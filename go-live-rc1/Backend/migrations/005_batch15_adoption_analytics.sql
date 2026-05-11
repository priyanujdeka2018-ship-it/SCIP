-- SCIP Batch 15 adoption analytics and optimization backlog
-- Contract: adoption_optimization.v1.batch15

CREATE TABLE IF NOT EXISTS adoption_events (
    event_id TEXT PRIMARY KEY,
    event_ts TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    actor_hash TEXT NOT NULL,
    session_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('board_cxo','cco_gm_agm','finance','mis_qcg_admin','collector_rm')),
    world TEXT NOT NULL CHECK (world IN ('live_pulse','narratives')),
    focus TEXT,
    depth TEXT,
    event_type TEXT NOT NULL,
    output_type TEXT,
    source_contract TEXT NOT NULL,
    properties_json TEXT NOT NULL,
    redaction_applied INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_adoption_events_role_ts ON adoption_events(role, event_ts);
CREATE INDEX IF NOT EXISTS idx_adoption_events_world_focus ON adoption_events(world, focus);
CREATE INDEX IF NOT EXISTS idx_adoption_events_type ON adoption_events(event_type);
CREATE INDEX IF NOT EXISTS idx_adoption_events_corr ON adoption_events(correlation_id);

CREATE TABLE IF NOT EXISTS adoption_recommendations (
    recommendation_id TEXT PRIMARY KEY,
    created_ts TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('P0','P1','P2')),
    theme TEXT NOT NULL,
    title TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    liquid_glass_guardrail TEXT NOT NULL,
    owner_role TEXT NOT NULL CHECK (owner_role IN ('board_cxo','cco_gm_agm','finance','mis_qcg_admin','collector_rm')),
    status TEXT NOT NULL DEFAULT 'proposed',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
