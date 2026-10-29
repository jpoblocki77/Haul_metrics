# Full regression: SQLite CRUD, auth, reports, telemetry, encrypted backup/restore.
import ast
import base64
import copy
import csv
import io
import json
import os
from pathlib import Path
import uuid
import pytest
import requests
from regression_safety import safeguard
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

BASE = os.environ['REACT_APP_BACKEND_URL'].rstrip('/')
API = BASE + '/api'
PASS = 'TEST_regression_backup_2026!'
ROOT = Path('/app/test_reports')
TABLES = ['users','categories','trucks','drivers','loads','income','expenses','fuel','inspections','telemetry_sources','telemetry_events']

def login(username='owner', password='trucker123'):
    s = requests.Session()
    r = s.post(API+'/auth/login', json={'username':username,'password':password}, timeout=20)
    assert r.status_code == 200, r.text
    s.headers['Authorization'] = 'Bearer '+r.json()['token']
    s.user = r.json()['user']
    return s

def request(s, method, path, status=200, **kw):
    r = s.request(method, API+path, timeout=30, **kw)
    assert r.status_code == status, (method,path,r.status_code,r.text[:600])
    return r

def decrypt(blob):
    n = len(b'MCCOY-BACKUP-1\n')
    key = Scrypt(salt=blob[n:n+16],length=32,n=2**14,r=8,p=1).derive(PASS.encode())
    return json.loads(Fernet(base64.urlsafe_b64encode(key)).decrypt(blob[n+16:]))

def encrypt(data):
    salt = os.urandom(16)
    key = Scrypt(salt=salt,length=32,n=2**14,r=8,p=1).derive(PASS.encode())
    return b'MCCOY-BACKUP-1\n'+salt+Fernet(base64.urlsafe_b64encode(key)).encrypt(json.dumps(data).encode())

def archive(s):
    return request(s,'POST','/backup/export',json={'passphrase':PASS}).content

def body(blob):
    return {'archive':base64.b64encode(blob).decode(),'passphrase':PASS}

def normalize(data):
    d = copy.deepcopy(data['tables'])
    for u in d['users']: u.pop('session_version',None)
    return {k:sorted(v,key=lambda x:json.dumps(x,sort_keys=True)) for k,v in d.items()}

@pytest.fixture(scope='module')
def ctx():
    guard = safeguard('shared API fixture')
    guard.__enter__()
    ROOT.mkdir(exist_ok=True)
    s = login()
    original = archive(s)
    snapshot_path = ROOT/('api_safety_'+uuid.uuid4().hex+'.mccoy')
    snapshot_path.touch(mode=0o600)
    snapshot_path.write_bytes(original)
    data = decrypt(original)
    c = {'owner':s,'initial':original,'initial_data':data,'prefix':'test_r4_'+uuid.uuid4().hex[:8], 'created':[]}
    try:
        yield c
    finally:
        try:
            s = login()
            r = request(s,'POST','/backup/restore',json={**body(original),'confirm':'RESTORE MCCOY','owner_password':'trucker123'})
            assert r.json()['sign_in_required'] is True
            s = login()
            final = decrypt(archive(s))
            assert normalize(final) == normalize(data), 'INITIAL COMPANY STATE NOT RESTORED'
        finally:
            guard.__exit__(None,None,None)

def create(c, table, payload, s=None):
    s = s or c['owner']
    d = request(s,'POST','/'+table,json=payload).json()
    c['created'].append((table,d['id']))
    assert next(x for x in request(s,'GET','/'+table).json() if x['id']==d['id']).items() >= d.items()
    return d

def setup_mapping(c, role='dispatcher'):
    s = c['owner']
    name = c['prefix']+'_'+uuid.uuid4().hex[:4]
    u = request(s,'POST','/users',json={'username':name,'password':'secret123','role':role}).json()
    a = login(name,'secret123')
    d = create(c,'drivers',{'name':'TEST_'+name})
    t = create(c,'trucks',{'truck_number':'TEST_'+name,'tank_gallons':100})
    cfg = {'driver_id':d['id'],'truck_id':t['id'],'server_url':'http://127.0.0.1:25555/api/ets2/telemetry','enabled':True}
    request(a,'PUT','/telemetry/settings',json=cfg)
    return a,d,t,cfg

