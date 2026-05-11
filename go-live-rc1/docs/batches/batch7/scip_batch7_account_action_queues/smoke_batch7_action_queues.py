from __future__ import annotations

import json
from pathlib import Path
from account_action_queues import build_action_queue_payload

OUT = Path(__file__).resolve().parent
payload = build_action_queue_payload(Path('/mnt/data'))

checks = []
def check(name, cond, detail=None):
    checks.append({'name': name, 'passed': bool(cond), 'detail': detail})

check('contract version is Batch 7', payload.get('contract_version') == 'action_queues.v2.batch7', payload.get('contract_version'))
check('overall payload ready', payload.get('status') == 'ready_account_level_guarded', payload.get('status'))
check('entity head removed', 'entity_head' not in payload.get('roles', {}), list(payload.get('roles', {}).keys()))
check('locked hierarchy preserved', 'Sobha(Sobha Dubai, Sobha AUH)' in payload.get('guardrails', {}).get('locked_hierarchy',''), payload.get('guardrails'))
check('no silent fallback enabled', payload.get('guardrails', {}).get('no_silent_fallback') is True, payload.get('guardrails'))

sources = payload.get('source_availability', {})
for code in ['R10','R17','R20','R30','R31','R32','R34','R38','R09']:
    check(f'{code} source loaded', sources.get(code) == 'loaded', sources.get(code))

summary = payload.get('facts_summary', {})
check('R10 PTP facts extracted', summary.get('r10_ptp_facts',0) > 0, summary.get('r10_ptp_facts'))
check('R34 termination facts extracted', summary.get('r34_termination_facts',0) > 0, summary.get('r34_termination_facts'))
check('R31 PR issues extracted', summary.get('r31_pr_issues',0) > 0, summary.get('r31_pr_issues'))
check('R38 risk facts extracted', summary.get('r38_risk_facts',0) > 0, summary.get('r38_risk_facts'))
check('collector account actions unlocked', summary.get('collector_account_actions_ready',0) > 0, summary.get('collector_account_actions_ready'))
check('finance PR actions unlocked', summary.get('finance_pr_actions_ready',0) > 0, summary.get('finance_pr_actions_ready'))

validations = payload.get('validations', {})
check('backend validations pass', validations.get('passed') is True, validations)

roles = payload.get('roles', {})
collector_actions = roles.get('collector_rm', {}).get('account_actions', [])
finance_actions = roles.get('finance', {}).get('account_actions', [])
cco_actions = roles.get('cco_gm_agm', {}).get('account_actions', [])
mis_process = roles.get('mis_qcg_admin', {}).get('process_actions', [])

def has_required_action_fields(a):
    return all(a.get(k) not in (None, '', []) for k in ['account_id','unit','collector_rm_owner','entity_code','amount_aed','ageing_bucket','reporting_basis','lineage_refs'])

def all_lineage_refs_complete(a):
    req = ['source_code','source_file','sheet','cell_or_range','validation_status','confidence_state','reporting_basis']
    return bool(a.get('lineage_refs')) and all(all(ref.get(k) for k in req) for ref in a.get('lineage_refs'))

check('collector actions have required fields', collector_actions and all(has_required_action_fields(a) for a in collector_actions), len(collector_actions))
check('collector actions have complete lineage', collector_actions and all(all_lineage_refs_complete(a) for a in collector_actions), collector_actions[0] if collector_actions else None)
check('collector role has no finance PR action', all(a.get('action_type') != 'finance_pr_quality_exception' for a in collector_actions), [a.get('action_type') for a in collector_actions[:5]])
check('finance actions are not collector PTP calls', all(a.get('action_type') != 'collector_ptp_follow_up' for a in finance_actions), [a.get('action_type') for a in finance_actions[:5]])
check('CCO queue has account actions', len(cco_actions) > 0, len(cco_actions))
check('MIS/QCG has process actions', len(mis_process) > 0, len(mis_process))

app_text = (OUT / 'App.jsx').read_text(encoding='utf-8')
check('frontend fetches action-queues contract', '/action-queues' in app_text, None)
check('frontend renders account action cards', 'account-action-card' in app_text, None)
check('frontend shows owner/account/unit/amount metadata', all(t in app_text for t in ['Owner','Account','Unit','Amount']), None)
check('frontend keeps actions in risk_action focus', 'focus !== "risk_action"' in app_text, None)
check('frontend does not introduce entity_head role key', 'entity_head' not in app_text, None)

css_text = (OUT / 'liquidGlassTokens.css').read_text(encoding='utf-8')
check('CSS includes account action solid cards', '.account-action-card' in css_text, None)

results = {
    'overall_passed': all(c['passed'] for c in checks),
    'passed_count': sum(c['passed'] for c in checks),
    'total_count': len(checks),
    'checks': checks,
    'facts_summary': summary,
    'payload_status': payload.get('status'),
}
(OUT / 'action_queues_sample_payload_batch7.json').write_text(json.dumps(payload, indent=2, default=str), encoding='utf-8')
(OUT / 'smoke_batch7_action_queues_results.json').write_text(json.dumps(results, indent=2, default=str), encoding='utf-8')
print(json.dumps(results, indent=2, default=str))
