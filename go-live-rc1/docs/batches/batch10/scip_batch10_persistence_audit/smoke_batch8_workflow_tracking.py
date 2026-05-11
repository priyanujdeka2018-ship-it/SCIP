from __future__ import annotations

import json
from pathlib import Path

import workflow

OUT = Path(__file__).with_name("smoke_batch8_workflow_results.json")

results = {"checks": {}, "failures": []}


def check(name, condition, detail=None):
    results["checks"][name] = bool(condition)
    if not condition:
        results["failures"].append({"check": name, "detail": detail})


workflow.reset_workflow_store()
payload = workflow.seed_workflows(force=True)
records = payload["records"]
summary = payload["summary"]

check("workflow_payload_ready", payload["status"] == "ready_workflow_tracking_guarded", payload.get("status"))
check("all_required_states_present", set(["queued", "assigned", "in_progress", "promised", "escalated", "closed", "stale", "blocked"]).issubset(set(payload["workflow_states"])))
check("records_generated", summary["workflow_count"] > 0, summary)
check("seed_events_generated", summary["event_count"] >= summary["workflow_count"], summary)
check("all_records_lineaged", payload["validations"]["checks"].get("all_records_have_immutable_lineage"), payload["validations"])
check("all_events_lineaged", payload["validations"]["checks"].get("all_events_have_immutable_lineage_hash"), payload["validations"])
check("entity_head_removed", payload["validations"]["checks"].get("entity_head_removed"), payload["validations"])

# Select an assignable collector action visible to CCO/GM/AGM.
collector_record = next((r for r in workflow.WORKFLOW_STORE.values() if r["workflow_state"] == "queued" and "collector_rm" in r.get("role_visibility", [])), None)
check("collector_workflow_record_found", collector_record is not None)

if collector_record:
    action_id = collector_record["source_action_id"]
    before_hash = collector_record["lineage_hash"]
    assign = workflow.assign_action(action_id, assignee="Farheen", actor="Head Collections", actor_role="cco_gm_agm", due_date="2026-05-14", note="Batch 8 smoke assignment")
    check("assign_action_succeeds_for_manager", assign["record"]["workflow_state"] == "assigned", assign)
    due = workflow.set_due_date(action_id, due_date="2026-05-15", actor="Head Collections", actor_role="cco_gm_agm")
    check("due_date_update_succeeds", due["record"]["due_date"] == "2026-05-15", due)
    disp = workflow.update_disposition(action_id, disposition="Customer contacted; committed to payment confirmation", actor="Farheen", actor_role="collector_rm", next_state="promised")
    check("collector_can_update_visible_disposition", disp["record"]["workflow_state"] == "promised", disp)
    ev = workflow.attach_evidence(action_id, evidence_type="call_note", evidence_ref="CALL-20260509-001", actor="Farheen", actor_role="collector_rm", note="Customer call evidence")
    check("evidence_attachment_succeeds", len(ev["record"].get("evidence_attachments", [])) >= 1, ev)
    closed = workflow.close_action(action_id, closure_reason="Payment commitment captured and sent for finance verification", actor="Head Collections", actor_role="cco_gm_agm", evidence_ref="CALL-20260509-001")
    check("close_action_succeeds_with_reason", closed["record"]["workflow_state"] == "closed" and closed["record"].get("closure_reason"), closed)
    after_hash = workflow.WORKFLOW_STORE[action_id]["lineage_hash"]
    check("source_lineage_hash_immutable_after_workflow", before_hash == after_hash, {"before": before_hash, "after": after_hash})
    event_types = [e["event_type"] for e in workflow.EVENT_LOG if e["source_action_id"] == action_id]
    check("event_log_records_assignment_lifecycle", set(["queued", "assigned", "due_date_set", "disposition_updated", "evidence_attached", "closed"]).issubset(set(event_types)), event_types)

# Negative: finance cannot assign collector action.
if collector_record:
    second = next((r for r in workflow.WORKFLOW_STORE.values() if r["workflow_state"] == "queued" and "collector_rm" in r.get("role_visibility", [])), None)
    if second:
        try:
            workflow.assign_action(second["source_action_id"], assignee="Finance User", actor="Finance", actor_role="finance")
            check("finance_cannot_assign_collector_action", False, "assignment unexpectedly succeeded")
        except Exception as exc:
            check("finance_cannot_assign_collector_action", "role_not_visible" in str(exc) or "role_not_allowed" in str(exc), str(exc))

