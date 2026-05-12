# SCIP Frontend UAT Hardening Notes — Persistence/Audit Follow-up

## Context
The Cloudflare Pages frontend reached the Render backend and failed on:

```text
/persistence/summary 500 · {"detail":"required_demo_record_not_found"}
```

This proves the original static frontend issue and the earlier route diagnostics are working. The remaining issue is a backend durable-persistence seed/migration/runtime-data problem, not a Vite or Cloudflare build problem.

## UAT-only frontend behavior in this patch
`/persistence/summary` is now treated as a non-blocking staging Product UAT surface.

Reason:
- Persistence/audit is a Batch 10 governance and go-live control surface.
- It should not block first-paint Product UAT for Arrival, Live Pulse, Forecast, Action Queues, Workflows, or role navigation.
- The UI still shows persistence/audit as unavailable and does not invent table counts, validation checks, audit records, or financial values.

## Permanent production rule
Before production signoff, `/persistence/summary` must be restored as a passing live gate by fixing the backend/data layer:

- Apply the Batch 10 persistence migration.
- Ensure durable tables exist.
- Seed or create required workflow/audit/demo records where the backend expects them.
- Confirm `/persistence/summary` returns `200` with live table counts and validation checks.
- Confirm audit export works for JSON and CSV.
- Confirm workflow events, notifications, suppression state, and audit exports carry actor, timestamp, role, and lineage references.

This frontend patch must not be interpreted as production readiness evidence.

## Permanent frontend hardening in this patch
- Backend URL handling remains normalized across `VITE_BACKEND_URL`, `VITE_SCIP_API_BASE_URL`, and `VITE_API_BASE_URL`.
- Staging bypass detection now also accepts legacy aliases:
  - `VITE_SCIP_LOCAL_DEV_BYPASS`
  - `VITE_LOCAL_DEV_BYPASS`
  - `VITE_AUTH_BYPASS`
- Quickball requests should continue to use role-aware auth/bypass headers.
- Optional UAT surfaces remain non-blocking with explicit unavailable states.
- Core product/financial endpoints remain blocking:
  - `/command-centres`
  - `/forecast/month-end`
  - `/action-queues`
  - `/workflows`

## Staging reminder
If the diagnostic still says `Bypass headers disabled`, verify the Cloudflare Pages variables are set in the Production environment and that the site was redeployed after setting them:

```text
VITE_SCIP_LOCAL_DEV_BYPASS=true
VITE_BACKEND_URL=https://scip.onrender.com
VITE_SCIP_API_BASE_URL=https://scip.onrender.com
VITE_API_BASE_URL=https://scip.onrender.com
```

## Production reminder
Production must use real JWT/SSO. Local/dev bypass headers must be off:

```text
SCIP_AUTH_MODE=jwt
SCIP_LOCAL_DEV_BYPASS=false
```

Do not call SCIP production-live until durable persistence, audit export, RBAC, identity, source refresh, smoke tests, and role-wise UAT all pass.
