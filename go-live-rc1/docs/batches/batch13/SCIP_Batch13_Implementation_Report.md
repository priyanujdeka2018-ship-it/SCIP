# SCIP Batch 13 Implementation Report

## Scope
Batch 13 adds SSO/JWT identity and user provisioning on top of Batch 12 observability/performance and Batch 11 RBAC hardening.

## Preserved guardrails
- Batch 5.1 Liquid Glass model remains unchanged: no new Arrival door, no new dashboard-first security area.
- Locked hierarchy is preserved.
- 0.05% tolerance remains a data-governance rule.
- No-silent-fallback and reporting-basis labels remain unchanged.
- Entity Head remains removed.
- Account-action gate remains enforced.
- Immutable workflow event lineage and notification dedupe/suppression are untouched.
- Durable audit schema is extended, not replaced.
- Batch 11 RBAC row-level visibility remains the enforcement layer.
- Batch 12 observability correlation/redaction rules are preserved.

## What changed
Batch 11 accepted trusted `X-SCIP-*` headers as a development identity contract. Batch 13 replaces that default with verified JWT identity.

Production default:

```text
SCIP_AUTH_MODE=jwt
```

Header identity is allowed only when both are explicitly enabled:

```text
SCIP_AUTH_MODE=local_dev
SCIP_LOCAL_DEV_BYPASS=true
```

## New files
- `identity.py` - JWT verifier, claim-to-role mapping, provisioning, session recording, identity-denial audit.
- `migrations/004_batch13_identity_provisioning.sql` - migration-ready identity/provisioning schema.
- `frontend_contracts_batch13.ts` - frontend identity/provisioning contracts.
- `smoke_batch13_identity_rbac.py` - identity/RBAC smoke harness.
- `identity_provisioning_sample_batch13.json` - sample provisioning and actor payload.

## Patched files
- `auth.py` - Batch 13 identity entrypoint; legacy header actor renamed to `legacy_actor_from_headers`; denied attempts enriched with correlation ID and audit lineage.
- `main.py` - imports and registers `/identity` routes; CORS headers now prefer Authorization and correlation headers.
- `App.jsx` - fetches `/identity/me`, uses `Authorization: Bearer <JWT>` by default, and shows an Identity posture bar.
- `liquidGlassTokens.css` - adds identity posture styling using glass for context only.

## New backend routes

```text
GET  /identity/me
GET  /identity/policy
GET  /identity/provisioning
POST /identity/deactivate/{user_id}
POST /identity/test-token  # local_dev only
```

## Token requirements
Patch-pack JWT verification supports HS256 for deterministic local smoke tests. Production should use an enterprise IdP gateway or JWKS verifier for RS256/ES256 while preserving the same actor contract.

Required claims:

```text
sub
iss
aud
exp
scip_role OR mapped groups
```

Recommended claims:

```text
name
email
scip_entity_scope
scip_collector_id
```

## Claim-to-role mapping

```text
scip-board / scip-cxo              -> board_cxo
scip-management / scip-cco-gm-agm  -> cco_gm_agm
scip-finance                       -> finance
scip-admin / scip-mis-qcg-admin    -> mis_qcg_admin
scip-collector / scip-collector-rm -> collector_rm
```

Direct `scip_role` is also accepted if it maps to the locked role model.

## Provisioning models

```text
provisioned_users
provisioned_groups
user_group_memberships
role_assignments
entity_scope_assignments
collector_mappings
sso_sessions
identity_denials
```

## Smoke result

```text
16 / 16 checks passed
contract: identity_sso_jwt.v1.batch13
status: ready_sso_jwt_provisioning_guarded
```

Validated:
- invalid token rejected
- expired token rejected
- Entity Head claim rejected
- trusted headers rejected unless local-dev bypass is explicit
- claim/group role mapping works
- Collector/RM sees only own rows
- Board/CXO cannot access account queues
- Finance cannot access Collector/RM-only workflows
- identity denied attempts include correlation ID and audit lineage
- RBAC denied attempts include correlation ID and audit lineage
- sensitive emails/tokens are not persisted in denial audit rows

## Production notes
Before production external access:
1. Replace HS256 local verifier with gateway/JWKS verification.
2. Configure issuer and audience.
3. Map IdP groups to SCIP roles.
4. Confirm user deactivation flow with HR/IT source of truth.
5. Confirm collector ID mapping source and refresh cadence.
6. Confirm session expiry and refresh policy with security team.
7. Run full RBAC smoke tests with production-like claims.
