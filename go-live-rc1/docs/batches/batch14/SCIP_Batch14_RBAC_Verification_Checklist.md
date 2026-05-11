# SCIP Batch 14 RBAC Verification Checklist

## Access matrix smoke

- [ ] Board/CXO can access Narratives and executive summaries.
- [ ] Board/CXO cannot access account action queues.
- [ ] Board/CXO cannot export detailed account audit packs.
- [ ] CCO/GM/AGM can access management queues and assign permitted actions.
- [ ] Finance can access PR/TAT/finance exception queues.
- [ ] Finance cannot access collector-only workflows.
- [ ] MIS/QCG/Admin can access governance, audit, migration, backup, deployment checks.
- [ ] Collector/RM can access own rows only.
- [ ] Collector/RM cannot self-assign.
- [ ] Entity Head role claim is rejected.

## Denial audit fields

- [ ] actor ID.
- [ ] role.
- [ ] route/resource.
- [ ] permission attempted.
- [ ] reason.
- [ ] correlation ID.
- [ ] timestamp.
- [ ] audit lineage where available.
