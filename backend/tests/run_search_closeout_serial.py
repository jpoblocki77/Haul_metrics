# Narrow search suite with encrypted recovery and original-account/branding checks.
import json,os,re,subprocess,sys
from pathlib import Path
import test_full_regression as api

ROOT=Path('/app/test_reports');TESTS=Path(__file__).parent
text=Path('/app/memory/test_credentials.md').read_text()
USER=re.search(r'username: (\S+)',text)[1];PASSWORD=re.search(r'password: (\S+)',text)[1]
s=api.login(USER,PASSWORD);blob=api.archive(s);original=api.decrypt(blob)
for path in [ROOT/'closeout_original.mccoy',ROOT/'browser_iter6/safety.mccoy',ROOT/'browser_iter6/search_safety.mccoy']:
    assert api.normalize(original)==api.normalize(api.decrypt(path.read_bytes())),str(path)
safety=ROOT/'search_closeout_original_iter7.mccoy';safety.write_bytes(blob);safety.chmod(0o600)
brand=api.request(s,'GET','/company/branding').json();result={}
try:
    cmd=['pytest','-n0',str(TESTS/'test_telemetry_management.py'),'-v','--tb=short','--junitxml=/app/test_reports/pytest/pytest_results_iter7_search.xml']
    result['command']=' '.join(cmd)
    with (ROOT/'pytest_iter7_search.log').open('w') as log:
        run=subprocess.run(cmd,cwd=TESTS.parents[0],env=os.environ,stdout=log,stderr=subprocess.STDOUT,timeout=240)
    result['pytest_exit']=run.returncode
    print('Serial search pytest exit: '+str(run.returncode),flush=True)
    if run.returncode==0:
        with (ROOT/'search_encoding_iter7.log').open('w') as log:
            run=subprocess.run([sys.executable,str(TESTS/'check_telemetry_search_encoding.py')],cwd=TESTS.parents[0],env=os.environ,stdout=log,stderr=subprocess.STDOUT,timeout=90)
        result['api_browser_diagnostic_exit']=run.returncode
        print('API/browser diagnostic exit: '+str(run.returncode),flush=True)
finally:
    s=api.login(USER,PASSWORD)
    result['suites_restored_original']=api.normalize(api.decrypt(api.archive(s)))==api.normalize(original)
    api.request(s,'POST','/backup/restore',json={**api.body(blob),'confirm':'RESTORE MCCOY','owner_password':PASSWORD})
    s=api.login(USER,PASSWORD);final=api.decrypt(api.archive(s))
    assert api.normalize(final)==api.normalize(original)
    assert api.request(s,'GET','/company/branding').json()==brand
    assert {u['username'] for u in final['tables']['users']}=={'owner','dispatch1'}
    assert all(u['password_hash'].startswith('$2b$') for u in final['tables']['users'])
    assert api.login('dispatch1','haul1234').user['role']=='dispatcher'
    result.update(original_data_restored=True,accounts_password_hashes_and_branding_unchanged=True,prior_three_snapshots_match=True,credentials_verified=True,retained_test_accounts=[],counts={k:len(v) for k,v in final['tables'].items()})
    (ROOT/'final_cleanup_iter7.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2),flush=True)
sys.exit(0 if result.get('pytest_exit')==0 and result.get('api_browser_diagnostic_exit')==0 else 1)