# SCIP Batch 9 — Governance and Smoke Checkpoints

## Governance rules

1. No notification can be emitted without source-action lineage.
2. No notification can be emitted without workflow-event lineage.
3. No notification can be emitted without role visibility.
4. No notification can be emitted without rule evidence.
5. No notification can be emitted without reporting basis and confidence state.
6. No notification can be emitted without deduplication and suppression keys.
7. Entity Head must remain removed.
8. Notifications must remain L5 output under Live Pulse / Risk & Action.
9. Digests must be evidence-driven from notification IDs.
10. Frontend must not compute notification eligibility.

## Smoke checks passed

The smoke harness validates:

- Batch 9 contract version.
- Payload status is ready.
- All six escalation rules emit at least one notification.
- Collector/RM reminders are present.
- Manager escalations are present.
- Finance nudges are present.
- MIS/QCG alerts are present.
- A bad unlineaged action is blocked.
- All notifications have source-action lineage.
- All notifications have workflow-event lineage.
- All notifications have role visibility.
- All notifications have rule evidence.
- All notifications have dedupe keys.
- Dedupe keys are unique.
- Daily digest is present.
- Weekly digest is present.
- Digests have dedupe keys.
- Notifications are L5 output.
- There is no third Arrival door.
- Entity Head remains removed.
- Backend includes notification router.
- Frontend fetches `/notifications`.
- Frontend includes notification panel and digest cards.
- Module declares no external delivery.
- Frontend contains no notification business computation.

Smoke result: `34 / 34 passed`.
