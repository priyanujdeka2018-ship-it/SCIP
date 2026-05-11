# SCIP Batch 18 Runtime Patch - Analytics Transformation Engine

This pack is an additive runtime overlay for Batch 13. It does not overwrite the existing production baseline.

## Files to add

- `Backend/analytics_models.py`
- `Backend/analytics_utils.py`
- `Backend/report_profiler.py`
- `Backend/semantic_fact_builder.py`
- `Backend/metric_registry.py`
- `Backend/metric_compiler.py`
- `Backend/metric_linker.py`
- `Backend/metric_suggestion_engine.py`
- `Backend/chart_spec_factory.py`
- `Backend/analytics_validation.py`
- `Backend/analytics_engine.py`
- `Backend/analytics_api_patch.py`
- `config/*batch18*.json` and Batch 18 metric/contract config files
- `smoke/smoke_batch18_analytics_engine_runtime.py`

## What it does

The engine transforms R-series workbooks into:

1. report profiles
2. lineaged facts
3. governed metric values
4. linked metric families
5. proposed new metric candidates
6. backend chart specs
7. validation results

## Guardrails

- No silent fallback for critical metrics.
- Facts are lineaged with deterministic hashes.
- Frontend should render only backend-provided values, trust states, labels, assumptions, and chart specs.
- New candidate KPIs remain proposed until governed approval.
- Cross-report reconciliation is date-aware; non-aligned snapshot dates produce diagnostic caveats.

## Standalone smoke

From repo root after placing files:

```bash
SCIP_BATCH18_DATA_DIR=/path/to/staging/data python smoke/smoke_batch18_analytics_engine_runtime.py
```

If running the patch outside the repo, also point to the Batch 13 backend folder so the engine can import `source_adapters.py`:

```bash
SCIP_BATCH13_BACKEND=/path/to/Backend SCIP_BATCH18_DATA_DIR=/path/to/data python smoke/smoke_batch18_analytics_engine_runtime.py
```

## Optional API integration

Use `Backend/analytics_api_patch.py` as a copy-in snippet after JWT/RBAC gates. Do not expose the endpoint without role checks.
