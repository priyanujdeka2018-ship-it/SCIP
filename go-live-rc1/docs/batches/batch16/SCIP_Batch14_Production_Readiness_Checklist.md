# SCIP Batch 14 Production Readiness Checklist

## Build and deployment

- [ ] Frontend `npm install` completed.
- [ ] Frontend `npm run build` passed.
- [ ] Backend starts with all routers loaded.
- [ ] No router import errors in `/` or `/manifest`.
- [ ] Production environment variables loaded from secrets manager.
- [ ] `SCIP_AUTH_MODE=jwt`.
- [ ] `SCIP_LOCAL_DEV_BYPASS=false`.
- [ ] CORS origins are explicit; no wildcard outside local.
- [ ] Database migration runner tested.
- [ ] Rollback artifact available.

## Security and identity

- [ ] JWT issuer configured.
- [ ] JWT audience configured.
- [ ] JWKS/verification path configured if using RS256/ES256.
- [ ] Invalid tokens rejected.
- [ ] Expired tokens rejected.
- [ ] Deactivated users rejected.
- [ ] Entity Head claims rejected.
- [ ] Denied attempts logged.

## Data and lineage

- [ ] Critical sources present or waived with named owner.
- [ ] R02 target lineage checked.
- [ ] R04 actual lineage checked.
- [ ] R08 advance/rebate lineage checked.
- [ ] R18 OD/ageing lineage checked.
- [ ] R36 pipeline/year-bucket lineage checked.
- [ ] Account-action sources checked: R10/R17/R20/R30/R31/R32/R34/R38/R09 as available.
- [ ] No critical card uses fallback.

## Workflow and notification

- [ ] Assignment works for permitted roles.
- [ ] Closure requires reason.
- [ ] Workflow event lineage hash is immutable.
- [ ] Notification dedupe/suppression works after restart.
- [ ] External notification channels are disabled or explicitly approved.

## Observability

- [ ] Correlation ID in every request/event.
- [ ] Sensitive fields redacted.
- [ ] Slow endpoint alert configured.
- [ ] Missing lineage alert configured.
- [ ] Stale source alert configured.
- [ ] Migration/backup failure alerts configured.

## Business signoff

- [ ] Role UAT scripts completed.
- [ ] Executive acceptance criteria met.
- [ ] Rollback drill completed.
- [ ] Break-glass drill completed.
- [ ] Go-live signoff recorded.
