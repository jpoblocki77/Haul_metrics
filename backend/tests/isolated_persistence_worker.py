# Fresh real application workers against a disposable SQLite file; no production DB or API mocks.
import json, os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from fastapi.testclient import TestClient
from server import app
from db import get_conn, one
statefile=Path(sys.argv[2])
def snap(seq):
    return {'session_id':'same-worker-session','sequence':seq,'raw':{'game':{'connected':True,'gameName':'ATS'},'job':{'sourceCity':'TEST_A','destinationCity':'TEST_B','income':100},'trailer':{'attached':True}}}
with TestClient(app) as client:
    if sys.argv[1]=='write':
        credentials={'username':os.environ['OWNER_USERNAME'],'password':os.environ['OWNER_PASSWORD']}
        a=client.post('/api/auth/login',json=credentials).json()['token']
        b=client.post('/api/auth/login',json=credentials).json()['token']
        headers={'Authorization':'Bearer '+b}
        d=client.post('/api/drivers',headers=headers,json={'name':'TEST_worker'}).json()
        t=client.post('/api/trucks',headers=headers,json={'truck_number':'TEST_worker','tank_gallons':100}).json()
        assert client.put('/api/telemetry/settings',headers=headers,json={'driver_id':d['id'],'truck_id':t['id'],'enabled':True,'server_url':'http://127.0.0.1:25555/api/ets2/telemetry'}).status_code==200
        assert client.post('/api/telemetry/ingest',headers=headers,json=snap(1)).json()['accepted']
        assert client.post('/api/auth/logout',headers={'Authorization':'Bearer '+a}).json()['ok']
        for _ in range(5):assert client.post('/api/auth/login',json={'username':'TEST_missing','password':'bad'}).status_code==401
        with get_conn() as conn:owner=one(conn,'SELECT password_hash,session_version FROM users WHERE username=?',(credentials['username'],))
        statefile.write_text(json.dumps({'a':a,'b':b,'owner':owner}))
    else:
        data=json.loads(statefile.read_text());headers={'Authorization':'Bearer '+data['b']}
        assert client.get('/api/auth/me',headers={'Authorization':'Bearer '+data['a']}).status_code==401
        assert client.get('/api/auth/me',headers=headers).json()['role']=='owner'
        assert client.post('/api/auth/login',json={'username':'TEST_missing','password':'bad'}).status_code==429
        assert client.post('/api/telemetry/ingest',headers=headers,json=snap(2)).json()['accepted']
        assert len(client.get('/api/telemetry/events',headers=headers).json())==1
        assert client.get('/api/telemetry/status',headers=headers).json()['source']['live']['connected']
        with get_conn() as conn:owner=one(conn,'SELECT password_hash,session_version FROM users WHERE username=?',(os.environ['OWNER_USERNAME'],))
        assert owner==data['owner'],'Startup modified owner credentials/session'
        print('PASS persisted lockout, current-token revocation, separate live session, telemetry state/dedupe and creation-only seed across fresh workers')