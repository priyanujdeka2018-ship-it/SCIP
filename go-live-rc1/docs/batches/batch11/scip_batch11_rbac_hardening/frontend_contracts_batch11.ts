export type SCIPRole = 'board_cxo' | 'cco_gm_agm' | 'finance' | 'mis_qcg_admin' | 'collector_rm';

export interface SCIPActor {
  actor_id: string;
  actor_name: string;
  role: SCIPRole;
  role_label: string;
  entity_scope: string[];
  collector_id?: string | null;
  environment: string;
  permissions: string[];
}

export interface RBACPolicyMatrix {
  contract_version: 'rbac.v1.batch11';
  role_model: SCIPRole[];
  removed_roles: string[];
  permissions: Record<SCIPRole, string[]>;
  row_level_rules: {
    entity_scope: string;
    role_visibility: string;
    collector_rm_own: string;
    audit_export: string;
  };
}

export interface SecurityMePayload {
  contract_version: 'rbac.v1.batch11';
  actor: SCIPActor;
}

export interface AccessDenial {
  denial_id: string;
  actor_id?: string | null;
  actor_role?: SCIPRole | null;
  permission: string;
  reason: string;
  path?: string;
  method?: string;
  row_context: Record<string, unknown>;
  created_at: string;
}

export interface DeploymentHealthPayload {
  contract_version: 'deployment_hardening.v1.batch11';
  status: 'ok' | 'needs_attention' | 'failed';
  generated_at: string;
  environment_config: {
    environment: string;
    frontend_url: string;
    backend_url: string;
    audit_db: string;
    backup_dir: string;
    cors_allowed_origins: string[];
    auth_mode: string;
    secrets_expected: string[];
    secrets_present: string[];
    secrets_missing: string[];
    debug_enabled: boolean;
  };
  checks: Record<string, boolean>;
  migration_status: string;
  table_count: number;
  denial_count: number;
  hardening_notes: string[];
}

export interface BackupRestoreCheckPayload {
  contract_version: 'deployment_hardening.v1.batch11';
  check_id: string;
  status: 'passed' | 'failed';
  db_path: string;
  backup_path: string;
  restore_path: string;
  evidence: {
    source_table_count: number;
    restored_table_count: number;
  };
}

export interface Batch11Headers {
  'X-SCIP-Actor-ID': string;
  'X-SCIP-Actor-Name': string;
  'X-SCIP-Role': SCIPRole;
  'X-SCIP-Entity-Scope': string;
  'X-SCIP-Collector-ID'?: string;
  'X-SCIP-Environment': string;
}
