from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from pathlib import Path

# Environment must be set before importing Batch 13 modules because they read defaults at import.
tmp = tempfile.TemporaryDirectory()
DB_PATH = Path(tmp.name) / "batch13_identity.sqlite"
os.environ["SCIP_AUDIT_DB"] = str(DB_PATH)
os.environ["SCIP_AUTH_MODE"] = "jwt"
os.environ["SCIP_LOCAL_DEV_BYPASS"] = "false"
os.environ["SCIP_JWT_SECRET"] = "batch13-smoke-secret"
os.environ["SCIP_JWT_ISSUER"] = "https://identity.sobha.example/scip"
os.environ["SCIP_JWT_AUDIENCE"] = "scip-platform"
os.environ["SCIP_CORRELATION_ID"] = "scip-smoke-batch13"

import auth  # noqa: E402
import identity  # noqa: E402

# Align already-imported module constants for deterministic smoke execution.
identity.DEFAULT_DB_PATH = DB_PATH
identity.DEFAULT_JWT_SECRET = os.environ["SCIP_JWT_SECRET"]
identity.DEFAULT_JWT_ISSUER = os.environ["SCIP_JWT_ISSUER"]
identity.DEFAULT_JWT_AUDIENCE = os.environ["SCIP_JWT_AUDIENCE"]
identity.AUTH_MODE = "jwt"
identity.LOCAL_DEV_BYPASS = False
auth.DEFAULT_DB_PATH = DB_PATH

def check(name, condition, details=None):
    results.append({"name": name, "passed": bool(condition), "details": details or {}})
    if not condition:
        raise AssertionError(name)


def bearer(token):
    return {"authorization": f"Bearer {token}", "x-scip-correlation-id": "scip-smoke-batch13"}


results = []

board_token = identity.create_test_jwt({"sub": "u-board", "name": "Board User", "groups": ["scip-board"], "scip_entity_scope": ["Group"]}, secret=os.environ["SCIP_JWT_SECRET"])
collector_token = identity.create_test_jwt({"sub": "u-coll", "name": "Collector User", "groups": ["scip-collector-rm"], "scip_entity_scope": ["Sobha Dubai"], "scip_collector_id": "C123"}, secret=os.environ["SCIP_JWT_SECRET"])
finance_token = identity.create_test_jwt({"sub": "u-fin", "name": "Finance User", "scip_role": "finance", "scip_entity_scope": ["Group"]}, secret=os.environ["SCIP_JWT_SECRET"])
admin_token = identity.create_test_jwt({"sub": "u-admin", "name": "Admin User", "groups": ["scip-admin"], "scip_entity_scope": ["Group"]}, secret=os.environ["SCIP_JWT_SECRET"])

board = identity.actor_from_request_headers(bearer(board_token), path="/security/me", method="GET", db_path=DB_PATH)
collector = identity.actor_from_request_headers(bearer(collector_token), path="/action-queues", method="GET", db_path=DB_PATH)
finance = identity.actor_from_request_headers(bearer(finance_token), path="/workflows", method="GET", db_path=DB_PATH)
admin = identity.actor_from_request_headers(bearer(admin_token), path="/identity/provisioning", method="GET", db_path=DB_PATH)

check("claims_map_board_group_to_board_cxo", board.role == "board_cxo", board.to_dict())
check("claims_map_direct_finance_role", finance.role == "finance", finance.to_dict())
check("collector_scope_and_mapping_loaded", collector.role == "collector_rm" and collector.collector_id == "C123" and collector.entity_scope == ["Sobha Dubai"], collector.to_dict())
check("admin_group_maps_to_mis_qcg_admin", admin.role == "mis_qcg_admin", admin.to_dict())

own_row = {"role_visibility": ["collector_rm"], "entity": "Sobha Dubai", "collector_id": "C123", "amount": 1000, "source_lineage": {"lineage_hash": "abc"}}
other_row = {"role_visibility": ["collector_rm"], "entity": "Sobha Dubai", "collector_id": "C999", "amount": 1000, "source_lineage": {"lineage_hash": "abc"}}
finance_denied_row = {"role_visibility": ["collector_rm"], "entity": "Group", "collector_id": "C123", "source_lineage": {"lineage_hash": "abc"}}
check("collector_rm_sees_only_own_rows", auth.row_visible_to_actor(own_row, collector, "read:action_queues") and not auth.row_visible_to_actor(other_row, collector, "read:action_queues"))
check("finance_cannot_access_collector_only_workflows", not auth.row_visible_to_actor(finance_denied_row, finance, "read:workflows"))

