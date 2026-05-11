// SCIP Batch 16 frontend contracts
export type ScipGovernanceOwner =
  | "platform_owner"
  | "data_owner"
  | "source_owner"
  | "quickball_owner"
  | "ux_owner"
  | "board_cxo"
  | "cco_gm_agm"
  | "finance"
  | "mis_qcg_admin"
  | "collector_rm";

export type ScipGovernanceDecision = "proposed" | "approved" | "rejected" | "deferred" | "released" | "rolled_back";
export type ScipRolloutGate = "dev" | "staging" | "pilot" | "uat" | "production" | "break_glass" | "blocked";

export interface ScipEvidenceRef {
  source: string;
  metric?: string;
  value?: string | number;
  lineage_ref?: string;
}

export interface ScipImprovementItem {
  item_id: string;
  created_ts: string;
  theme: string;
  title: string;
  description: string;
  evidence_refs: ScipEvidenceRef[];
  owner: ScipGovernanceOwner;
  decision: ScipGovernanceDecision;
  expected_impact: string;
  rollout_gate: ScipRolloutGate;
  rollback_criteria: string;
  priority: "P0" | "P1" | "P2" | "P3";
  liquid_glass_guardrail: string;
}

export interface ScipMonthlyReviewPack {
  contract_version: "continuous_improvement_governance.v1.batch16";
  status: string;
  review_cadence: "monthly";
  review_name: string;
  liquid_glass_positioning: string;
  required_review_sections: string[];
  improvement_items: ScipImprovementItem[];
}
