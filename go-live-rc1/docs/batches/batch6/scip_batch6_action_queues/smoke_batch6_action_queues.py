from __future__ import annotations

import json
from pathlib import Path

from account_action_queues import build_action_queue_payload

OUT = Path(__file__).resolve().parent
payload = build_action_queue_payload(Path('/mnt/data'))

checks = []

def check(name, condition, details=None):
    checks.append({"name": name, "passed": bool(condition), "details": details})

check('payload_contract_version', payload.get('contract_version') == 'action_queues.v1.batch6')
check('no_silent_fallback_guardrail', payload.get('guardrails', {}).get('no_silent_fallback') is True)
check('tolerance_guardrail', payload.get('guardrails', {}).get('tolerance_pct') == 0.05)
check('r18_loaded', payload.get('source_availability', {}).get('R18') == 'loaded_project_ageing_grain')
check('account_collector_source_disclosed_missing', payload.get('source_availability', {}).get('account_collector_report') == 'missing_not_attached')
check('facts_extracted', payload.get('facts_summary', {}).get('project_ageing_facts', 0) > 0, payload.get('facts_summary'))
check('top_project_risk_cohorts_exist', payload.get('facts_summary', {}).get('top_project_risk_cohorts', 0) > 0)
check('eligible_account_actions_zero_when_owner_missing', payload.get('facts_summary', {}).get('eligible_account_actions') == 0)

for role in ['collector_rm', 'cco_gm_agm', 'finance', 'mis_qcg_admin']:
    rp = payload.get('roles', {}).get(role, {})
    check(f'{role}_role_present', bool(rp))
    check(f'{role}_reporting_basis_present', bool(rp.get('reporting_basis')))
    check(f'{role}_required_fields_include_owner', 'collector_rm_owner' in (rp.get('required_source_fields') or []))

collector = payload.get('roles', {}).get('collector_rm', {})
check('collector_account_actions_blocked', len(collector.get('account_actions') or []) == 0)
check('collector_blocked_actions_have_lineage', all(a.get('lineage_refs') for a in (collector.get('blocked_actions') or [])))
check('collector_blocked_reason_present', all(a.get('blocked_reason') for a in (collector.get('blocked_actions') or [])))

for role in ['cco_gm_agm', 'finance', 'mis_qcg_admin']:
    actions = payload.get('roles', {}).get(role, {}).get('project_risk_cohorts') or []
    check(f'{role}_project_cohorts_lineaged', actions and all(a.get('lineage_refs') for a in actions))
    check(f'{role}_project_cohorts_have_entity_ageing_amount', actions and all(a.get('entity_code') and a.get('ageing_bucket') and a.get('amount_aed') is not None for a in actions))

validations = payload.get('validations', {}).get('checks', {})
check('payload_validation_passed', payload.get('validations', {}).get('passed') is True, payload.get('validations'))
check('no_account_action_without_owner_and_lineage', validations.get('no_account_action_without_owner_and_lineage') is True)
check('collector_rm_queue_blocked_without_owner_source', validations.get('collector_rm_queue_blocked_without_owner_source') is True)
check('source_row_reconciliation_passed', validations.get('source_row_reconciliation_passed') is True)

app = (OUT / 'App.jsx').read_text(encoding='utf-8')
css = (OUT / 'liquidGlassTokens.css').read_text(encoding='utf-8')
check('frontend_fetches_action_queues_endpoint', '/action-queues' in app)
check('frontend_action_queue_panel_exists', 'function ActionQueuePanel' in app)
check('frontend_action_panel_gated_to_risk_action', 'focus !== "risk_action"' in app)
check('frontend_solid_evidence_table_used', 'solid-evidence-table' in app and '.solid-evidence-table' in css)
check('frontend_no_new_business_calculation_for_action_queue', 'project_ageing_observation_amount_aed_non_additive' not in app and 'reduce(' not in app[app.find('function ActionQueuePanel'):app.find('function LineageDrawer')])

result = {
    'overall_passed': all(c['passed'] for c in checks),
    'checks_passed': sum(1 for c in checks if c['passed']),
    'checks_total': len(checks),
    'checks': checks,
    'payload_summary': payload.get('facts_summary'),
    'payload_status': payload.get('status'),
    'data_grain_disclosure': payload.get('data_grain_disclosure'),
}

(OUT / 'smoke_batch6_action_queues_results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
(OUT / 'action_queues_sample_payload_batch6.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
