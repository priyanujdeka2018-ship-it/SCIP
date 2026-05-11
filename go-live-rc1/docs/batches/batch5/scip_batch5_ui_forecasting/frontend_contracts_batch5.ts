// SCIP Batch 5 frontend contract types

export type RoleKey = 'board_cxo' | 'cco_gm_agm' | 'finance' | 'mis_qcg_admin' | 'collector_rm';

export interface LineageRef {
  metric_key: string;
  lineage_bucket?: string;
  lineage_key?: string;
  has_lineage: boolean;
  source_file: string;
  sheet: string;
  cell_or_range: string;
  validation_status: string;
  confidence_state: string;
  reporting_basis: string;
  value?: number | string | null;
}

export interface CommandCentreCard {
  card_id: string;
  title: string;
  value: number | string | null | Record<string, unknown>;
  display_value: string;
  reporting_basis: string;
  action: string;
  severity: 'info' | 'risk' | 'monitor' | 'strategic' | 'control' | 'forecast' | string;
  trust_state: 'lineaged' | 'blocked_or_partial_lineage';
  lineage_refs: LineageRef[];
  lineage_display: LineageRef[];
  assumptions?: string[];
  basis_disclosure?: string;
  forecast?: MonthEndForecast;
}

export interface DataConfidenceTrustBar {
  snapshot_date: string;
  load_timestamp: string;
  platform_version: string;
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
  trust_bar: DataConfidenceTrustBar;
  cards: CommandCentreCard[];
}

export interface CommandCentresResponse {
  status: 'ok';
  contract_version: 'command_centres.v2.batch5' | string;
  role_order: RoleKey[];
  roles: Record<RoleKey, RoleCommandCentre>;
  forecast: MonthEndForecast;
  guardrails: {
    no_silent_fallback: boolean;
    critical_cards_require_lineage_refs: boolean;
    finance_vs_mdo_label_required: boolean;
    entity_head_removed: boolean;
    every_card_requires_reporting_basis: boolean;
    every_card_requires_lineage_display: boolean;
    month_end_forecast_assumptions_required: boolean;
  };
}

export interface MonthEndForecast {
  status: 'ok' | 'blocked_untrusted_forecast' | string;
  contract_version: 'forecast.month_end.v1.batch5' | string;
  forecast_date: string;
  forecast_name: string;
  reporting_basis: 'R04 Finance actuals vs R02 MDO target' | string;
  basis_disclosure: string;
  tolerance_pct: number;
  inputs: Record<string, number | null>;
  working_days: {
    status: 'inferred_from_r04_prorata' | 'fallback_default' | string;
    elapsed_working_days: number;
    total_working_days: number;
    remaining_working_days: number;
    source: string;
    ratio?: number;
    fraction_error?: number;
    basis: string;
    lineage_refs?: LineageRef[];
  };
  outputs: {
    current_daily_run_rate: number;
    required_daily_run_rate_remaining: number;
    projected_month_end_landing: number;
    gap_to_may_mdo_target: number;
    mtd_achievement_pct: number;
    projected_achievement_pct: number;
    mdo_prorata_target_as_of_snapshot: number;
    mdo_prorata_gap_as_of_snapshot: number;
    da_daily_run_rate: number | null;
    new_sales_daily_run_rate: number | null;
  };
  display: Record<string, string>;
  assumptions: string[];
  lineage_refs: LineageRef[];
  guardrails: Record<string, boolean>;
}

export interface QuickballExplainResponse {
  status: 'ok' | 'blocked_untrusted_metric' | string;
  role: string;
  metric_key: string;
  metric_label: string;
  answer: string;
  reason?: string;
  lineage?: LineageRef | null;
}
