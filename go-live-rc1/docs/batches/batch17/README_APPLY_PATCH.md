# SCIP Batch 15 Apply Patch

1. Copy these files into the backend/frontend repo, preserving paths.
2. Apply migration `migrations/005_batch15_adoption_analytics.sql` after Batch 14 migrations.
3. Ensure JWT/SSO and RBAC environment variables from Batch 13/14 remain in place.
4. Run backend smoke:

```bash
python smoke/static_adoption_smoke.py
```

5. Run frontend build in target repo:

```bash
npm install
npm run build
npm run dev
```

6. Review `/adoption/summary`, `/adoption/dashboards`, and `/adoption/backlog` from an MIS/QCG/Admin actor.

Do not add adoption analytics to Arrival. Keep it in Live Pulse → Risk & Action as governance evidence/output.
