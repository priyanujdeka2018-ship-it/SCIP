from pathlib import Path
import json
import data_loader

payload = data_loader.load_all(Path('/mnt/data'))
computed = payload['computed']
checks = {
    'R08_live': computed.get('R08_SOURCE') == 'R08_live',
    'R36_live': computed.get('PIPELINE_SOURCE') == 'R36_live',
    'R08_validated': computed.get('R08_CONFIDENCE') == 'live_validated',
    'R36_validated': computed.get('PIPELINE_CONFIDENCE') == 'live_validated',
    'R08_lineage_present': bool(computed.get('R08_LINEAGE')),
    'R36_lineage_present': bool(computed.get('R36_LINEAGE')),
    'no_silent_fallback_pipeline': computed.get('PIPELINE_SOURCE') != 'fallback_reference',
    'no_silent_fallback_r08': computed.get('R08_SOURCE') != 'fallback_reference',
    'r08_cy_fy_reconciles': computed['R08_VALIDATIONS']['R08_CY_PLUS_FY_EQUALS_ADVANCE_2026_TOTAL']['passed'],
    'r36_forward_calendar_reconciles': computed['R36_VALIDATIONS']['R36_ACTIVE_FORWARD_BUCKETS_EQUAL_PIPELINE_GROSS']['passed'],
}
print(json.dumps({'overall_passed': all(checks.values()), 'load_status': payload['status'], 'checks': checks}, indent=2))