board_can_action_queue = auth.authorize(board, "read:action_queues", path="/action-queues", method="GET", row_context={"correlation_id": "scip-smoke-batch13"})
check("board_cxo_cannot_access_account_queues", board_can_action_queue is False)

# Invalid/expired/entity-head/local-header failure cases must be rejected and audited.
try:
    identity.actor_from_request_headers({"authorization": "Bearer " + board_token[:-2] + "xx", "x-scip-correlation-id": "scip-smoke-batch13"}, path="/security/me", method="GET", db_path=DB_PATH)
    invalid_rejected = False
except Exception:
    invalid_rejected = True
check("invalid_token_rejected", invalid_rejected)

expired_token = identity.create_test_jwt({"sub": "u-exp", "name": "Expired User", "groups": ["scip-board"]}, secret=os.environ["SCIP_JWT_SECRET"], lifetime_seconds=-5)
try:
    identity.actor_from_request_headers(bearer(expired_token), path="/security/me", method="GET", db_path=DB_PATH)
    expired_rejected = False
except Exception:
    expired_rejected = True
check("expired_token_rejected", expired_rejected)

entity_head_token = identity.create_test_jwt({"sub": "u-eh", "name": "Removed Role", "scip_role": "entity_head"}, secret=os.environ["SCIP_JWT_SECRET"])
try:
    identity.actor_from_request_headers(bearer(entity_head_token), path="/security/me", method="GET", db_path=DB_PATH)
    removed_role_rejected = False
except Exception:
    removed_role_rejected = True
check("entity_head_claim_rejected", removed_role_rejected)

try:
    identity.actor_from_request_headers({"x-scip-role": "mis_qcg_admin", "x-scip-actor-id": "header-admin"}, path="/security/me", method="GET", db_path=DB_PATH)
    header_rejected = False
except Exception:
    header_rejected = True
check("trusted_headers_rejected_without_local_dev_bypass", header_rejected)

# Deactivation blocks subsequent token use.
identity.deactivate_user("u-coll", "smoke_deactivation", db_path=DB_PATH)
try:
    identity.actor_from_request_headers(bearer(collector_token), path="/action-queues", method="GET", db_path=DB_PATH)
    deactivated_rejected = False
except Exception:
    deactivated_rejected = True
check("deactivated_user_rejected", deactivated_rejected)

summary = identity.provisioning_summary(DB_PATH)
check("provisioning_summary_counts_users_and_sessions", summary["counts"]["users"] >= 3 and summary["counts"]["sessions"] >= 4, summary["counts"])

with sqlite3.connect(DB_PATH) as conn:
    conn.row_factory = sqlite3.Row
    identity_denials = [dict(r) for r in conn.execute("SELECT * FROM identity_denials").fetchall()]
    access_denials = [dict(r) for r in conn.execute("SELECT * FROM access_denials").fetchall()]

check("identity_denials_include_correlation_and_audit_lineage", all(r.get("correlation_id") and json.loads(r["audit_lineage_json"]).get("contract_version") for r in identity_denials), {"count": len(identity_denials)})
check("rbac_denials_include_correlation_and_audit_lineage", all(json.loads(r["row_context_json"]).get("correlation_id") and json.loads(r["row_context_json"]).get("audit_lineage") for r in access_denials), {"count": len(access_denials)})
check("no_sensitive_email_logged", not any("@" in json.dumps(r).lower() for r in identity_denials + access_denials))

output = {
    "contract_version": identity.IDENTITY_CONTRACT_VERSION,
    "overall_passed": all(r["passed"] for r in results),
    "checks_passed": sum(1 for r in results if r["passed"]),
    "checks_total": len(results),
    "db_path": str(DB_PATH),
    "actors": {
        "board": board.to_dict(),
        "collector": collector.to_dict(),
        "finance": finance.to_dict(),
        "admin": admin.to_dict(),
    },
    "identity_denials_count": len(identity_denials),
    "access_denials_count": len(access_denials),
    "provisioning_summary": summary,
    "results": results,
}
print(json.dumps(output, indent=2, sort_keys=True, default=str))
