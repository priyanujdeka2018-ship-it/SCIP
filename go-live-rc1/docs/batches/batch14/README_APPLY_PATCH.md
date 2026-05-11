# SCIP Batch 14 Rollout and UAT Signoff Pack

Apply this pack after Batch 13.

## Files to apply

- `rollout_uat.py` → backend root.
- `main.py` → replace current Batch 13 `main.py` if you want rollout/UAT governance endpoints.
- Documentation folders can be stored in repo `/docs/rollout` or shared with rollout owners.

## Local validation

```bash
python smoke/static_rollout_uat_smoke.py
```

## Live deployment smoke

```bash
SCIP_BASE_URL=https://your-scip-url SCIP_JWT=<jwt> python smoke/deployment_smoke_runner.py
```

Full production smoke requires a deployed base URL and real JWT token.
