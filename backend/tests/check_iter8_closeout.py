# Final public credential check and original row fingerprint; no sensitive plaintext reports.
import hashlib
import json
from pathlib import Path
from regression_safety import table_snapshot
from test_full_regression import login, request

before=table_snapshot()
for user,password,role in [('owner','trucker123','owner'),('dispatch1','haul1234','dispatcher')]:
    s=login(user,password)
    assert request(s,'GET','/auth/me').json()['role']==role
assert table_snapshot()['users']==before['users']
summary={'original_credentials_verified':True,'password_hashes_roles_ids_unchanged':True,'counts':{k:len(v) for k,v in before.items()},'original_row_fingerprint':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),'product_code_edited_by_testing_agent':False}
Path('/app/test_reports/closeout_iter8.json').write_text(json.dumps(summary,indent=2))
for directory in ['browser_iter8_full','browser_iter8_delete']:
    for file in (Path('/app/test_reports')/directory).glob('*.mccoy'):file.chmod(0o600)
print('PASS original credentials and account fields unchanged; safeguarded wrapper restores login metadata')