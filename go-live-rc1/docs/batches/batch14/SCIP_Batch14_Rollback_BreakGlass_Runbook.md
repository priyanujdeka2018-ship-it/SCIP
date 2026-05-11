# SCIP Batch 14 Rollback and Break-Glass Runbook

## Rollback command sequence template

1. Announce rollback window to rollout owners.
2. Freeze workflow assignments and notification emissions.
3. Snapshot current database.
4. Switch traffic to previous known-good deployment.
5. Restore database only if schema/data corruption is confirmed.
6. Re-run production smoke runner.
7. Confirm identity/RBAC works.
8. Confirm no stale/fallback data is shown as live.
9. Publish rollback outcome.

## Break-glass workflow

1. Request break-glass from MIS/QCG/Admin owner.
2. Security owner approves time-boxed access.
3. Enable emergency actor with explicit read-only scope unless write access is approved.
4. Record reason and expiry.
5. Capture all actions through audit log.
6. Disable break-glass access after expiry or incident closure.
7. Conduct post-event review.

## Prohibited break-glass use

- Routine convenience access.
- Bypassing RBAC for account-level collector rows.
- Fixing unclear navigation.
- Hiding stale or missing data.