def sample(seq, session='regression', fuel=100, odo=1000, connected=True, paused=False, job=None, attached=False):
    return {'session_id':session,'sequence':seq,'raw':{'game':{'connected':connected,'paused':paused,'gameName':'ATS'},'truck':{'fuel':fuel,'fuelCapacity':200,'odometer':odo,'speed':0},'job':job or {},'trailer':{'attached':attached,'name':'TEST_Cargo'}}}

def events(a): return request(a,'GET','/telemetry/events').json()

def test_01_auth_cookies_cors_lockout(ctx):
    s=ctx['owner']
    assert request(s,'GET','/auth/me').json()['role']=='owner'
    r=request(requests.Session(),'POST','/auth/login',json={'username':'owner','password':'trucker123'})
    cookie=r.headers['set-cookie'].lower()
    assert all(v in cookie for v in ['httponly','secure'])
    # Public attack resistance is distinct from strict source Lax policy (isolated suite).
    assert 'samesite=lax' in cookie or ('samesite=none' in cookie and 'partitioned' in cookie)
    for ep in ['/trucks','/users','/stats/dashboard']:
        assert request(requests.Session(),'GET',ep,401).json()['detail']=='Not authenticated'
    uname=ctx['prefix']+'_lock'
    for _ in range(5): request(requests.Session(),'POST','/auth/login',401,json={'username':uname,'password':'wrong'})
    assert 'Too many' in request(requests.Session(),'POST','/auth/login',429,json={'username':uname,'password':'wrong'}).json()['detail']
    r=request(s,'OPTIONS','/auth/login',headers={'Origin':BASE,'Access-Control-Request-Method':'POST'})
    assert r.headers['access-control-allow-origin']==BASE
    assert r.headers['access-control-allow-credentials']=='true'

def test_02_users_create_edit_revoke_permissions(ctx):
    s=ctx['owner']; name=ctx['prefix']+'_user'
    u=request(s,'POST','/users',json={'username':name,'password':'secret123'}).json()
    a=login(name,'secret123')
    assert a.user['role']=='dispatcher'
    request(s,'POST','/users',400,json={'username':name,'password':'secret123'})
    for payload in [{'username':'ab','password':'secret123'},{'username':'bad name!','password':'secret123'},{'username':name+'a','password':'123'}]:
        assert 'detail' in request(s,'POST','/users',422,json=payload).json()
    for ep,method,payload in [('/users','GET',None),('/users','POST',{'username':'TEST_forbidden','password':'secret123'}),('/users/'+str(u['id']),'PATCH',{'role':'owner'}),('/backup/export','POST',{'passphrase':PASS}),('/test-data','POST',None),('/test-data','DELETE',None)]:
        assert 'owner' in request(a,method,ep,403,json=payload).json()['detail']
    request(s,'PATCH','/users/'+str(u['id']),json={'role':'owner','password':'changed123'})
    request(a,'GET','/auth/me',401)
    request(requests.Session(),'POST','/auth/login',401,json={'username':name,'password':'secret123'})
    a=login(name,'changed123'); assert a.user['role']=='owner'
    request(a,'PATCH','/users/'+str(u['id']),400,json={'role':'dispatcher'})
    request(a,'DELETE','/users/'+str(u['id']),400)
    request(a,'DELETE','/users/'+str(s.user['id']),400)
    request(s,'PATCH','/users/'+str(u['id']),json={'role':'dispatcher'})
    request(a,'GET','/auth/me',401)
    assert login(name,'changed123').user['role']=='dispatcher'
    request(s,'PATCH','/users/999999',404,json={'password':'secret123'})
    request(s,'PATCH','/users/'+str(u['id']),400,json={})
    request(s,'DELETE','/users/'+str(u['id']))
    assert not any(x['id']==u['id'] for x in request(s,'GET','/users').json())

