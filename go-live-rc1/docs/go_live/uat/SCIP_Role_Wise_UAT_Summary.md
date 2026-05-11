# SCIP Role-Wise UAT Summary

Use the detailed Batch 14 UAT scripts as the source. This summary lists the minimum signoff expectations.

## Board/CXO

- [ ] Arrival shows only Live Pulse and Narratives.
- [ ] Executive view does not expose account-level queues.
- [ ] Board-safe Narrative can be generated with lineage.
- [ ] Forecast assumptions are visible.
- [ ] No silent fallback shown as live.

## CCO/GM/AGM

- [ ] Risk & Action shows management queues.
- [ ] OD and action queues reconcile to lineaged source facts.
- [ ] Workflow assignment works for permitted rows.
- [ ] Notifications and escalations are visible for management scope.
- [ ] Audit trail is visible for owned actions.

## Finance

- [ ] Finance sees PR/TAT and finance exceptions.
- [ ] Finance cannot access collector-only workflows.
- [ ] Finance can review audit/export within permitted scope.
- [ ] MDO vs Finance labels are visible where relevant.

## MIS/QCG/Admin

- [ ] Source health, deployment health, migrations, audit exports available.
- [ ] Denied attempts are logged with correlation ID.
- [ ] Backup/restore check passes.
- [ ] Observability redaction confirmed.

## Collector/RM

- [ ] Collector sees only own rows.
- [ ] Collector can update disposition where permitted.
- [ ] Collector cannot self-assign or view other collectors' queues.
- [ ] PTP/broken-promise actions are lineaged.

## Signoff rule

Production go-live requires all roles to pass, or an executive waiver with owner, expiry date, and rollback condition.
