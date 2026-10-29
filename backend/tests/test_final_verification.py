# Final fixes: independent sessions, malformed backup envelopes, dated CRUD, CSV and job detach dedupe.
import copy
import csv
import io
from test_full_regression import login, request, archive, decrypt, encrypt, body, normalize, setup_mapping, sample, events, create

def test_current_logout_preserves_separate_bridge_session(ctx):
    a, d, t, cfg = setup_mapping(ctx)
    b = login(a.user['username'], 'secret123')
    assert a.headers['Authorization'] != b.headers['Authorization']
    request(a, 'POST', '/auth/logout')
    assert 'signed out' in request(a, 'GET', '/auth/me', 401).json()['detail']
    assert request(b, 'GET', '/auth/me').json()['username'] == a.user['username']
    assert request(b, 'POST', '/telemetry/ingest', json=sample(1)) .json()['accepted']

def test_malformed_envelopes_reject_without_mutation(ctx):
    s = ctx['owner']; original = decrypt(archive(s))
    variants = [[], None, 'bad', 1]
    for key, value in [('created_at',None),('created_at','bad'),('created_at','2026-01-01T12:00:00'),('created_at',5),('version',True),('version','1'),('tables',[]),('tables',None),('format',None)]:
        d = copy.deepcopy(original);d[key] = value;variants.append(d)
    for key in ['version','created_at','tables','format']:
        d=copy.deepcopy(original);d.pop(key);variants.append(d)
    for d in variants:
        payload=body(encrypt(d))
        assert 'backup' in request(s,'POST','/backup/inspect',400,json=payload).json()['detail']
        request(s,'POST','/backup/restore',400,json={**payload,'confirm':'RESTORE MCCOY','owner_password':'trucker123'})
    assert normalize(decrypt(archive(s))) == normalize(original)

def test_invalid_calendar_dates_all_manual_create_and_update(ctx):
    s=ctx['owner'];a,d,t,cfg=setup_mapping(ctx)
    payloads={'income':{'date':'2026-01-01','amount':1,'source':'TEST_date'},'expenses':{'date':'2026-01-01','amount':1},'fuel':{'date':'2026-01-01','truck_id':t['id'],'price_per_gallon':1},'inspections':{'date':'2026-01-01','result':'Passed'},'loads':{'origin':'TEST_A','destination':'TEST_B','due_date':'2026-01-01','delivered_date':'2026-01-01'}}
    for table,payload in payloads.items():
        row=create(ctx,table,payload)
        for field in ['due_date','delivered_date'] if table=='loads' else ['date']:
            for invalid in ['not-a-date','2026-02-30','2026-13-01','20261028','2026-01-01T00:00:00','']:
                bad={**payload,field:invalid}
                for method,path in [('POST','/'+table),('PUT',f'/{table}/{row["id"]}')]:
                    result=request(s,method,path,422,json=bad).json();assert result['detail']
        saved=next(x for x in request(s,'GET','/'+table).json() if x['id']==row['id'])
        assert saved['due_date' if table=='loads' else 'date']=='2026-01-01'

def test_csv_formula_text_escaped_numeric_preserved(ctx):
    s=ctx['owner']
    for value in ['=1+1','+SUM(1,2)','-cmd','@SUM(1)','  =1+1']:
        row=create(ctx,'income',{'date':'2026-01-01','amount':-10,'source':value})
        exported=list(csv.DictReader(io.StringIO(request(s,'GET','/export/income').text)))
        match=next(x for x in exported if x['source']=="'"+value)
        assert float(match['amount'])==-10

def test_detach_and_reconnect_same_job_do_not_duplicate(ctx):
    a,d,t,cfg=setup_mapping(ctx);job={'sourceCity':'TEST_A','destinationCity':'TEST_B','income':100}
    for snap in [sample(1,job=job,attached=True),sample(2,job=job,attached=False),sample(3,job=job,attached=True),sample(1,session='reconnect',job=job,attached=True)]:
        request(a,'POST','/telemetry/ingest',json=snap)
    assert len(events(a))==1 and events(a)[0]['status']=='pending'