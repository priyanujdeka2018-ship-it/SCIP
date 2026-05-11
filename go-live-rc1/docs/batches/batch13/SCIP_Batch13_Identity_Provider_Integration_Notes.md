# SCIP Batch 13 Identity Provider Integration Notes

## Supported pattern
Batch 13 introduces the application-side actor contract and a deterministic JWT verifier for patch-pack smoke testing.

For production, prefer one of these patterns:

1. **Gateway verified JWT**
   - API gateway verifies IdP JWT using JWKS.
   - Gateway forwards the original Authorization bearer token or verified claims.
   - SCIP validates issuer/audience and maps claims to the actor contract.

2. **Application JWKS verification**
   - SCIP fetches IdP JWKS and verifies RS256/ES256 signatures.
   - Cache JWKS by key ID with safe rotation.
   - Reject tokens with missing `kid`, unknown key, invalid issuer/audience, expired `exp`, or unsigned alg.

## Required claims

```text
sub: stable user subject
iss: configured issuer
aud: configured audience
exp: expiry timestamp
scip_role or groups: role mapping input
```

## Recommended claims

```text
name: display name
email: only hash is stored
scip_entity_scope: Group/Sobha/Sobha Dubai/Sobha AUH/UAQ/Siniya/Downtown UAQ
scip_collector_id: collector/RM owner ID for row-level visibility
groups: IdP group names mapped to SCIP roles
```

## Role mapping
Do not provision Entity Head. It is intentionally removed.

```text
scip-board -> Board/CXO
scip-management -> CCO/GM/AGM
scip-finance -> Finance
scip-admin -> MIS/QCG/Admin
scip-collector -> Collector/RM
```

## Deactivation
User deactivation should revoke active sessions and deactivate role/entity/collector assignments. Batch 13 implements this locally through `/identity/deactivate/{user_id}`; production should bind it to HR/IT source of truth.

## Logging and privacy
- Do not log raw tokens.
- Do not persist emails; store only email hash when needed.
- Identity denials include claim fingerprint, not claim payload.
- Correlation ID is mandatory.
