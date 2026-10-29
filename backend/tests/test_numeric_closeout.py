"""Disposable actual application numeric CRUD, derived-write and encrypted archive regressions."""
import base64
import copy
import json
import math
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parents[1]))

FIELDS = [('income', 'amount'), ('expenses', 'amount'), ('trucks', 'tank_gallons'),
          ('fuel', 'gallons'), ('fuel', 'price_per_gallon'), ('fuel', 'miles'),
          ('loads', 'pay'), ('loads', 'miles'), ('inspections', 'fine_amount')]
POSITIVE = {'tank_gallons', 'gallons', 'price_per_gallon'}
BAD = [('string_nan', 'NaN', False), ('string_inf', 'Infinity', False),
       ('string_minus_inf', '-Infinity', False), ('raw_nan', 'NaN', True),
       ('raw_inf', 'Infinity', True), ('raw_minus_inf', '-Infinity', True),
       ('giant_exponent', '1e999', True), ('huge_finite', '1e16', True)]


def snapshot():
    from db import get_conn
    with get_conn() as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        return {t: sorted([dict(r) for r in conn.execute(f'SELECT * FROM "{t}"')], key=lambda r: json.dumps(r, sort_keys=True)) for t in tables}


@pytest.fixture
def isolated(tmp_path):
    import db
    from server import app, APP_ORIGIN
    patch = pytest.MonkeyPatch()
    patch.setattr(db, 'DB_PATH', tmp_path / 'company.db')
    try:
        with TestClient(app, base_url=APP_ORIGIN, raise_server_exceptions=False) as client:
            response = client.post('/api/auth/login', json={'username': os.environ['OWNER_USERNAME'], 'password': os.environ['OWNER_PASSWORD']})
            assert response.status_code == 200
            client.headers['Authorization'] = 'Bearer ' + response.json()['token']
            truck = client.post('/api/trucks', json={'truck_number': 'TEST_numeric', 'tank_gallons': 100}).json()
            payloads = {'income': {'date': '2026-10-29', 'amount': 12, 'source': 'TEST_numeric'},
                        'expenses': {'date': '2026-10-29', 'amount': 5, 'description': 'TEST_numeric'},
                        'trucks': {'truck_number': 'TEST_numeric_update', 'tank_gallons': 100},
                        'fuel': {'date': '2026-10-29', 'truck_id': truck['id'], 'gallons': 10, 'price_per_gallon': 4, 'miles': 60},
                        'loads': {'origin': 'TEST_origin', 'destination': 'TEST_destination', 'pay': 50, 'miles': 100},
                        'inspections': {'date': '2026-10-29', 'result': 'Fined', 'fine_amount': 20}}
            ids = {}
            for table, payload in payloads.items():
                r = client.post('/api/' + table, json=payload)
                assert r.status_code == 200, r.text
                ids[table] = r.json()['id']
            yield client, payloads, ids
    finally:
        patch.undo()


def assert_healthy(client):
    for table in ['income', 'expenses', 'trucks', 'fuel', 'loads', 'inspections']:
        r = client.get('/api/' + table)
        assert r.status_code == 200 and isinstance(r.json(), list)
    r = client.get('/api/stats/dashboard')
    assert r.status_code == 200 and math.isfinite(r.json()['profit'])


@pytest.mark.parametrize('table,field', FIELDS)
@pytest.mark.parametrize('method', ['POST', 'PUT'])
def test_create_update_numeric_attacks(isolated, table, field, method):
    client, payloads, ids = isolated
    baseline = snapshot()
    attacks = list(BAD)
    if field in POSITIVE:
        attacks += [('tiny_positive', '1e-320', True), ('zero', '0', True), ('negative', '-1', True)]
    if field == 'miles':
        attacks += [('negative_miles', '-1', True)]
    for label, value, raw in attacks:
        payload = {**payloads[table], field: '__NUMERIC__', 'password': 'TEST_DO_NOT_ECHO_SECRET'}
        if table == 'trucks' and method == 'POST':
            payload['truck_number'] = 'TEST_numeric_attack_' + label
        content = json.dumps(payload).replace('"__NUMERIC__"', value if raw else json.dumps(value))
        path = '/api/' + table + ('/' + str(ids[table]) if method == 'PUT' else '')
        r = client.request(method, path, content=content, headers={'Content-Type': 'application/json'})
        assert r.status_code == 422, (table, field, method, label, r.status_code, r.text)
        errors = r.json()['detail']
        assert errors and all(set(e) == {'loc', 'msg', 'type'} for e in errors)
        assert 'TEST_DO_NOT_ECHO_SECRET' not in r.text
        assert snapshot() == baseline, (table, field, method, label, 'MUTATION')
        assert_healthy(client)
        print('PASS_NUMERIC', table, field, method, label)


