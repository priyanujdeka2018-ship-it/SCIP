# SCIP release/go-live-rc1 upload map

Branch: `release/go-live-rc1`

This scaffold is rooted at the repository root. Extract/upload these contents directly into the `SCIP` repo root, not into a nested `SCIP/` folder.

## Core rule

- Do not commit live `.xlsx` R-series source files to GitHub.
- Keep `data/.gitkeep` only.
- Upload source workbooks to Render/staging storage.
- Batch 0-12 must be represented as product history, docs, contracts, smoke, lineage, and governance artifacts.
- Batch 13 is the safest cumulative runtime baseline for Batches 0-13.
- Batch 14-17 are overlays, not replacements for the foundation.

## Final repo structure

```text
SCIP/
  Backend/
    main.py
    constants.py
    utils.py
    file_resolver.py
    data_loader.py
    source_adapters.py
    quickball.py
    command_centres.py
    forecast.py
    account_action_queues.py
    workflow.py
    notifications.py
    persistence.py
    auth.py
    deployment.py
    observability.py
    identity.py
    rollout_uat.py
    adoption.py
    governance.py
    roadmap.py
    pipeline_config.json
    rbac_policy_matrix_batch11.json
    observability_config_batch12.json
    migrations/
    load_tests/
    audit_exports/
  src/
    App.jsx
    main.jsx
    liquidGlassTokens.css
    frontend_contracts/
  config/
  docs/
    architecture/
    batches/batch0 ... batch17/
    rollout/
    uat/
    governance/
    roadmap/
    go_live/
  smoke/
  data/.gitkeep
```

## Recommended upload order

1. Create base folders using this scaffold.
2. Upload Batch 0 docs/config references.
3. Upload Batch 1-5.1 docs/contracts/smoke references.
4. Upload Batch 13 as the main cumulative runtime baseline.
5. Overlay Batch 14 rollout/UAT files.
6. Overlay Batch 15 adoption.
7. Overlay Batch 16 governance.
8. Overlay Batch 17 roadmap.
9. Upload go-live consolidation under `docs/go_live/`.
10. Add loose frontend/build/deployment files.
11. Add `.env.example`, `README.md`, `requirements.txt`, `render.yaml`, `index.html`, `.gitignore`.
12. Run compile/build/smoke before merging.

## Batch upload summary

### Batch 0 - architecture, lineage, semantic model

From `scip_upgrade_pack_batch0.zip`:

- `config/pipeline_config_v8.json`
- `config/lineage_contract_v1.json`
- `config/semantic_model_v2.json`
- `config/smoke_test_checkpoints_v2.json`
- `docs/batches/batch0/*`

Do not use Batch 0 Python files as final runtime files. Keep them as references/docs.

### Batch 1 - ingestion foundation / R18

From `scip_batch1_ingestion_foundation.zip` to `docs/batches/batch1/`. Preserve implementation reports, governance/smoke checkpoints, lineage contract v1.1, smoke tests, results, and patches. Runtime files are superseded.

### Batch 2 - R04 / R02

From `scip_batch2_r04_r02.zip` to `docs/batches/batch2/`. Preserve reports, README, smoke tests, result JSONs, and patches. Runtime files are superseded.

### Batch 3 - R08 / R36

From `scip_batch3_r08_r36.zip` to `docs/batches/batch3/`. Preserve reports, governance/smoke checkpoints, smoke tests, and result JSONs. Runtime files are superseded.

### Batch 4 - Quickball / command centres

From `scip_batch4_quickball_command_centres.zip`:

- docs to `docs/batches/batch4/`
- `src/frontend_contracts/frontend_contracts_batch4.ts`

Runtime `quickball.py`, `command_centres.py`, and `main.py` are superseded by later cumulative batches.

### Batch 5 - UI / forecasting

From `scip_batch5_ui_forecasting.zip`:

- docs/sample payloads to `docs/batches/batch5/`
- `src/frontend_contracts/frontend_contracts_batch5.ts`

Runtime `forecast.py` and `App.jsx` are superseded.

### Batch 5.1 - Liquid Glass

From `scip_batch5_1_liquid_glass.zip`:

- `src/liquidGlassTokens.css`
- docs/checks to `docs/batches/batch5_1/`
- `src/frontend_contracts/frontend_contracts_batch5_1.ts`

Do not let later UI changes break the locked Liquid Glass two-door model.

### Batch 6 - initial action queues

From `scip_batch6_action_queues.zip`:

- `docs/batches/batch6/`
- `src/frontend_contracts/frontend_contracts_batch6.ts`

Do not use Batch 6 `account_action_queues.py` as final. Batch 7 supersedes it.

### Batch 7 - account action queues

From `scip_batch7_account_action_queues.zip`:

- final runtime: `Backend/account_action_queues.py`
- `docs/batches/batch7/`
- `src/frontend_contracts/frontend_contracts_batch7.ts`

### Batch 8 - workflow tracking

From `scip_batch8_workflow_tracking.zip`:

- final runtime: `Backend/workflow.py`
- `docs/batches/batch8/`
- `src/frontend_contracts/frontend_contracts_batch8.ts`
- `smoke/smoke_batch8_workflow_tracking.py`

### Batch 9 - notifications / escalations

From `scip_batch9_notifications_escalations.zip`:

