# SCIP Batch 14 UAT Scripts by Role

## Shared UAT prerequisites

- User is provisioned through JWT/SSO, not trusted production headers.
- Correlation ID is visible in response headers or observability events.
- No Entity Head role exists.
- Liquid Glass Arrival has only Live Pulse and Narratives.
- Data-confidence/trust state is visible after entry.
- No silent fallback numbers appear.

## Board/CXO UAT

### Scenario B1 — Arrival and executive journey
1. Open SCIP.
2. Confirm only Live Pulse and Narratives are primary choices.
3. Open Narratives.
4. Navigate Story → Portfolio → Dues → Advance → Roadmap.
5. Confirm dense tables and collector details are not exposed by default.
6. Ask Quickball to explain `PIPELINE_GROSS`.

Expected:
- Board-safe explanation appears.
- Source file/sheet/range/validation/confidence are available on evidence request.
- No account-level action queue is accessible.

### Scenario B2 — Board export readiness
1. Open Narratives → Story.
2. Trigger Present/Executive summary output.
3. Export or copy the summary if enabled.

Expected:
- Reporting basis labels remain visible.
- No raw operational clutter at executive depth.

## CCO/GM/AGM UAT

### Scenario M1 — Live Pulse risk review
1. Open Live Pulse.
2. Choose Risk & Action.
3. Open action queues.
4. Review management escalations.
5. Assign one eligible action.

Expected:
- Only permitted management/collector escalation rows are visible.
- Each action shows owner, entity, amount/status, ageing/process status, and lineage.
- Assignment event creates immutable workflow event.

### Scenario M2 — Notification review
1. Open notifications/digest output.
2. Review manager escalations.
3. Confirm duplicate notification is suppressed.

Expected:
- Notification includes source action lineage and workflow event lineage.
- Suppression/deduplication key is present.

## Finance UAT

### Scenario F1 — Finance exception queue
1. Open Live Pulse → Risk & Action.
2. Open Finance queue.
3. Review PR/TAT ageing and PR exception nudges.
4. Attempt to access collector-only workflow.

Expected:
- Finance rows are visible.
- Collector-only rows are denied.
- Denied attempt is audit-logged with correlation ID.

### Scenario F2 — Audit export
1. Export audit pack in CSV and JSON if role permits.
2. Confirm fields include source action lineage, workflow event lineage, notification lineage, actor, timestamp, role, state, and closure/escalation evidence.

Expected:
- Export succeeds for permitted scope only.
- Export volume is logged in observability.

## MIS/QCG/Admin UAT

### Scenario A1 — Governance and health
1. Open deployment health.
2. Run migration status check.
3. Run backup/restore check.
4. Review observability alerts.
5. Review denied attempts.

Expected:
- Migration and backup results are recorded.
- Denials include actor, role, route, reason, correlation ID.
- Alerts are evidence-based.

### Scenario A2 — Identity provisioning
1. Provision a test Collector/RM with one collector scope.
2. Deactivate the user.
3. Attempt access with old token/session.

Expected:
- Active user has scoped access only.
- Deactivated user is denied.
- Identity denial is logged.

## Collector/RM UAT

### Scenario C1 — Own action queue
1. Open Live Pulse → Risk & Action.
2. Open Collector/RM queue.
3. Confirm only own assigned/scoped rows are visible.
4. Update disposition.
5. Add evidence note/attachment reference.
6. Mark promised where applicable.

Expected:
- Collector cannot self-assign.
- Collector cannot see other owners' rows.
- Disposition/evidence events retain source lineage hash.

### Scenario C2 — Blocked access
1. Attempt to open Board/CXO audit export or management-only queue.

Expected:
- Access denied.
- Denial logged with correlation ID and audit lineage.
