# Disposable database security: fail-closed config, host spoofing, cookie flags and hostile numeric input.
import os
import sys
from pathlib import Path
import pytest
from dotenv import load_dotenv
sys.path.insert(0,str(Path(__file__).parents[1]))
load_dotenv('/app/backend/.env')
import browser_security as policy

def test_hosted_origin_fails_closed(monkeypatch):
    monkeypatch.delenv('MCCOY_DESKTOP',raising=False)
    monkeypatch.delenv('REACT_APP_BACKEND_URL',raising=False)
    monkeypatch.setattr(policy,'dotenv_values',lambda path:{})
    with pytest.raises(RuntimeError):policy.configured_app_origin()
    monkeypatch.setenv('REACT_APP_BACKEND_URL','http://app.example')
    with pytest.raises(RuntimeError):policy.configured_app_origin()

def test_desktop_loopback_exact_configuration(monkeypatch):
    monkeypatch.setenv('MCCOY_DESKTOP','1')
    monkeypatch.setenv('DESKTOP_APP_ORIGIN','http://127.0.0.1:43210')
    assert policy.configured_app_origin()=='http://127.0.0.1:43210' and not policy.secure_cookie()
    monkeypatch.setenv('DESKTOP_APP_ORIGIN','http://attacker.example')
    with pytest.raises(RuntimeError):policy.configured_app_origin()

@pytest.fixture
def client(tmp_path,monkeypatch):
    import db
    monkeypatch.setattr(db,'DB_PATH',tmp_path/'isolated-security.db')
    from server import app, APP_ORIGIN
    from fastapi.testclient import TestClient
    with TestClient(app,base_url=APP_ORIGIN,raise_server_exceptions=False) as c:
        r=c.post('/api/auth/login',json={'username':os.environ['OWNER_USERNAME'],'password':os.environ['OWNER_PASSWORD']})
        assert r.status_code==200
        assert all(s in r.headers['set-cookie'].lower() for s in ['httponly','secure','samesite=lax','path=/'])
        c.csrf=r.json()['csrf_token'];c.token=r.json()['token']
        yield c

def test_cookie_flags_origin_host_spoof_and_logout(client):
    from server import APP_ORIGIN
    before=client.get('/api/users').json()
    from test_browser_security_regression import BAD_ORIGINS
    for origin in BAD_ORIGINS:
        r=client.post('/api/users',json={'username':'TEST_intruder','password':'secret123','role':'owner'},headers={'Origin':origin,'Host':APP_ORIGIN.split('://')[1],'X-Forwarded-Host':APP_ORIGIN.split('://')[1]})
        assert r.status_code==403 and r.json()['code']=='untrusted_origin'
        assert 'access-control-allow-origin' not in r.headers and 'access-control-allow-credentials' not in r.headers
        p=client.options('/api/users',headers={'Origin':origin,'Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'content-type,x-csrf-token'})
        assert p.status_code==400 and 'access-control-allow-origin' not in p.headers and 'access-control-allow-credentials' not in p.headers
    assert client.get('/api/users').json()==before
    r=client.post('/api/auth/logout',json={},headers={'Origin':APP_ORIGIN,'X-CSRF-Token':client.csrf,'Host':'attacker.example','X-Forwarded-Host':'attacker.example'})
    assert r.status_code==200 and r.json()['ok']
    assert all(s in r.headers['set-cookie'].lower() for s in ['httponly','secure','samesite=lax','max-age=0'])
    assert r.headers['cache-control']=='no-store'
    assert client.get('/api/auth/me',headers={'Authorization':'Bearer '+client.token}).status_code==401

@pytest.mark.parametrize('amount',['NaN','Infinity','-Infinity'])
def test_nonfinite_manual_financial_input_rejected_without_persistence(client,amount):
    headers={'Authorization':'Bearer '+client.token}
    before=client.get('/api/income').json()
    r=client.post('/api/income',json={'date':'2026-10-29','source':'TEST_nonfinite','amount':amount},headers=headers)
    from db import get_conn, rows
    with get_conn() as c: persisted=rows(c,'SELECT id,source,amount FROM income')
    print('NONFINITE_DIAGNOSTIC',amount,'POST',r.status_code,'GET',client.get('/api/income').status_code,'DASHBOARD',client.get('/api/stats/dashboard').status_code,'PERSISTED',persisted)
    assert r.status_code==422 and r.json()['detail'],(amount,r.status_code,r.text)
    assert client.get('/api/income').json()==before

def test_sql_payload_is_text_not_query_and_password_hashes_private(client):
    headers={'Authorization':'Bearer '+client.token}
    value="TEST_'); DROP TABLE users; -- <img src=x onerror=alert(1)>"
    r=client.post('/api/drivers',json={'name':value},headers=headers)
    assert r.status_code==200 and r.json()['name']==value
    users=client.get('/api/users').json()
    assert len(users)==1 and all('password_hash' not in row for row in users)