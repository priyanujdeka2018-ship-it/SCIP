# SCIP Batch 17 — 12-Month Roadmap

## Purpose
Create the long-term execution roadmap for SCIP after production rollout, preserving all existing governance gates: locked hierarchy, 0.05% tolerance, no-silent-fallback, reporting-basis labels, RBAC row-level visibility, immutable lineage, JWT/SSO provisioning, observability redaction, adoption analytics, and continuous-improvement governance.

## Liquid Glass rule
Roadmap material is an L5 executive/governance output. It must not create a third Arrival door. User-facing experience remains Live Pulse and Narratives.

## Quarter themes
| Quarter | Executive question | Outcomes |
|---|---|---|
| Q1 Stabilize and Trust | Can leadership trust SCIP every day? | production trust, source freshness, Quickball confidence, metric governance, DW blueprint |
| Q2 Operational Workflow Adoption | Is SCIP changing operating behavior? | collector adoption, management escalations, finance/QCG exception closure |
| Q3 Intelligence Expansion | Can SCIP make better decisions, not just faster ones? | risk scoring v2, forecast confidence, board narrative automation, evidence catalogue |
| Q4 Enterprise Scale | Can SCIP scale beyond workbook-first operations? | enterprise pipeline pilot, master data stewardship, mobile action pilot |

## Roadmap items

### RM-01 — Stabilize production launch and source-refresh governance
- **Horizon:** Month 1 / Q1 Stabilize and Trust
- **Theme:** Production stabilization
- **Strategic objective:** Make SCIP trusted for daily leadership and operations use immediately after launch.
- **Evidence:** Batch 14 production readiness gates, Batch 12 observability stale-source alerts, Batch 16 source-owner SLA review
- **Owner:** SCIP Product Owner + MIS/QCG/Admin
- **Success metric:** 95%+ critical source freshness SLA for R18/R04/R02/R08/R36 and account-action sources; zero silent fallback incidents.
- **Rollout gate:** UAT signoff, production smoke, identity provisioning, RBAC verification, backup/restore check.
- **Risk:** Users lose trust if source freshness or lineage is unclear during first month.
- **Dependency:** Batch 14 signoff, Batch 12 alerts, production source owners.
- **Rollback / exit criteria:** Disable new operational action surfaces and revert to read-only executive pulse if any critical source lacks lineage for more than one refresh cycle.
- **Liquid Glass guardrail:** Expose health as L5 evidence from Live Pulse Risk & Action; do not add a health dashboard at Arrival.


### RM-02 — Quickball answer-quality review loop
- **Horizon:** Month 1 / Q1 Stabilize and Trust
- **Theme:** Quickball trust
- **Strategic objective:** Ensure every explanation remains lineage-backed and board-safe.
- **Evidence:** Batch 4 Quickball lineage gate, Batch 16 Quickball answer review template, Batch 12 blocked-answer observability
- **Owner:** Product Owner + Board/CXO delegate + MIS/QCG/Admin
- **Success metric:** 100% sampled critical answers carry source, sheet/range, confidence, and reporting basis; blocked-answer false positives reviewed monthly.
- **Rollout gate:** Monthly model/answer review pack approved by change-control board.
- **Risk:** Quickball becomes a workaround for unclear screens or overexplains without evidence.
- **Dependency:** Lineage registry, Quickball review cadence, adoption telemetry.
- **Rollback / exit criteria:** Disable affected Quickball intents if any sampled answer uses unlineaged financial data.
- **Liquid Glass guardrail:** Quickball remains a contextual command capsule with max two follow-up actions.


### RM-03 — Metric definition catalogue and change-log hardening
- **Horizon:** Month 2 / Q1 Stabilize and Trust
- **Theme:** Metric governance
- **Strategic objective:** Prevent ambiguity between Finance, MDO, R08, R36, workflow, and adoption metrics.
- **Evidence:** Batch 2 Finance-vs-MDO labelling, Batch 3 R08/R36 reporting labels, Batch 16 metric-definition change log
- **Owner:** Finance + MIS/QCG/Admin
- **Success metric:** 100% critical metrics have owner, formula, source basis, reporting basis, and change history.
- **Rollout gate:** Metric change-control approval before release train cut.
- **Risk:** Leadership decisions may be challenged if target basis or formula changes are not explicit.
- **Dependency:** Metric catalogue, source owner SLAs, finance signoff.
- **Rollback / exit criteria:** Revert metric definition and publish release note if signoff is missing or user-visible values materially change without approved basis.
- **Liquid Glass guardrail:** Metric definitions remain L4 evidence; not visible on Arrival or L1.


