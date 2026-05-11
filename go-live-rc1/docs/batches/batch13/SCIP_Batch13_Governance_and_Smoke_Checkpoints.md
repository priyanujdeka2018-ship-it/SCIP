# SCIP Batch 13 Governance and Smoke Checkpoints

## Governance gates

| Gate | Requirement | Status |
|---|---|---|
| Identity default | JWT/SSO, not trusted headers | Passed |
| Local bypass | Explicit env-only local dev path | Passed |
| Role model | Board/CXO, CCO/GM/AGM, Finance, MIS/QCG/Admin, Collector/RM | Passed |
| Removed role | Entity Head rejected | Passed |
| Row visibility | Existing Batch 11 RBAC row rules preserved | Passed |
| Collector scope | Collector/RM sees only own rows | Passed |
| Denial audit | Identity/RBAC denied attempts include correlation/audit lineage | Passed |
| Redaction | Sensitive claims are not logged | Passed |
| Liquid Glass | No new L0 door or security dashboard | Passed |
| Frontend business logic | No financial/business calculation moved to client | Passed |

## Smoke checks

```text
claims_map_board_group_to_board_cxo
claims_map_direct_finance_role
collector_scope_and_mapping_loaded
admin_group_maps_to_mis_qcg_admin
collector_rm_sees_only_own_rows
finance_cannot_access_collector_only_workflows
board_cxo_cannot_access_account_queues
invalid_token_rejected
expired_token_rejected
entity_head_claim_rejected
trusted_headers_rejected_without_local_dev_bypass
deactivated_user_rejected
provisioning_summary_counts_users_and_sessions
identity_denials_include_correlation_and_audit_lineage
rbac_denials_include_correlation_and_audit_lineage
no_sensitive_email_logged
```

Result:

```text
16 / 16 passed
```

## Production deployment checklist
1. Set `SCIP_AUTH_MODE=jwt`.
2. Disable `SCIP_LOCAL_DEV_BYPASS`.
3. Configure `SCIP_JWT_ISSUER` and `SCIP_JWT_AUDIENCE`.
4. Replace local HS256 secret with IdP gateway/JWKS verification.
5. Confirm group-to-role mappings with IT/Security.
6. Confirm collector ID claim/mapping source.
7. Confirm deactivation source of truth.
8. Run Batch 11 RBAC, Batch 12 observability, and Batch 13 identity smoke suites.
9. Confirm denied attempts flow into audit export.
10. Confirm no sensitive claim values appear in logs or telemetry.