def test_03_all_crud_dispatcher_and_relationships(ctx):
    s=ctx['owner']; a,d,t,cfg=setup_mapping(ctx)
    cat=create(ctx,'categories',{'name':'TEST_'+ctx['prefix']},a)
    payloads={'drivers':{'name':'TEST_'+ctx['prefix']+'_CRUD'},'trucks':{'truck_number':'TEST_'+ctx['prefix']+'_CRUD','tank_gallons':180},'categories':{'name':'TEST_'+ctx['prefix']+'_CRUD'},'income':{'date':'2026-08-01','source':'TEST_manual','amount':77,'driver_id':d['id'],'truck_id':t['id']},'expenses':{'date':'2026-08-01','amount':33,'description':'TEST_exp','category_id':cat['id']},'fuel':{'date':'2026-08-01','truck_id':t['id'],'driver_id':d['id'],'price_per_gallon':4,'miles':600},'loads':{'origin':'TEST_A','destination':'TEST_B','pay':900,'driver_id':d['id'],'truck_id':t['id'],'delivered_date':'2026-08-01','status':'On Time'},'inspections':{'date':'2026-08-01','result':'Out of Service','fine_amount':100,'fine_reason':'TEST_brakes','driver_id':d['id'],'truck_id':t['id']}}
    for table,p in payloads.items():
        r=create(ctx,table,p,a); rid=r['id']; p=dict(p)
        key=next(k for k in ['name','truck_number','amount','price_per_gallon','pay','fine_amount'] if k in p)
        p[key]=p[key]+'_edit' if isinstance(p[key],str) else p[key]+1
        u=request(a,'PUT',f'/{table}/{rid}',json=p).json(); assert u[key]==p[key]
        assert next(x for x in request(a,'GET','/'+table).json() if x['id']==rid)[key]==p[key]
        request(a,'DELETE',f'/{table}/{rid}',403)
        if table=='loads':
            linked=[x for x in request(s,'GET','/income').json() if x['load_id']==rid]
            assert len(linked)==1 and linked[0]['amount']==901
        request(s,'DELETE',f'/{table}/{rid}')
        assert not any(x['id']==rid for x in request(s,'GET','/'+table).json())
        request(s,'DELETE',f'/{table}/{rid}',404)
        request(s,'PUT',f'/{table}/{rid}',404,json=p)
        if table=='loads': assert not any(x['load_id']==rid for x in request(s,'GET','/income').json())
    r=request(s,'POST','/expenses',400,json={'date':'2026-01-01','amount':1,'category_id':999999})
    assert 'reference' in r.json()['detail']
    request(s,'POST','/fuel',400,json={'date':'2026-01-01','truck_id':999999,'price_per_gallon':4})
    for table,p in [('trucks',{'truck_number':'TEST_bad','tank_gallons':0}),('loads',{'origin':'A','destination':'B','status':'Early'}),('inspections',{'date':'2026-01-01','result':'bad'})]: request(s,'POST','/'+table,422,json=p)

def test_04_fuel_weighted_stats_dot_and_profile(ctx):
    a,d,t,cfg=setup_mapping(ctx); s=ctx['owner']
    f=create(ctx,'fuel',{'date':'2026-08-02','truck_id':t['id'],'driver_id':d['id'],'price_per_gallon':4,'miles':600})
    assert (f['gallons'],f['total'],f['mpg'])==(100,400,6)
    f2=create(ctx,'fuel',{'date':'2026-08-02','truck_id':t['id'],'driver_id':d['id'],'gallons':50,'price_per_gallon':3,'miles':500})
    create(ctx,'fuel',{'date':'2026-08-02','truck_id':t['id'],'driver_id':d['id'],'gallons':25,'price_per_gallon':3})
    st=next(x for x in request(s,'GET','/stats/trucks').json() if x['id']==t['id'])
    assert st['avg_mpg']==pytest.approx(1100/150) and st['gallons_bought']==175
    p=create(ctx,'inspections',{'date':'2026-08-02','driver_id':d['id'],'result':'Fined','fine_amount':250,'fine_reason':'TEST_speed'})
    request(s,'PUT',f"/inspections/{p['id']}",json={'date':'2026-08-02','driver_id':d['id'],'result':'Passed','fine_amount':200,'fine_reason':'bad'})
    r=next(x for x in request(s,'GET','/inspections').json() if x['id']==p['id']); assert r['fine_amount'] is None and r['fine_reason'] is None
    p=request(s,'GET',f"/drivers/{d['id']}/profile",params={'start':'2026-08-01','end':'2026-08-31'}).json()
    assert p['stats']['avg_mpg']==pytest.approx(1100/150) and len(p['fuel'])==3
    assert p['mpg_trend'][0]['mpg']==pytest.approx(1100/150)
    empty=request(s,'GET',f"/drivers/{d['id']}/profile",params={'start':'1990-01-01','end':'1990-01-31'}).json()
    assert empty['loads']==[] and empty['fuel']==[] and empty['trophies']==p['trophies']
    assert request(s,'GET','/drivers/999999/profile',404).json()['detail']=='Driver not found'

