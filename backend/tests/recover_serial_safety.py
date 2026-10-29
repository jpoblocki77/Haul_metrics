# Repair only test-created state after accidental pytest configuration enabled parallel workers.
import json
from pathlib import Path
from test_full_regression import login, request, decrypt, archive, body, normalize
p=Path('/app/test_reports/initial_state_iter4.mccoy')
blob=p.read_bytes(); original=decrypt(blob)
assert {u['username'] for u in original['tables']['users']} == {'owner','dispatch1'}, 'Snapshot is not original baseline'
s=login()
request(s,'POST','/backup/restore',json={**body(blob),'confirm':'RESTORE MCCOY','owner_password':'trucker123'})
s=login(); current=decrypt(archive(s)); assert normalize(current)==normalize(original)
Path('/app/test_reports/recovered_parallel_safety.json').write_text(json.dumps({'restored':True,'counts':{t:len(v) for t,v in current['tables'].items()}},indent=2))
print('Original baseline restored and compared')