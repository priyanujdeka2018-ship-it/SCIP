# SCIP Batch 14 Staged Rollout Plan

## Rollout principles

- Roll out by evidence, not by calendar pressure.
- Do not promote an environment if any critical source, lineage, identity, RBAC, workflow, notification, audit, observability, or Liquid Glass gate fails.
- Do not expose account-level queues before JWT identity, row-level visibility, and account-action gate pass.
- Do not allow silent fallback in any stage.
- Do not add a third Arrival door during rollout.

## Stage 0 — Dev validation

### Goal
Prove the integrated package boots locally and all patch-pack smoke tests pass.

### Entry criteria
- Batch 13 code applied.
- Batch 14 rollout artifacts added.
- Local environment variables present.
- Local dev bypass allowed only in `SCIP_AUTH_MODE=local_dev`.

### Required checks
- `npm install && npm run build` passes.
- Backend starts without router import errors.
- `/manifest`, `/deployment/health`, `/identity/me`, `/security/policy-matrix`, `/observability/summary` respond.
- `SCIP_AUTH_MODE=jwt` rejects missing/invalid JWT.
- Liquid Glass Arrival shows only Live Pulse and Narratives.

### Exit criteria
- All local smoke checks passed.
- No blocker defects open.
- Dev lead signoff recorded.

## Stage 1 — Staging technical validation

### Goal
Validate production-like infrastructure, SSO/JWT, database migrations, source refresh, audit exports, backups, alerting, and rollback readiness.

### Required checks
- Migration runner completes with recorded migration history.
- Backup check passes before and after seed/load.
- JWT tokens from IdP validate.
- CORS wildcard rejected outside local.
- Source refresh loads R02/R04/R08/R18/R36/R10/R17/R20/R30/R31/R32/R34/R38/R09 as available.
- Critical lineage coverage is 100% for critical cards and action queues.
- Notification dedupe survives restart.
- Audit export generates CSV/JSON.
- Dashboard alerts are wired but notification delivery can remain dry-run.

### Exit criteria
- Security, Data, Engineering, and MIS/QCG/Admin sign off.

## Stage 2 — Pilot

### Goal
Run a controlled user pilot with a small set of provisioned users across roles.

### Suggested pilot group
- 1 Board/CXO reader.
- 2 CCO/GM/AGM management users.
- 2 Finance users.
- 2 MIS/QCG/Admin users.
- 5 Collector/RM users.

### Pilot scope
- Live Pulse Current Signal.
- Live Pulse Month Movement.
- Live Pulse Risk & Action.
- Narratives Story/Portfolio/Dues/Advance/Roadmap.
- Account queues, workflow assignment, closure, notifications, audit export, Quickball explain-this-number.

### Exit criteria
- No severity-1 defects.
- No security leakage.
- No unlineaged critical numbers.
- Role users confirm UAT scripts pass.

## Stage 3 — Formal UAT

### Goal
Role owners validate production readiness using scripted scenarios and signoff matrix.

### Required evidence
- Screenshots or export references for each role script.
- Failed cases logged with owner/severity/resolution.
- RBAC denied-attempt samples retained.
- Audit export contains UAT events.
- Observability event correlation IDs captured for key journeys.

### Exit criteria
- Role owners sign off.
- Executive acceptance criteria met.
- Rollback and break-glass rehearsed.

## Stage 4 — Production release

### Release strategy
Use a gated release window. Run production smoke with read-only checks first, then identity/RBAC, then source refresh, then workflow/notification dry-run, then monitored access opening.

### Go-live gates
- Production migration complete.
- Backup restore check complete.
- Critical sources fresh or explicitly waived.
- IdP/JWT validation complete.
- RBAC row-level tests pass.
- Audit export works.
- Observability dashboards green.
- Rollback package available.
- Break-glass owners available.

## Rollback plan

### Rollback triggers
- Incorrect financial numbers shown without lineage.
- Unauthorized row visibility.
- Identity provider failure with no safe read-only fallback.
- Database migration corruption.
- Notification/emission runaway.
- Broken production navigation.
- Critical audit export failure.

### Rollback steps
1. Freeze new user access.
2. Disable external notification delivery.
3. Put workflows into read-only mode.
4. Restore previous deployment image.
5. Restore database from verified backup if schema/data corruption occurred.
6. Re-run smoke tests.
7. Publish incident note to rollout owners.

## Break-glass plan

### Break-glass use only when
- Production access is blocked for critical leadership review.
- IdP outage prevents urgent operational access.
- Rollback is unsafe or slower than emergency read-only access.

### Break-glass controls
- Time-boxed access.
- MIS/QCG/Admin approval.
- Security approval.
- Read-only by default.
- Full audit logging.
- Automatic expiry.
- Post-event review.