# Negative: collector cannot assign, even if visible.
third = next((r for r in workflow.WORKFLOW_STORE.values() if r["workflow_state"] == "queued" and "collector_rm" in r.get("role_visibility", [])), None)
if third:
    try:
        workflow.assign_action(third["source_action_id"], assignee="Self", actor="Collector", actor_role="collector_rm")
        check("collector_cannot_self_assign", False, "self-assignment unexpectedly succeeded")
    except Exception as exc:
        check("collector_cannot_self_assign", "role_not_allowed" in str(exc), str(exc))

# Negative: unlineaged record cannot be assigned.
bad_action_id = "bad::missing_lineage"
workflow.WORKFLOW_STORE[bad_action_id] = {
    "workflow_id": "wf::bad_missing_lineage",
    "source_action_id": bad_action_id,
    "title": "Bad unlineaged action",
    "role_visibility": ["cco_gm_agm"],
    "workflow_state": "blocked",
    "assigned_owner": "Unknown",
    "source_snapshot": {
        "account_id": "A-1",
        "unit": "U-1",
        "collector_rm_owner": "Owner",
        "entity_code": "sobha_dubai",
        "entity_display": "Sobha Dubai",
        "amount_aed": 1000,
        "ageing_bucket": "31-60",
        "reporting_basis": "test",
        "confidence_state": "test",
    },
    "immutable_lineage_refs": [],
    "lineage_hash": "",
    "source_gate": {"assignable": False, "failures": ["missing_or_incomplete_source_lineage"]},
}
try:
    workflow.assign_action(bad_action_id, assignee="Owner", actor="Manager", actor_role="cco_gm_agm")
    check("unlineaged_action_assignment_blocked", False, "unlineaged assignment unexpectedly succeeded")
except Exception as exc:
    check("unlineaged_action_assignment_blocked", "cannot_assign_terminal_or_blocked_action" in str(exc) or "cannot_assign_untrusted_source_action" in str(exc), str(exc))

# Negative: closure reason required.
fourth = next((r for r in workflow.WORKFLOW_STORE.values() if r["workflow_state"] == "queued" and "cco_gm_agm" in r.get("role_visibility", [])), None)
if fourth:
    try:
        workflow.close_action(fourth["source_action_id"], closure_reason="", actor="Head", actor_role="cco_gm_agm")
        check("closure_reason_required", False, "closure without reason unexpectedly succeeded")
    except Exception as exc:
        check("closure_reason_required", "closure_reason_required" in str(exc), str(exc))

# Frontend static contract checks.
app = Path(__file__).with_name("App.jsx").read_text(encoding="utf-8")
check("frontend_fetches_workflows", "fetch(`${BACKEND_URL}/workflows`)" in app)
check("frontend_has_workflow_drawer", "function WorkflowDrawer" in app and "solid evidence timeline" in app.lower())
check("frontend_no_business_computation_keywords", "amount_aed +" not in app and ".reduce((" not in app)
check("frontend_labels_batch8", "SCIP Batch 8" in app)

# Backend/static contract checks.
main = Path(__file__).with_name("main.py").read_text(encoding="utf-8")
check("main_includes_workflow_router", "from workflow import router as workflow_router" in main and "app.include_router(workflow_router)" in main)
check("workflow_contract_routes_present", all(token in Path(__file__).with_name("workflow.py").read_text(encoding="utf-8") for token in ["/assign", "/reassign", "/due-date", "/disposition", "/evidence", "/close"]))

final_payload = workflow.build_workflow_payload()
Path(__file__).with_name("workflow_sample_payload_batch8.json").write_text(json.dumps(final_payload, indent=2, default=str), encoding="utf-8")

results["overall_passed"] = all(results["checks"].values())
results["summary"] = final_payload["summary"]
results["sample_record_count"] = len(final_payload["records"])
results["sample_event_count"] = len(final_payload["event_log"])
OUT.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
print(json.dumps(results, indent=2, default=str))
