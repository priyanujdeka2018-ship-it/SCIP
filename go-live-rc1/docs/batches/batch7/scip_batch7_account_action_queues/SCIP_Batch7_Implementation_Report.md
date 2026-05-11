# SCIP Batch 7 Implementation Report

## Purpose

Batch 7 upgrades the Batch 6 action-queue foundation from project-risk cohorts into guarded account-level queues. It onboards the newly attached R-series sources and only exposes actions where source lineage, owner mapping, entity mapping, amount/status and ageing/process validation are present.

## Source reports onboarded

| Source | Role in Batch 7 |
|---|---|
| R10 Dues Coverage | Account allocation, owner mapping, dues coverage, PTP amount/date, not-worked coverage |
| R17 SPA / Pre-registration | Project-level legal / SPA / pre-registration enrichment |
| R20 PR-to-SOA TAT | Finance/QCG process backlog by TAT bucket |
| R30 Monthly Feedback | Collector performance and activity context |
| R31 PR Unit Update | PR quality / rejected / pending finance exceptions |
| R32 RM Collectors & PRs | Collector performance and receipts context |
| R34 Termination Status | Account-level overdue, ageing bucket, termination / PDN / eligibility evidence |
| R38 Risk Analysis | CIV / paid-band project risk enrichment |
| R09 Collections | Project-level collection / overdue / MTD collection enrichment |

## Key implementation files

- `account_action_queues.py` introduces Batch 7 adapters and endpoint contract `action_queues.v2.batch7`.
- `main.py` is upgraded to `v8.7 Batch 7`.
- `App.jsx` renders account action cards, process actions, management actions and detailed evidence rows inside Live Pulse -> Risk & Action.
- `liquidGlassTokens.css` adds solid truth account-action cards inside the Liquid Glass flow.
- `pipeline_config.json` records the Batch 7 source/contract metadata.

## Account action gate

No account-level action is returned unless it has:

```text
account_id + unit + collector/RM owner + entity mapping + amount/status + ageing/process status + lineage
```

Collector/RM actions are generated from the safe join:

```text
R10 PTP Data + R34 Termination Status / ageing + R10 Allocation owner mapping
```

Finance actions are generated from:

```text
R31 PR Unit Update + R20 PR-to-SOA TAT
```

Management / MIS actions are enriched with:

```text
R30, R32, R17, R09, R38
```

## Batch 7 extraction result from uploaded samples

| Fact group | Count |
|---|---:|
| R10 allocation facts | 18,241 |
| R10 PTP facts | 364 |
| R34 termination / ageing facts | 27,890 |
| R31 PR issues | 1,151 |
| R32 collector metrics | 126 |
| R30 collector feedback facts | 26 |
| R17 SPA project facts | 182 |
| R09 project collection facts | 186 |
| R20 TAT facts | 60 |
| R38 risk facts | 4,261 |
| Collector account actions ready | 40 |
| Termination review actions ready | 40 |
| Finance PR actions ready | 40 |
| Process actions ready | 22 |

## Liquid Glass preservation

Batch 7 does not add a new homepage, new sidebar, or a third entry door. Action queues remain an L5 action output under Live Pulse -> Risk & Action. Dense tables and collector evidence use solid surfaces, while glass remains reserved for navigation, command, context and reveal.

## Limitations and intentional safeguards

- R17, R09 and R38 are used as project/legal/risk enrichment, not as owner sources.
- R32 provides collector performance and receipt context, but the safe account-action join is still anchored by R10 + R34.
- The payload returns top guarded queues, not every possible raw record, to keep UI response size reasonable.
- No frontend business computation was introduced.
