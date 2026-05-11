from __future__ import annotations

import csv
import json
import os
import sqlite3
from pathlib import Path

import persistence

OUT_DIR = Path(__file__).resolve().parent
DB_PATH = OUT_DIR / 'scip_batch10_smoke.sqlite'
EXPORT_DIR = OUT_DIR / 'audit_exports'


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()
    seed = persistence.seed_persistent_store(DB_PATH, as_of_date='2026-05-09', reset=True, data_dir='/mnt/data')
    validation = persistence.validate_persistence(DB_PATH)
    json_path = persistence.export_audit_json(DB_PATH, EXPORT_DIR, created_by='batch10_smoke')
    csv_path = persistence.export_audit_csv(DB_PATH, EXPORT_DIR, created_by='batch10_smoke')
    dedupe = persistence.run_dedupe_restart_check(DB_PATH, as_of_date='2026-05-09')
    summary = persistence.build_persistence_payload(DB_PATH)

    json_export = read_json(json_path)
    with csv_path.open('r', encoding='utf-8') as f:
        csv_rows = list(csv.DictReader(f))

    # Verify DB-level lineage immutability trigger blocks tampering.
    tamper_blocked = False
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute('SELECT workflow_id FROM workflow_records LIMIT 1').fetchone()
        try:
            conn.execute('UPDATE workflow_records SET lineage_hash=? WHERE workflow_id=?', ('tampered_again', row[0]))
            conn.commit()
        except sqlite3.DatabaseError:
            tamper_blocked = True
            conn.rollback()

    counts = persistence.table_counts(DB_PATH)
    checks = {
        'contract_version_batch10': summary.get('contract_version') == 'persistence_audit.v1.batch10',
        'status_ready': summary.get('status') == 'ready_persistence_audit_guarded',
        'source_actions_persisted': counts['source_actions'] > 0,
        'workflow_records_persisted': counts['workflow_records'] > 0,
        'workflow_events_persisted': counts['workflow_events'] > 0,
        'notification_emissions_persisted': counts['notification_emissions'] > 0,
        'suppression_state_persisted': counts['suppression_state'] == counts['notification_emissions'],
        'delivery_status_persisted': counts['delivery_status'] == counts['notification_emissions'],
        'notification_dedupe_survives_restart': dedupe['dedupe_survived_restart'],
        'second_pass_emitted_zero_duplicates': dedupe['second_pass_inserted'] == 0,
        'lineage_hashes_immutable_round_trip': validation['checks']['lineage_triggers_block_tampering'] and tamper_blocked,
        'closed_workflows_remain_auditable': validation['checks']['closed_records_remain_auditable'],
        'audit_json_created': json_path.exists() and json_export['record_count'] > 0,
        'audit_csv_created': csv_path.exists() and len(csv_rows) > 0,
        'audit_exports_registered': persistence.table_counts(DB_PATH)['audit_exports'] >= 2,
        'audit_export_includes_source_action_lineage': any(row.get('source_action_lineage') for row in json_export['rows']),
        'audit_export_includes_workflow_event_lineage': any(row.get('workflow_event_lineage_hash') for row in json_export['rows']),
        'audit_export_includes_notification_lineage': any(row.get('notification_lineage') for row in json_export['rows']),
        'audit_export_includes_actor': any(row.get('actor') for row in json_export['rows']),
        'audit_export_includes_timestamp': any(row.get('event_created_at') for row in json_export['rows']),
        'audit_export_includes_role': any(row.get('actor_role') for row in json_export['rows']),
        'audit_export_includes_state': any(row.get('workflow_state') for row in json_export['rows']),
        'audit_export_includes_closure_evidence': any(row.get('closure_reason') for row in json_export['rows']),
        'audit_export_includes_escalation_rule_evidence': any((row.get('notification_rule_evidence') or {}).get('rule_id') for row in json_export['rows']),
        'no_entity_head_role': validation['checks']['role_model_without_entity_head'],
        'schema_file_present': (OUT_DIR / 'migrations' / '001_batch10_persistence.sql').exists(),
        'main_includes_persistence_router': 'persistence_router' in (OUT_DIR / 'main.py').read_text(encoding='utf-8'),
        'frontend_fetches_persistence_summary': 'fetch(`${BACKEND_URL}/persistence/summary`)' in (OUT_DIR / 'App.jsx').read_text(encoding='utf-8'),
        'frontend_links_audit_exports': '/audit/export?format=json' in (OUT_DIR / 'App.jsx').read_text(encoding='utf-8') and '/audit/export?format=csv' in (OUT_DIR / 'App.jsx').read_text(encoding='utf-8'),
        'no_business_computation_in_frontend': 'evaluate_rules' not in (OUT_DIR / 'App.jsx').read_text(encoding='utf-8') and 'HIGH_RISK_AMOUNT_AED' not in (OUT_DIR / 'App.jsx').read_text(encoding='utf-8'),
    }

    result = {
        'contract_version': 'batch10.smoke.v1',
        'overall_passed': all(checks.values()),
        'passed_count': sum(1 for v in checks.values() if v),
        'total_count': len(checks),
        'checks': checks,
        'seed': seed,
        'counts': counts,
        'dedupe_restart_check': dedupe,
        'validation': validation,
        'exports': {
            'json_path': str(json_path),
            'csv_path': str(csv_path),
            'json_record_count': json_export['record_count'],
            'csv_record_count': len(csv_rows),
        },
    }
    (OUT_DIR / 'smoke_batch10_persistence_audit_results.json').write_text(json.dumps(result, indent=2, default=str), encoding='utf-8')
    (OUT_DIR / 'persistence_summary_sample_batch10.json').write_text(json.dumps(summary, indent=2, default=str), encoding='utf-8')
    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
