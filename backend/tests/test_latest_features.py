# Latest regression: executable bridge startup, company settings, optional telemetry, backups and continuity.
import ast, copy, os, subprocess, sys
from pathlib import Path
import pytest, requests
from test_full_regression import login, request, archive, decrypt, encrypt, body, normalize, setup_mapping, sample, events, create

def test_15_bridge_process_contract(ctx, tmp_path):
    r=request(ctx['owner'],'GET','/telemetry/bridge')
    bridge=tmp_path/'McCoyTelemetry.py';bridge.write_text(r.text)
    tree=ast.parse(r.text)
    default=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DEFAULT_APP_URL' for t in n.targets))
    assert default.startswith('https://')
    for mode in ['retry','network','lockout','expired','scs','source']:
        target=Path('/app/backend/telemetry_bridge.py') if mode=='source' else bridge
        local=tmp_path/mode
        result=subprocess.run([sys.executable,str(Path(__file__).with_name('bridge_process_harness.py')),str(target),mode],env={**os.environ,'LOCALAPPDATA':str(local)},capture_output=True,text=True,timeout=15)
        out=result.stdout+result.stderr
        assert result.returncode==0,out
        assert 'McCoy username:' in out and 'Press Enter to close' in out,out
        if mode=='retry':assert 'Incorrect username' in out and 'Signed in.' in out and '/telemetry/ingest' in out
        if mode=='network':assert 'Cannot reach' in out
        if mode=='lockout':assert 'Too many sign-in' in out
        if mode=='expired':assert 'session expired' in out
        if mode=='scs':assert 'Retrying' in out and 'SLEEP 3' in out
        logfile=local/'McCoyTrucking'/'telemetry-bridge.log'
        text=out+(logfile.read_text() if logfile.exists() else '')
        assert not any(secret in text for secret in ['TEST_secret_password','TEST_secret_token','TEST_private_remote_error'])
    launcher=request(ctx['owner'],'GET','/telemetry/launcher').text
    assert all(v in launcher for v in ['cd /d "%~dp0"','if not exist "McCoyTelemetry.py"','where py','where python','pause'])
    for ep in ['/telemetry/bridge','/telemetry/launcher']:request(requests.Session(),'GET',ep,401)

def test_16_company_branding_auth_validation_persistence(ctx):
    s=ctx['owner'];a,d,t,cfg=setup_mapping(ctx)
    public=request(requests.Session(),'GET','/company/branding').json()
    assert set(public)=={'company_name','primary_color','accent_color','dark_background','light_background'}
    brand={**public,'company_name':'  TEST_Fleet  ','primary_color':'#228844','accent_color':'#8844aa','dark_background':'#101010','light_background':'#eeeeee'}
    request(a,'PUT','/company/branding',403,json=brand)
    request(requests.Session(),'PUT','/company/branding',401,json=brand)
    changed=request(s,'PUT','/company/branding',json=brand).json();assert changed['company_name']=='TEST_Fleet'
    assert request(requests.Session(),'GET','/company/branding').json()==changed
    for key,value in [('company_name','  '),('company_name','TEST\x01bad'),('primary_color','red'),('dark_background','#ffffff'),('light_background','#000000')]:request(s,'PUT','/company/branding',422,json={**brand,key:value})
    data=decrypt(archive(s));assert data['tables']['company_settings'][0]['company_name']=='TEST_Fleet'
    legacy=copy.deepcopy(data);legacy['tables'].pop('company_settings')
    preview=request(s,'POST','/backup/inspect',json=body(encrypt(legacy))).json();assert preview['counts']['company_settings']==0
    request(s,'POST','/backup/restore',json={**body(encrypt(legacy)),'confirm':'RESTORE MCCOY','owner_password':'trucker123'})
    request(s,'GET','/auth/me',401)
    ctx['owner']=s=login()
    assert request(requests.Session(),'GET','/company/branding').json()['company_name']=='McCoy Trucking'
    request(s,'PUT','/company/branding',json=public)

def test_17_optional_snapshots_unicode_password(ctx):
    a,d,t,cfg=setup_mapping(ctx)
    for n,raw in enumerate([{'game':{'connected':False}},{'game':{'connected':False},'truck':{'fuelCapacity':0}},{'game':{'connected':True}}]):
        assert request(a,'POST','/telemetry/ingest',json={'session_id':'minimal','sequence':n,'raw':raw}).json()['accepted']
    assert events(a)==[]
    for url in ['http://169.254.169.254/api/ets2/telemetry','http://localhost.example.com/api/ets2/telemetry','http://x:y@localhost/api/ets2/telemetry','http://localhost/api/wrong']:
        request(a,'PUT','/telemetry/settings',422,json={**cfg,'server_url':url})
    request(ctx['owner'],'POST','/users',422,json={'username':ctx['prefix']+'_unicode','password':'🚚'*24})
    u=request(ctx['owner'],'POST','/users',json={'username':ctx['prefix']+'_utf8','password':'🚚'*18}).json()
    assert login(u['username'],'🚚'*18).user['role']=='dispatcher'

def test_18_backup_metadata_invalid_not_500(ctx):
    s=ctx['owner'];data=decrypt(archive(s));data.pop('created_at')
    request(s,'POST','/backup/inspect',400,json=body(encrypt(data)))

def test_19_telemetry_reset_mileage_continuity(ctx):
    a,d,t,cfg=setup_mapping(ctx);seq=0
    def send(fuel,odo,paused=False):
        nonlocal seq
        seq+=1;request(a,'POST','/telemetry/ingest',json=sample(seq,session='odo_reset',fuel=fuel,odo=odo,paused=paused))
    send(100,1000);send(200,1000)
    for _ in range(3):send(200,1000)
    send(50,100);send(50,1100);send(200,1100)
    for _ in range(3):send(200,1100)
    assert events(a)[0]['payload']['miles'] is None, events(a)[0]['payload']

def test_20_telemetry_paused_stop_discard(ctx):
    a,d,t,cfg=setup_mapping(ctx)
    snaps=[sample(1,fuel=100),sample(2,fuel=150),sample(3,fuel=180,paused=True),sample(4,fuel=180),sample(5,fuel=180),sample(6,fuel=180),sample(7,fuel=180)]
    for snap in snaps:request(a,'POST','/telemetry/ingest',json=snap)
    assert events(a)==[], 'Paused fuel gap should discard partial stop rather than create an incomplete purchase'