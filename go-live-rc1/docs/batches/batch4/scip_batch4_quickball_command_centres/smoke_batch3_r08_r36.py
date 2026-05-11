from pathlib import Path
import json
from source_adapters import run_adapter

base = Path('/mnt/data')
r08 = run_adapter('R08', base / 'R08_Advance Summary 06-05-2026.xlsx').to_dict()
r36 = run_adapter('R36', base / 'R36_year on year Milestone Report as on 05-05-2026.xlsx').to_dict()

critical_r08 = [
    'R08_REQUIRED_SHEETS_PRESENT',
    'R08_CY_PLUS_FY_EQUALS_ADVANCE_2026_TOTAL',
    'R08_CYFY_TOTAL_EQUALS_SUMMARY_2026_ADVANCE',
    'R08_REBATE_2026_ADVANCE_EQUALS_CYFY_TOTAL',
]
critical_r36 = [
    'R36_REQUIRED_SHEETS_PRESENT',
    'R36_ACTIVE_ROW_TOTAL_EQUALS_PURCHASE_PRICE',
    'R36_TOTAL_ROW_TOTAL_EQUALS_PURCHASE_PRICE',
    'R36_ACTIVE_FORWARD_BUCKETS_EQUAL_PIPELINE_GROSS',
    'R36_TOTAL_FORWARD_BUCKETS_EQUAL_VISIBLE_TOTAL',
    'R36_PIPELINE_CONSTANTS_LABELLED',
]

results = {
    'overall_passed': all(r08['validations'][k]['passed'] for k in critical_r08)
    and all(r36['validations'][k]['passed'] for k in critical_r36),
    'r08_status': r08['status'],
    'r36_status': r36['status'],
    'r08_validations': r08['validations'],
    'r36_validations': r36['validations'],
    'r08_metric_extract': {k: r08['metrics'].get(k) for k in ['ADVANCE_2026_TOTAL', 'ADVANCE_2026_CY', 'ADVANCE_2026_FY', 'CY_ADV_MIX_YTD']},
    'r36_metric_extract': {k: r36['metrics'].get(k) for k in ['PIPELINE_GROSS', 'PIPELINE_TOTAL_FORWARD_CALENDAR', 'FORWARD_COLLECTIBLE_CALENDAR']},
}
print(json.dumps(results, indent=2, default=str))
