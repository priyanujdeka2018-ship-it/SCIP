export type ScipRole = "board_cxo" | "cco_gm_agm" | "finance" | "mis_qcg_admin" | "collector_rm";

export interface ObservabilityTimingSummary {
  count: number;
  p50_ms: number | null;
  p95_ms: number | null;
  max_ms: number | null;
}

export interface ObservabilitySummaryPayload {
  contract_version: "observability_performance.v1.batch12" | string;
  generated_at: string;
  event_count: number;
  metrics_catalog: string[];
  counters: Record<string, number>;
  timings: Record<string, ObservabilityTimingSummary>;
  api_error_rate_pct: number;
  cache_entries: number;
  active_alerts: ObservabilityAlert[];
  actor_role?: ScipRole;
}

export interface ObservabilityEvent {
  event_id: string;
  timestamp: string;
  correlation_id: string;
  event_type: string;
  component: string;
  status: "ok" | "attention" | "blocked" | "error" | string;
  actor_role?: ScipRole;
  endpoint?: string;
  method?: string;
  duration_ms?: number;
  metric_name?: string;
  metric_value?: number;
  source_code?: string;
  snapshot_date?: string;
  metadata: Record<string, unknown>;
}

export interface ObservabilityDashboardSpec {
  contract_version: "observability_performance.v1.batch12" | string;
  generated_at: string;
  dashboards: Array<{
    dashboard_id: string;
    title: string;
    surface: "L5 governance output" | "solid evidence" | string;
    panels: string[];
  }>;
  alert_thresholds: Record<string, number>;
  liquid_glass_placement: {
    entry_model: string;
    observability_visibility: string;
    financial_truth_surfaces: string;
  };
}

export interface ObservabilityAlert {
  alert_key: string;
  severity: "low" | "medium" | "high" | "critical" | string;
  threshold: number;
  actual: number;
}

export interface FrontendTimingPostBody {
  route: "arrival" | "live_pulse" | "narratives" | string;
  view: string;
  duration_ms: number;
  device?: Record<string, unknown>;
  browser?: string;
}

export interface FrontendTimingResponse {
  status: "accepted";
  event_id: string;
  correlation_id: string;
  actor_role?: ScipRole;
}
