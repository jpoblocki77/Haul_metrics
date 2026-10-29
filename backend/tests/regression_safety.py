"""Private SQLite online snapshots: preserve exact live sources, accounts and security state."""
import contextlib
import json
import os
import sqlite3
import tempfile
from pathlib import Path
from dotenv import dotenv_values

def database_path():
    value = os.environ.get('SQLITE_DB_FILE') or dotenv_values('/app/backend/.env')['SQLITE_DB_FILE']
    return Path('/app/backend') / value

def table_snapshot(path=None):
    with sqlite3.connect(path or database_path()) as conn:
        conn.row_factory = sqlite3.Row
        names = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        return {t: sorted([dict(r) for r in conn.execute('SELECT * FROM "'+t+'"')], key=lambda r: json.dumps(r,sort_keys=True)) for t in names}

@contextlib.contextmanager
def safeguard(label):
    # Plaintext backup is private and ephemeral, never placed in public report artifacts.
    with tempfile.TemporaryDirectory(prefix='mccoy-private-') as directory:
        os.chmod(directory, 0o700)
        backup = Path(directory)/'original.sqlite'
        with sqlite3.connect(database_path()) as live, sqlite3.connect(backup) as saved:
            live.backup(saved)
        os.chmod(backup,0o600)
        original = table_snapshot(backup)
        try:
            yield original
        finally:
            with sqlite3.connect(backup) as saved, sqlite3.connect(database_path()) as live:
                saved.backup(live)
            actual = table_snapshot()
            assert actual == original, 'EXACT SQLITE PRESERVATION FAILED: '+label
            report=Path(os.environ.get('REGRESSION_PRESERVATION_REPORT', '/app/test_reports/preservation_iter8.json'))
            history=json.loads(report.read_text()) if report.exists() else []
            history.append({'label':label,'exact_all_tables_restored':True,'counts':{k:len(v) for k,v in actual.items()},'private_sqlite_snapshot_deleted_on_exit':True})
            report.write_text(json.dumps(history,indent=2))
            print('EXACT_PRESERVATION_PASS',label,{k:len(v) for k,v in actual.items()},flush=True)