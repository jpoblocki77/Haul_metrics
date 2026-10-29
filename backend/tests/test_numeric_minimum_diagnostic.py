"""Disposable RCA: merged lower bounds, zero tank fallback, and self-export compatibility."""
import base64
import json
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parents[1]))


def test_positive_minimum_and_zero_tank_fallback(tmp_path, monkeypatch):
    import db
    from server import app, APP_ORIGIN, TruckIn, FuelIn
    from test_numeric_closeout import snapshot
    monkeypatch.setattr(db, 'DB_PATH', tmp_path / 'diagnostic.db')
    results = {'schema_minima': {'tank_gallons': TruckIn.model_json_schema()['properties']['tank_gallons']['minimum'],
                                 'price_per_gallon': FuelIn.model_json_schema()['properties']['price_per_gallon']['minimum']}, 'requests': []}
    failures = []
    with TestClient(app, base_url=APP_ORIGIN, raise_server_exceptions=False) as c:
        login = c.post('/api/auth/login', json={'username': os.environ['OWNER_USERNAME'], 'password': os.environ['OWNER_PASSWORD']})
        assert login.status_code == 200
        c.headers['Authorization'] = 'Bearer ' + login.json()['token']
        good = c.post('/api/trucks', json={'truck_number': 'TEST_valid', 'tank_gallons': 100}).json()
        baseline = snapshot()
        zero_truck = None
        for value in [1e-320, 0, -1]:
            for table, field, payload in [('trucks', 'tank_gallons', {'truck_number': 'TEST_diagnostic_' + str(value), 'tank_gallons': value}),
                                           ('fuel', 'price_per_gallon', {'date': '2026-10-29', 'truck_id': good['id'], 'gallons': 10, 'miles': 60, 'price_per_gallon': value})]:
                r = c.post('/api/' + table, json=payload)
                results['requests'].append({'table': table, 'field': field, 'value': str(value), 'status': r.status_code})
                if r.status_code != 422:
                    failures.append((table, field, str(value), r.status_code))
                else:
                    assert snapshot() == baseline, 'Rejected quantity mutated DB'
                if table == 'trucks' and value == 0 and r.status_code == 200:
                    zero_truck = r.json()['id']
        if zero_truck:
            r = c.post('/api/fuel', json={'date': '2026-10-29', 'truck_id': zero_truck, 'price_per_gallon': 4, 'miles': 60})
            results['zero_tank_default_fuel'] = {'status': r.status_code, 'body': r.text}
        passphrase = 'TEST_private_numeric_archive!'
        r = c.post('/api/backup/export', json={'passphrase': passphrase})
        assert r.status_code == 200
        check = c.post('/api/backup/inspect', json={'passphrase': passphrase, 'archive': base64.b64encode(r.content).decode()})
        results['self_export_inspect'] = {'status': check.status_code, 'body': check.json()}
        assert check.status_code == 200
        results['legacy_tank_fallback'] = []
        # Poison only this disposable DB; fallback validation must precede division and writes.
        for value in [0, -1, 1e-320, 1e16, float('inf'), float('-inf')]:
            with db.get_conn() as conn:
                conn.execute('UPDATE trucks SET tank_gallons=? WHERE id=?', (value, good['id']))
            poisoned = snapshot()
            r = c.post('/api/fuel', json={'date': '2026-10-29', 'truck_id': good['id'], 'price_per_gallon': 4, 'miles': 60})
            results['legacy_tank_fallback'].append({'value': str(value), 'status': r.status_code})
            assert r.status_code == 422, (str(value), r.status_code, r.text)
            assert snapshot() == poisoned, 'Invalid legacy fallback mutated DB'
        assert all(v == 1e-6 for v in results['schema_minima'].values()), results['schema_minima']
        Path(os.environ.get('NUMERIC_DIAGNOSTIC_REPORT', '/app/test_reports/numeric_minimum_rca_iter9.json')).write_text(json.dumps(results, indent=2))
        print('MINIMUM_DIAGNOSTICS', json.dumps(results))
    assert not failures, failures