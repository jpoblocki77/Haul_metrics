# Nonmutating original-data and permanent credential verification for iteration 5.
import json
from pathlib import Path
from test_full_regression import login, request, archive, decrypt, normalize
s=login();current=decrypt(archive(s));original=decrypt(Path('/app/test_reports/initial_state_iter4.mccoy').read_bytes())
assert normalize(current)==normalize(original), 'Original tables/settings differ'
assert {u['username'] for u in current['tables']['users']}=={'owner','dispatch1'}
assert len(current['tables']['categories'])==8
for table in ['trucks','drivers','income','expenses','fuel','loads','inspections','telemetry_events','telemetry_sources']:
    assert current['tables'][table]==[],table
assert request(s,'GET','/company/branding').json()['company_name']=='McCoy Trucking'
assert login('dispatch1','haul1234').user['role']=='dispatcher'
result={'original_records_and_settings_unchanged':True,'owner_and_dispatch_credentials_verified':True,'retained_test_users':[],'counts':{k:len(v) for k,v in current['tables'].items()}}
Path('/app/test_reports/final_cleanup_iter5.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))