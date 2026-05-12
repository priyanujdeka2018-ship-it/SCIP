# SCIP Frontend UAT Hardening Notes

Scope: Cloudflare Pages staging Product UAT only.

This patch hardens `src/App.jsx` after observed staging failures:

- `identityJson is not defined` runtime failure.
- Generic Safari `Load failed` messages during browser fetch/CORS failures.
- `/command-centres network/CORS: Load failed` diagnostic.
- `/notifications network/CORS: Load failed` diagnostic.

## Permanent fixes

These are appropriate to keep beyond UAT:

1. Backend URL normalization
   - Reads `VITE_BACKEND_URL`, `VITE_SCIP_API_BASE_URL`, then `VITE_API_BASE_URL`.
   - Removes trailing slash to prevent double-slash API paths.

2. Defensive rendering for backend shapes
   - `entity_scope` can be an array or string.
   - `permissions`, observability alerts, dashboards, and critical source lists are guarded with `safeArray`.

3. Quickball auth alignment
   - Quickball calls now use the same auth/bypass headers as the rest of the frontend.

4. Per-endpoint diagnostics
   - Required endpoint failures show the exact route and failure class.
   - Helps distinguish CORS/network failure, HTTP status failure, and invalid JSON.

## Staging/UAT-only behavior

These are intentionally for Product UAT while security/SSO is deferred:

1. Notifications are non-blocking at startup.
   - Notifications are an L5 Risk & Action output, not required for Arrival/Live Pulse initial load.
   - Board/CXO calls `/notifications/digests`; other roles call `/notifications`.
   - If unavailable, the UI renders a clean unavailable state and does not invent notifications.

2. Identity, security posture, deployment health, and observability are non-blocking.
   - These surfaces are shown when available.
   - They do not block Product UAT while JWT/SSO/JWKS remains deferred.

3. Staging diagnostic panel appears on startup failure.
   - Shows backend URL, endpoint, status, role, bypass mode, and correlation ID.
   - This is helpful for UAT and can be removed or hidden before production polish.

## Core rules preserved

- No frontend financial computation.
- No fake fallback figures.
- Core product/financial endpoints remain blocking:
  - `/command-centres`
  - `/forecast/month-end`
  - `/action-queues`
  - `/workflows`
  - `/persistence/summary`
- Entity Head remains removed.
- Security/SSO validation remains deferred only for staging Product UAT, not production.

## Production reminder

Before production:

- `SCIP_AUTH_MODE=jwt`
- `SCIP_LOCAL_DEV_BYPASS=false`
- Real JWT issuer/audience/JWKS configured.
- CORS must explicitly allow production frontend origin and required headers.
- Optional UAT diagnostics should be hidden or gated behind a debug flag.