def test_05_dashboard_report_charts_csv_ranges(ctx):
    s=ctx['owner']; tables={t:request(s,'GET','/'+t).json() for t in ['income','expenses','fuel','loads','inspections']}
    for start,end in [('2026-08-01','2026-08-31'),('1990-01-01','1990-01-31'),(None,None)]:
        p={'start':start,'end':end}; selected={t:[x for x in v if (not start or (x.get('delivered_date') or x.get('due_date') or x.get('date') or '')>=start) and (not end or (x.get('delivered_date') or x.get('due_date') or x.get('date') or '')<=end)] for t,v in tables.items()}
        d=request(s,'GET','/stats/dashboard',params=p).json(); inc=sum(x['amount'] for x in selected['income']); exp=sum(x['amount'] for x in selected['expenses'])+sum(x['total'] for x in selected['fuel'])+sum(x['fine_amount'] or 0 for x in selected['inspections'])
        assert d['income']==pytest.approx(inc) and d['expenses']==pytest.approx(exp) and d['profit']==pytest.approx(inc-exp)
        chart=request(s,'GET','/stats/report-charts',params=p).json()
        assert sum(x['income'] for x in chart['cash'])==pytest.approx(inc) and sum(x['expenses'] for x in chart['cash'])==pytest.approx(exp)
        for point in chart['fuel']:
            valid=[x for x in selected['fuel'] if x['date']==point['date'] and x['miles'] and x['miles']>0]
            assert point['mpg']==pytest.approx(sum(x['miles'] for x in valid)/sum(x['gallons'] for x in valid))
        for table in tables:
            r=request(s,'GET','/export/'+table,params=p); exported=list(csv.DictReader(io.StringIO(r.text)))
            assert len(exported)==len(selected[table])
            assert ('total' if table=='fuel' else 'pay' if table=='loads' else 'fine_reason' if table=='inspections' else 'amount') in exported[0] if exported else r.text.strip()
    request(s,'GET','/export/users',404)
    h=request(s,'GET','/stats/leaderboard-history').json()
    assert sum(t['trophies'] for t in h['trophies'])==len(h['history'])
    assert [x['month'] for x in h['history']]==sorted([x['month'] for x in h['history']],reverse=True)
    for win in h['history']:
        stats=request(s,'GET','/stats/drivers',params={'start':win['month']+'-01','end':win['month']+'-31'}).json()
        active=[dict(x,rate=x['on_time']/x['loads']*100) for x in stats if x['loads']]; score={x['id']:0 for x in active}
        for k in ['rate','avg_mpg','revenue']:
            values=sorted({x[k] if x[k] is not None else -1 for x in active},reverse=True)
            for x in active: score[x['id']]+=values.index(x[k] if x[k] is not None else -1)+1
        assert min(active,key=lambda x:score[x['id']])['id']==win['driver_id']

def test_06_telemetry_load_dedup_review_isolation(ctx):
    a,d,t,cfg=setup_mapping(ctx); s=ctx['owner']; job={'sourceCity':'TEST_Origin','destinationCity':'TEST_Destination','sourceCompany':'A','destinationCompany':'B','income':1000,'deadlineTime':'2026-08-04T12:00:00Z'}
    before=len(request(s,'GET','/loads').json())
    request(a,'POST','/telemetry/ingest',json=sample(1,job=job,attached=True))
    assert len(events(a))==1 and events(a)[0]['status']=='pending'
    assert len(request(s,'GET','/loads').json())==before
    for snap in [sample(1,job=job,attached=True),sample(0,job=job,attached=True),sample(2,job=job,attached=True),sample(1,session='reconnect',job=job,attached=True),sample(2,session='reconnect')]: request(a,'POST','/telemetry/ingest',json=snap)
    assert len(events(a))==1 and len(request(s,'GET','/loads').json())==before
    e=events(a)[0]; endpoint=f"/telemetry/events/{e['id']}/review"
    other,_,_,_=setup_mapping(ctx)
    assert not any(x['id']==e['id'] for x in events(other))
    request(other,'POST',endpoint,404,json={'action':'dismiss'})
    request(a,'POST',endpoint,422,json={'action':'approve','record':e['payload']})
    valid={'origin':'TEST_O','destination':'TEST_D','pay':1234,'driver_id':d['id'],'truck_id':t['id'],'delivered_date':'2026-08-04','status':'Late'}
    request(a,'POST',endpoint,400,json={'action':'approve','record':{**valid,'truck_id':999999}})
    assert events(a)[0]['status']=='pending'
    r=request(s,'POST',endpoint,json={'action':'approve','record':valid}).json()
    assert events(a)[0]['status']=='approved'
    inc=[x for x in request(s,'GET','/income').json() if x['load_id']==r['record_id']]
    assert len(inc)==1 and inc[0]['amount']==1234
    request(a,'POST',endpoint,409,json={'action':'approve','record':valid})
    job['destinationCity']='TEST_DISMISS'
    request(a,'POST','/telemetry/ingest',json=sample(3,session='reconnect',job=job,attached=True))
    e=events(a)[0]; request(a,'POST',f"/telemetry/events/{e['id']}/review",json={'action':'dismiss'})
    assert events(a)[0]['status']=='dismissed'