def test_valid_finite_negative_adjustments_tiny_and_extreme_fuel(isolated):
    client, payloads, ids = isolated
    for table, field in [('income', 'amount'), ('expenses', 'amount'), ('loads', 'pay'), ('inspections', 'fine_amount')]:
        payload = {**payloads[table], field: -12.5}
        r = client.put(f'/api/{table}/{ids[table]}', json=payload)
        assert r.status_code == 200 and r.json()[field] == -12.5
        assert next(x for x in client.get('/api/' + table).json() if x['id'] == ids[table])[field] == -12.5
    for gallons, price, miles in [(1e-6, 4, 1e-6), (1e15, 1e15, 1e15), (1e-6, 1e-6, 1e15)]:
        r = client.put(f"/api/fuel/{ids['fuel']}", json={**payloads['fuel'], 'gallons': gallons, 'price_per_gallon': price, 'miles': miles})
        assert r.status_code == 200, r.text
        assert r.json()['total'] == round(gallons * price, 2)
        assert r.json()['mpg'] == round(miles / gallons, 2)
        assert_healthy(client)


def test_nonfinite_derived_values_rejected_before_sql_write(isolated):
    from db import get_conn
    from server import insert, update
    _, _, ids = isolated
    baseline = snapshot()
    for value in [float('inf'), float('-inf'), float('nan')]:
        for write in ['insert', 'update']:
            with pytest.raises(Exception) as caught:
                with get_conn() as conn:
                    if write == 'insert':
                        insert(conn, 'income', {'date': '2026-10-29', 'source': 'TEST_derived', 'amount': value})
                    else:
                        update(conn, 'income', ids['income'], {'amount': value})
            assert caught.value.status_code == 422
            assert snapshot() == baseline


@pytest.mark.parametrize('attack', ['NaN', 'Infinity', '-Infinity', 'giant', 'huge', 'tiny_fuel', 'tiny_price', 'tiny_tank', 'stored_REAL'])
def test_malicious_backup_no_mutation(isolated, attack):
    from backups import MAGIC, cipher
    client, _, _ = isolated
    passphrase = 'TEST_private_numeric_archive!'
    exported = client.post('/api/backup/export', json={'passphrase': passphrase})
    assert exported.status_code == 200
    n = len(MAGIC)
    data = json.loads(cipher(passphrase, exported.content[n:n+16]).decrypt(exported.content[n+16:]))
    data = copy.deepcopy(data)
    if attack in ['NaN', 'Infinity', '-Infinity', 'giant', 'huge']:
        data['tables']['income'][0]['amount'] = {'NaN': float('nan'), 'Infinity': float('inf'), '-Infinity': float('-inf'), 'giant': float('1e999'), 'huge': 1e16}[attack]
    elif attack == 'tiny_fuel':
        data['tables']['fuel'][0]['gallons'] = 1e-320
    elif attack == 'tiny_price':
        data['tables']['fuel'][0]['price_per_gallon'] = 1e-320
    elif attack == 'tiny_tank':
        data['tables']['trucks'][0]['tank_gallons'] = 1e-320
    else:
        data['tables']['fuel'][0]['total'] = 1e31
    salt = os.urandom(16)
    archive = MAGIC + salt + cipher(passphrase, salt).encrypt(json.dumps(data).encode())
    payload = {'archive': base64.b64encode(archive).decode(), 'passphrase': passphrase,
               'confirm': 'RESTORE MCCOY', 'owner_password': os.environ['OWNER_PASSWORD']}
    baseline = snapshot()
    for endpoint in ['inspect', 'restore']:
        r = client.post('/api/backup/' + endpoint, json=payload)
        assert r.status_code == 400 and 'damaged file' in r.json()['detail'], r.text
        assert snapshot() == baseline
        assert_healthy(client)


def test_valid_archive_roundtrip_and_password_validation_privacy(isolated):
    from backups import MAGIC, cipher
    client, _, _ = isolated
    # Password validation must not echo raw input (including secrets nested in numeric requests).
    r = client.post('/api/users', json={'username': 'TEST_privacy', 'password': 'abc', 'role': 'invalid'})
    assert r.status_code == 422 and 'abc' not in r.text
    assert all(set(e) == {'loc', 'msg', 'type'} for e in r.json()['detail'])
    passphrase = 'TEST_private_numeric_archive!'
    r = client.post('/api/backup/export', json={'passphrase': passphrase})
    assert r.status_code == 200 and b'password_hash' not in r.content
    n = len(MAGIC)
    data = json.loads(cipher(passphrase, r.content[n:n+16]).decrypt(r.content[n+16:]))
    payload = {'archive': base64.b64encode(r.content).decode(), 'passphrase': passphrase,
               'confirm': 'RESTORE MCCOY', 'owner_password': os.environ['OWNER_PASSWORD']}
    inspected = client.post('/api/backup/inspect', json=payload)
    assert inspected.status_code == 200 and inspected.json()['counts'] == {k: len(v) for k, v in data['tables'].items()}
    restored = client.post('/api/backup/restore', json=payload)
    assert restored.status_code == 200 and restored.json()['sign_in_required']
    assert client.get('/api/auth/me').status_code == 401
    login = client.post('/api/auth/login', json={'username': os.environ['OWNER_USERNAME'], 'password': os.environ['OWNER_PASSWORD']})
    assert login.status_code == 200
    client.headers['Authorization'] = 'Bearer ' + login.json()['token']
    actual = snapshot()
    for table, expected in data['tables'].items():
        if table == 'users':
            assert [r['password_hash'] for r in actual[table]] == [r['password_hash'] for r in expected]
        else:
            assert actual[table] == sorted(expected, key=lambda r: json.dumps(r, sort_keys=True))
    assert_healthy(client)