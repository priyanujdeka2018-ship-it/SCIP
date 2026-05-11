"""Generate Batch 4 sample answer and command-centre JSON artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import data_loader
import quickball
import command_centres

HERE = Path(__file__).parent
payload = data_loader.load_all(data_dir=Path('/mnt/data'))

sample_answers = quickball.build_sample_answers(payload)
(HERE / 'quickball_sample_answers_batch4.json').write_text(json.dumps(sample_answers, indent=2, default=str), encoding='utf-8')

centres = command_centres.build_command_centres(payload)
(HERE / 'command_centres_sample_payload_batch4.json').write_text(json.dumps(centres, indent=2, default=str), encoding='utf-8')

metric_catalog = {k: quickball.asdict(v) for k, v in quickball.METRIC_CATALOG.items()}
(HERE / 'quickball_metric_catalog_batch4.json').write_text(json.dumps(metric_catalog, indent=2, default=str), encoding='utf-8')

print(json.dumps({
    'sample_answers': len(sample_answers['samples']),
    'roles': list(centres['roles'].keys()),
    'catalog_count': len(metric_catalog),
}, indent=2))
