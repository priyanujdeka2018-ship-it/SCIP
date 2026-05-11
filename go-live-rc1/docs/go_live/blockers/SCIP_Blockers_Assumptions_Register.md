# SCIP Blockers and Environment Assumptions Register

## Current blockers before production

| Blocker | Severity | Required resolution |
|---|---|---|
| Actual production repository not available inside this sandbox | High | Apply the patch packs to the real repo and resolve merge conflicts. |
| Full frontend build not executed in actual repo | High | Run `npm install`, `npm run build`, and `npm run dev`. |
| Backend integration tests not executed against real deployed services | High | Run backend tests and deployment smoke in staging. |
| Real SSO/JWT provider details not configured here | High | Configure issuer, audience, JWKS/keys, algorithms, token expiry and provisioning claims. |
| Production database credentials and host unknown | High | Configure `DATABASE_URL`, SSL, backup, migration rights, and restore path. |
| CORS production origin unknown | Medium | Configure exact allowed origins; no wildcard in production. |
| Production R-series latest files not loaded in target environment | High | Load latest R02/R04/R08/R18/R36 and R09/R10/R17/R20/R30/R31/R32/R34/R38. |
| Real deployment base URL and role-specific JWTs unavailable here | High | Generate staging/prod URLs and role tokens, then run deployment smoke runner. |
| UAT signoff not yet completed | High | Execute role-wise UAT and signoff matrix. |
| Break-glass owner and approval path not confirmed here | Medium | Confirm owner, duration, logging, and review process. |

## Environment assumptions

- The backend is FastAPI-compatible and exposes `main.py` as app entrypoint.
- The frontend is Vite/React-compatible and can consume `App.jsx` and `liquidGlassTokens.css`.
- The deployment target supports environment variables and HTTPS.
- The database is PostgreSQL-compatible or can run the SQL with minor dialect adjustments.
- IdP supports JWT with stable role/group/entity/collector claims.
- R-series file delivery remains Excel-based until warehouse integration is approved.
- Local-dev header identity is forbidden in production.

## Production go-live risk rating

```text
If all gates pass: low to medium risk
If SSO/RBAC/source lineage gates are skipped: high risk
If deployed directly without staging/UAT: unacceptable risk
```
