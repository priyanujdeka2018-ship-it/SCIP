// SCIP Batch 15 frontend contracts
// Adoption analytics are L5 governance/evidence outputs. They must never become a third Arrival door.

export type SCIPRole = "board_cxo" | "cco_gm_agm" | "finance" | "mis_qcg_admin" | "collector_rm";
export type SCIPWorld = "live_pulse" | "narratives";
export type SCIPFocus = "current_signal" | "month_movement" | "risk_action" | "story" | "portfolio" | "dues" | "advance" | "roadmap" | "target_track";
export type SCIPDepth = "summary" | "detailed" | "executive" | "evidence" | "action";

export interface AdoptionSummary {
  contract_version: "adoption_optimization.v1.batch15";
  status: "ready_adoption_analytics_guarded";
  role_filter: string;
  total_events: number;
  active_sessions: number;
  world_usage: Record<SCIPWorld, number>;
  focus_usage: Record<string, number>;
  depth_usage: Record<string, number>;
  role_level_engagement: Record<SCIPRole, number>;
  event_usage: Record<string, number>;
  metrics: {
    world_focus_depth_usage: object;
    quickball_explanation_usage: { explanations: number; blocked_answers: number; blocked_rate_pct: number };
    evidence_path_opens: { opens: number; per_100_sessions: number };
    action_queue_conversion_rate: number;
    workflow_closure_rate: number;
    notification_effectiveness: number;
    forecast_review_frequency: { reviews: number; per_session: number };
    role_level_engagement: Record<SCIPRole, number>;
    stale_source_impact: { events: number; sessions_affected_estimate: number };
    uat_to_production_defect_trends: { uat_defects: number; production_defects: number; prod_escape_rate_pct: number };
  };
  guardrails: {
    arrival_doors: ["live_pulse", "narratives"];
    third_door_allowed: false;
    entity_head_removed: true;
    frontend_business_computation_allowed: false;
    analytics_surface: string;
  };
}

export interface OptimizationRecommendation {
  recommendation_id: string;
  created_ts: string;
  priority: "P0" | "P1" | "P2";
  theme: string;
  title: string;
  evidence: Record<string, unknown>;
  recommendation: string;
  liquid_glass_guardrail: string;
  owner_role: SCIPRole;
  status: "proposed" | "accepted" | "in_progress" | "closed";
}
