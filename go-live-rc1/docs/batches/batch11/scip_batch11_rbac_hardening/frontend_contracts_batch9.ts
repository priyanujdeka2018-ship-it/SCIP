/** SCIP Batch 9 notification contracts */

export type ScipRole = "board_cxo" | "cco_gm_agm" | "finance" | "mis_qcg_admin" | "collector_rm";

export type NotificationRuleId =
  | "overdue_due_date"
  | "stale_workflow"
  | "broken_ptp_promise"
  | "termination_risk"
  | "pr_tat_ageing"
  | "unassigned_high_risk";

export type NotificationType =
  | "collector_rm_reminder"
  | "manager_escalation"
  | "finance_exception_nudge"
  | "mis_qcg_governance_alert";

export interface NotificationLineageRef {
  source_code: string;
  source_file: string;
  sheet: string;
  cell_or_range: string;
  validation_status: string;
  confidence_state: string;
  reporting_basis: string;
  [key: string]: unknown;
}

export interface WorkflowEventLineage {
  latest_event_id: string;
  latest_event_type: string;
  latest_event_created_at: string;
  workflow_lineage_hash: string;
  immutable_lineage_refs: NotificationLineageRef[];
}

export interface ScipNotification {
  notification_id: string;
  contract_version: "notifications.v1.batch9";
  notification_type: NotificationType;
  rule_id: NotificationRuleId;
  severity: "medium" | "high" | "critical";
  recipient_role: ScipRole;
  recipient_role_label: string;
  recipient_owner?: string | null;
  title: string;
  message: string;
  recommended_action: string;
  world: "live_pulse";
  focus: "risk_action";
  output_layer: "L5_notification_output";
  source_action_id: string;
  workflow_id: string;
  workflow_state: string;
  reporting_basis: string;
  confidence_state: string;
  lineage: {
    source_action_lineage_refs: NotificationLineageRef[];
    source_lineage_hash: string;
    workflow_event_lineage: WorkflowEventLineage;
  };
  rule_evidence: Record<string, unknown> & { rule_id: NotificationRuleId; as_of_date: string };
  suppression: {
    dedupe_key: string;
    suppression_scope: string;
    suppress_reemit_until?: string;
    dedupe_material_hash: string;
  };
  delivery: {
    channel: "in_app";
    external_delivery_enabled: false;
    delivery_note: string;
  };
  created_at: string;
}

export interface ScipNotificationDigest {
  digest_id: string;
  title: string;
  world: "live_pulse";
  focus: "risk_action";
  output_layer: "L5_digest_output";
  as_of_date: string;
  notification_count: number;
  evidence_notification_ids: string[];
  aggregate_counts: {
    by_severity: Record<string, number>;
    by_role: Record<string, number>;
    by_rule: Record<string, number>;
  };
  suppression: {
    dedupe_key: string;
    suppression_scope: string;
  };
  lineage_hashes: string[];
  delivery: {
    channel: "in_app_digest";
    external_delivery_enabled: false;
  };
}

export interface ScipNotificationsPayload {
  contract_version: "notifications.v1.batch9";
  status: "ready_notifications_guarded" | "validation_failed";
  generated_at: string;
  as_of_date: string;
  guardrails: Record<string, unknown>;
  rules: Record<NotificationRuleId, Record<string, unknown>>;
  summary: {
    notification_count: number;
    blocked_candidate_count: number;
    by_role: Record<string, number>;
    by_rule: Record<string, number>;
    by_severity: Record<string, number>;
  };
  notifications: ScipNotification[];
  digests: {
    daily_live_pulse_risk_action: ScipNotificationDigest;
    weekly_management_review: ScipNotificationDigest;
  };
  validations: {
    passed: boolean;
    checks: Record<string, boolean>;
    invalid_notifications: Array<{ notification_id?: string; failures: string[] }>;
  };
}
