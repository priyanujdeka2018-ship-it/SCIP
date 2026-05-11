export type SCIPRole = "board_cxo" | "cco_gm_agm" | "finance" | "mis_qcg_admin" | "collector_rm";

export type PersistenceTableCounts = {
  source_actions: number;
  workflow_records: number;
  workflow_events: number;
  notification_eligibility: number;
  notification_emissions: number;
  suppression_state: number;
  delivery_status: number;
  audit_exports: number;
};

export type PersistenceValidationChecks = {
  source_actions_persisted: boolean;
  workflow_records_persisted: boolean;
  workflow_events_persisted: boolean;
  notifications_persisted: boolean;
  suppression_state_persisted: boolean;
  delivery_status_persisted: boolean;
  workflow_lineage_hashes_present: boolean;
  event_lineage_hashes_present: boolean;
  notification_dedupe_keys_unique: boolean;
  lineage_triggers_block_tampering: boolean;
  closed_records_remain_auditable: boolean;
  audit_rows_have_source_action_lineage: boolean;
  audit_rows_have_workflow_event_lineage: boolean;
  audit_rows_include_actor_timestamp_role_state: boolean;
  audit_rows_include_closure_or_escalation_evidence: boolean;
  role_model_without_entity_head: boolean;
};

export type PersistenceSummaryPayload = {
  contract_version: "persistence_audit.v1.batch10";
  status: "ready_persistence_audit_guarded" | "validation_failed";
  generated_at: string;
  db_path: string;
  table_counts: PersistenceTableCounts;
  validations: {
    passed: boolean;
    checks: PersistenceValidationChecks;
    counts: PersistenceTableCounts;
    audit_row_count: number;
  };
  routes: string[];
};

export type AuditExportRow = {
  workflow_id: string;
  source_action_id: string;
  workflow_state: "queued" | "assigned" | "in_progress" | "promised" | "escalated" | "closed" | "stale" | "blocked";
  assigned_owner?: string | null;
  closure_reason?: string | null;
  event_id?: string | null;
  event_type?: string | null;
  actor_role?: SCIPRole | "system" | string | null;
  actor?: string | null;
  event_created_at?: string | null;
  notification_id?: string | null;
  rule_id?: string | null;
  recipient_role?: SCIPRole | string | null;
  dedupe_key?: string | null;
  workflow_record_lineage_hash?: string | null;
  workflow_event_lineage_hash?: string | null;
  notification_source_lineage_hash?: string | null;
  notification_workflow_lineage_hash?: string | null;
  source_action_lineage: unknown[];
  notification_lineage?: unknown;
  notification_rule_evidence?: unknown;
};

export type AuditExportPayload = {
  contract_version: "persistence_audit.v1.batch10";
  export_type: "audit_json";
  created_at: string;
  created_by: string;
  record_count: number;
  guardrails: {
    locked_hierarchy: string;
    tolerance_pct: 0.05;
    no_silent_fallback: true;
    role_model_without_entity_head: true;
    immutable_lineage_required: true;
  };
  rows: AuditExportRow[];
};
