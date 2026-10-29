# Foreground shared-database serial suites with an outer encrypted recovery guard.
import json,os,subprocess,sys
from pathlib import Path
import test_full_regression as api

ROOT=Path('/app/test_reports');TESTS=Path(__file__).parent
s=api.login();blob=api.archive(s);original=api.decrypt(blob)
path=ROOT/'closeout_original.mccoy';path.write_bytes(blob);path.chmod(0o600)
brand=api.request(s,'GET','/company/branding').json()
result={}
try:
    files=['test_full_regression.py','test_latest_features.py','test_final_verification.py','test_isolated_persistence.py','test_delete_erase_regression.py','test_telemetry_management.py']
    cmd=['pytest','-n0',*[str(TESTS/f) for f in files],'-v','--tb=short','--junitxml=/app/test_reports/pytest/pytest_results_iter6_serial.xml']
    result['command']=' '.join(cmd)
    with (ROOT/'pytest_iter6_serial.log').open('w') as log:
        run=subprocess.run(cmd,cwd=TESTS.parents[0],env=os.environ,stdout=log,stderr=subprocess.STDOUT,timeout=280)
    result['pytest_exit']=run.returncode
    with (ROOT/'bridge_iter6.log').open('w') as log:
        run=subprocess.run([sys.executable,str(TESTS/'check_bridge_real_startup.py')],cwd=TESTS.parents[0],env=os.environ,stdout=log,stderr=subprocess.STDOUT,timeout=60)
    result['bridge_exit']=run.returncode
finally:
    s=api.login();pre_restore=api.decrypt(api.archive(s))
    result['suites_restored_original']=api.normalize(pre_restore)==api.normalize(original)
    api.request(s,'POST','/backup/restore',json={**api.body(blob),'confirm':'RESTORE MCCOY','owner_password':'trucker123'})
    s=api.login();final=api.decrypt(api.archive(s))
    assert api.normalize(final)==api.normalize(original)
    assert api.request(s,'GET','/company/branding').json()==brand
    assert api.login('dispatch1','haul1234').user['role']=='dispatcher'
    result.update(original_data_restored=True,accounts_password_hashes_and_branding_unchanged=True,credentials_verified=True,retained_test_accounts=[],counts={k:len(v) for k,v in final['tables'].items()})
    (ROOT/'final_cleanup_iter6.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2),flush=True)