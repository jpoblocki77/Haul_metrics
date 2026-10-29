# Targeted public API completeness, literal search, validation and ownership regression.
import pytest
from test_full_regression import request, setup_mapping, sample, events

@pytest.fixture(scope='module')
def history(ctx):
    a,d,t,cfg=setup_mapping(ctx)
    prefix='TEST_management_'+ctx['prefix']
    for n in range(501):
        origin=prefix+'_oldest_%_\\' if n==0 else prefix+('_plainXtoken' if n==1 else '_plain_token' if n==2 else '_Montréal' if n==3 else '_'+str(n))
        assert request(a,'POST','/telemetry/ingest',json=sample(n,session=prefix,job={'sourceCity':origin,'destinationCity':'TEST_end','income':1},attached=True)).json()['accepted']
    rows=events(a)
    return ctx['owner'],a,rows,prefix

def test_complete_history_and_dispatcher_ownership(history):
    s,a,rows,prefix=history
    assert len(rows)==501 and rows[-1]['payload']['origin']==prefix+'_oldest_%_\\'
    assert all(r['user_id']==a.user['id'] for r in rows)
    assert {r['id'] for r in rows}<={r['id'] for r in events(s)}
    other=__import__('test_full_regression').login('dispatch1','haul1234')
    assert not ({r['id'] for r in rows}&{r['id'] for r in events(other)})
    assert 'owner' in request(a,'GET','/telemetry/manage-events',403).json()['detail']

def test_pages_totals_and_oldest_search(history):
    s,a,rows,prefix=history
    ids=[]
    for offset in range(0,501,100):
        data=request(s,'GET','/telemetry/manage-events',params={'q':prefix,'offset':offset,'limit':100}).json()
        assert (data['total'],data['offset'],data['limit'])==(501,offset,100)
        assert len(data['items'])==min(100,501-offset)
        ids.extend(x['id'] for x in data['items'])
    assert ids==[r['id'] for r in rows]
    for q in ['%','\\',prefix+'_oldest','pending','load',str(rows[-1]['id']),rows[-1]['detected_at'][:10]]:
        data=request(s,'GET','/telemetry/manage-events',params={'q':q}).json()
        assert data['total']>=1 and isinstance(data['items'][0]['payload'],dict)
    assert request(s,'GET','/telemetry/manage-events',params={'q':'%'}).json()['total']==1
    assert request(s,'GET','/telemetry/manage-events',params={'q':'\\'}).json()['total']==1
    assert request(s,'GET','/telemetry/manage-events',params={'q':'plain_token'}).json()['total']==1
    assert request(s,'GET','/telemetry/manage-events',params={'q':prefix+'_oldest_%_\\'}).json()['items'][0]['id']==rows[-1]['id']
    empty=request(s,'GET','/telemetry/manage-events',params={'q':'TEST_definitely_absent_!'}).json()
    assert empty=={'items':[],'total':0,'offset':0,'limit':100}

def test_query_validation(history):
    s,*_=history
    for params in [{'q':'x'*201},{'offset':-1},{'limit':0},{'limit':101},{'offset':'invalid'}]:
        assert isinstance(request(s,'GET','/telemetry/manage-events',422,params=params).json()['detail'],list)
    assert request(s,'GET','/telemetry/manage-events',params={'q':'x'*200,'limit':1}).json()['limit']==1

def test_unicode_city_search_matches_visible_payload(history):
    s,a,rows,prefix=history
    expected=next(r for r in rows if r['payload']['origin']==prefix+'_Montréal')
    for q in ['Montréal','MONTRÉAL']:
        data=request(s,'GET','/telemetry/manage-events',params={'q':q}).json()
        assert data['total']==1 and [r['id'] for r in data['items']]==[expected['id']],data

def test_delete_oldest_and_adjust_total(history):
    s,a,rows,prefix=history
    oldest=rows[-1]
    assert request(s,'DELETE',f"/telemetry/events/{oldest['id']}").json()['ok']
    assert not any(r['id']==oldest['id'] for r in events(s))
    data=request(s,'GET','/telemetry/manage-events',params={'q':prefix,'offset':500}).json()
    assert data['total']==500 and data['items']==[]
    assert request(s,'GET','/telemetry/manage-events',params={'q':prefix+'_oldest'}).json()['total']==0