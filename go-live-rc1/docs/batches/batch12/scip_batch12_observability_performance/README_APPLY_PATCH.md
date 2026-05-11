# Apply SCIP Batch 12 Patch

1. Copy these files into the backend app folder:
   - `observability.py`
   - `main.py`
   - `migrations/003_batch12_observability.sql`
   - `observability_config_batch12.json`

2. Copy these frontend files into the UI app folder:
   - `App.jsx`
   - `liquidGlassTokens.css`
   - `frontend_contracts_batch12.ts` if using TypeScript contract docs.

3. Run backend checks:

```bash
python -m py_compile observability.py main.py
python smoke_batch12_observability_performance.py
```

4. Run synthetic telemetry load check:

```bash
python load_tests/batch12_synthetic_load.py
```

5. Run frontend build in the deployment repo:

```bash
npm install
npm run build
npm run dev
```

6. Production telemetry wiring:

Batch 12 provides a local in-process telemetry store and API contracts. For production, forward structured events to your selected sink: OpenTelemetry, CloudWatch, Datadog, Grafana/Loki, Azure Monitor, or an internal secure logging pipeline.

## Required environment variables

```text
SCIP_ENV
FRONTEND_URL
BACKEND_URL
CORS_ALLOWED_ORIGINS
SCIP_AUDIT_DB
SCIP_TELEMETRY_EVENT_LIMIT
SCIP_CACHE_TTL_SECONDS
```

## Guardrails

- Do not enable body logging.
- Do not cache workflow mutations, raw source lineage, actor identity, or audit exports.
- Do not add an Observability Arrival door.
- Do not move forecast/action/notification computation into frontend.
