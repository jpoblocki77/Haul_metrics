# Non-mutating final data/credential check after safeguarded regression restore.
import json
from pathlib import Path
from test_full_regression import login,request,archive,decrypt,normalize

s=login();current=decrypt(archive(s));initial=decrypt(Path('/app/test_reports/initial_state_iter4.mccoy').read_bytes())
if normalize(current)!=normalize(initial):
    for k in current['tables']:
        if normalize(current).get(k)!=normalize(initial).get(k):print('DIFF',k,'current count',len(current['tables'][k]),'initial count',len(initial['tables'].get(k,[])), 'current ids',[r.get('id') for r in current['tables'][k]],'initial ids',[r.get('id') for r in initial['tables'].get(k,[])])
assert normalize(current)==normalize(initial), 'Original company data changed'
assert len(current['tables']['users'])==2
try:
    d=login('dispatch1','haul1234');dispatch=d.user['role']=='dispatcher'
except AssertionError:dispatch=False
report=Path('/app/test_reports/iteration_4.json');data=json.loads(report.read_text())
if dispatch:data['test_credentials']=data['test_credentials'].replace('dispatch1 credentials documented but not independently verified in this continuation.','dispatch1 / haul1234 also independently verified as dispatcher.')
report.write_text(json.dumps(data,indent=2))
result={'original_records_unchanged':True,'permanent_owner_password_verified':True,'dispatch1_verified':dispatch,'retained_test_users':[], 'counts':{k:len(v) for k,v in current['tables'].items()}}
Path('/app/test_reports/final_cleanup_iter4.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))