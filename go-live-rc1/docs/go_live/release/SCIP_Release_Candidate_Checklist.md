# SCIP Release-Candidate Checklist

## Scope

This checklist combines the selected production code baseline from Batch 13, rollout/UAT controls from Batch 14, and executive roadmap governance from Batch 17.

## Release-candidate source of truth

| Layer | Source batch | Use in release candidate |
|---|---|---|
| Ingestion, lineage, action queues, workflow, notifications, persistence, audit, RBAC, observability, SSO/JWT | Batch 13 pack | Production code baseline |
| Rollout, UAT, cutover, source refresh, RBAC verification, smoke runner, signoff, rollback, break-glass | Batch 14 pack | Go-live governance baseline |
| Roadmap, executive rhythm, OKRs, ownership, release train, benefits tracking, steering committee pack | Batch 17 pack | Post-go-live operating model |

## Go-live readiness gates

### Gate 0: Release branch creation

- [ ] Create release branch from current production candidate branch.
- [ ] Record commit SHA before patch merge.
- [ ] Tag pre-merge state as rollback anchor.
- [ ] Confirm repository contains frontend and backend folders expected by deploy config.

### Gate 1: Patch merge

- [ ] Apply Batch 13 production code baseline.
- [ ] Apply Batch 14 rollout/UAT governance docs and smoke runner.
- [ ] Apply Batch 17 roadmap/rhythm governance docs and read-only roadmap endpoints only if desired for production.
- [ ] Resolve conflicts in `main.py`, `App.jsx`, `liquidGlassTokens.css`, `auth.py`, `identity.py`, `observability.py`, and migrations.
- [ ] Confirm Entity Head does not reappear in role model.

### Gate 2: Backend verification

- [ ] Python import/compile checks pass.
- [ ] Unit/smoke tests pass.
- [ ] Backend starts without local-dev bypass in staging.
- [ ] Critical routes return expected status.
- [ ] Structured logs include correlation IDs.
- [ ] No sensitive data is logged.

### Gate 3: Frontend verification

- [ ] `npm install` passes.
- [ ] `npm run build` passes.
- [ ] `npm run dev` loads locally.
- [ ] Liquid Glass two-door Arrival is preserved.
- [ ] No top-level Observability, Governance, Roadmap, Audit, or Workflow door is added.
- [ ] Lineage drawer, trust bar, blocked-answer warning, forecast assumptions, and role-aware views are intact.

### Gate 4: Database and migration verification

- [ ] Staging database available.
- [ ] Backup taken before migrations.
- [ ] Migrations 001-007 apply in order.
- [ ] Migration history table updated.
- [ ] Rollback SQL or restore point verified.
- [ ] Post-migration row counts and constraints verified.

### Gate 5: SSO/JWT and provisioning

- [ ] Production IdP details available.
- [ ] JWT issuer, audience, JWKS URL/secret, algorithms, and expiry rules configured.
- [ ] Local-dev header bypass disabled.
- [ ] Users provisioned.
- [ ] Groups mapped to SCIP roles.
- [ ] Entity and collector scopes provisioned.
- [ ] Deactivated users cannot authenticate.

### Gate 6: Source data cutover

- [ ] Latest production R-series files available.
- [ ] Critical reports R02/R04/R08/R18/R36 loaded.
- [ ] Account/action reports R09/R10/R17/R20/R30/R31/R32/R34/R38 loaded.
- [ ] Snapshot dates verified.
- [ ] Source owner signoff completed.
- [ ] No silent fallback is active for critical metrics.

### Gate 7: Deployment smoke

- [ ] Deployment base URL available.
- [ ] Production-like JWT available for each role.
- [ ] Deployment smoke runner passes.
- [ ] RBAC row-level tests pass.
- [ ] Audit export tests pass.
- [ ] Notification dedupe/suppression tests pass.
- [ ] Workflow closure tests pass.
- [ ] Observability correlation tests pass.

### Gate 8: UAT and signoff

- [ ] Board/CXO UAT passed.
- [ ] CCO/GM/AGM UAT passed.
- [ ] Finance UAT passed.
- [ ] MIS/QCG/Admin UAT passed.
- [ ] Collector/RM UAT passed.
- [ ] Executive acceptance criteria passed.
- [ ] Production go/no-go meeting completed.

### Gate 9: Production rollout

- [ ] Production backup complete.
- [ ] Change freeze agreed.
- [ ] Release tag created.
- [ ] Production deploy completed.
- [ ] Production smoke passed.
- [ ] Monitoring dashboard green.
- [ ] Rollback owner on standby.
- [ ] Break-glass owner on standby.

## Final go-live decision

Production deployment is allowed only when every Gate 0-9 item is complete or has a documented executive waiver.
