# SCIP Batch 14 Identity Provisioning Checklist

## Required identity attributes

- [ ] `sub` / user ID.
- [ ] display name.
- [ ] email or enterprise username.
- [ ] role/group claim mapped to one of: Board/CXO, CCO/GM/AGM, Finance, MIS/QCG/Admin, Collector/RM.
- [ ] entity scope where applicable.
- [ ] collector/RM scope where applicable.
- [ ] active/deactivated status.

## Provisioning checks

- [ ] Board/CXO has no account-queue permission.
- [ ] CCO/GM/AGM has management/assignment scope.
- [ ] Finance has finance exception scope and finance audit scope.
- [ ] MIS/QCG/Admin has deployment, provisioning, audit, migration, and governance scope.
- [ ] Collector/RM has only own collector rows.
- [ ] Entity Head is not provisionable.

## Deprovisioning checks

- [ ] Deactivated user rejected.
- [ ] Group removal reflected in role mapping.
- [ ] Existing sessions expire or are invalidated per policy.
- [ ] Denial event logged with correlation ID.
