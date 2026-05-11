# SCIP Batch 14 Source Refresh Checklist

## Daily refresh checks

- [ ] R04 daily collections uploaded and validated.
- [ ] R02 MDO target workbook is current for active month.
- [ ] R18 OD/ageing snapshot is current.
- [ ] R08 advance summary is current for latest YTD/NPV position.
- [ ] R36 milestone cohort is current for forward calendar.
- [ ] R10/R32/R34/R31/R20 action sources are current before action queues are refreshed.

## Refresh validation

- [ ] File resolver maps each source to correct R-code.
- [ ] Adapter emits snapshot date.
- [ ] Adapter emits lineage for every critical metric/fact.
- [ ] Reconciliation within 0.05% or blocked.
- [ ] Cache invalidated when source snapshot date changes.
- [ ] No previous-source fallback shown as live.

## Stale-source handling

- [ ] Stale source is marked attention/risk.
- [ ] Board/CXO view uses unavailable/stale label, not hidden fallback.
- [ ] MIS/QCG/Admin receives governance alert.
- [ ] Source owner is named.
