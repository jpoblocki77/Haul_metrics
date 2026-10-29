"""Validate fresh iteration-10 artifacts without merging historical results or touching SQLite."""
import json
from pathlib import Path
from xml.etree import ElementTree

root = Path('/app/test_reports')
counts = {}
for name in ['numeric', 'functional', 'security']:
    tree = ElementTree.parse(root / 'pytest' / f'pytest_results_iter10_{name}.xml')
    cases = tree.findall('.//testcase')
    counts[name] = {
        'total': len(cases),
        'passed': sum(not any(c.find(tag) is not None for tag in ['failure', 'error', 'skipped']) for c in cases),
        'failed': sum(any(c.find(tag) is not None for tag in ['failure', 'error']) for c in cases),
        'skipped': sum(c.find('skipped') is not None for c in cases),
    }
assert [counts[k]['total'] for k in counts] == [31, 36, 26], counts
assert sum(c['passed'] for c in counts.values()) == 93, counts
assert all(c['failed'] == 0 and c['skipped'] == 0 for c in counts.values()), counts
browser = {}
for name in ['report', 'fuel']:
    data = json.loads((root / f'browser_iter10_{name}' / 'results.json').read_text())
    browser[name] = {'total': len(data['results']), 'passed': sum(r['status'] == 'PASS' for r in data['results'])}
    assert browser[name] == {'total': 4, 'passed': 4}
    assert not data['diagnostics']['responses_429'] and not data['diagnostics']['page_errors']
baseline = json.loads((root / 'original_audit_iter10.json').read_text())
final = json.loads((root / 'closeout_iter10.json').read_text())
assert final.pop('exact_original_baseline_preserved') and final == baseline
guards = json.loads((root / 'preservation_iter10.json').read_text())
assert all(r['exact_all_tables_restored'] and r['counts'] == baseline['counts'] for r in guards)
summary = {'pytest': counts, 'pytest_total': 93, 'pytest_passed': 93,
           'browser': browser, 'all_original_tables_exactly_preserved': True,
           'nonfinite_original_values': baseline['nonfinite_total'], 'invalid_original_values': baseline['invalid_total']}
(root / 'execution_counts_iter10.json').write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))