-- SCIP Batch 17: Long-term roadmap and executive operating rhythm
CREATE TABLE IF NOT EXISTS roadmap_items (
  roadmap_item_id TEXT PRIMARY KEY,
  quarter TEXT NOT NULL,
  horizon TEXT NOT NULL,
  title TEXT NOT NULL,
  strategic_objective TEXT NOT NULL,
  evidence_refs_json TEXT NOT NULL,
  owner TEXT NOT NULL,
  success_metric TEXT NOT NULL,
  rollout_gate TEXT NOT NULL,
  risk TEXT NOT NULL,
  dependency TEXT NOT NULL,
  rollback_exit_criteria TEXT NOT NULL,
  liquid_glass_guardrail TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS executive_operating_rhythm_events (
  rhythm_event_id TEXT PRIMARY KEY,
  cadence TEXT NOT NULL,
  owner TEXT NOT NULL,
  meeting_date TEXT NOT NULL,
  agenda_json TEXT NOT NULL,
  evidence_refs_json TEXT NOT NULL,
  decisions_json TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS benefits_realization_records (
  benefit_id TEXT PRIMARY KEY,
  benefit TEXT NOT NULL,
  baseline TEXT NOT NULL,
  target TEXT NOT NULL,
  measure TEXT NOT NULL,
  owner TEXT NOT NULL,
  review_frequency TEXT NOT NULL,
  latest_status TEXT DEFAULT 'not_started',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS steering_committee_decisions (
  decision_id TEXT PRIMARY KEY,
  decision TEXT NOT NULL,
  owner TEXT NOT NULL,
  due_date TEXT NOT NULL,
  evidence_refs_json TEXT NOT NULL,
  expected_impact TEXT NOT NULL,
  rollout_gate TEXT NOT NULL,
  rollback_criteria TEXT NOT NULL,
  decision_state TEXT NOT NULL CHECK(decision_state IN ('proposed','approved','held','rejected','rolled_back','closed')),
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