- final runtime: `Backend/notifications.py`
- `docs/batches/batch9/`
- `src/frontend_contracts/frontend_contracts_batch9.ts`
- `smoke/smoke_batch9_notifications.py`

### Batch 10 - persistence / audit

From `scip_batch10_persistence_audit.zip`:

- final runtime: `Backend/persistence.py`
- migration: `Backend/migrations/001_batch10_persistence.sql`
- audit exports to `Backend/audit_exports/`
- `docs/batches/batch10/`
- `src/frontend_contracts/frontend_contracts_batch10.ts`
- `smoke/smoke_batch10_persistence_audit.py`

### Batch 11 - RBAC / deployment hardening

From `scip_batch11_rbac_hardening.zip`:

- final runtime/config: `Backend/auth.py`, `Backend/deployment.py`, `Backend/rbac_policy_matrix_batch11.json`
- migration: `Backend/migrations/002_batch11_rbac_hardening.sql`
- `docs/batches/batch11/`
- `src/frontend_contracts/frontend_contracts_batch11.ts`
- `smoke/smoke_batch11_rbac_hardening.py`

### Batch 12 - observability / performance

From `scip_batch12_observability_performance.zip`:

- final runtime/config: `Backend/observability.py`, `Backend/observability_config_batch12.json`, observability samples/specs, load tests
- migration: `Backend/migrations/003_batch12_observability.sql`
- `docs/batches/batch12/`
- `src/frontend_contracts/frontend_contracts_batch12.ts`
- `smoke/smoke_batch12_observability_performance.py`

### Batch 13 - production identity / SSO / cumulative code baseline

From `scip_batch13_sso_jwt_provisioning.zip`, use as the main cumulative runtime baseline for foundation code:

- `Backend/main.py`
- `Backend/constants.py`
- `Backend/file_resolver.py`
- `Backend/data_loader.py`
- `Backend/source_adapters.py`
- `Backend/pipeline_config.json`
- `Backend/quickball.py`
- `Backend/command_centres.py`
- `Backend/forecast.py`
- `Backend/account_action_queues.py`
- `Backend/workflow.py`
- `Backend/notifications.py`
- `Backend/persistence.py`
- `Backend/auth.py`
- `Backend/deployment.py`
- `Backend/observability.py`
- `Backend/identity.py`
- migration: `Backend/migrations/004_batch13_identity_provisioning.sql`
- `docs/batches/batch13/`
- `src/frontend_contracts/frontend_contracts_batch13.ts`
- `smoke/smoke_batch13_identity_rbac.py`

Apply the known migration fix to avoid inserting into missing `migration_history.description` / `migration_history.evidence_json` columns unless those columns exist.

### Batch 14 - rollout / UAT / rollback / break-glass

From `scip_batch14_rollout_uat_signoff.zip`:

- final runtime overlay: `Backend/rollout_uat.py`
- only overwrite listed Batch 13 runtime/frontend files if newer and compile-compatible
- docs to `docs/rollout/`, `docs/uat/`, and `docs/batches/batch14/`
- smoke files to `smoke/`

### Batch 15 - adoption analytics

From `scip_batch15_post_launch_adoption.zip`:

- final runtime: `Backend/adoption.py`
- migration: `Backend/migrations/005_batch15_adoption_analytics.sql`
- governance docs
- `docs/batches/batch15/`
- `src/frontend_contracts/frontend_contracts_batch15.ts`
- `smoke/static_adoption_smoke.py`

### Batch 16 - continuous improvement governance

From `scip_batch16_continuous_improvement_governance.zip`:

- final runtime: `Backend/governance.py`
- migration: `Backend/migrations/006_batch16_continuous_improvement.sql`
- governance docs
- `docs/batches/batch16/`
- `src/frontend_contracts/frontend_contracts_batch16.ts`
- `smoke/static_batch16_governance_smoke.py`

### Batch 17 - roadmap / executive rhythm

From `scip_batch17_long_term_roadmap_exec_rhythm.zip`:

- final runtime: `Backend/roadmap.py`
- migration: `Backend/migrations/007_batch17_roadmap_exec_rhythm.sql`
- roadmap docs
- `docs/batches/batch17/`
- `smoke/static_batch17_roadmap_smoke.py`

Only overwrite `Backend/main.py` or `src/App.jsx` from Batch 17 after checking they still include operational routes from Batches 7-14.

## Go-live consolidation pack

From `scip_go_live_readiness_consolidation.zip`, upload all contents under `docs/go_live/` using this mapping:

- `README.md` -> `docs/go_live/README.md`
- `release/*` -> `docs/go_live/release/`
- `checklists/*` -> `docs/go_live/checklists/`
- `uat/*` -> `docs/go_live/uat/`
- `signoff/*` -> `docs/go_live/signoff/`
- `smoke/*` -> `docs/go_live/smoke/`
- `env/SCIP_Environment_Variables_Template.env` -> `docs/go_live/env/`
- `source_refresh/*` -> `docs/go_live/source_refresh/`
- `blockers/*` -> `docs/go_live/blockers/`
- `manifests/*` -> `docs/go_live/manifests/`
- `references/*` -> `docs/go_live/references/`

## Exclude from GitHub

```text
__pycache__/
*.pyc
*.sqlite
.env
*.xlsx source files
node_modules/
dist/
```

Keep source workbooks outside the public repo: R02, R04, R08, R09, R10, R17, R18, R20, R30, R31, R32, R34, R36, R38.
