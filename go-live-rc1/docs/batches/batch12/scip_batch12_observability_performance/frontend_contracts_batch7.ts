export type SCIPRole = 'collector_rm' | 'cco_gm_agm' | 'finance' | 'mis_qcg_admin';

export type ActionQueueLineageRef = {
  metric_key: string;
  metric_label: string;
  has_lineage: boolean;
  source_code: string;
  source_file: string;
  sheet: string;
  cell_or_range: string;
  snapshot_date?: string | null;
  validation_status: 'passed' | 'warning' | 'failed';
  confidence_state: string;
  reporting_basis: string;
};

export type AccountAction = {
  action_id: string;
  action_type: 'collector_ptp_follow_up' | 'termination_escalation_review' | 'finance_pr_quality_exception' | string;
  grain: 'account_unit' | 'payment_request_account_unit' | 'collector' | 'process_bucket_month' | string;
  role_visibility: SCIPRole[];
  status: 'ready' | string;
  title: string;
  summary: string;
  recommended_action: string;
  severity: 'watch' | 'attention' | 'risk';
  account_id?: string;
  unit?: string;
  customer_name?: string | null;
  collector_rm_owner?: string;
  manager_name?: string | null;
  entity_code?: string;
  entity_display?: string;
  parent_entity_code?: string | null;
  parent_entity_display?: string | null;
  project?: string | null;
  sub_project?: string | null;
  amount_aed?: number;
  display_amount?: string;
  overdue_amount_aed?: number | null;
  ageing_bucket?: string;
  ptp_date?: string | null;
  ptp_amount_aed?: number | null;
  ptp_status?: string | null;
  pr_status?: string | null;
  receipt_status?: string | null;
  escalation_status?: string | null;
  reporting_basis: string;
  confidence_state: string;
  lineage_refs: ActionQueueLineageRef[];
};

export type RoleActionQueue = {
  role: SCIPRole;
  status: string;
  headline: string;
  disclosure: string;
  account_actions: AccountAction[];
  process_actions: AccountAction[];
  management_actions: AccountAction[];
  required_source_fields: string[];
  reporting_basis: string;
};

export type ActionQueuesBatch7Payload = {
  contract_version: 'action_queues.v2.batch7';
  status: 'ready_account_level_guarded' | 'validation_failed' | string;
  generated_at: string;
  guardrails: {
    tolerance_pct: 0.05;
    no_silent_fallback: true;
    locked_hierarchy: string;
    role_model: string[];
    removed_role: 'Entity Head';
    account_action_gate: string;
    liquid_glass_gate: string;
  };
  source_availability: Record<string, 'loaded' | 'missing' | string>;
  data_grain_disclosure: {
    current_grain: string;
    true_account_level_available: boolean;
    rule: string;
  };
  facts_summary: Record<string, number>;
  roles: Partial<Record<SCIPRole, RoleActionQueue>>;
  validations: {
    passed: boolean;
    checked_action_count: number;
    checked_account_action_count: number;
    checks: Record<string, boolean>;
  };
  lineage_sample: ActionQueueLineageRef[];
  source_notes: Record<string, string>;
};
