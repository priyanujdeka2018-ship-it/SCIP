export type WorkflowState =
  | "queued"
  | "assigned"
  | "in_progress"
  | "promised"
  | "escalated"
  | "closed"
  | "stale"
  | "blocked";

export type WorkflowRole = "collector_rm" | "cco_gm_agm" | "finance" | "mis_qcg_admin";

export interface WorkflowLineageRef {
  metric_key: string;
  metric_label?: string;
  has_lineage: boolean;
  source_code: string;
  source_file: string;
  sheet: string;
  cell_or_range: string;
  snapshot_date?: string | null;
  validation_status: string;
  confidence_state: string;
  reporting_basis: string;
}

export interface WorkflowSourceSnapshot {
  account_id?: string;
  unit?: string;
  customer_name?: string;
  project?: string;
  sub_project?: string;
  collector_rm_owner?: string;
  manager_name?: string;
  entity_code?: string;
  entity_display?: string;
  parent_entity_code?: string;
  parent_entity_display?: string;
  amount_aed?: number;
  display_amount?: string;
  ageing_bucket?: string;
  ptp_date?: string;
  ptp_amount_aed?: number;
  ptp_status?: string;
  pr_status?: string;
  escalation_status?: string;
  reporting_basis?: string;
  confidence_state?: string;
}

export interface WorkflowRecord {
  workflow_id: string;
  source_action_id: string;
  action_type: string;
  grain: string;
  title: string;
  summary?: string;
  recommended_action?: string;
  role_visibility: WorkflowRole[];
  workflow_state: WorkflowState;
  assigned_owner?: string;
  original_owner?: string;
  due_date?: string | null;
  disposition?: string | null;
  closure_reason?: string | null;
  closed_at?: string | null;
  stale_reason?: string | null;
  blocked_reason?: string | null;
  evidence_attachments: WorkflowEvidenceAttachment[];
  event_count: number;
  source_snapshot: WorkflowSourceSnapshot;
  immutable_lineage_refs: WorkflowLineageRef[];
  lineage_hash: string;
  source_gate: {
    assignable: boolean;
    failures: string[];
    rule: string;
  };
  created_at: string;
  updated_at: string;
}

export interface WorkflowEvent {
  event_id: string;
  workflow_id: string;
  source_action_id: string;
  event_type: string;
  actor_role: WorkflowRole | "system";
  actor: string;
  from_state: WorkflowState | "none";
  to_state: WorkflowState;
  event_payload: Record<string, unknown>;
  immutable_lineage_refs: WorkflowLineageRef[];
  lineage_hash: string;
  created_at: string;
}

export interface WorkflowEvidenceAttachment {
  evidence_id: string;
  evidence_type: string;
  evidence_ref: string;
  note?: string;
  attached_by: string;
  attached_by_role: WorkflowRole;
  attached_at: string;
}

export interface WorkflowPayloadBatch8 {
  contract_version: "workflow.v1.batch8";
  status: "ready_workflow_tracking_guarded" | "validation_failed";
  generated_at: string;
  workflow_states: WorkflowState[];
  guardrails: Record<string, unknown>;
  permission_model: Record<WorkflowRole, Record<string, unknown>>;
  summary: {
    workflow_count: number;
    event_count: number;
    state_counts: Record<WorkflowState, number>;
    lineaged_event_count: number;
  };
  records: WorkflowRecord[];
  event_log: WorkflowEvent[];
  validations: {
    passed: boolean;
    checks: Record<string, boolean>;
    checked_record_count: number;
    checked_event_count: number;
  };
}

export interface WorkflowAssignRequest {
  action_id: string;
  assignee: string;
  actor: string;
  actor_role: WorkflowRole;
  due_date?: string;
  note?: string;
}

export interface WorkflowDispositionRequest {
  action_id: string;
  disposition: string;
  next_state?: Exclude<WorkflowState, "closed" | "blocked">;
  actor: string;
  actor_role: WorkflowRole;
  note?: string;
}

export interface WorkflowCloseRequest {
  action_id: string;
  closure_reason: string;
  evidence_ref?: string;
  actor: string;
  actor_role: WorkflowRole;
  note?: string;
}
