# SCIP Batch 14 Data Cutover Checklist

## Pre-cutover

- [ ] Freeze source-report naming convention for cutover window.
- [ ] Confirm source owners for R02, R04, R08, R18, R36, R10, R17, R20, R30, R31, R32, R34, R38, R09.
- [ ] Confirm expected snapshot dates.
- [ ] Confirm entity hierarchy mapping.
- [ ] Confirm 0.05% tolerance.
- [ ] Confirm no-silent-fallback rule.

## Load sequence

1. Load critical executive sources: R18, R04, R02, R08, R36.
2. Load account/action sources: R10, R32, R34, R31, R20.
3. Load enrichment sources: R17, R09, R38, R30.
4. Run adapter success/failure metrics.
5. Run lineage coverage check.
6. Run reconciliation checks.
7. Run action-queue generation check.
8. Run workflow/notification dry-run check.

## Post-cutover

- [ ] Snapshot dates visible.
- [ ] Data-confidence trust bar green or explicitly attention-labelled.
- [ ] No unlineaged critical number displayed.
- [ ] Audit export includes cutover source load evidence.
- [ ] Observability events captured with correlation IDs.
