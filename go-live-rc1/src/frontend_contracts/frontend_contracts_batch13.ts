export type SCIPRole = "board_cxo" | "cco_gm_agm" | "finance" | "mis_qcg_admin" | "collector_rm";

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

export interface IdentityMeResponse {
  contract_version: "identity_sso_jwt.v1.batch13";
  auth_mode: "jwt" | "local_dev";
  actor: SCIPActor;
}

export interface IdentityPolicyResponse {
  contract_version: "identity_sso_jwt.v1.batch13";
  default_auth_mode: "jwt";
  local_dev_bypass: string;
  accepted_token: {
    authorization_header: "Bearer <JWT>";
    algorithms: string[];
    required_claims: string[];
    recommended_claims: string[];
  };
  group_role_map: Record<string, SCIPRole>;
  role_model: SCIPRole[];
  removed_roles: string[];
  provisioning_models: string[];
  denied_attempts: string;
}

export interface ProvisioningSummaryResponse {
  contract_version: "identity_sso_jwt.v1.batch13";
  auth_mode: "jwt" | "local_dev";
  local_dev_bypass_enabled: boolean;
  counts: {
    users: number;
    active_users: number;
    groups: number;
    role_assignments: number;
    entity_scope_assignments: number;
    collector_mappings: number;
    sessions: number;
    identity_denials: number;
  };
  users: Array<{
    user_id: string;
    subject: string;
    display_name: string;
    active: number;
    source_idp: string;
    updated_at: string;
  }>;
}

export function buildIdentityHeaders(jwt: string, correlationId: string): Record<string, string> {
  return {
    Authorization: `Bearer ${jwt}`,
    "X-SCIP-Correlation-ID": correlationId,
  };
}
