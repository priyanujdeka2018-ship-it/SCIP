# SCIP Batch 11 Backend / Frontend Contracts

## Actor identity contract

For this patch pack, actor identity is carried by request headers. In production these headers should be set by a trusted gateway after SSO/JWT validation.

```ts
type SCIPRole = 'board_cxo' | 'cco_gm_agm' | 'finance' | 'mis_qcg_admin' | 'collector_rm';
```

Required headers:

```http
X-SCIP-Actor-ID
X-SCIP-Actor-Name
X-SCIP-Role
X-SCIP-Entity-Scope
X-SCIP-Environment
```

Optional header:

```http
X-SCIP-Collector-ID
```

## Row-level visibility

Rows are visible only when all applicable checks pass:

1. actor role is in row `role_visibility`,
2. actor entity scope contains `Group` or the row entity,
3. Collector/RM can see only rows where owner/collector matches `actor_id` or `collector_id`,
4. audit export is filtered by role-specific permission.

## New security endpoints

### `GET /security/me`

Returns the authenticated actor and permissions.

### `GET /security/policy-matrix`

Returns the RBAC policy matrix. Intended for MIS/QCG/Admin and governance review.

### `GET /security/denied-attempts`

Returns denied access attempts for audit review. Restricted to MIS/QCG/Admin.

## New deployment endpoints

### `GET /deployment/health`

Returns environment config posture, CORS checks, secrets presence, migration status and hardening notes.

### `POST /deployment/migrate`

Runs migrations with checksum tracking. Restricted to MIS/QCG/Admin.

### `POST /deployment/backup-check`

Creates a backup copy, restores it to a check database and compares table counts. Restricted to MIS/QCG/Admin.

## Frontend contract

The frontend sends `X-SCIP-*` headers with all backend calls and displays a Liquid Glass security posture bar showing:

- actor ID,
- role,
- permission count,
- denied-attempt audit status.

No financial or workflow business computation moves into the frontend.
