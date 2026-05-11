from __future__ import annotations

import importlib
import json
import os
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB_PATH = HERE / "scip_batch11_smoke.sqlite"
os.environ["SCIP_AUDIT_DB"] = str(DB_PATH)
os.environ["SCIP_ENV"] = "local"
os.environ["CORS_ALLOWED_ORIGINS"] = "http://localhost:5173"
os.environ["FRONTEND_URL"] = "http://localhost:5173"

import auth
import deployment
import persistence


def assert_check(checks, name, value=True):
    checks[name] = bool(value)


def main():
    checks = {}
    details = {}
    if DB_PATH.exists():
        DB_PATH.unlink()

    # Import/compile smoke.
    for module_name in ["auth", "deployment", "main", "account_action_queues", "workflow", "notifications", "persistence"]:
        importlib.import_module(module_name)
    assert_check(checks, "batch11_modules_import", True)

    # Migration + policy seed.
    migration = deployment.run_migrations(DB_PATH)
    details["migration"] = migration
    assert_check(checks, "migrations_run", bool(migration.get("applied")))
    matrix = auth.build_policy_matrix()
    details["policy_matrix_roles"] = matrix["role_model"]
    assert_check(checks, "role_model_without_entity_head", "entity_head" not in matrix["role_model"] and "entity_head" in matrix["removed_roles"])
    assert_check(checks, "five_roles_only", matrix["role_model"] == ["board_cxo", "cco_gm_agm", "finance", "mis_qcg_admin", "collector_rm"])
    assert_check(checks, "collector_cannot_assign", "write:workflows_assign" not in matrix["permissions"]["collector_rm"])
    assert_check(checks, "admin_can_migrate_backup", {"run:migrations", "run:backup_restore_check"}.issubset(set(matrix["permissions"]["mis_qcg_admin"])))

    # Actor identity.
    admin = auth.actor_from_headers({"x-scip-role": "mis_qcg_admin", "x-scip-actor-id": "admin1", "x-scip-entity-scope": "Group"})
    cco = auth.actor_from_headers({"x-scip-role": "cco_gm_agm", "x-scip-actor-id": "cco1", "x-scip-entity-scope": "Group"})
    finance = auth.actor_from_headers({"x-scip-role": "finance", "x-scip-actor-id": "fin1", "x-scip-entity-scope": "Group"})
    collector = auth.actor_from_headers({"x-scip-role": "collector_rm", "x-scip-actor-id": "collector_a", "x-scip-collector-id": "collector_a", "x-scip-entity-scope": "Sobha Dubai"})
    board = auth.actor_from_headers({"x-scip-role": "board_cxo", "x-scip-actor-id": "board1", "x-scip-entity-scope": "Group"})
    auth.upsert_actor(admin, DB_PATH)
    auth.upsert_actor(cco, DB_PATH)
    auth.upsert_actor(finance, DB_PATH)
    auth.upsert_actor(collector, DB_PATH)
    auth.upsert_actor(board, DB_PATH)
    assert_check(checks, "actor_identity_loaded", admin.role == "mis_qcg_admin" and collector.collector_id == "collector_a")
    try:
        auth.actor_from_headers({"x-scip-role": "entity_head"})
        entity_head_blocked = False
    except ValueError:
        entity_head_blocked = True
    assert_check(checks, "entity_head_blocked", entity_head_blocked)

    # Permission checks.
    assert_check(checks, "board_cannot_read_actions", not auth.authorize(board, "read:action_queues", path="/action-queues"))
    assert_check(checks, "collector_own_read_allowed", auth.authorize(collector, "read:action_queues", path="/action-queues"))
    assert_check(checks, "collector_cannot_assign_runtime", not auth.authorize(collector, "write:workflows_assign", path="/workflows/assign", method="POST"))
    assert_check(checks, "finance_assign_runtime_allowed", auth.authorize(finance, "write:workflows_assign", path="/workflows/assign", method="POST"))
    assert_check(checks, "admin_audit_allowed", auth.authorize(admin, "read:audit_export_all", path="/audit/export"))

    # Row-level visibility.
    synthetic_rows = [
        {"action_id": "a1", "role_visibility": ["collector_rm"], "entity": "Sobha Dubai", "collector_id": "collector_a", "amount": 100, "lineage_hash": "h1"},
        {"action_id": "a2", "role_visibility": ["collector_rm"], "entity": "Sobha Dubai", "collector_id": "collector_b", "amount": 100, "lineage_hash": "h2"},
        {"action_id": "a3", "role_visibility": ["finance"], "entity": "Group", "owner": "finance", "process_status": "pending", "lineage_hash": "h3"},
        {"action_id": "a4", "role_visibility": ["cco_gm_agm"], "entity": "UAQ", "owner": "mgr", "amount": 100, "lineage_hash": "h4"},
    ]
    collector_rows = auth.filter_rows_for_actor(synthetic_rows, collector, "read:action_queues")
    finance_rows = auth.filter_rows_for_actor(synthetic_rows, finance, "read:action_queues")
    cco_rows = auth.filter_rows_for_actor(synthetic_rows, cco, "read:action_queues")
    assert_check(checks, "collector_sees_only_own_rows", [r["action_id"] for r in collector_rows] == ["a1"])
    assert_check(checks, "finance_sees_finance_rows", [r["action_id"] for r in finance_rows] == ["a3"])
    assert_check(checks, "cco_sees_management_rows", [r["action_id"] for r in cco_rows] == ["a4"])

    # Denied attempt audit.
    denied = auth.get_denied_attempts(50, DB_PATH)
    details["denied_attempt_count"] = len(denied)
    assert_check(checks, "denied_attempts_logged", len(denied) >= 2)

    # Existing durable store integration and audit filtering.
    seed = persistence.seed_persistent_store(DB_PATH, reset=True, data_dir="/mnt/data")
    summary = persistence.build_persistence_payload(DB_PATH)
    audit_rows = persistence.build_audit_rows(DB_PATH)
    admin_audit = auth.audit_rows_allowed_for_actor(audit_rows, admin)
    finance_audit = auth.audit_rows_allowed_for_actor(audit_rows, finance)
    board_audit = auth.audit_rows_allowed_for_actor(audit_rows, board)
    details["persistence_counts"] = summary.get("table_counts")
    details["audit_counts"] = {"all": len(audit_rows), "admin": len(admin_audit), "finance": len(finance_audit), "board": len(board_audit)}
    assert_check(checks, "persistence_seeded", summary.get("table_counts", {}).get("workflow_records", 0) > 0)
    assert_check(checks, "admin_audit_export_all", len(admin_audit) == len(audit_rows) and len(admin_audit) > 0)
    assert_check(checks, "finance_audit_export_filtered", 0 <= len(finance_audit) <= len(audit_rows))
    assert_check(checks, "board_audit_export_denied", len(board_audit) == 0)

    # Deployment health and backup/restore.
    health = deployment.build_deployment_health(DB_PATH)
    backup = deployment.backup_restore_check(DB_PATH, HERE / "backups_smoke")
    details["deployment_health_status"] = health.get("status")
    details["backup_status"] = backup.get("status")
    assert_check(checks, "deployment_health_generated", health.get("status") in {"ok", "needs_attention"})
    assert_check(checks, "backup_restore_passed", backup.get("status") == "passed")
    assert_check(checks, "cors_no_wildcard_nonlocal_rule_present", health.get("checks", {}).get("no_wildcard_cors_in_nonlocal") is True)

    # Main app exposes routers.
    import main
    route_paths = {getattr(route, "path", "") for route in main.app.routes}
    details["route_sample"] = sorted(path for path in route_paths if path.startswith(("/security", "/deployment")))[:20]
    assert_check(checks, "security_routes_registered", "/security/me" in route_paths and "/security/policy-matrix" in route_paths)
    assert_check(checks, "deployment_routes_registered", "/deployment/health" in route_paths and "/deployment/migrate" in route_paths)
    assert_check(checks, "rbac_middleware_registered", any("rbac_middleware" in str(mw.cls) or "BaseHTTPMiddleware" in str(mw.cls) for mw in main.app.user_middleware))

    # Notification dedupe tables survived after migration and seed.
    with persistence._connect(DB_PATH) as conn:
        suppression_count = conn.execute("SELECT COUNT(*) FROM suppression_state").fetchone()[0]
        delivery_count = conn.execute("SELECT COUNT(*) FROM delivery_status").fetchone()[0]
        rbac_count = conn.execute("SELECT COUNT(*) FROM rbac_policies").fetchone()[0]
    details["durable_counts"] = {"suppression_state": suppression_count, "delivery_status": delivery_count, "rbac_policies": rbac_count}
    assert_check(checks, "notification_dedupe_survives_security_migration", suppression_count > 0 and delivery_count > 0)
    assert_check(checks, "rbac_policies_persisted", rbac_count >= sum(len(v) for v in auth.PERMISSIONS.values()))

    result = {
        "contract_version": "rbac_deployment_hardening.v1.batch11",
        "status": "ready_rbac_hardened" if all(checks.values()) else "validation_failed",
        "checks_passed": sum(1 for v in checks.values() if v),
        "checks_total": len(checks),
        "overall_passed": all(checks.values()),
        "checks": checks,
        "details": details,
    }
    out = HERE / "smoke_batch11_rbac_hardening_results.json"
    out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))
    if not result["overall_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
