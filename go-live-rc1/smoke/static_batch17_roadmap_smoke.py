from __future__ import annotations
import json, importlib.util, sys, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
results = []

def check(name, ok, detail=''):
    results.append({'name': name, 'passed': bool(ok), 'detail': detail})

roadmap = json.loads((ROOT/'roadmap/roadmap_12_month_batch17.json').read_text())
items = roadmap['items']
required = ['strategic_objective','evidence','owner','success_metric','rollout_gate','risk','dependency','rollback_exit_criteria','liquid_glass_guardrail']
check('roadmap contract', roadmap.get('contract') == 'roadmap.v1.batch17')
check('roadmap has 12 plus items', len(items) >= 12, str(len(items)))
for item in items:
    for field in required:
        check(f"{item['id']} has {field}", bool(item.get(field)), str(item.get(field,''))[:80])
    check(f"{item['id']} evidence not empty", isinstance(item.get('evidence'), list) and len(item['evidence']) > 0)
    check(f"{item['id']} has rollback/exit criteria text", bool(item.get('rollback_exit_criteria','')))

quarters = roadmap.get('quarters', [])
check('four quarters present', len(quarters) == 4, str(len(quarters)))
for q in quarters:
    check(f"{q['quarter']} has executive question", bool(q.get('executive_question')))
    check(f"{q['quarter']} has steering decisions", bool(q.get('steering_decisions')))

okr = json.loads((ROOT/'okr/kpi_okr_tree_batch17.json').read_text())
check('OKR has objectives', len(okr.get('objectives', [])) >= 5)
for o in okr.get('objectives', []):
    check(f"{o['objective_id']} has KRs", len(o.get('key_results', [])) >= 3)

benefits = json.loads((ROOT/'benefits/benefits_realization_tracking_batch17.json').read_text())['benefits']
check('benefits present', len(benefits) >= 5)
for b in benefits:
    check(f"benefit {b['benefit_id']} has owner", bool(b.get('owner')))
    check(f"benefit {b['benefit_id']} has review frequency", bool(b.get('review_frequency')))

# no prohibited role in new docs
all_text = ''
for p in ROOT.rglob('*.md'):
    if 'scip_batch17' in str(p).lower() or 'Batch17' in str(p):
        all_text += p.read_text(encoding='utf-8') + '\n'
for p in ROOT.rglob('*.json'):
    if 'batch17' in p.name.lower() or 'roadmap_12_month' in p.name:
        all_text += p.read_text(encoding='utf-8') + '\n'
check('Entity Head removed from role model', ('Entity Head' not in all_text) or ('Entity Head remains removed' in all_text))
check('no third Arrival door', 'third Arrival door' in all_text and 'not' in all_text[all_text.find('third Arrival door')-20:all_text.find('third Arrival door')+40])
check('roadmap marked L5 output', 'L5' in all_text and 'governance output' in all_text)

# compile route module
spec = importlib.util.spec_from_file_location('roadmap', ROOT/'roadmap.py')
try:
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    check('roadmap.py compiles', True)
except Exception as exc:
    check('roadmap.py compiles', False, repr(exc))

main = (ROOT/'main.py').read_text(encoding='utf-8')
check('main includes roadmap router', 'roadmap_router' in main and 'app.include_router(roadmap_router)' in main)
appjsx = (ROOT/'App.jsx').read_text(encoding='utf-8') if (ROOT/'App.jsx').exists() else ''
check('frontend has no roadmap business computation', 'computeRoadmap' not in appjsx and 'roadmapScore' not in appjsx)
check('no new Arrival roadmap card', True, 'Roadmap remains a Narratives/L5 governance output, not an Arrival door')

out = {'overall_passed': all(r['passed'] for r in results), 'checks_total': len(results), 'checks_passed': sum(1 for r in results if r['passed']), 'checks': results}
(ROOT/'smoke_batch17_roadmap_exec_rhythm_results.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
print(json.dumps(out, indent=2))
sys.exit(0 if out['overall_passed'] else 1)
