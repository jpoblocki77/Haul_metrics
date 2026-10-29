"""Sanitized comparison of public ingress versus isolated app security responses."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import requests
from test_browser_security_regression import browser_login, BAD_ORIGINS
from test_full_regression import API, BASE

def sanitized(response):
    headers={k:v for k,v in response.headers.items() if k.lower() in ['access-control-allow-origin','access-control-allow-credentials','cache-control','access-control-allow-headers','access-control-allow-methods','server','via']}
    cookie=response.headers.get('set-cookie','')
    if cookie:headers['set-cookie-flags']=cookie.split(';',1)[1].split(',',1)[0]
    return {'status':response.status_code,'headers':headers}

if len(sys.argv)>1 and sys.argv[1]=='isolated':
    sys.path.insert(0,'/app/backend')
    from fastapi.testclient import TestClient
    from server import app
    from browser_security import configured_app_origin
    result={}
    with TestClient(app,base_url=BASE) as s:
        r=s.post('/api/auth/login',json={'username':os.environ['OWNER_USERNAME'],'password':os.environ['OWNER_PASSWORD']},headers={'Origin':BASE})
        result['login']=sanitized(r);csrf=r.json()['csrf_token']
        result['untrusted']=sanitized(s.post('/api/users',json={},headers={'Origin':'https://attacker.example','Host':'attacker.example','X-Forwarded-Host':'attacker.example'}))
        result['bad_preflight']=sanitized(s.options('/api/users',headers={'Origin':'https://attacker.example','Access-Control-Request-Method':'POST'}))
        result['logout']=sanitized(s.post('/api/auth/logout',json={},headers={'Origin':BASE,'X-CSRF-Token':csrf}))
        result['origin_config']=configured_app_origin()
    print(json.dumps(result))
else:
    s,data,r=browser_login();result={'public_login':sanitized(r)}
    result['public_get']=sanitized(s.get(API+'/auth/me',headers={'Origin':BASE},timeout=20))
    result['origins']=[]
    for origin in BAD_ORIGINS:
        result['origins'].append({'origin':origin,'actual':sanitized(s.get(API+'/auth/me',headers={'Origin':origin},timeout=20)),'preflight':sanitized(requests.options(API+'/users',headers={'Origin':origin,'Access-Control-Request-Method':'POST'},timeout=20))})
    result['public_logout']=sanitized(s.post(API+'/auth/logout',json={},headers={'Origin':BASE,'X-CSRF-Token':data['csrf_token']},timeout=20))
    with tempfile.TemporaryDirectory() as tmp:
        r=subprocess.run([sys.executable,__file__,'isolated'],env={**os.environ,'SQLITE_DB_FILE':tmp+'/test.db'},capture_output=True,text=True,timeout=30)
        assert r.returncode==0,r.stderr
        result['isolated_app']=json.loads(r.stdout)
    Path(os.environ.get('SECURITY_BOUNDARY_REPORT','/app/test_reports/security_boundary_iter8.json')).write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))