def test_07_telemetry_fuel_conversion_full_tanks_and_review(ctx):
    a,d,t,cfg=setup_mapping(ctx); seq=0
    def send(f,odo=1000,session='fuel'):
        nonlocal seq
        seq+=1; return request(a,'POST','/telemetry/ingest',json=sample(seq,session,fuel=f,odo=odo)).json()
    send(100);send(120);send(150)
    for _ in range(3): send(150)
    e=events(a)[0]
    assert e['kind']=='fuel' and e['payload']['gallons']==pytest.approx(50/3.785411784,abs=.0001)
    assert e['payload']['price_per_gallon'] is None and e['payload']['miles'] is None
    request(a,'POST',f"/telemetry/events/{e['id']}/review",422,json={'action':'approve','record':e['payload']})
    record={**e['payload'],'price_per_gallon':4}
    r=request(a,'POST',f"/telemetry/events/{e['id']}/review",json={'action':'approve','record':record}).json()
    f=next(x for x in request(ctx['owner'],'GET','/fuel').json() if x['id']==r['record_id']); assert f['total']==round(f['gallons']*4,2) and f['mpg'] is None
    send(200)
    for _ in range(3):send(200)
    assert events(a)[0]['payload']['miles'] is None
    send(100,1600);send(200,1600)
    for _ in range(3):send(200,1600)
    assert events(a)[0]['payload']['miles']==round(600/1.609344,2)
    send(50,1800,'restart');send(200,1800,'restart')
    for _ in range(3):send(200,1800,'restart')
    assert events(a)[0]['payload']['miles'] is None

def test_08_telemetry_validation_disabled_paused_gaps_bridge(ctx):
    a,d,t,cfg=setup_mapping(ctx)
    request(a,'PUT','/telemetry/settings',422,json={**cfg,'server_url':'https://example.com/api/ets2/telemetry'})
    request(a,'PUT','/telemetry/settings',400,json={**cfg,'driver_id':999999})
    request(a,'POST','/local-poll',404) if False else request(a,'POST','/telemetry/local-poll',400)
    for snap in [sample(1,connected=False),sample(2,paused=True,job={'sourceCity':'A','destinationCity':'B'},attached=True),sample(3,fuel=250),sample(4,fuel=100),sample(5,session='new',fuel=180)]:request(a,'POST','/telemetry/ingest',json=snap)
    assert events(a)==[]
    request(a,'POST','/telemetry/ingest',422,json=sample(6,fuel=-1))
    request(a,'POST','/telemetry/ingest',413,data='x'*(128*1024+1))
    request(a,'PUT','/telemetry/settings',json={**cfg,'enabled':False})
    assert request(a,'POST','/telemetry/ingest',json=sample(10)).json()['accepted'] is False
    script=request(a,'GET','/telemetry/bridge',headers={'Origin':BASE}).text
    tree=ast.parse(script)
    assert any(isinstance(n,ast.If) and '__main__' in ast.unparse(n.test) for n in tree.body)
    assert BASE in script, 'Downloaded bridge must use the user-facing public host, not the internal proxy hostname'

