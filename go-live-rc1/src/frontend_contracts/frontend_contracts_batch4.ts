// SCIP Batch 4 frontend contracts
// Contract versions: quickball.v1.batch4, command_centres.v1.batch4

export type SCIPRoleKey =
  | 'board_cxo'
  | 'cco_gm_agm'
  | 'finance'
  | 'mis_qcg_admin'
  | 'collector_rm';

export type QuickballStatus = 'answered' | 'blocked_untrusted_metric' | 'unknown_metric';

export interface SCIPRoleMode {
  label: string;
  purpose: string;
  tone?: string;
  focus?: string[];
}

export interface LineageRecord {
  metric_key?: string;
  metric_label?: string;
  value?: number | string | null;
  unit?: string;
  source_code: string;
  source_file: string;
  sheet: string;
  cell_or_range: string;
  snapshot_date?: string | null;
  extraction_method?: string;
  entity_scope?: string;
  business_definition?: string;
  validation_status: string;
  confidence_state: string;
  last_loaded_at?: string;
  reporting_basis?: string;
}

export interface QuickballGuardrail {
  critical_metric: boolean;
  no_silent_fallback: boolean;
  requires_lineage: boolean;
  lineage_gate_passed?: boolean;
}

export interface QuickballExplainResponse {
  status: QuickballStatus;
  role: SCIPRoleMode;
  metric_key?: string;
  metric_label?: string;
  value?: number | string | null;
  display_value?: string;
  unit?: string;
  reporting_basis?: string;
  source_code?: string;
  business_definition?: string;
  answer: string;
  role_interpretation?: string;
  lineage?: LineageRecord | null;
  guardrail?: QuickballGuardrail;
  reason?: string;
}

export interface CommandCentreMetricRef {
  metric_key: string;
  lineage_bucket: string;
  lineage_key: string;
  has_lineage: boolean;
  source_file?: string | null;
  sheet?: string | null;
  cell_or_range?: string | null;
  validation_status?: string | null;
  confidence_state?: string | null;
  reporting_basis?: string | null;
}

export interface CommandCentreCard {
  card_id: string;
  title: string;
  value: number | string | Record<string, unknown> | null;
  display_value: string;
  reporting_basis: string;
  action: string;
  severity: 'info' | 'monitor' | 'risk' | 'strategic' | 'control' | string;
  lineage_refs: CommandCentreMetricRef[];
  trust_state: 'lineaged' | 'blocked_or_partial_lineage' | string;
}

export interface CommandCentreTrustBar {
  snapshot_date?: string | null;
  load_timestamp?: string | null;
  platform_version?: string | null;
  sources_loaded: string[];
  sources_missing: string[];
  critical_sources: string[];
  critical_lineage_counts: Record<string, number>;
  critical_validation_counts: Record<string, number>;
  no_silent_fallback: boolean;
  tolerance_pct: number;
}

export interface RoleCommandCentre {
  role_label: string;
  purpose: string;
  trust_bar: CommandCentreTrustBar;
  cards: CommandCentreCard[];
}

export interface CommandCentresResponse {
  status: 'ok' | string;
  contract_version: 'command_centres.v1.batch4' | string;
  roles: Record<SCIPRoleKey, RoleCommandCentre>;
  role_order: SCIPRoleKey[];
  guardrails: {
    no_silent_fallback: boolean;
    critical_cards_require_lineage_refs: boolean;
    finance_vs_mdo_label_required: boolean;
    entity_head_removed: boolean;
  };
}

export function shouldShowTrustWarning(card: CommandCentreCard): boolean {
  return card.trust_state !== 'lineaged' || card.lineage_refs.some((ref) => !ref.has_lineage);
}

export function shouldRenderQuickballBlockedState(answer: QuickballExplainResponse): boolean {
  return answer.status === 'blocked_untrusted_metric';
}
