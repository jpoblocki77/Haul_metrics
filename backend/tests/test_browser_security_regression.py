# Real preview security: exact origins, CSRF binding, cookie flags and independent sessions.
import requests
import pytest
from test_full_regression import API, BASE, login, request, create
from regression_safety import table_snapshot

BAD_ORIGINS=['null','https://attacker.example','https://sibling.preview.emergentagent.com',BASE+'.attacker.example',BASE.replace('https:','http:'),BASE+':444','not-an-origin',BASE+'/evil','https://[broken','https://evil.example@'+BASE.split('://')[1]]

def browser_login(username='owner',password='trucker123'):
    session=requests.Session()
    response=session.post(API+'/auth/login',json={'username':username,'password':password},headers={'Origin':BASE},timeout=20)
    assert response.status_code==200,response.text
    return session,response.json(),response

@pytest.mark.parametrize('origin',BAD_ORIGINS)
def test_untrusted_actual_and_preflight(ctx,origin):
    before=table_snapshot()
    s=ctx['owner']
    r=s.post(API+'/users',json={'username':'TEST_security_intruder','password':'secret123','role':'owner'},headers={'Origin':origin,'X-Forwarded-Host':origin,'X-Forwarded-Proto':'https'},timeout=20)
    assert r.status_code==403 and r.json()['code']=='untrusted_origin',r.text
    # Preview ingress adds wildcard ACAO on denied requests, never credential grants.
    assert r.headers.get('access-control-allow-origin') in (None, '*')
    assert 'access-control-allow-credentials' not in r.headers
    assert 'no-store' in r.headers['cache-control']
    p=requests.options(API+'/users',headers={'Origin':origin,'Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'content-type,x-csrf-token'},timeout=20)
    assert p.status_code==400 and 'access-control-allow-origin' not in p.headers and 'access-control-allow-credentials' not in p.headers
    assert table_snapshot()==before

def test_trusted_origin_cookie_flags_csrf_no_store(ctx):
    s,data,r=browser_login()
    assert data['user']['role']=='owner' and len(data['csrf_token'])==64
    cookie=r.headers['set-cookie'].lower()
    assert all(x in cookie for x in ['httponly','secure','path=/'])
    assert 'samesite=lax' in cookie or ('samesite=none' in cookie and 'partitioned' in cookie)
    assert r.headers['access-control-allow-origin']==BASE and r.headers['access-control-allow-credentials']=='true'
    for path in ['/auth/me','/auth/csrf','/company/branding']:
        r=s.get(API+path,headers={'Origin':BASE},timeout=20)
        assert r.status_code==200 and 'no-store' in r.headers['cache-control']
        if path=='/auth/csrf':assert r.json()['csrf_token']==data['csrf_token']
    r=s.post(API+'/auth/logout',json={},headers={'Origin':BASE,'X-CSRF-Token':data['csrf_token']},timeout=20)
    assert r.status_code==200 and r.json()['ok'] and 'no-store' in r.headers['cache-control']
    cookie=r.headers['set-cookie'].lower()
    assert all(x in cookie for x in ['httponly','secure','max-age=0'])
    assert 'samesite=lax' in cookie or 'samesite=none' in cookie
    assert requests.get(API+'/auth/me',headers={'Authorization':'Bearer '+data['token']},timeout=20).status_code==401

def test_cookie_csrf_missing_wrong_nonascii_cross_session_reject_before_write(ctx):
    s,data,_=browser_login();other,otherdata,_=browser_login()
    before=table_snapshot()
    for token in ['', 'wrong', 'é',otherdata['csrf_token']]:
        r=s.post(API+'/income',json={'date':'2026-10-29','source':'TEST_CSRF_REJECT','amount':1},headers={'Origin':BASE,'X-CSRF-Token':token},timeout=20)
        assert r.status_code==403 and r.json()['code']=='csrf_failed',r.text
        assert table_snapshot()==before
    r=s.post(API+'/income',json={'date':'2026-10-29','source':'TEST_CSRF_GOOD','amount':1},headers={'Origin':BASE,'X-CSRF-Token':data['csrf_token']},timeout=20)
    assert r.status_code==200 and r.json()['source']=='TEST_CSRF_GOOD'
    rid=r.json()['id'];assert sum(x['id']==rid for x in request(ctx['owner'],'GET','/income').json())==1
    request(ctx['owner'],'DELETE','/income/'+str(rid))

def test_erase_cookie_rejections_exact_no_mutation(ctx):
    s,data,_=browser_login();dp,dpdata,_=browser_login('dispatch1','haul1234')
    before=table_snapshot()
    payload={'confirmation':'ERASE ALL RECORDS','owner_password':'trucker123'}
    for headers,body,status in [({'Origin':BASE},payload,403),({'Origin':BASE,'X-CSRF-Token':'wrong'},payload,403),({'Origin':BASE,'X-CSRF-Token':data['csrf_token']},{**payload,'owner_password':'wrong'},403),({'Origin':BASE,'X-CSRF-Token':data['csrf_token']},{**payload,'confirmation':'wrong'},400),({'Origin':BASE,'X-CSRF-Token':data['csrf_token']},{},422)]:
        r=s.post(API+'/company/erase-records',json=body,headers=headers,timeout=20)
        assert r.status_code==status and r.json()['detail']
        assert table_snapshot()==before
    for token in ['', 'wrong',dpdata['csrf_token']]:
        r=dp.post(API+'/company/erase-records',json=payload,headers={'Origin':BASE,'X-CSRF-Token':token},timeout=20)
        assert r.status_code==403 and r.json()['detail']
        assert table_snapshot()==before

def test_fetch_metadata_no_origin_rejected_with_bearer(ctx):
    before=table_snapshot()
    for value in ['cross-site','same-site']:
        r=ctx['owner'].get(API+'/income',headers={'Sec-Fetch-Site':value},timeout=20)
        assert r.status_code==403 and r.json()['code']=='untrusted_origin'
    assert table_snapshot()==before

def test_invalid_bearer_cannot_fallback_to_cookie(ctx):
    s,data,_=browser_login();before=table_snapshot()
    r=s.post(API+'/income',headers={'Origin':BASE,'Authorization':'Bearer invalid'},json={'date':'2026-10-29','source':'TEST_INVALID_BEARER','amount':1},timeout=20)
    assert r.status_code==401 and r.json()['detail']=='Invalid token'
    assert table_snapshot()==before

def test_login_json_only_origin_guard_and_csrf_auth_required(ctx):
    before=table_snapshot()
    for content in ['text/plain','application/x-www-form-urlencoded','multipart/form-data']:
        r=requests.post(API+'/auth/login',headers={'Origin':BASE,'Content-Type':content},data='{}',timeout=20)
        assert r.status_code==415 and r.json()['code']=='invalid_content_type'
    for origin in BAD_ORIGINS:
        r=requests.post(API+'/auth/login',headers={'Origin':origin},json={'username':'owner','password':'trucker123'},timeout=20)
        assert r.status_code==403 and r.json()['code']=='untrusted_origin'
    r=requests.get(API+'/auth/csrf',timeout=20)
    assert r.status_code==401 and r.json()['detail']=='Not authenticated' and 'no-store' in r.headers['cache-control'].split(', ')
    assert table_snapshot()==before

def test_old_csrf_new_cookie_and_logout_session_isolation(ctx):
    s,old,_=browser_login();_,new,r=browser_login()
    s.cookies.update(r.cookies)
    before=table_snapshot()
    r=s.post(API+'/income',json={'date':'2026-10-29','source':'TEST_OLD_CSRF','amount':1},headers={'Origin':BASE,'X-CSRF-Token':old['csrf_token']},timeout=20)
    assert r.status_code==403 and r.json()['code']=='csrf_failed' and table_snapshot()==before
    request(s,'POST','/auth/logout',headers={'Origin':BASE,'X-CSRF-Token':new['csrf_token']},json={})
    assert requests.get(API+'/auth/me',headers={'Authorization':'Bearer '+new['token']},timeout=20).status_code==401
    assert requests.get(API+'/auth/me',headers={'Authorization':'Bearer '+old['token']},timeout=20).json()['role']=='owner'

def test_bearer_no_origin_no_csrf_machine_compatibility(ctx):
    s=login();s.cookies.clear()
    row=create(ctx,'income',{'date':'2026-10-29','source':'TEST_BRIDGE_NO_CSRF','amount':2},s)
    request(s,'DELETE','/income/'+str(row['id']))
    assert not any(x['id']==row['id'] for x in request(s,'GET','/income').json())

def test_trusted_preflight_methods_headers(ctx):
    for method in ['GET','POST','PUT','PATCH','DELETE','OPTIONS']:
        r=requests.options(API+'/income',headers={'Origin':BASE,'Access-Control-Request-Method':method,'Access-Control-Request-Headers':'Authorization,Content-Type,X-CSRF-Token'},timeout=20)
        assert r.status_code==200 and r.headers['access-control-allow-origin']==BASE and r.headers['access-control-allow-credentials']=='true'
    r=requests.options(API+'/income',headers={'Origin':BASE,'Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'X-Evil'},timeout=20)
    assert r.status_code==400