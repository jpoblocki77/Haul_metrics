"""Read-only original REAL audit and complete-row fingerprint; report counts, never company values."""
import hashlib
import json
import math
import sqlite3
import sys
from pathlib import Path
from dotenv import load_dotenv
from regression_safety import database_path, table_snapshot

load_dotenv('/app/backend/.env')
load_dotenv('/app/frontend/.env')
original = table_snapshot()
counts = {}
with sqlite3.connect(f'file:{database_path()}?mode=ro', uri=True) as conn:
    for table in original:
        columns = [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")') if r[2] == 'REAL']
        for column in columns:
            values = [r[0] for r in conn.execute(f'SELECT "{column}" FROM "{table}"')]
            counts[f'{table}.{column}'] = {'rows': len(values), 'nonfinite': sum(isinstance(v, (int, float)) and not math.isfinite(v) for v in values)}
summary = {'counts': {k: len(v) for k, v in original.items()}, 'nonfinite_REAL_counts': counts,
           'nonfinite_total': sum(v['nonfinite'] for v in counts.values()),
           'all_rows_fingerprint': hashlib.sha256(json.dumps(original, sort_keys=True).encode()).hexdigest()}
path = Path('/app/test_reports/original_audit_iter9.json')
if '--closeout' in sys.argv:
    assert json.loads(path.read_text()) == summary, 'Original complete SQLite state differs from baseline'
    summary['exact_original_baseline_preserved'] = True
    Path('/app/test_reports/closeout_iter9.json').write_text(json.dumps(summary, indent=2))
else:
    assert not path.exists(), 'Do not overwrite an original baseline'
    path.write_text(json.dumps(summary, indent=2))
print('PASS_READ_ONLY_AUDIT', summary['nonfinite_total'], 'nonfinite REAL values; counts only; no data edited')