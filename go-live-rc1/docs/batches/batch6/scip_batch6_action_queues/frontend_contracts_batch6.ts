export type ActionQueueStatus =
  | "ready"
  | "account_source_required"
  | "partial_project_grain_account_source_required"
  | "blocked_missing_r18";

export type SCIPRole = "collector_rm" | "cco_gm_agm" | "finance" | "mis_qcg_admin" | "board_cxo";

export interface ActionLineageRef {
  metric_key?: string;
  metric_label?: string;
  source_code: string;
  source_file: string;
  sheet: string;
  cell_or_range: string;
  snapshot_date?: string;
  validation_status: string;
  confidence_state: string;
  reporting_basis: string;
}

export interface ActionQueueItem {
  action_id: string;
  action_type: "project_risk_cohort" | "account_action";
  grain: "project_ageing_bucket" | "account";
  status: "available_project_grain" | "blocked_missing_owner_lineage" | "ready";
  title: string;
  summary: string;
  recommended_action: string;
  severity: "watch" | "attention" | "risk";
  amount_aed: number;
  display_amount: string;
  ageing_bucket: string;
  project: string;
  entity_code: string;
  entity_display: string;
  parent_entity_code?: string;
  parent_entity_display?: string;
  account_id?: string | null;
  customer_id?: string | null;
  collector_rm_owner?: string | null;
  owner_mapping_status: string;
  blocked_reason?: string | null;
  lineage_refs: ActionLineageRef[];
  reporting_basis: string;
  confidence_state: string;
}

export interface ActionQueueRolePayload {
  role: SCIPRole;
  status: "ready" | "account_source_required";
  headline: string;
  disclosure: string;
  account_actions: ActionQueueItem[];
  project_risk_cohorts: ActionQueueItem[];
  blocked_actions: ActionQueueItem[];
  required_source_fields: string[];
  reporting_basis: string;
}

export interface ActionQueuesPayload {
  contract_version: "action_queues.v1.batch6";
  status: ActionQueueStatus;
  generated_at: string;
  snapshot_date?: string;
  guardrails: {
    tolerance_pct: number;
    no_silent_fallback: boolean;
    locked_hierarchy: string;
    account_action_gate: string;
    liquid_glass_gate: string;
  };
  source_availability: Record<string, string>;
  data_grain_disclosure: {
    current_grain: string;
    true_account_level_available: boolean;
    reason: string;
  };
  facts_summary: {
    project_ageing_facts: number;
    top_project_risk_cohorts: number;
    eligible_account_actions: number;
    project_ageing_observation_amount_aed_non_additive: number;
    amount_sum_disclosure: string;
  };
  roles: Partial<Record<SCIPRole, ActionQueueRolePayload>>;
  validations: {
    passed: boolean;
    checks: Record<string, boolean>;
  };
}
