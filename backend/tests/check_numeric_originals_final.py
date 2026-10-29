"""Read-only final numeric audit and exact all-table fingerprint, without original repairs."""
import hashlib
import json
import math
import os
import sqlite3
import sys
from pathlib import Path

from dotenv import load_dotenv
from regression_safety import database_path, table_snapshot

load_dotenv('/app/backend/.env')
load_dotenv('/app/frontend/.env')
original = table_snapshot()
positive = {('trucks', 'tank_gallons'), ('fuel', 'gallons'), ('fuel', 'price_per_gallon')}
nonnegative = {('loads', 'miles'), ('fuel', 'miles')}
derived = {('fuel', 'total'): 1e30, ('fuel', 'mpg'): 1e21}
columns = {}
with sqlite3.connect(f'file:{database_path()}?mode=ro', uri=True) as conn:
    for table in original:
        for column in [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")') if r[2] == 'REAL']:
            values = [r[0] for r in conn.execute(f'SELECT "{column}" FROM "{table}"')]
            key = (table, column)
            minimum = 1e-6 if key in positive else 0 if key in nonnegative or key in derived else -1e15
            maximum = derived.get(key, 1e15)
            def invalid(value):
                return value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value) or not minimum <= value <= maximum)
            columns[f'{table}.{column}'] = {
                'rows': len(values),
                'nonfinite': sum(isinstance(v, (int, float)) and not math.isfinite(v) for v in values),
                'invalid': sum(invalid(v) or (v is None and key in positive) for v in values),
            }
summary = {
    'counts': {k: len(v) for k, v in original.items()},
    'numeric_columns': columns,
    'nonfinite_total': sum(v['nonfinite'] for v in columns.values()),
    'invalid_total': sum(v['invalid'] for v in columns.values()),
    'all_rows_fingerprint': hashlib.sha256(json.dumps(original, sort_keys=True).encode()).hexdigest(),
    'all_original_password_hashes_bcrypt_2b': all(r['password_hash'].startswith('$2b$') for r in original['users']),
}
path = Path(os.environ['FINAL_NUMERIC_AUDIT_BASELINE'])
if '--closeout' in sys.argv:
    assert json.loads(path.read_text()) == summary, 'Original complete SQLite state differs from baseline'
    summary['exact_original_baseline_preserved'] = True
    Path(os.environ['FINAL_NUMERIC_AUDIT_CLOSEOUT']).write_text(json.dumps(summary, indent=2))
else:
    assert not path.exists(), 'Do not overwrite original baseline'
    path.write_text(json.dumps(summary, indent=2))
print('READ_ONLY_AUDIT', summary['nonfinite_total'], 'nonfinite;', summary['invalid_total'], 'invalid; no data edited')
assert summary['invalid_total'] == 0 and summary['all_original_password_hashes_bcrypt_2b']