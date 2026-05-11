# SCIP Batch 13 Apply Patch

1. Copy backend files into the FastAPI backend:
   - `identity.py`
   - `auth.py`
   - `main.py`
   - `migrations/004_batch13_identity_provisioning.sql`

2. Copy frontend files into the React/Vite app:
   - `App.jsx`
   - `liquidGlassTokens.css`
   - `frontend_contracts_batch13.ts`

3. Set environment variables for production:

```bash
SCIP_AUTH_MODE=jwt
SCIP_LOCAL_DEV_BYPASS=false
SCIP_JWT_ISSUER=<your-idp-issuer>
SCIP_JWT_AUDIENCE=scip-platform
SCIP_AUDIT_DB=<durable-db-path-or-url>
```

4. For local smoke only:

```bash
python smoke_batch13_identity_rbac.py
```

5. Production SSO note: the patch-pack verifier supports HS256 for deterministic smoke tests. For external production, verify RS256/ES256 tokens through your IdP gateway or application JWKS verifier while preserving the `/identity/me` actor contract.
