# Final nonmutating comparison of the original closeout archive, credentials and branding.
import json
from pathlib import Path
import test_full_regression as api

root=Path('/app/test_reports');s=api.login();current=api.decrypt(api.archive(s))
for path in [root/'closeout_original.mccoy',root/'browser_iter6/safety.mccoy',root/'browser_iter6/search_safety.mccoy']:
    assert api.normalize(current)==api.normalize(api.decrypt(path.read_bytes())),str(path)
assert {u['username'] for u in current['tables']['users']}=={'owner','dispatch1'}
assert all(u['password_hash'].startswith('$2b$') for u in current['tables']['users'])
assert api.login('dispatch1','haul1234').user['role']=='dispatcher'
brand=api.request(s,'GET','/company/branding').json()
assert brand=={'company_name':'McCoy Trucking','primary_color':'#3b82f6','accent_color':'#dc2626','dark_background':'#0b0f17','light_background':'#f5f7fa'}
assert len(current['tables']['categories'])==8
assert all(not rows for table,rows in current['tables'].items() if table not in ('users','categories'))
result=json.loads((root/'final_cleanup_iter6.json').read_text())
result.update(final_post_diagnostic_comparison=True,compared_all_three_safety_snapshots=True,retained_test_users=[],retained_company_test_records=0,password_hashes_unchanged=True,effective_branding_unchanged=True)
(root/'final_cleanup_iter6.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))