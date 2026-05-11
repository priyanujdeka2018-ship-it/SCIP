# SCIP Final Production Readiness Checklist

## Application

- [ ] Backend starts with `SCIP_AUTH_MODE=jwt`.
- [ ] Frontend builds successfully.
- [ ] CORS only allows approved origins.
- [ ] Secrets are not committed.
- [ ] Local-dev bypass disabled.
- [ ] Health endpoints green.

## Data and lineage

- [ ] R-series production files loaded.
- [ ] Critical lineage coverage is complete.
- [ ] Fallback is blocked or visibly labelled.
- [ ] Snapshot dates shown.
- [ ] Reconciliation tolerance is 0.05%.

## Identity and RBAC

- [ ] JWT issuer/audience/keys configured.
- [ ] Provisioned users active.
- [ ] Deactivated users blocked.
- [ ] Entity/collector scopes mapped.
- [ ] Row-level visibility verified.
- [ ] Entity Head role absent.

## Workflow and notifications

- [ ] Workflow assignment permissions verified.
- [ ] Closure reason required.
- [ ] Immutable lineage hash preserved.
- [ ] Notification dedupe and suppression verified.
- [ ] External notification delivery disabled or explicitly approved.

## Persistence and audit

- [ ] Database migrations applied.
- [ ] Backup completed.
- [ ] Restore tested.
- [ ] Audit export works.
- [ ] Denied attempts logged.

## Observability

- [ ] Correlation IDs present.
- [ ] Sensitive data redacted.
- [ ] Alert thresholds configured.
- [ ] Stale-source alert configured.
- [ ] Missing-lineage alert configured.
- [ ] Migration/backup failure alerts configured.

## Rollback and break-glass

- [ ] Pre-release tag created.
- [ ] Database backup tested.
- [ ] Rollback owner assigned.
- [ ] Break-glass owner assigned.
- [ ] Break-glass log location confirmed.
