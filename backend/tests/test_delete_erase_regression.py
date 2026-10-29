# New owner deletion and bulk erase contracts against the public API with encrypted snapshot cleanup.
import copy
import os
import subprocess
import sys
from pathlib import Path
from test_full_regression import login, request, archive, decrypt, body, normalize, setup_mapping, sample, events, create

def test_delete_telemetry_pending_suppression_and_new_occurrence(ctx):
    a,d,t,cfg=setup_mapping(ctx);s=ctx['owner']
    job={'sourceCity':'TEST_delete_job','destinationCity':'TEST_end','income':123}
    request(a,'POST','/telemetry/ingest',json=sample(1,job=job,attached=True))
    e=events(a)[0]
    request(a,'DELETE',f"/telemetry/events/{e['id']}",403)
    assert request(s,'DELETE',f"/telemetry/events/{e['id']}").json()['ok']
    assert not any(x['id']==e['id'] for x in events(s))
    assert request(s,'DELETE',f"/telemetry/events/{e['id']}",404).json()['detail']=='Detection not found'
    for snap in [sample(2,job=job,attached=True),sample(1,session='reconnect_deleted',job=job,attached=True),sample(2,session='reconnect_deleted',job=job,attached=False),sample(3,session='reconnect_deleted',job=job,attached=True)]:
        request(a,'POST','/telemetry/ingest',json=snap)
    assert events(a)==[]
    request(a,'POST','/telemetry/ingest',json=sample(4,session='reconnect_deleted'))
    request(a,'POST','/telemetry/ingest',json=sample(5,session='reconnect_deleted',job=job,attached=True))
    assert len(events(a))==1 and events(a)[0]['id']>e['id']

def test_delete_approved_detection_keeps_saved_load_income_and_fuel(ctx):
    a,d,t,cfg=setup_mapping(ctx);s=ctx['owner']
    request(a,'POST','/telemetry/ingest',json=sample(1,job={'sourceCity':'TEST_approved','destinationCity':'TEST_end','income':123},attached=True))
    e=events(a)[0];record={'origin':'TEST_approved','destination':'TEST_end','pay':123,'delivered_date':'2026-10-28','driver_id':d['id'],'truck_id':t['id'],'status':'On Time'}
    rid=request(a,'POST',f"/telemetry/events/{e['id']}/review",json={'action':'approve','record':record}).json()['record_id']
    request(s,'DELETE',f"/telemetry/events/{e['id']}")
    assert next(x for x in request(s,'GET','/loads').json() if x['id']==rid)['pay']==123
    assert next(x for x in request(s,'GET','/income').json() if x['load_id']==rid)['amount']==123
    for i,f in enumerate([100,150,150,150,150],2):request(a,'POST','/telemetry/ingest',json=sample(i,fuel=f))
    e=events(a)[0]
    rid=request(a,'POST',f"/telemetry/events/{e['id']}/review",json={'action':'approve','record':{**e['payload'],'price_per_gallon':4}}).json()['record_id']
    request(s,'DELETE',f"/telemetry/events/{e['id']}")
    assert next(x for x in request(s,'GET','/fuel').json() if x['id']==rid)['price_per_gallon']==4

def test_erase_rejects_bad_phrase_password_missing_fields_and_dispatcher(ctx):
    s=ctx['owner'];a,d,t,cfg=setup_mapping(ctx);before=normalize(decrypt(archive(s)))
    for payload,status in [({'confirmation':'erase all records','owner_password':'trucker123'},400),({'confirmation':'ERASE ALL RECORDS','owner_password':'wrong'},403),({'confirmation':'ERASE ALL RECORDS'},422),({'owner_password':'trucker123'},422),({'confirmation':'ERASE ALL RECORDS','owner_password':''},422)]:
        assert request(s,'POST','/company/erase-records',status,json=payload).json()['detail']
        assert normalize(decrypt(archive(s)))==before
    for method,path,payload in [('GET','/company/record-counts',None),('POST','/company/erase-records',{'confirmation':'ERASE ALL RECORDS','owner_password':'trucker123'})]:
        assert 'owner' in request(a,method,path,403,json=payload).json()['detail']
    assert normalize(decrypt(archive(s)))==before