### RM-04 — Enterprise data warehouse alignment blueprint
- **Horizon:** Month 3 / Q1 Stabilize and Trust
- **Theme:** Data warehouse alignment discovery
- **Strategic objective:** Move from workbook-first ingestion toward governed enterprise source alignment without breaking current R-series trust.
- **Evidence:** Batch 1-7 adapter lineage contracts, Batch 10 durable audit schema, SystemMap R-series source model
- **Owner:** Data Engineering + MIS/QCG/Admin
- **Success metric:** Approved canonical fact/dimension model and source-to-DW mapping for collections, OD, target, advance, workflow, and audit facts.
- **Rollout gate:** Architecture review, data owner approval, pilot reconciliation against current adapters.
- **Risk:** Premature DW migration could break trusted workbook reconciliation.
- **Dependency:** Enterprise warehouse access, source system owners, reconciliation harness.
- **Rollback / exit criteria:** Keep workbook adapters as source of truth until DW facts reconcile within 0.05% tolerance and lineage parity is achieved.
- **Liquid Glass guardrail:** DW alignment is backend governance; no user-facing IA change.


### RM-05 — Collector/RM action queue adoption scale-up
- **Horizon:** Month 4 / Q2 Operational Workflow Adoption
- **Theme:** Collector adoption
- **Strategic objective:** Convert lineaged account actions into measurable collections follow-through.
- **Evidence:** Batch 7 account-action gate, Batch 8 workflow events, Batch 15 action queue conversion analytics
- **Owner:** CCO/GM/AGM + Collection Operations
- **Success metric:** 70%+ eligible collector actions dispositioned within SLA; workflow closure rate improves month over month.
- **Rollout gate:** Pilot results, role-level RBAC confirmation, collector training signoff.
- **Risk:** Collectors may treat SCIP as monitoring rather than help if actions are noisy.
- **Dependency:** R10/R32/R34 freshness, notification tuning, collector scope provisioning.
- **Rollback / exit criteria:** Disable noisy queue rules if false-positive action rate exceeds agreed threshold for two consecutive review cycles.
- **Liquid Glass guardrail:** Action queues remain Risk & Action L5 output; no collector table on Arrival.


### RM-06 — Escalation operating rhythm for overdue, stale, and high-risk workflows
- **Horizon:** Month 5 / Q2 Operational Workflow Adoption
- **Theme:** Management intervention
- **Strategic objective:** Create a repeatable management cadence for resolving overdue/high-risk action pools.
- **Evidence:** Batch 8 workflow states, Batch 9 escalation rules, Batch 12 alert thresholds
- **Owner:** CCO/GM/AGM
- **Success metric:** Stale workflow rate reduced by 30%; unassigned high-risk actions remain below threshold.
- **Rollout gate:** Weekly management review evidence pack and escalation acceptance criteria.
- **Risk:** Too many escalations create alert fatigue and reduce operational credibility.
- **Dependency:** Notification suppression rules, owner mappings, workflow event quality.
- **Rollback / exit criteria:** Suppress or lower priority of escalation rule if duplicate/suppressed ratio exceeds governance threshold.
- **Liquid Glass guardrail:** Escalations surface through Risk & Action, not as separate escalation dashboard.


### RM-07 — Finance/QCG exception closure program
- **Horizon:** Month 6 / Q2 Operational Workflow Adoption
- **Theme:** Finance and QCG efficiency
- **Strategic objective:** Reduce PR, SOA, TAT, and documentation leakage that blocks cash recognition or customer action.
- **Evidence:** Batch 7 R31/R20 queues, Batch 8 closure reasons, Batch 10 audit exports
- **Owner:** Finance + MIS/QCG/Admin
- **Success metric:** PR/TAT ageing exceptions reduced by 25%; closure reasons complete for 95%+ resolved finance exceptions.
- **Rollout gate:** Finance UAT, QCG owner signoff, audit export review.
- **Risk:** Process exceptions may be misclassified as collector issues.
- **Dependency:** R31/R20 freshness, finance workflow roles, process ageing rules.
- **Rollback / exit criteria:** Reclassify queue rules and pause notifications if finance exception owner mapping accuracy drops below threshold.
- **Liquid Glass guardrail:** Finance exceptions remain solid evidence/timeline surfaces.


### RM-08 — Risk scoring v2 and forecast confidence bands
- **Horizon:** Month 7 / Q3 Intelligence Expansion
- **Theme:** Risk intelligence
- **Strategic objective:** Move beyond static action priority into risk-adjusted intervention and forecast confidence.
- **Evidence:** Batch 3 R36 forward calendar, Batch 7 R38 risk analysis, Batch 5 forecast assumptions
- **Owner:** Analytics Lead + CCO/GM/AGM
- **Success metric:** Risk score v2 explains priority drivers and improves high-risk closure conversion versus baseline.
- **Rollout gate:** Model review, back-test evidence, Quickball explanation review, rollback rule approved.
- **Risk:** Model opacity could reduce trust or create unfair collector prioritization.
- **Dependency:** Historical closure data, R38 quality, workflow outcome labels.
- **Rollback / exit criteria:** Revert to rule-based queues if model explanations are incomplete or performance does not beat baseline.
- **Liquid Glass guardrail:** Model score explanations are L4 evidence, not decorative signal chips.


