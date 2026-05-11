# SCIP Final Smoke Test Command Set

## Local static smoke

```bash
python -m compileall .
python smoke_batch10_persistence_audit.py
python smoke_batch11_rbac_hardening.py
python smoke_batch12_observability_performance.py
python smoke_batch13_identity_rbac.py
```

## Frontend smoke

```bash
npm install
npm run build
npm run dev
```

Manual checks:

- [ ] Arrival has only Live Pulse and Narratives.
- [ ] No Entity Head role appears.
- [ ] Role selector, if present for testing, is hidden/disabled in production with SSO identity.
- [ ] Trust bar visible after entry.
- [ ] Lineage drawer opens.
- [ ] Forecast assumptions are visible.
- [ ] Quickball blocked answer appears if lineage is removed.

## Deployment smoke

```bash
export SCIP_BASE_URL=https://staging-scip.example.com
export SCIP_JWT=<valid-jwt>
python smoke/deployment_smoke_runner.py
```

## Role-wise endpoint smoke

```bash
# Board/CXO
curl -fsS -H "Authorization: Bearer $BOARD_CXO_JWT" "$SCIP_BASE_URL/identity/me"
curl -i   -H "Authorization: Bearer $BOARD_CXO_JWT" "$SCIP_BASE_URL/action-queues"

# CCO/GM/AGM
curl -fsS -H "Authorization: Bearer $CCO_GM_AGM_JWT" "$SCIP_BASE_URL/action-queues"

# Finance
curl -fsS -H "Authorization: Bearer $FINANCE_JWT" "$SCIP_BASE_URL/notifications?role=finance"

# MIS/QCG/Admin
curl -fsS -H "Authorization: Bearer $MIS_QCG_ADMIN_JWT" "$SCIP_BASE_URL/audit/export?format=json"

# Collector/RM
curl -fsS -H "Authorization: Bearer $COLLECTOR_RM_JWT" "$SCIP_BASE_URL/action-queues?role=collector_rm"
```

Expected access pattern:

| Role | Expected |
|---|---|
| Board/CXO | Can see executive summaries; cannot read account queues. |
| CCO/GM/AGM | Can see management and escalation rows. |
| Finance | Can see finance exceptions and finance audit scope. |
| MIS/QCG/Admin | Can see governance, audit, migrations, source health. |
| Collector/RM | Can see only own scoped rows. |

## Critical production smoke gates

- [ ] `/identity/me` resolves JWT actor.
- [ ] Invalid/expired JWT is rejected.
- [ ] `X-SCIP-*` headers are ignored in production.
- [ ] `/command-centres` returns role-safe payload.
- [ ] `/forecast/month-end` returns assumptions and lineage.
- [ ] `/quickball/explain` blocks missing-lineage critical metric.
- [ ] `/action-queues` enforces row-level visibility.
- [ ] `/workflows` supports closure and audit trail.
- [ ] `/notifications` dedupes and suppresses repeated notification.
- [ ] `/audit/export` returns source/workflow/notification lineage.
- [ ] `/observability/summary` includes correlation IDs and redaction status.
- [ ] `/deployment/health` is green.
