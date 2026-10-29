# Diagnose real urllib login versus requests; log status/headers only, never credentials/tokens.
import json, os, urllib.request, urllib.error
from pathlib import Path
import requests
url=os.environ['REACT_APP_BACKEND_URL'].rstrip('/')+'/api/auth/login'
payload={'username':'owner','password':'trucker123'}
results=[]
for ua in ['Python-urllib/3.11','python-requests/'+requests.__version__,'Mozilla/5.0']:
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','User-Agent':ua})
    try:
        with urllib.request.urlopen(req,timeout=15) as r:result={'client':'urllib','ua':ua,'status':r.status,'server':r.headers.get('server'),'cf_mitigated':r.headers.get('cf-mitigated')}
    except urllib.error.HTTPError as e:result={'client':'urllib','ua':ua,'status':e.code,'server':e.headers.get('server'),'cf_mitigated':e.headers.get('cf-mitigated'),'body_prefix':e.read(300).decode(errors='replace')}
    results.append(result)
for ua in ['Python-urllib/3.11',requests.utils.default_user_agent()]:
    r=requests.post(url,json=payload,headers={'User-Agent':ua},timeout=15)
    results.append({'client':'requests','ua':ua,'status':r.status_code,'server':r.headers.get('server'),'cf_mitigated':r.headers.get('cf-mitigated')})
print(json.dumps(results,indent=2));Path('/app/test_reports/bridge_network.json').write_text(json.dumps(results,indent=2))