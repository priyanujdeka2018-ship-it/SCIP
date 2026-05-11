# Apply SCIP Batch 11 Patch

1. Copy backend files into the SCIP backend app:
   - `auth.py`
   - `deployment.py`
   - `main.py`
   - patched `account_action_queues.py`
   - patched `workflow.py`
   - patched `notifications.py`
   - patched `persistence.py`
   - `migrations/002_batch11_rbac_hardening.sql`

2. Copy frontend files into the SCIP frontend app:
   - `App.jsx`
   - `liquidGlassTokens.css`
   - optionally `frontend_contracts_batch11.ts`

3. Run backend validation:

```bash
python smoke_batch11_rbac_hardening.py
python -m py_compile main.py auth.py deployment.py persistence.py workflow.py notifications.py account_action_queues.py
```

4. Run frontend validation in the target repo:

```bash
npm install
npm run build
npm run dev
```

5. Configure production identity. Header-based identity is a patch-pack contract and should be replaced by SSO/JWT verification before external deployment.