def test_09_backup_inspect_invalid_atomic(ctx):
    s=ctx['owner']; blob=archive(s); original=decrypt(blob)
    assert b'password_hash' not in blob and b'JWT_SECRET' not in blob
    assert all(u['password_hash'].startswith('$2b$') for u in original['tables']['users'])
    preview=request(s,'POST','/backup/inspect',json=body(blob)).json()
    assert preview['counts']=={k:len(v) for k,v in original['tables'].items()} and 'owner' in preview['owners']
    request(s,'POST','/backup/export',422,json={'passphrase':'short'})
    bads=[{**body(blob),'passphrase':'incorrect12345'},body(blob[:-5]+b'XXXXX'),body(b'invalid')]
    for mutate in ['version','schema','type','fk','owner']:
        d=copy.deepcopy(original)
        if mutate=='version': d['version']=2
        elif mutate=='schema': d['tables']['trucks'][0]['extra']='oops'
        elif mutate=='type': d['tables']['trucks'][0]['tank_gallons']='bad'
        elif mutate=='fk': d['tables']['income'][0]['driver_id']=999999
        else:
            for u in d['tables']['users']:u['role']='dispatcher'
        bads.append(body(encrypt(d)))
    for bad in bads:
        request(s,'POST','/backup/inspect',400,json=bad)
        request(s,'POST','/backup/restore',400,json={**bad,'confirm':'RESTORE MCCOY','owner_password':'trucker123'})
        assert normalize(decrypt(archive(s)))==normalize(original)
    request(s,'POST','/backup/restore',400,json={**body(blob),'owner_password':'trucker123'})
    request(s,'POST','/backup/restore',403,json={**body(blob),'confirm':'RESTORE MCCOY','owner_password':'wrong'})
    request(s,'POST','/backup/inspect',422,json={'archive':'notbase64','passphrase':'short'})
    request(s,'POST','/backup/inspect',413,data=b'x'*(25*1024*1024+1))
    assert normalize(decrypt(archive(s)))==normalize(original)

def test_10_backup_full_roundtrip_revoke_sessions(ctx):
    s=ctx['owner']; a,d,t,cfg=setup_mapping(ctx); blob=archive(s); data=decrypt(blob)
    create(ctx,'drivers',{'name':'TEST_NOT_IN_BACKUP'})
    r=request(s,'POST','/backup/restore',json={**body(blob),'confirm':'RESTORE MCCOY','owner_password':'trucker123'}).json()
    assert r['ok'] and r['sign_in_required']
    request(s,'GET','/auth/me',401);request(a,'GET','/auth/me',401)
    ctx['owner']=login(); restored=decrypt(archive(ctx['owner']))
    assert normalize(restored)==normalize(data)
    a=login(a.user['username'],'secret123')
    st=request(a,'GET','/telemetry/status').json()['source'];assert st['enabled']==0 and st['last_seen'] is None and st['live'] is None

def test_11_testdata_preserves_non_test_and_restores(ctx):
    s=ctx['owner']; blob=archive(s); before=decrypt(blob)
    try:
        added=request(s,'POST','/test-data').json();assert added['loads']==60 and added['fuel']==70
        non_test={t:[r for r in v if not r.get('is_test',0)] for t,v in before['tables'].items() if t not in ['telemetry_events','telemetry_sources','users']}
        after=decrypt(archive(s))
        for t,v in non_test.items():
            assert all(r in after['tables'][t] for r in v), t
        removed=request(s,'DELETE','/test-data').json();assert removed['removed']['loads']==60
        assert all(v==0 for v in request(s,'GET','/test-data').json().values())
        after=decrypt(archive(s))
        for t,v in non_test.items(): assert all(r in after['tables'][t] for r in v),t
    finally:
        request(s,'POST','/backup/restore',json={**body(blob),'confirm':'RESTORE MCCOY','owner_password':'trucker123'})
        ctx['owner']=login()

def test_12_logout_revokes_bearer(ctx):
    a,d,t,cfg=setup_mapping(ctx)
    request(a,'POST','/auth/logout')
    # A signed-out user's copied Bearer token must not remain usable.
    request(a,'GET','/auth/me',401)

def test_13_manual_invalid_date_rejected(ctx):
    request(ctx['owner'],'POST','/income',422,json={'date':'not-a-date','amount':10,'source':'TEST_invalid_date'})

def test_14_telemetry_repeat_legitimate_identical_job(ctx):
    a,d,t,cfg=setup_mapping(ctx); job={'sourceCity':'TEST_SameOrigin','destinationCity':'TEST_SameDestination','income':100}
    request(a,'POST','/telemetry/ingest',json=sample(1,job=job,attached=True))
    e=events(a)[0];request(a,'POST',f"/telemetry/events/{e['id']}/review",json={'action':'dismiss'})
    request(a,'POST','/telemetry/ingest',json=sample(2))
    request(a,'POST','/telemetry/ingest',json=sample(3,job=job,attached=True))
    assert len(events(a))==2, 'Distinct jobs with identical snapshot fields are suppressed forever'