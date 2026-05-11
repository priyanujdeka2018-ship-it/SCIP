# Apply SCIP Batch 6 Patch

## Backend

Copy these files into the backend package:

- `account_action_queues.py`
- `main.py`
- `command_centres.py`
- `forecast.py`
- `quickball.py`
- `data_loader.py`
- `source_adapters.py`
- `pipeline_config.json`
- `constants.py`
- `file_resolver.py`

Run:

```bash
python -m py_compile account_action_queues.py main.py
uvicorn main:app --reload
```

Validate:

```bash
curl http://localhost:8000/action-queues
curl http://localhost:8000/action-queues/collector-drilldown
```

## Frontend

Copy these files into the frontend source folder:

- `App.jsx`
- `liquidGlassTokens.css`

Run:

```bash
npm install
npm run build
npm run dev
```

## Important deployment note

Batch 6 intentionally blocks Collector/RM account actions until an account/collector source report is onboarded. The current attached R18 sample supports project-risk cohorts, not true account-owner actions.