def test_erase_atomic_zero_counts_sessions_portable_backup_and_recreate(ctx):
    s=ctx['owner'];a,d,t,cfg=setup_mapping(ctx)
    request(s,'POST','/test-data')
    create(ctx,'categories',{'name':'TEST_erase_category'})
    request(a,'POST','/telemetry/ingest',json=sample(1,job={'sourceCity':'TEST_erase','destinationCity':'TEST_end','income':99},attached=True))
    before=decrypt(archive(s));counts=request(s,'GET','/company/record-counts').json()
    assert all(count>0 for count in counts.values()),counts
    brand=request(s,'GET','/company/branding').json()
    result=request(s,'POST','/company/erase-records',json={'confirmation':'ERASE ALL RECORDS','owner_password':'trucker123'}).json()
    assert result['ok'] and result['removed']==counts
    assert all(n==0 for n in request(s,'GET','/company/record-counts').json().values())
    after=decrypt(archive(s))
    assert after['tables']['users']==before['tables']['users']
    assert after['tables']['company_settings']==before['tables']['company_settings']
    assert request(s,'GET','/company/branding').json()==brand
    assert request(s,'GET','/auth/me').json()['role']=='owner'
    assert request(a,'GET','/auth/me').json()['username']==a.user['username']
    assert request(a,'POST','/telemetry/ingest',json=sample(2)).json()['accepted'] is False
    assert request(a,'GET','/telemetry/status').json()['source'] is None
    assert request(s,'GET',f"/drivers/{d['id']}/profile",404).json()['detail']=='Driver not found'
    stats=request(s,'GET','/stats/dashboard').json()
    assert [stats[k] for k in ['income','expenses','profit','loads_total']]==[0,0,0,0]
    assert stats['monthly']==[] and stats['fuel_trend']==[] and stats['drivers']==[]
    assert request(s,'GET','/stats/report-charts').json()=={'cash':[],'fuel':[]}
    assert request(s,'GET','/stats/leaderboard-history').json()=={'history':[],'trophies':[]}
    blank=archive(s);preview=request(s,'POST','/backup/inspect',json=body(blank)).json()
    assert all(preview['counts'][k]==0 for k in counts)
    for table,payload in [('drivers',{'name':'TEST_after_erase'}),('trucks',{'truck_number':'TEST_after_erase','tank_gallons':100}),('categories',{'name':'TEST_after_erase'})]:
        row=create(ctx,table,payload);assert row['id']>max(x['id'] for x in before['tables'][table])
    truck=request(s,'GET','/trucks').json()[0];driver=request(s,'GET','/drivers').json()[0];category=request(s,'GET','/categories').json()[0]
    for table,payload in [('loads',{'origin':'TEST_after','destination':'TEST_end','pay':55,'delivered_date':'2026-10-28','driver_id':driver['id'],'truck_id':truck['id']}),('income',{'date':'2026-10-28','source':'TEST_after','amount':3}),('expenses',{'date':'2026-10-28','amount':1,'category_id':category['id']}),('fuel',{'date':'2026-10-28','truck_id':truck['id'],'price_per_gallon':2,'miles':600}),('inspections',{'date':'2026-10-28','driver_id':driver['id'],'result':'Passed'})]:create(ctx,table,payload)
    request(s,'POST','/backup/restore',json={**body(blank),'confirm':'RESTORE MCCOY','owner_password':'trucker123'})
    ctx['owner']=s=login()
    assert normalize(decrypt(archive(s)))==normalize(after)

def test_deleted_categories_stay_empty_after_disposable_db_init(tmp_path):
    env={**os.environ,'SQLITE_DB_FILE':str(tmp_path/'erase.db')}
    result=subprocess.run([sys.executable,str(Path(__file__).with_name('isolated_erase_worker.py'))],env=env,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stdout+result.stderr
    print(result.stdout)