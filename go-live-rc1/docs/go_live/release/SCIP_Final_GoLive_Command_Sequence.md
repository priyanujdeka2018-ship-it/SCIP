# SCIP Final Go-Live Command Sequence

> Adjust paths for the actual SCIP repository. Commands assume Linux/macOS shell.

## 0. Preflight

```bash
export SCIP_REPO=/path/to/scip-repo
export SCIP_PATCH_ROOT=/path/to/scip-release-candidate-patches
cd "$SCIP_REPO"
git status --short
git rev-parse --short HEAD
```

Create a rollback anchor:

```bash
git checkout -b release/scip-go-live-candidate
git tag pre-scip-go-live-$(date +%Y%m%d-%H%M)
```

## 1. Merge patch layers

Recommended merge order:

```bash
# 1. Production code/security baseline from Batch 13
rsync -av "$SCIP_PATCH_ROOT/batch13/" "$SCIP_REPO/"

# 2. Rollout/UAT governance from Batch 14
rsync -av "$SCIP_PATCH_ROOT/batch14/rollout/" "$SCIP_REPO/docs/rollout/"
rsync -av "$SCIP_PATCH_ROOT/batch14/uat/" "$SCIP_REPO/docs/uat/"
rsync -av "$SCIP_PATCH_ROOT/batch14/checklists/" "$SCIP_REPO/docs/checklists/"
rsync -av "$SCIP_PATCH_ROOT/batch14/signoff/" "$SCIP_REPO/docs/signoff/"
rsync -av "$SCIP_PATCH_ROOT/batch14/smoke/" "$SCIP_REPO/smoke/"

# 3. Executive roadmap/rhythm from Batch 17
rsync -av "$SCIP_PATCH_ROOT/batch17/roadmap/" "$SCIP_REPO/docs/roadmap/"
rsync -av "$SCIP_PATCH_ROOT/batch17/cadence/" "$SCIP_REPO/docs/cadence/"
rsync -av "$SCIP_PATCH_ROOT/batch17/okr/" "$SCIP_REPO/docs/okr/"
rsync -av "$SCIP_PATCH_ROOT/batch17/ownership/" "$SCIP_REPO/docs/ownership/"
rsync -av "$SCIP_PATCH_ROOT/batch17/release_train/" "$SCIP_REPO/docs/release_train/"
rsync -av "$SCIP_PATCH_ROOT/batch17/benefits/" "$SCIP_REPO/docs/benefits/"
rsync -av "$SCIP_PATCH_ROOT/batch17/steering/" "$SCIP_REPO/docs/steering/"
```

If the app is single-root rather than separated backend/frontend, copy files into the actual app structure manually:

```bash
# Backend candidates
main.py auth.py identity.py observability.py deployment.py persistence.py workflow.py notifications.py account_action_queues.py roadmap.py rollout_uat.py

# Frontend candidates
App.jsx liquidGlassTokens.css

# Migrations
migrations/001_batch10_persistence.sql
migrations/002_batch11_rbac_hardening.sql
migrations/003_batch12_observability.sql
migrations/004_batch13_identity_provisioning.sql
migrations/005_batch15_adoption_analytics.sql
migrations/006_batch16_continuous_improvement.sql
migrations/007_batch17_roadmap_exec_rhythm.sql
```

Commit the merged release candidate:

```bash
git add .
git commit -m "Release candidate: SCIP go-live readiness consolidation"
```

## 2. Backend local verification

```bash
python -m compileall .
python smoke_batch13_identity_rbac.py || true
python smoke_batch12_observability_performance.py || true
python smoke_batch10_persistence_audit.py || true
```

Start backend:

```bash
export SCIP_ENV=staging
export SCIP_AUTH_MODE=jwt
export SCIP_LOCAL_DEV_BYPASS=false
uvicorn main:app --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl -sS http://localhost:8000/health
curl -sS http://localhost:8000/deployment/health
```

## 3. Frontend local verification

```bash
npm install
npm run build
npm run dev
```

Manual checks:

- `/` shows only Live Pulse and Narratives.
- No Entity Head role appears.
- Lineage drawer opens from financial cards.
- Blocked-answer warning appears when lineage is missing.
- Trust bar shows source freshness and validation state.

## 4. Database migration in staging