### RM-09 — Executive narrative and board pack generation
- **Horizon:** Month 8 / Q3 Intelligence Expansion
- **Theme:** Board narrative automation
- **Strategic objective:** Reduce board-preparation effort while improving evidence-backed storytelling.
- **Evidence:** Batch 4 Quickball explanations, Batch 5.1 Narratives rail, Batch 10 audit export
- **Owner:** Board/CXO delegate + Product Owner
- **Success metric:** Board pack preparation time reduced by 50%; 100% board narrative claims trace to approved lineage.
- **Rollout gate:** Executive review, legal/audit approval for export contents, presentation smoke.
- **Risk:** Narratives may over-summarize operational complexity or omit important caveats.
- **Dependency:** Narratives evidence templates, export controls, source freshness.
- **Rollback / exit criteria:** Disable auto-generated board pack export if any claim lacks lineage or approved caveat.
- **Liquid Glass guardrail:** Present remains an output action, never a browsing mode.


### RM-10 — Self-serve evidence catalogue for definitions, formulas, and source basis
- **Horizon:** Month 9 / Q3 Intelligence Expansion
- **Theme:** Evidence catalogue
- **Strategic objective:** Let users verify numbers without exposing raw architecture too early.
- **Evidence:** Batch 4 lineage drawer, Batch 10 audit exports, Liquid Glass L4 evidence rule
- **Owner:** MIS/QCG/Admin + Finance
- **Success metric:** 80%+ repeated “source basis” questions resolved through evidence paths rather than manual MIS support.
- **Rollout gate:** Evidence template QA, RBAC review, metric owner approval.
- **Risk:** Evidence catalogue could become a raw data dump if not gated.
- **Dependency:** Metric catalogue, lineage registry, RBAC evidence visibility.
- **Rollback / exit criteria:** Hide overly dense evidence templates until simplified if users bypass focus screens or support tickets rise.
- **Liquid Glass guardrail:** Evidence appears only after explicit L4 intent.


### RM-11 — Source-system and warehouse integration pilot
- **Horizon:** Month 10 / Q4 Enterprise Scale
- **Theme:** Enterprise integrations
- **Strategic objective:** Start replacing manual R-series refresh dependency with governed enterprise pipelines.
- **Evidence:** RM-04 DW blueprint, Batch 12 ingestion latency metrics, Batch 10 lineage/audit schema
- **Owner:** Data Engineering + IT + MIS/QCG/Admin
- **Success metric:** At least two critical domains run from enterprise pipeline in parallel and reconcile against R-series within 0.05% tolerance.
- **Rollout gate:** Parallel-run signoff, rollback plan, source owner approval, data contract acceptance.
- **Risk:** New pipeline changes numbers without user-visible source-basis clarity.
- **Dependency:** DW access, source APIs, reconciliation test harness.
- **Rollback / exit criteria:** Fallback to workbook adapter for any domain with failed reconciliation or missing lineage parity.
- **Liquid Glass guardrail:** No user-facing route change; only source-basis and freshness labels change after approval.


### RM-12 — Enterprise hierarchy and master-data stewardship
- **Horizon:** Month 11 / Q4 Enterprise Scale
- **Theme:** Master data governance
- **Strategic objective:** Make entity/project/customer/collector mappings durable across platforms and reporting cycles.
- **Evidence:** Locked hierarchy from Batch 1, Batch 13 provisioning scopes, Batch 7 account-action joins
- **Owner:** Data Governance + MIS/QCG/Admin
- **Success metric:** 100% critical action rows have entity, project, owner, and scope mapping; mapping exception backlog below SLA.
- **Rollout gate:** Data governance board approval and mapping exception review.
- **Risk:** Mis-mapped owner/entity scopes can break RBAC or action ownership.
- **Dependency:** IdP groups, collector mappings, project master, customer/unit master.
- **Rollback / exit criteria:** Block action generation for mapping segments with unresolved ownership ambiguity.
- **Liquid Glass guardrail:** Master data exceptions are governance evidence, not a user-facing filter-first experience.


### RM-13 — Mobile-first collector action experience pilot
- **Horizon:** Month 12 / Q4 Enterprise Scale
- **Theme:** Mobile and field adoption
- **Strategic objective:** Bring focused, role-safe actions to collectors without exposing executive or audit complexity.
- **Evidence:** Batch 7 Collector/RM queue, Batch 8 workflow disposition states, Batch 15 role engagement analytics
- **Owner:** Collection Operations + Product Owner
- **Success metric:** Collector daily active use reaches target; disposition completion time improves without increasing false closures.
- **Rollout gate:** Pilot cohort signoff, security review, mobile UX test, notification policy approval.
- **Risk:** Mobile experience can become a mini-dashboard instead of an action aid.
- **Dependency:** SSO/session behavior, RBAC row scope, workflow API stability.
- **Rollback / exit criteria:** Restrict mobile to read-only action reminders if closure quality or RBAC test fails.
- **Liquid Glass guardrail:** Mobile is action-first; no KPI grid or operational dashboard at entry.
