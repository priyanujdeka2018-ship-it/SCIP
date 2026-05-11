# SCIP Batch 13 Backend / Frontend Contracts

## Contract version

```text
identity_sso_jwt.v1.batch13
```

## Authentication header

Production/default:

```http
Authorization: Bearer <JWT>
X-SCIP-Correlation-ID: <correlation-id>
```

Local development bypass only:

```http
X-SCIP-Actor-ID: <actor>
X-SCIP-Role: <role>
X-SCIP-Entity-Scope: <scope>
X-SCIP-Collector-ID: <collector-id>
```

The local header path is disabled unless:

```text
SCIP_AUTH_MODE=local_dev
SCIP_LOCAL_DEV_BYPASS=true
```

## GET /identity/me

Returns the verified actor derived from JWT claims and provisioning.

```json
{
  "contract_version": "identity_sso_jwt.v1.batch13",
  "auth_mode": "jwt",
  "actor": {
    "actor_id": "u-coll",
    "actor_name": "Collector User",
    "role": "collector_rm",
    "role_label": "Collector/RM",
    "entity_scope": ["Sobha Dubai"],
    "collector_id": "C123",
    "environment": "production",
    "permissions": ["read:action_queues_own"]
  }
}
```

## GET /identity/policy

Returns IdP/JWT expectations, group-to-role mapping, local-dev bypass rule, and provisioning model names.

## GET /identity/provisioning

Admin-only view of provisioned users, group/role assignments, entity scopes, collector mappings, sessions, and identity-denial counts.

Requires:

```text
read:security_audit
```

## POST /identity/deactivate/{user_id}

Admin-only user deactivation. Deactivation disables user, roles, entity scopes, collector mappings, and active sessions.

Requires:

```text
read:security_audit
```

## Frontend behavior
- Use `Authorization: Bearer <JWT>` by default.
- Do not send trusted actor headers unless local development bypass is explicitly enabled.
- Fetch `/identity/me` next to `/security/me`.
- Display actor role, scope, collector mapping, and auth mode in an identity posture context surface.
- Keep business computation server-side.

## Row-level visibility preserved
After identity verification, the existing RBAC row-level rules still apply:
- Board/CXO cannot access account queues.
- Collector/RM sees only rows where owner/collector matches the actor or collector mapping.
- Finance sees Finance rows, not Collector/RM-only workflows.
- MIS/QCG/Admin has governance/admin visibility.

## Denied attempt audit
Identity denials are recorded in `identity_denials` with:

```text
denial_id
subject
reason
path
method
correlation_id
audit_lineage_json
created_at
```

RBAC denials continue in `access_denials`; Batch 13 enriches row context with correlation ID and audit lineage.
