"""Batch 4 smoke tests for Quickball lineage and command-centre contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import data_loader
import quickball
import command_centres

DATA_DIR = Path('/mnt/data')
OUT = Path(__file__).with_name('smoke_quickball_batch4_results.json')

CRITICAL_EXPLAIN_METRICS = [
    ('OD_TODAY', 'board_cxo'),
    ('OD_SOBHA', 'cco_gm_agm'),
    ('OD_UAQ', 'cco_gm_agm'),
    ('MTD_TOTAL_COLLECTIONS', 'cco_gm_agm'),
    ('MTD_DA_TOTAL', 'finance'),
    ('MAY_DA_TARGET', 'finance'),
    ('MAY_TOTAL_COLLECTIONS_TARGET', 'finance'),
    ('FY_TOTAL_COLLECTIONS_TARGET', 'board_cxo'),
    ('ADVANCE_2026_TOTAL', 'board_cxo'),
    ('ADVANCE_2026_CY', 'board_cxo'),
    ('ADVANCE_2026_FY', 'board_cxo'),
    ('CY_ADV_MIX_YTD', 'board_cxo'),
    ('YTD_2026_REBATE', 'finance'),
    ('PIPELINE_GROSS', 'board_cxo'),
    ('PIPELINE_FORWARD_2026', 'mis_qcg_admin'),
    ('PIPELINE_FORWARD_2027', 'mis_qcg_admin'),
]


def assert_answer(ans: Dict[str, Any]) -> Dict[str, Any]:
    lineage = ans.get('lineage') or {}
    checks = {
        'answered': ans.get('status') == 'answered',
        'has_lineage': bool(lineage),
        'has_source_file': bool(lineage.get('source_file')),
        'has_sheet': bool(lineage.get('sheet')),
        'has_cell_or_range': bool(lineage.get('cell_or_range')),
        'has_validation_status': bool(lineage.get('validation_status')),
        'has_confidence_state': bool(lineage.get('confidence_state')),
        'lineage_gate_passed': bool((ans.get('guardrail') or {}).get('lineage_gate_passed')),
        'no_silent_fallback': bool((ans.get('guardrail') or {}).get('no_silent_fallback')),
    }
    return {'passed': all(checks.values()), 'checks': checks, 'answer': ans}


def run() -> Dict[str, Any]:
    payload = data_loader.load_all(data_dir=DATA_DIR)
    explain_results: Dict[str, Any] = {}
    for metric, role in CRITICAL_EXPLAIN_METRICS:
        ans = quickball.explain_metric(payload, metric, role)
        explain_results[f'{metric}:{role}'] = assert_answer(ans)

    centres = command_centres.build_command_centres(payload)
    centre_checks: Dict[str, Any] = {}
    for role_key, centre in centres.get('roles', {}).items():
        cards = centre.get('cards', [])
        card_results: List[Dict[str, Any]] = []
        for card in cards:
            refs = card.get('lineage_refs', [])
            # MIS-only data quality cards are allowed to be aggregate governance cards without direct refs.
            refs_ok = True if not refs else all(r.get('has_lineage') for r in refs)
            card_results.append({
                'card_id': card.get('card_id'),
                'trust_state': card.get('trust_state'),
                'refs_ok': refs_ok,
                'refs_count': len(refs),
            })
        centre_checks[role_key] = {
            'has_cards': bool(cards),
            'role_label': centre.get('role_label'),
            'trust_bar_present': bool(centre.get('trust_bar')),
            'cards': card_results,
            'passed': bool(cards) and bool(centre.get('trust_bar')) and all(c['refs_ok'] for c in card_results),
        }

    # Negative gate test: remove lineage for OD_TODAY and ensure Quickball blocks.
    tampered = json.loads(json.dumps(payload, default=str))
    tampered.get('computed', {}).get('OD_LINEAGE', {}).pop('OD_TODAY', None)
    blocked = quickball.explain_metric(tampered, 'OD_TODAY', 'board_cxo')
    negative_gate = {
        'status': blocked.get('status'),
        'passed': blocked.get('status') == 'blocked_untrusted_metric',
        'reason': blocked.get('reason'),
    }

    result = {
        'overall_passed': all(v['passed'] for v in explain_results.values()) and all(v['passed'] for v in centre_checks.values()) and negative_gate['passed'],
        'payload_status': payload.get('status'),
        'critical_sources_loaded': {k: payload.get('dataframes', {}).get(k, {}).get('status') for k in ['R18','R04','R02','R08','R36']},
        'explain_results': explain_results,
        'command_centre_checks': centre_checks,
        'negative_lineage_gate_test': negative_gate,
    }
    OUT.write_text(json.dumps(result, indent=2, default=str), encoding='utf-8')
    return result


if __name__ == '__main__':
    res = run()
    print(json.dumps({
        'overall_passed': res['overall_passed'],
        'payload_status': res['payload_status'],
        'critical_sources_loaded': res['critical_sources_loaded'],
        'negative_lineage_gate_test': res['negative_lineage_gate_test'],
    }, indent=2))
