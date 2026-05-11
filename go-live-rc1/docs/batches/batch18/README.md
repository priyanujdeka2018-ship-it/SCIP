# SCIP Batch 18 Analytics Transformation Engine - Runtime Patch

This ZIP is the implementation overlay that follows the Batch 18 specification pack.

It is designed to be added after the Batch 13 runtime baseline and before any UI publication work.

## Contents

- Backend analytics transformation modules
- Config contracts and metric registry
- Standalone smoke test
- Runtime patch application notes

## Non-goals

- Does not replace Batch 13 data loader or source adapters.
- Does not alter `main.py` automatically.
- Does not publish new KPI candidates directly to production UI.
- Does not commit R-series `.xlsx` files.

## Recommended first command

```bash
SCIP_BATCH18_DATA_DIR=/path/to/staging/data python smoke/smoke_batch18_analytics_engine_runtime.py
```
