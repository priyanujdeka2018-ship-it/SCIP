from __future__ import annotations
import importlib.util, json, os, sqlite3, tempfile, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADOPTION_PATH = ROOT / 'adoption.py'
APP_PATH = ROOT / 'App.jsx'

spec = importlib.util.spec_from_file_location('adoption', ADOPTION_PATH)
adoption = importlib.util.module_from_spec(spec)
sys.modules['adoption'] = adoption
spec.loader.exec_module(adoption)

checks = []

def check(name, passed, details=None):
    checks.append({'name': name, 'passed': bool(passed), 'details': details or {}})

with tempfile.TemporaryDirectory() as td:
    db = Path(td) / 'adoption.sqlite'
    conn = adoption.connect(db)
    adoption.initialize_db(conn)
    seed = adoption.seed_sample_data(conn)
    summary = adoption.adoption_summary(conn)
    dashboards = adoption.dashboard_specs(summary)
    recs = adoption.build_recommendations(summary)
    adoption.upsert_recommendations(conn, recs)
    rows = conn.execute('SELECT * FROM adoption_events').fetchall()

    check('seed_created_events', seed.get('event_count', 0) > 100, seed)
    check('contract_version', summary.get('contract_version') == 'adoption_optimization.v1.batch15')
    check('all_events_have_correlation_id', all(row['correlation_id'] for row in rows))
    check('all_actor_ids_hashed', all(len(row['actor_hash']) == 24 and '@' not in row['actor_hash'] for row in rows))
    check('no_entity_head_role', all(row['role'] != 'entity_head' for row in rows))
    check('worlds_only_two_doors', set(summary.get('world_usage', {}).keys()).issubset({'live_pulse','narratives'}), summary.get('world_usage'))
    required_metrics = set(adoption.METRIC_CATALOG)
    check('all_required_metrics_present', required_metrics.issubset(summary.get('metrics', {}).keys()), {'missing': sorted(required_metrics - set(summary.get('metrics', {}).keys()))})
    props = [row['properties_json'] for row in rows]
    check('sensitive_data_redacted', all('example.com' not in p and 'redacted_seed' not in p for p in props))
    check('dashboards_not_arrival_door', all(d.get('not_arrival_door') for d in dashboards.get('dashboards', [])))
    check('dashboards_are_l5_outputs', all('L5' in d.get('surface','') or 'governance' in d.get('surface','').lower() for d in dashboards.get('dashboards', [])))
    check('recommendations_have_guardrails', all('third Arrival' in r.get('liquid_glass_guardrail','') or 'two doors' in r.get('liquid_glass_guardrail','') for r in recs), {'count': len(recs)})
    check('recommendations_have_evidence', all(r.get('evidence') for r in recs), {'count': len(recs)})
    check('action_conversion_server_side', isinstance(summary['metrics']['action_queue_conversion_rate'], (int, float)))
    check('workflow_closure_server_side', isinstance(summary['metrics']['workflow_closure_rate'], (int, float)))
    check('notification_effectiveness_server_side', isinstance(summary['metrics']['notification_effectiveness'], (int, float)))

    # Invalid cases blocked
    try:
        adoption.record_event(conn, role='entity_head', world='live_pulse', event_type='world_open', correlation_id='bad')
        entity_head_blocked = False
    except ValueError:
        entity_head_blocked = True
    check('entity_head_event_blocked', entity_head_blocked)

    try:
        adoption.record_event(conn, role='mis_qcg_admin', world='observability', event_type='world_open', correlation_id='bad2')
        third_door_blocked = False
    except ValueError:
        third_door_blocked = True
    check('third_door_world_blocked', third_door_blocked)

app = APP_PATH.read_text(encoding='utf-8')
check('frontend_fetches_adoption_summary', '/adoption/summary' in app)
check('frontend_fetches_adoption_dashboards', '/adoption/dashboards' in app)
check('frontend_fetches_optimization_backlog', '/adoption/backlog' in app)
check('frontend_has_adoption_panel', 'AdoptionOptimizationPanel' in app)
check('frontend_declares_not_third_door_guardrail', 'third Arrival door' in app or 'third Arrival' in app)
check('frontend_no_entity_head_literal', 'entity_head' not in app.lower())
# Ensure frontend only displays provided fields. The component must not compute conversion rates itself.
forbidden_snippets = ['action_queue_conversion_rate =', 'workflow_closure_rate =', 'notification_effectiveness =']
check('frontend_no_adoption_business_calculation', not any(s in app for s in forbidden_snippets), {'forbidden': forbidden_snippets})

main = (ROOT / 'main.py').read_text(encoding='utf-8')
check('main_includes_adoption_router', 'adoption_router' in main and 'app.include_router(adoption_router)' in main)
check('main_root_exposes_adoption_links', 'adoption_summary' in main and 'optimization_backlog' in main)

results = {
    'contract_version': 'adoption_optimization.v1.batch15',
    'overall_passed': all(c['passed'] for c in checks),
    'checks_passed': sum(1 for c in checks if c['passed']),
    'checks_total': len(checks),
    'checks': checks,
    'summary_sample': summary,
    'dashboard_sample': dashboards,
    'recommendation_sample': recs,
}
( ROOT / 'smoke_batch15_adoption_analytics_results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
( ROOT / 'analytics' / 'adoption_summary_sample_batch15.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
( ROOT / 'analytics' / 'adoption_dashboards_sample_batch15.json').write_text(json.dumps(dashboards, indent=2), encoding='utf-8')
( ROOT / 'backlog' / 'optimization_backlog_sample_batch15.json').write_text(json.dumps({'contract_version': 'adoption_optimization.v1.batch15', 'recommendations': recs}, indent=2), encoding='utf-8')
print(json.dumps({'overall_passed': results['overall_passed'], 'checks_passed': results['checks_passed'], 'checks_total': results['checks_total']}, indent=2))
if not results['overall_passed']:
    raise SystemExit(1)
