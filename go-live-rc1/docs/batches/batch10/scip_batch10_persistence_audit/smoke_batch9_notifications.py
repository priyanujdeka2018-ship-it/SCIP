from __future__ import annotations

import json
from pathlib import Path

import notifications
import workflow

DATA_DIR = Path('/mnt/data')
OUT_DIR = Path(__file__).resolve().parent


def pick_record(predicate):
    for record in workflow.WORKFLOW_STORE.values():
        if predicate(record):
            return record
    raise AssertionError('required record not found')


def prepare_demo_workflows():
    workflow.reset_workflow_store()
    workflow.seed_workflows(data_dir=DATA_DIR, force=True)

    collector_1 = pick_record(lambda r: r.get('workflow_state') == 'queued' and 'collector_rm' in (r.get('role_visibility') or []))
    workflow.assign_action(collector_1['source_action_id'], collector_1.get('assigned_owner') or 'RM Owner', 'batch9_smoke_manager', 'cco_gm_agm', due_date='2026-05-01', note='Batch 9 overdue due-date seed')

    collector_2 = pick_record(lambda r: r.get('source_action_id') != collector_1.get('source_action_id') and r.get('workflow_state') == 'queued' and 'collector_rm' in (r.get('role_visibility') or []))
    workflow.mark_stale(collector_2['source_action_id'], 'Batch 9 stale workflow seed', 'batch9_smoke_manager', 'cco_gm_agm')

    collector_3 = pick_record(lambda r: r.get('source_action_id') not in {collector_1.get('source_action_id'), collector_2.get('source_action_id')} and r.get('workflow_state') == 'queued' and 'collector_rm' in (r.get('role_visibility') or []))
    collector_3['assigned_owner'] = None
    workflow._append_event(collector_3, 'owner_removed_for_unassigned_high_risk_smoke', 'system', 'batch9_smoke', collector_3['workflow_state'], collector_3['workflow_state'], {'reason': 'Batch 9 unassigned high-risk seed'})

    # Add a deliberately bad triggered record to prove notification emission is blocked.
    bad = dict(collector_3)
    bad['source_action_id'] = 'bad_unlineaged_action_for_batch9_smoke'
    bad['workflow_id'] = 'wf::bad_unlineaged_action_for_batch9_smoke'
    bad['assigned_owner'] = None
    bad['due_date'] = '2026-05-01'
    bad['immutable_lineage_refs'] = []
    bad['lineage_hash'] = None
    bad['source_gate'] = {'assignable': False, 'failures': ['missing_source_action_lineage']}
    bad['role_visibility'] = ['collector_rm', 'cco_gm_agm']
    workflow.WORKFLOW_STORE[bad['source_action_id']] = bad
    workflow.EVENT_LOG.append({
        'event_id': 'evt_bad_unlineaged_batch9',
        'workflow_id': bad['workflow_id'],
        'source_action_id': bad['source_action_id'],
        'event_type': 'queued',
        'actor_role': 'system',
        'actor': 'batch9_smoke',
        'from_state': 'none',
        'to_state': 'queued',
        'event_payload': {'reason': 'bad smoke record'},
        'immutable_lineage_refs': [],
        'lineage_hash': None,
        'created_at': '2026-05-09T00:00:00Z',
    })


