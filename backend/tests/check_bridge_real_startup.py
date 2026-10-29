# Public API bridge download and actual Python process; no network mocks, no simulator required.
import json, os, subprocess, sys, tempfile
from pathlib import Path
from test_full_regression import login, request

s=login();script=request(s,'GET','/telemetry/bridge').text
with tempfile.TemporaryDirectory() as tmp:
    path=Path(tmp)/'McCoyTelemetry.py';path.write_text(script)
    p=subprocess.Popen([sys.executable,str(path)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env={**os.environ,'LOCALAPPDATA':tmp})
    try:out,err=p.communicate('owner\ntrucker123\n\n',timeout=12)
    except subprocess.TimeoutExpired:
        p.kill();out,err=p.communicate()
    print(out);print(err)
    results={'downloaded':{'signed_in':'Signed in.' in out,'stdout':out,'stderr':err,'exit':p.returncode}}
    p=subprocess.Popen([sys.executable,'/app/backend/telemetry_bridge.py'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env={**os.environ,'LOCALAPPDATA':tmp})
    try:out,err=p.communicate(os.environ['REACT_APP_BACKEND_URL']+'\nowner\ntrucker123\n\n',timeout=12)
    except subprocess.TimeoutExpired:
        p.kill();out,err=p.communicate()
    print(out);print(err)
    results['source_public_url']={'signed_in':'Signed in.' in out,'stdout':out,'stderr':err,'exit':p.returncode}
    Path(os.environ.get('BRIDGE_STARTUP_REPORT','/app/test_reports/bridge_real_startup.json')).write_text(json.dumps(results,indent=2))
    assert all(result['signed_in'] for result in results.values()), 'Actual bridge authentication failed'