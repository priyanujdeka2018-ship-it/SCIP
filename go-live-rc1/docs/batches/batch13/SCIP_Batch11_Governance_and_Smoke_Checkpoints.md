# SCIP Batch 11 Governance and Smoke Checkpoints

## Governance checkpoints

- [x] Entity Head removed from allowed role model.
- [x] Board/CXO, CCO/GM/AGM, Finance, MIS/QCG/Admin and Collector/RM remain the only roles.
- [x] Actor identity is explicit and auditable.
- [x] Row-level action visibility is role, entity and owner aware.
- [x] Denied attempts are durably logged.
- [x] Audit export is role filtered.
- [x] Notification dedupe and suppression state survive the security migration.
- [x] Workflow/event lineage hashes remain managed by Batch 10 persistence controls.
- [x] Deployment health checks are explicit.
- [x] CORS wildcard is blocked outside local development.
- [x] Secrets are checked by name only and never returned.
- [x] Backup/restore check is available before production deploy.

## Smoke checkpoints

`smoke_batch11_rbac_hardening.py` validates:

1. all Batch 11 modules import,
2. migrations run,
3. five-role model only,
4. Entity Head blocked,
5. collector assignment denied,
6. manager/admin/finance permissions resolved,
7. row-level visibility filters by owner/entity/role,
8. denied attempts logged,
9. durable store still seeds,
10. audit export filters by role,
11. deployment health generated,
12. backup/restore check passes,
13. security routes registered,
14. deployment routes registered,
15. middleware registered,
16. notification dedupe/suppression survives migration,
17. RBAC policies persisted.

## Production deployment gates

Before production rollout:

```bash
python smoke_batch11_rbac_hardening.py
python -m py_compile main.py auth.py deployment.py persistence.py workflow.py notifications.py account_action_queues.py
npm install
npm run build
npm run dev
```

Then verify:

- `/health`
- `/security/me`
- `/deployment/health`
- `/persistence/summary`
- `/audit/export?format=json`
- `/action-queues` with each role header set
- `/workflows` with each role header set
- `/notifications` with each role header set