def main():
    prepare_demo_workflows()
    payload = notifications.build_notifications_payload(as_of_date='2026-05-09', data_dir=str(DATA_DIR))
    (OUT_DIR / 'notifications_sample_payload_batch9.json').write_text(json.dumps(payload, indent=2, default=str), encoding='utf-8')

    rules = payload['summary']['by_rule']
    notifications_list = payload['notifications']
    ids = {n.get('source_action_id') for n in notifications_list}

    checks = {
        'payload_status_ready': payload.get('status') == 'ready_notifications_guarded',
        'contract_version_batch9': payload.get('contract_version') == 'notifications.v1.batch9',
        'has_notifications': payload['summary']['notification_count'] > 0,
        'overdue_due_date_rule_emitted': rules.get('overdue_due_date', 0) > 0,
        'stale_workflow_rule_emitted': rules.get('stale_workflow', 0) > 0,
        'broken_ptp_rule_emitted': rules.get('broken_ptp_promise', 0) > 0,
        'termination_risk_rule_emitted': rules.get('termination_risk', 0) > 0,
        'pr_tat_ageing_rule_emitted': rules.get('pr_tat_ageing', 0) > 0,
        'unassigned_high_risk_rule_emitted': rules.get('unassigned_high_risk', 0) > 0,
        'collector_rm_reminders_present': payload['summary']['by_role'].get('collector_rm', 0) > 0,
        'manager_escalations_present': payload['summary']['by_role'].get('cco_gm_agm', 0) > 0,
        'finance_nudges_present': payload['summary']['by_role'].get('finance', 0) > 0,
        'mis_qcg_alerts_present': payload['summary']['by_role'].get('mis_qcg_admin', 0) > 0,
        'no_notification_for_bad_unlineaged_action': 'bad_unlineaged_action_for_batch9_smoke' not in ids,
        'bad_unlineaged_candidate_blocked': any(c.get('source_action_id') == 'bad_unlineaged_action_for_batch9_smoke' for c in payload.get('blocked_candidates', [])),
        'all_notifications_have_source_action_lineage': payload['validations']['checks']['all_notifications_have_source_action_lineage'],
        'all_notifications_have_workflow_event_lineage': payload['validations']['checks']['all_notifications_have_workflow_event_lineage'],
        'all_notifications_have_role_visibility': payload['validations']['checks']['all_notifications_have_role_visibility'],
        'all_notifications_have_rule_evidence': payload['validations']['checks']['all_notifications_have_rule_evidence'],
        'all_notifications_have_dedupe_keys': payload['validations']['checks']['all_notifications_have_dedupe_keys'],
        'dedupe_keys_unique': payload['validations']['checks']['dedupe_keys_unique'],
        'daily_digest_present': payload['digests']['daily_live_pulse_risk_action']['notification_count'] > 0,
        'weekly_digest_present': payload['digests']['weekly_management_review']['notification_count'] > 0,
        'digests_have_dedupe_keys': bool(payload['digests']['daily_live_pulse_risk_action']['suppression']['dedupe_key'] and payload['digests']['weekly_management_review']['suppression']['dedupe_key']),
        'notifications_are_l5_output': payload['validations']['checks']['notifications_are_l5_output'],
        'no_third_arrival_door': payload['validations']['checks']['no_third_arrival_door'],
        'entity_head_removed': payload['validations']['checks']['entity_head_removed'],
    }

    # Static frontend/backend checks
    app_js = (OUT_DIR / 'App.jsx').read_text(encoding='utf-8')
    main_py = (OUT_DIR / 'main.py').read_text(encoding='utf-8')
    notifications_py = (OUT_DIR / 'notifications.py').read_text(encoding='utf-8')
    checks.update({
        'backend_includes_notifications_router': 'notifications_router' in main_py and '/notifications' in main_py,
        'frontend_fetches_notifications': 'fetch(`${BACKEND_URL}/notifications`)' in app_js,
        'frontend_has_notification_panel': 'NotificationEscalationPanel' in app_js,
        'frontend_has_digest_cards': 'DigestCard' in app_js,
        'module_requires_dedupe_keys': 'dedupe_key' in notifications_py and 'suppression_scope' in notifications_py,
        'module_declares_no_external_delivery': 'external_delivery_enabled' in notifications_py,
        'no_business_computation_in_frontend': 'HIGH_RISK_AMOUNT_AED' not in app_js and 'evaluate_rules' not in app_js,
    })

    result = {
        'contract_version': 'batch9.smoke.v1',
        'overall_passed': all(checks.values()),
        'passed_count': sum(1 for v in checks.values() if v),
        'total_count': len(checks),
        'checks': checks,
        'summary': payload['summary'],
        'sample_notification_ids': [n.get('notification_id') for n in notifications_list[:10]],
        'sample_rules': rules,
    }
    (OUT_DIR / 'smoke_batch9_notifications_results.json').write_text(json.dumps(result, indent=2, default=str), encoding='utf-8')
    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
