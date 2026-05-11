# SCIP Batch 17 — Release Train Model

## Cadence
monthly_standard_release_with_weekly_hotfix_window

## Release naming
SCIP YYYY.MM train, e.g., SCIP 2026.06

## Standard stages
- intake
- evidence_check
- change_control
- build
- validation
- UAT
- release_notes
- production_smoke
- post_release_review

## Hotfix rule
Only source trust, identity/security, audit, or production-blocking defects qualify for out-of-cycle hotfix.

## Rollback rule
Every release must carry rollback criteria, data rollback plan, and user-visible release note if metric meaning changes.

## Liquid Glass guardrail
No release may add a third Arrival door, expose raw section tree early, or turn governance into dashboard-first UI.
