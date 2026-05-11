from pathlib import Path
import json, sys, importlib.util
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import governance
checks=[]

def check(name, condition, details=None):
    checks.append({"name": name, "passed": bool(condition), "details": details or {}})

with governance.connect(ROOT/'smoke_batch16.sqlite') as conn:
    seed=governance.seed_governance(conn)
    pack=governance.monthly_review_pack(conn)

check('seeded_improvement_items', seed['seeded_items'] >= 4)
check('contract_version', pack['contract_version'] == governance.GOVERNANCE_CONTRACT_VERSION)
for item in pack['improvement_items']:
    check(f"item_{item['item_id']}_has_evidence", len(item.get('evidence_refs', [])) > 0)
    check(f"item_{item['item_id']}_has_owner", bool(item.get('owner')))
    check(f"item_{item['item_id']}_has_decision", item.get('decision') in governance.ALLOWED_DECISIONS)
    check(f"item_{item['item_id']}_has_expected_impact", bool(item.get('expected_impact')))
    check(f"item_{item['item_id']}_has_rollout_gate", item.get('rollout_gate') in governance.ALLOWED_GATES)
    check(f"item_{item['item_id']}_has_rollback", bool(item.get('rollback_criteria')))
    check(f"item_{item['item_id']}_has_lg_guardrail", 'third Arrival door' in item.get('liquid_glass_guardrail','') or 'Live Pulse' in item.get('liquid_glass_guardrail',''))
    check(f"item_{item['item_id']}_has_priority", item.get('priority') in {'P0','P1','P2','P3'})
check('entity_head_removed', 'Entity Head' not in json.dumps(pack))
check('backlog_scoring_model_priority', governance.backlog_scoring_model()['priority_bands']['P0'] == '>= 30')
check('templates_available', len(governance.templates()) >= 7)
app=(ROOT/'App.jsx').read_text(errors='ignore')
check('frontend_governance_l5_panel_present', 'ContinuousImprovementPanel' in app and 'L5 Governance Evidence' in app)
check('no_third_arrival_door_in_frontend', 'third Arrival door' not in app.lower().replace('no third arrival door',''))
main=(ROOT/'main.py').read_text(errors='ignore')
check('main_includes_governance_router', 'governance_router' in main)
sql=(ROOT/'migrations'/'006_batch16_continuous_improvement.sql').read_text()
for table in ['improvement_items','change_control_decisions','metric_definition_change_log','source_owner_sla_reviews','quickball_answer_reviews','ux_simplification_reviews','release_notes_governance']:
    check(f'migration_has_{table}', table in sql)

out={
    'contract_version': governance.GOVERNANCE_CONTRACT_VERSION,
    'overall_passed': all(c['passed'] for c in checks),
    'checks_passed': sum(1 for c in checks if c['passed']),
    'checks_total': len(checks),
    'checks': checks,
}
(Path(ROOT)/'smoke_batch16_continuous_improvement_results.json').write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
if not out['overall_passed']:
    sys.exit(1)
