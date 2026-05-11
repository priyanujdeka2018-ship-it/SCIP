# SCIP Migration Order

Apply migrations in the following order in staging, then production after backup.

```text
001_batch10_persistence.sql
002_batch11_rbac_hardening.sql
003_batch12_observability.sql
004_batch13_identity_provisioning.sql
005_batch15_adoption_analytics.sql
006_batch16_continuous_improvement.sql
007_batch17_roadmap_exec_rhythm.sql
```

## Pre-migration checks

- [ ] Database URL points to staging first.
- [ ] Backup completed.
- [ ] Migration user has create/alter/index/trigger rights.
- [ ] Migration lock is available.
- [ ] Rollback/restore path tested.

## Post-migration checks

```sql
select table_name
from information_schema.tables
where table_schema = 'public'
order by table_name;
```

Required table groups:

```text
source actions
workflow records and events
notification eligibility/emissions/suppression/delivery
audit exports
actors, policies, denials
migration history, backup checks, deployment health
observability events and frontend performance events
provisioned users/groups/roles/scopes/collector mappings
adoption analytics
continuous improvement governance
roadmap and executive rhythm
```
