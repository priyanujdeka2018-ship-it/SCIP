from __future__ import annotations

import json
import re
from pathlib import Path

import data_loader
import command_centres
import forecast

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path('/mnt/data')
APP_PATH = ROOT / 'App.jsx'


def fail(name, detail):
    return {'name': name, 'passed': False, 'detail': detail}


def passed(name, detail='ok'):
    return {'name': name, 'passed': True, 'detail': detail}


def validate_card_contract(centres):
    checks = []
    failures = []
    for role_key, role_payload in centres.get('roles', {}).items():
        for card in role_payload.get('cards', []):
            label = f'{role_key}.{card.get("card_id")}'
            if not card.get('reporting_basis'):
                failures.append(f'{label} missing reporting_basis')
            refs = card.get('lineage_display') or card.get('lineage_refs') or []
            if not refs:
                failures.append(f'{label} missing lineage refs')
            for idx, ref in enumerate(refs):
                if not ref.get('has_lineage'):
                    failures.append(f'{label} ref[{idx}] not lineaged')
                for field in ['metric_key', 'source_file', 'sheet', 'cell_or_range', 'validation_status', 'confidence_state', 'reporting_basis']:
                    if not ref.get(field):
                        failures.append(f'{label} ref[{idx}] missing {field}')
    if failures:
        checks.append(fail('every_card_has_reporting_basis_and_lineage', failures[:20]))
    else:
        checks.append(passed('every_card_has_reporting_basis_and_lineage'))
    return checks


def validate_forecast(fc):
    checks = []
    if fc.get('status') != 'ok':
        return [fail('forecast_status_ok', fc)]
    for field in ['reporting_basis', 'basis_disclosure', 'assumptions', 'lineage_refs', 'working_days', 'outputs']:
        if not fc.get(field):
            checks.append(fail(f'forecast_has_{field}', fc.get(field)))
        else:
            checks.append(passed(f'forecast_has_{field}'))
    required_outputs = ['current_daily_run_rate', 'required_daily_run_rate_remaining', 'projected_month_end_landing', 'gap_to_may_mdo_target', 'projected_achievement_pct']
    missing_outputs = [k for k in required_outputs if fc.get('outputs', {}).get(k) is None]
    checks.append(passed('forecast_outputs_complete') if not missing_outputs else fail('forecast_outputs_complete', missing_outputs))
    critical_refs = [r for r in fc.get('lineage_refs', []) if r.get('metric_key') in {'MTD_TOTAL_COLLECTIONS','MAY_TOTAL_COLLECTIONS_TARGET'}]
    checks.append(passed('forecast_critical_inputs_lineaged') if len(critical_refs) == 2 and all(r.get('has_lineage') for r in critical_refs) else fail('forecast_critical_inputs_lineaged', critical_refs))
    assumptions = ' '.join(fc.get('assumptions', []))
    for phrase in ['straight-line', 'Working days', 'R04 Finance', 'R02 MDO', 'No silent fallback']:
        checks.append(passed(f'forecast_assumption_mentions_{phrase}') if phrase in assumptions else fail(f'forecast_assumption_mentions_{phrase}', assumptions))
    return checks


def validate_frontend_static():
    checks = []
    text = APP_PATH.read_text(encoding='utf-8')
    required_symbols = [
        'DataConfidenceTrustBar',
        'LineageDrawer',
        'BlockedAnswerWarning',
        'ForecastPanel',
        '/command-centres',
        '/forecast/month-end',
        '/quickball/explain',
        'Reporting basis',
        'Forecast assumptions',
    ]
    for symbol in required_symbols:
        checks.append(passed(f'frontend_contains_{symbol}') if symbol in text else fail(f'frontend_contains_{symbol}', 'missing'))
    role_literals = ['board_cxo', 'cco_gm_agm', 'finance', 'mis_qcg_admin', 'collector_rm']
    missing_roles = [r for r in role_literals if r not in text]
    checks.append(passed('frontend_role_model_without_entity_head') if not missing_roles and 'entity_head' not in text else fail('frontend_role_model_without_entity_head', {'missing': missing_roles, 'contains_entity_head': 'entity_head' in text}))
    return checks


def main():
    payload = data_loader.load_all(data_dir=DATA_DIR)
    fc = forecast.build_month_end_forecast(payload)
    centres = command_centres.build_command_centres(payload)

    checks = []
    checks.append(passed('critical_sources_loaded', {k: payload['dataframes'].get(k, {}).get('status') for k in ['R18','R04','R02','R08','R36']}) if all(payload['dataframes'].get(k, {}).get('status') == 'ok' for k in ['R18','R04','R02','R08','R36']) else fail('critical_sources_loaded', {k: payload['dataframes'].get(k, {}).get('status') for k in ['R18','R04','R02','R08','R36']}))
    checks.extend(validate_card_contract(centres))
    checks.extend(validate_forecast(fc))
    checks.extend(validate_frontend_static())

    result = {
        'batch': 'Batch 5',
        'overall_passed': all(c['passed'] for c in checks),
        'checks': checks,
        'forecast_summary': {
            'status': fc.get('status'),
            'reporting_basis': fc.get('reporting_basis'),
            'mtd_total_collections': fc.get('display', {}).get('mtd_total_collections'),
            'may_total_collections_target': fc.get('display', {}).get('may_total_collections_target'),
            'projected_month_end_landing': fc.get('display', {}).get('projected_month_end_landing'),
            'projected_achievement_pct': fc.get('display', {}).get('projected_achievement_pct'),
            'working_days': fc.get('working_days'),
        },
        'role_card_counts': {k: len(v.get('cards', [])) for k, v in centres.get('roles', {}).items()},
    }
    out = ROOT / 'smoke_batch5_ui_forecast_results.json'
    out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['overall_passed'] else 1)


if __name__ == '__main__':
    main()
