# SCIP Merge Order and File Map

## Primary code baseline

Use **Batch 13** as the primary code baseline because it already contains the cumulative production layers through identity/SSO:

- core backend routers and services
- durable persistence and audit
- workflow tracking
- notifications/escalations
- RBAC hardening
- observability/performance
- SSO/JWT identity and provisioning
- frontend Liquid Glass shell

## Overlay governance files

Overlay Batch 14 documents and smoke runner:

```text
rollout/
uat/
checklists/
signoff/
smoke/deployment_smoke_runner.py
smoke/final_deployment_smoke_manifest_batch14.json
rollout_uat.py
```

Overlay Batch 17 executive operating files:

```text
roadmap/
cadence/
okr/
ownership/
release_train/
benefits/
steering/
roadmap.py
migrations/007_batch17_roadmap_exec_rhythm.sql
```

## Conflict rules

If files conflict:

| File | Winner | Reason |
|---|---|---|
| `main.py` | Batch 13 plus manually add Batch 14 `rollout_uat` router and Batch 17 `roadmap` router | Batch 13 is latest security baseline; Batch 14/17 add read-only governance routers. |
| `App.jsx` | Batch 13 unless Batch 17 adds necessary read-only governance links | Avoid reintroducing dashboard-first surfaces. |
| `auth.py` | Batch 13 | Contains JWT/SSO identity handoff and RBAC. |
| `identity.py` | Batch 13 | Contains provisioning model. |
| `observability.py` | Batch 13 | Contains correlation/redaction. |
| `liquidGlassTokens.css` | Batch 13 unless later Liquid Glass-only tokens are intentionally added | Preserve two-door UI. |
| migrations | Apply all 001-007 in order | Later migrations depend on previous tables. |

## Do not merge as top-level navigation

Do not add these as L0 Arrival doors:

- Observability
- Governance
- Roadmap
- Audit
- Workflow
- Notifications
- UAT

They remain L5 outputs/governance/evidence.
