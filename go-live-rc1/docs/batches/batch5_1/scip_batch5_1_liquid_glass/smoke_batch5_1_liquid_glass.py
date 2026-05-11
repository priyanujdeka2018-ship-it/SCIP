import json
import re
from pathlib import Path

base = Path(__file__).resolve().parent
app = (base / 'App.jsx').read_text()
css = (base / 'liquidGlassTokens.css').read_text()

checks = []

def check(name, condition, detail=''):
    checks.append({'name': name, 'passed': bool(condition), 'detail': detail})

# Liquid Glass strategy acceptance checks
check('imports_liquid_glass_tokens', 'import "./liquidGlassTokens.css"' in app)
check('has_two_door_arrival', all(x in app for x in ['Live Pulse', 'Narratives', 'ArrivalScreen']) and 'arrival-doors' in css)
check('arrival_has_no_role_tabs', 'roleTabs' not in app and 'role-tab' not in css)
check('live_pulse_three_choices_only', all(x in app for x in ['current_signal', 'month_movement', 'risk_action']) and 'target_track' not in re.search(r'const LIVE_PULSE_CHOICES = \[(.*?)\];', app, re.S).group(1))
check('target_track_deep_link_only', 'Open Target Track/YTD lens' in app and 'not as a fourth first-level choice' in app)
check('narratives_guided_rail', all(x in app for x in ['story', 'portfolio', 'dues', 'advance', 'roadmap']) and 'narrative-rail' in css)
check('glass_surfaces_defined', all(x in css for x in ['--glass-quiet', '--glass-medium', '--glass-strong', '--glass-blur', '.glass-surface']))
check('solid_truth_surfaces_defined', '.solid-truth' in css and 'Financial truth' in css)
check('tokens_match_strategy', all(x in css for x in ['#080D14', '#0F1623', '#172232', '#C9A84C', '#E2C76C', '#F4EFE5', '#C8C0B3']))
check('trust_bar_preserved', 'DataConfidenceTrustBar' in app and 'No silent fallback' in app and 'Tolerance:' in app)
check('lineage_drawer_preserved', 'LineageDrawer' in app and all(x in app for x in ['Source', 'Sheet', 'Cell/range', 'Validation', 'Confidence', 'Basis']))
check('blocked_answer_warning_preserved', 'blocked_untrusted_metric' in app and 'Quickball blocked an untrusted answer' in app)
check('forecast_assumptions_visible', 'Forecast assumptions' in app and 'forecast.assumptions' in app)
check('reporting_basis_visible_on_cards', 'Reporting basis:' in app and 'card?.reporting_basis' in app)
check('role_model_without_entity_head', 'entity_head' not in app.lower() and all(x in app for x in ['board_cxo', 'cco_gm_agm', 'finance', 'mis_qcg_admin', 'collector_rm']))
check('quickball_max_two_actions_enforced', 'slice(0, 2)' in app)
check('quickball_backend_only', '/quickball/explain' in app and 'fetch(`${BACKEND_URL}/quickball/explain?' in app)
check('backend_contracts_preserved', all(x in app for x in ['/command-centres', '/forecast/month-end', '/quickball/explain']))

# No frontend financial computation heuristic: financial outputs are displayed from server payload; no arithmetic with forecast output fields.
forbidden_finance_patterns = [
    r'outputs\.[a-zA-Z0-9_]+\s*[+\-*/]',
    r'forecast\.outputs\.[a-zA-Z0-9_]+\s*[+\-*/]',
    r'mtd_total_collections\s*[+\-*/]',
    r'may_total_collections_target\s*[+\-*/]',
    r'projected_month_end_landing\s*[+\-*/]',
]
violations = [pat for pat in forbidden_finance_patterns if re.search(pat, app)]
check('no_frontend_financial_computation_static', not violations, f'violations={violations}')

# Accessibility/motion checks from strategy
check('reduced_motion_supported', '@media (prefers-reduced-motion: reduce)' in css)
check('focus_visible_supported', ':focus-visible' in css)
check('aria_labels_present', all(x in app for x in ['aria-label="SCIP arrival"', 'aria-label="Data confidence trust bar"', 'aria-label="Lineage drawer"', 'aria-label="Quickball command capsule"']))

results = {
    'batch': 'SCIP Batch 5.1',
    'scope': 'Liquid Glass UI system alignment',
    'overall_passed': all(c['passed'] for c in checks),
    'checks': checks,
    'summary': {
        'checks_total': len(checks),
        'checks_passed': sum(1 for c in checks if c['passed']),
        'checks_failed': sum(1 for c in checks if not c['passed']),
    }
}
(base / 'smoke_batch5_1_liquid_glass_results.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