```bash
export DATABASE_URL="postgresql://USER:PASSWORD@HOST:5432/scip_staging"
psql "$DATABASE_URL" -f migrations/001_batch10_persistence.sql
psql "$DATABASE_URL" -f migrations/002_batch11_rbac_hardening.sql
psql "$DATABASE_URL" -f migrations/003_batch12_observability.sql
psql "$DATABASE_URL" -f migrations/004_batch13_identity_provisioning.sql
psql "$DATABASE_URL" -f migrations/005_batch15_adoption_analytics.sql
psql "$DATABASE_URL" -f migrations/006_batch16_continuous_improvement.sql
psql "$DATABASE_URL" -f migrations/007_batch17_roadmap_exec_rhythm.sql
```

Verify tables:

```bash
psql "$DATABASE_URL" -c "select table_name from information_schema.tables where table_schema='public' order by table_name;"
```

## 5. SSO/JWT configuration

```bash
export SCIP_AUTH_MODE=jwt
export SCIP_LOCAL_DEV_BYPASS=false
export SCIP_JWT_ISSUER="https://idp.example.com/tenant"
export SCIP_JWT_AUDIENCE="api://scip"
export SCIP_JWT_JWKS_URL="https://idp.example.com/tenant/.well-known/jwks.json"
export SCIP_JWT_ALGORITHMS="RS256"
```

Token validation smoke:

```bash
curl -sS -H "Authorization: Bearer $SCIP_JWT" "$SCIP_BASE_URL/identity/me"
```

## 6. Source refresh and ingestion smoke

Place latest production R-series files in configured source folder:

```bash
mkdir -p "$SCIP_SOURCE_ROOT"
ls -lh "$SCIP_SOURCE_ROOT"
```

Required minimum files:

```text
R02, R04, R08, R18, R36
R09, R10, R17, R20, R30, R31, R32, R34, R38
```

Run ingestion and adapter smoke scripts available in the merged repo:

```bash
python smoke_r18_batch1.py || true
python smoke_r04_r02_batch2.py || true
python smoke_r08_r36_batch3.py || true
python smoke_batch7_action_queues.py || true
```

## 7. Deployment smoke against staging URL

```bash
export SCIP_BASE_URL="https://staging-scip.example.com"
export SCIP_JWT="<valid staging jwt>"
python smoke/deployment_smoke_runner.py
```

Repeat with role-specific JWTs:

```bash
for role in board_cxo cco_gm_agm finance mis_qcg_admin collector_rm; do
  export SCIP_JWT="$(cat ./secrets/staging-${role}.jwt)"
  python smoke/deployment_smoke_runner.py || exit 1
done
```

## 8. UAT signoff

Use `docs/uat/SCIP_Batch14_UAT_Scripts_By_Role.md`.

Record signoff in:

```text
docs/signoff/SCIP_Batch14_Signoff_Matrix.csv
```

## 9. Production deployment

Before production:

```bash
git tag scip-prod-rc-approved-$(date +%Y%m%d)
```

Production migration:

```bash
# backup first
pg_dump "$PROD_DATABASE_URL" > backups/scip-prod-pre-go-live-$(date +%Y%m%d-%H%M).sql

# apply migrations in order
psql "$PROD_DATABASE_URL" -f migrations/001_batch10_persistence.sql
psql "$PROD_DATABASE_URL" -f migrations/002_batch11_rbac_hardening.sql
psql "$PROD_DATABASE_URL" -f migrations/003_batch12_observability.sql
psql "$PROD_DATABASE_URL" -f migrations/004_batch13_identity_provisioning.sql
psql "$PROD_DATABASE_URL" -f migrations/005_batch15_adoption_analytics.sql
psql "$PROD_DATABASE_URL" -f migrations/006_batch16_continuous_improvement.sql
psql "$PROD_DATABASE_URL" -f migrations/007_batch17_roadmap_exec_rhythm.sql
```

Production smoke:

```bash
export SCIP_BASE_URL="https://scip.example.com"
export SCIP_JWT="<production smoke jwt>"
python smoke/deployment_smoke_runner.py
```

## 10. Rollback

```bash
# app rollback
git checkout pre-scip-go-live-<tag>
# redeploy previous artifact

# db rollback: restore backup if migration rollback is required
psql "$PROD_DATABASE_URL" < backups/scip-prod-pre-go-live-YYYYMMDD-HHMM.sql
```

## 11. Break-glass

Break-glass may be enabled only with written incident reason and time-bound owner approval. It must be logged and reviewed within 24 hours.
