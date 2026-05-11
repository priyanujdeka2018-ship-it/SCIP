# SCIP Batch 11 Implementation Report — Secured RBAC and Production Deployment Hardening

## Status

Batch 11 is ready for review and integration.

Contract versions:

- `rbac.v1.batch11`
- `deployment_hardening.v1.batch11`
- existing durable schema preserved from `persistence_audit.v1.batch10`

## Preserved platform rules

- Liquid Glass remains the interaction model: security, deployment and audit are L5 evidence/output layers, not a new dashboard or third Arrival door.
- Locked hierarchy remains: `Group > Sobha(Sobha Dubai, Sobha AUH) + UAQ(Siniya, Downtown UAQ)`.
- General tolerance remains `0.05%`.
- No silent fallback remains enforced.
- Reporting basis labels remain mandatory.
- Entity Head remains removed.
- Account-action gate remains intact.
- Workflow event lineage remains immutable.
- Notification dedupe and suppression rules remain durable.
- Audit schema remains durable and migration-ready.

## What changed

Batch 11 adds:

1. Authenticated actor identity through `X-SCIP-*` headers for the patch pack.
2. A production hook to replace header identity with SSO/JWT verification later.
3. Role-to-permission matrix for Board/CXO, CCO/GM/AGM, Finance, MIS/QCG/Admin and Collector/RM.
4. Row-level visibility rules by role, entity scope and collector owner.
5. Authorization middleware for protected API paths.
6. Denied-attempt audit logging to durable tables.
7. Environment-specific configuration.
8. CORS hardening with no wildcard origins outside local development.
9. Secrets presence checks without exposing secret values.
10. Migration runner with checksum tracking.
11. Backup/restore check routine.
12. Deployment health endpoint.
13. Frontend actor/RBAC posture bar.
14. Production smoke tests.

## Backend files

- `auth.py` — actor identity, RBAC policy, row filters, middleware and denied-attempt logging.
- `deployment.py` — environment config, migration runner, backup/restore checks and deployment health.
- `main.py` — Batch 11 app wiring, security middleware, hardened CORS, security/deployment routers.
- `migrations/002_batch11_rbac_hardening.sql` — RBAC and deployment hardening schema.
- Existing Batch 10 files are preserved and patched only where security filtering is required.

## Frontend files

- `App.jsx` — adds Batch 11 security posture bar and authenticated `X-SCIP-*` headers on backend calls.
- `liquidGlassTokens.css` — adds security posture Liquid Glass styles.
- `frontend_contracts_batch11.ts` — actor, RBAC, denied-attempt, deployment-health and backup-check contracts.

## New routes

- `GET /security/me`
- `GET /security/policy-matrix`
- `GET /security/denied-attempts`
- `GET /deployment/health`
- `POST /deployment/migrate`
- `POST /deployment/backup-check`

Existing routes remain:

- `/command-centres`
- `/forecast/month-end`
- `/action-queues`
- `/workflows`
- `/notifications`
- `/persistence/summary`
- `/audit/export`

## Security posture

Patch-pack authentication is header based:

```http
X-SCIP-Actor-ID: admin1
X-SCIP-Actor-Name: MIS Admin
X-SCIP-Role: mis_qcg_admin
X-SCIP-Entity-Scope: Group
X-SCIP-Collector-ID: collector_a
X-SCIP-Environment: local
```

Production should replace header trust with verified SSO/JWT identity while preserving the same actor and permission contract.

## Smoke result

`smoke_batch11_rbac_hardening_results.json` passed all checks.

Validated:

- Entity Head blocked.
- Five-role model retained.
- Collector/RM cannot assign actions.
- Finance can use finance assignment permission path.
- Board/CXO cannot read account queues or audit export.
- Collector/RM sees only own rows.
- Finance sees finance rows.
- CCO/GM/AGM sees management rows.
- Denied attempts are logged durably.
- Persistence seed still works.
- Audit export is all for MIS/QCG/Admin, filtered for Finance, denied for Board/CXO.
- Migration runner works.
- Backup/restore check passes.
- Security and deployment routers are registered.
- Notification dedupe/suppression survives security migration.

