# Apply SCIP Batch 7 Patch

Copy these files into the active app repository, replacing the prior Batch 6 versions:

```text
account_action_queues.py
main.py
App.jsx
liquidGlassTokens.css
pipeline_config.json
frontend_contracts_batch7.ts
```

Then run backend smoke locally:

```bash
python smoke_batch7_action_queues.py
```

For frontend validation, run the normal app build from the repository root:

```bash
npm install
npm run build
npm run dev
```

The `/action-queues` endpoint expects the R-series files to be available in the data directory. In this sandbox it reads `/mnt/data`; in production wire the same files through the app's source resolver or object store.
