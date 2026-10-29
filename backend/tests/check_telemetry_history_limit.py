# Public API reproduction: old telemetry detections are omitted from the global delete search.
import json,uuid
from pathlib import Path
from test_full_regression import login,request,archive,decrypt,body,normalize,sample
s=login();blob=archive(s);original=decrypt(blob)
try:
    prefix='TEST_limit_'+uuid.uuid4().hex[:6]
    d=request(s,'POST','/drivers',json={'name':prefix}).json();t=request(s,'POST','/trucks',json={'truck_number':prefix,'tank_gallons':100}).json()
    request(s,'PUT','/telemetry/settings',json={'driver_id':d['id'],'truck_id':t['id'],'enabled':True,'server_url':'http://127.0.0.1:25555/api/ets2/telemetry'})
    for n in range(501):
        assert request(s,'POST','/telemetry/ingest',json=sample(n,session=prefix,job={'sourceCity':prefix+'_'+str(n),'destinationCity':'TEST_end','income':1},attached=True)).json()['accepted']
    total=request(s,'GET','/company/record-counts').json()['telemetry_events'];listed=request(s,'GET','/telemetry/events').json();allrows=decrypt(archive(s))['tables']['telemetry_events']
    earliest=min(x['id'] for x in allrows)
    result={'database_events':total,'listed_events':len(listed),'earliest_id':earliest,'earliest_omitted':not any(x['id']==earliest for x in listed),'global_search_cannot_find_oldest':not any(x['payload'].get('origin')==prefix+'_0' for x in listed)}
    assert result['database_events']==501 and result['listed_events']==501 and not result['earliest_omitted']
    print(json.dumps(result,indent=2));Path('/app/test_reports/telemetry_history_limit.json').write_text(json.dumps(result,indent=2))
finally:
    s=login();request(s,'POST','/backup/restore',json={**body(blob),'confirm':'RESTORE MCCOY','owner_password':'trucker123'});s=login();assert normalize(decrypt(archive(s)))==normalize(original)