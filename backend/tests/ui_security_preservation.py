"""Real browser regression for photos, logout, CSRF retry and six-table erase preservation."""
import asyncio
import json
import os
import traceback
from pathlib import Path
from playwright.async_api import async_playwright, expect
import test_full_regression as api
from regression_safety import table_snapshot

BASE=os.environ['REACT_APP_BACKEND_URL'].rstrip('/')
OUT=Path('/app/test_reports/browser_iter8_security');OUT.mkdir(exist_ok=True)
results=[];errors=[];diagnostics={}

async def main():
    s=api.login()
    async with async_playwright() as p:
        browser=await p.chromium.launch(args=['--no-sandbox'])
        context=await browser.new_context(viewport={'width':1920,'height':800})
        page=await context.new_page();page.set_default_timeout(12000)
        page.on('pageerror',lambda e:errors.append(str(e)))
        network=[]
        page.on('response',lambda r:network.append({'path':r.url.split('/api/')[-1],'status':r.status}) if '/api/' in r.url else None)
        async def step(name,fn):
            try:await fn();results.append({'name':name,'status':'PASS'});print('PASS',name,flush=True)
            except Exception:
                results.append({'name':name,'status':'FAIL','error':traceback.format_exc()});print('FAIL',name,traceback.format_exc(),flush=True)
        async def login(target=page,user='owner',password='trucker123'):
            await target.goto(BASE+'/login')
            await target.get_by_test_id('login-username-input').fill(user);await target.get_by_test_id('login-password-input').fill(password)
            await target.get_by_test_id('login-submit-btn').click(force=True)
            await expect(target.get_by_test_id('dashboard-page')).to_be_visible()
        async def nav(slug):
            if page.viewport_size['width']==390:
                await page.get_by_test_id('mobile-menu-btn').click(force=True)
            link=page.locator('[data-testid="nav-'+slug+'"]:visible').first
            await expect(link).to_be_visible();await link.click(force=True)
            await page.wait_for_timeout(600)
        async def theme(mode):
            if await page.evaluate('document.documentElement.dataset.theme')!=mode:
                if page.viewport_size['width']==390:
                    await page.get_by_test_id('mobile-menu-btn').click(force=True);await page.get_by_test_id('mobile-theme-toggle').click(force=True);await page.get_by_test_id('mobile-menu-close').click(force=True)
                else:await page.get_by_test_id('theme-toggle').click(force=True)
        try:
            async def login_photo():
                await page.goto(BASE+'/login');await expect(page.get_by_test_id('login-form')).to_be_visible()
                photo=page.get_by_test_id('login-trucking-photo')
                await expect(photo).to_be_visible()
                assert await photo.evaluate('e=>e.complete&&e.naturalWidth>0&&new URL(e.currentSrc).origin===location.origin')
                await page.screenshot(path=str(OUT/'login_desktop.jpg'),quality=40,full_page=False)
            await step('local highway signin photograph desktop',login_photo)
            await login()
            async def cookie_reload():
                assert await page.evaluate('localStorage.getItem("vtc_token")') is None
                cookies=await context.cookies();cookie=next(c for c in cookies if c['name']=='access_token')
                diagnostics['browser_cookie_flags']={k:cookie[k] for k in ['httpOnly','secure','sameSite']}
                assert cookie['httpOnly'] and cookie['secure']
                assert 'access_token' not in await page.evaluate('document.cookie')
                await page.reload();await expect(page.get_by_test_id('dashboard-page')).to_be_visible()
            await step('cookie login reload HttpOnly no persistent bearer',cookie_reload)
            routes=['dashboard','income','expenses','fuel','trucks','loads','telemetry','drivers','leaderboard','inspections','users','create-user','company','report','backup','test-data']
            for width,height in [(1920,800),(390,844)]:
                await page.set_viewport_size({'width':width,'height':height})
                for mode in ['dark','light']:
                    await theme(mode)
                    async def matrix():
                        for slug in routes:
                            await nav(slug);await expect(page.get_by_test_id('header-logout-btn')).to_be_visible()
                            assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),slug
                        await nav('dashboard')
                        for name in ['open-road','red-truck','highway']:
                            photo=page.get_by_test_id('trucking-photo-'+name)
                            await expect(photo).to_be_visible()
                            assert await photo.evaluate('e=>e.complete&&e.naturalWidth>0&&new URL(e.currentSrc).origin===location.origin&&!!e.alt')
                        await page.screenshot(path=str(OUT/f'dashboard_{width}_{mode}.jpg'),quality=40,full_page=False)
                    await step(f'owner sixteen routes header logout photos no overflow {width} {mode}',matrix)
            await page.set_viewport_size({'width':1920,'height':800})
            async def csrf_retry():
                await page.reload();await expect(page.get_by_test_id('dashboard-page')).to_be_visible();await nav('income')
                attempts=[]
                async def wrong_once(route):
                    if route.request.method!='POST':
                        return await route.continue_()
                    headers=dict(route.request.headers);attempts.append(headers.get('x-csrf-token'))
                    if len(attempts)==1:headers['x-csrf-token']='wrong'
                    await route.continue_(headers=headers)
                await page.route('**/api/income',wrong_once)
                await page.get_by_test_id('add-income-btn').click(force=True)
                for field,value in [('date','2026-10-29'),('source','TEST_ACTUAL_CSRF_RETRY'),('amount','11')]:await page.get_by_test_id('input-'+field).fill(value)
                await page.get_by_test_id('income-save-btn').click(force=True)
                await expect(page.get_by_test_id('income-dialog')).to_have_count(0)
                await page.unroute('**/api/income',wrong_once)
                rows=[x for x in api.request(s,'GET','/income').json() if x['source']=='TEST_ACTUAL_CSRF_RETRY']
                diagnostics['real_csrf_retry']={'requests':len(attempts),'persisted_rows':len(rows),'statuses':[x['status'] for x in network if x['path']=='income']}
                assert len(attempts)==2 and len(rows)==1
                api.request(s,'DELETE','/income/'+str(rows[0]['id']))
            await step('actual middleware csrf403 one retry one business write after reload',csrf_retry)
            async def logout_fault():
                async def fail(route):await asyncio.sleep(0.4);await route.fulfill(status=503,content_type='application/json',body='{"detail":"TEST injected server failure"}')
                await page.route('**/api/auth/logout',fail)
                await page.get_by_test_id('header-logout-btn').click(force=True)
                await expect(page.get_by_test_id('header-logout-btn')).to_be_disabled()
                await expect(page.get_by_test_id('header-logout-btn-error')).to_be_visible()
                await expect(page.get_by_test_id('header-logout-btn')).to_be_enabled()
                assert '/login' not in page.url
                r=await context.request.get(BASE+'/api/auth/me');assert r.status==200
                await page.unroute('**/api/auth/logout',fail)
                async def abort(route):await route.abort('failed')
                await page.route('**/api/auth/logout',abort)
                await page.get_by_test_id('header-logout-btn').click(force=True);await expect(page.get_by_test_id('header-logout-btn-error')).to_be_visible()
                await expect(page.get_by_test_id('header-logout-btn')).to_be_enabled();assert '/login' not in page.url
                await page.unroute('**/api/auth/logout',abort)
            await step('MOCKED logout server503 and network failure busy error remain signed in retry',logout_fault)
            async def sibling_isolation():
                sibling=await context.new_page();await sibling.goto(BASE+'/');await expect(sibling.get_by_test_id('dashboard-page')).to_be_visible()
                separate=await browser.new_context();sp=await separate.new_page();await login(sp)
                copied=next(c['value'] for c in await context.cookies() if c['name']=='access_token')
                await page.get_by_test_id('header-logout-btn').click(force=True)
                await expect(page.get_by_test_id('login-form')).to_be_visible();await expect(sibling.get_by_test_id('login-form')).to_be_visible()
                assert api.requests.get(api.API+'/auth/me',headers={'Authorization':'Bearer '+copied},timeout=20).status_code==401
                assert (await separate.request.get(BASE+'/api/auth/me')).status==200
                assert api.request(s,'GET','/auth/me').json()['role']=='owner'
                await sibling.close();await separate.close();await login()
            await step('header logout revocation sibling tabs separate browser bridge unaffected',sibling_isolation)
            async def expired_logout():
                cookie=next(c['value'] for c in await context.cookies() if c['name']=='access_token')
                machine=api.requests.Session();machine.headers['Authorization']='Bearer '+cookie
                api.request(machine,'POST','/auth/logout')
                await page.get_by_test_id('header-logout-btn').click(force=True);await expect(page.get_by_test_id('login-form')).to_be_visible();await login()
            await step('already revoked401 logout signs out safely',expired_logout)
            async def late_me():
                ready=asyncio.Event()
                async def delay(route):
                    response=await route.fetch();ready.set();await asyncio.sleep(1);await route.fulfill(response=response)
                await page.route('**/api/auth/me',delay)
                await page.evaluate("localStorage.setItem('vtc_token','legacy-test')")
                task=asyncio.create_task(page.reload());await ready.wait()
                await page.evaluate("window.dispatchEvent(new StorageEvent('storage',{key:'vtc_logout_event',newValue:'TEST_nonsecret_logout'}))")
                await task;await expect(page.get_by_test_id('login-form')).to_be_visible();await page.wait_for_timeout(1200)
                await expect(page.get_by_test_id('login-form')).to_be_visible();assert await page.evaluate('localStorage.getItem("vtc_token")') is None
                await page.unroute('**/api/auth/me',delay)
                # This event deliberately did not revoke the server session; clear its cookie to reauthenticate.
                await context.clear_cookies();await login()
            await step('late me response cannot resurrect logout legacy bearer removed',late_me)
            async def erase():
                d=api.request(s,'POST','/drivers',json={'name':'TEST_preserve_UI_driver','notes':'TEST precise notes 🚚'}).json()
                t=api.request(s,'POST','/trucks',json={'truck_number':'TEST_preserve_UI_truck','tank_gallons':123,'make_model':'TEST retained'}).json()
                cat=api.request(s,'POST','/categories',json={'name':'TEST_preserve_UI_category'}).json()
                uid=(await (await context.request.get(BASE+'/api/auth/me')).json())['id']
                api.request(s,'PUT','/telemetry/settings',json={'driver_id':d['id'],'truck_id':t['id'],'enabled':True,'server_url':'http://127.0.0.1:25555/api/ets2/telemetry'})
                job={'sourceCity':'TEST_preserve_UI','destinationCity':'TEST_end','income':50}
                api.request(s,'POST','/telemetry/ingest',json=api.sample(1,session='ui_erase',job=job,attached=True))
                for table,payload in [('income',{'date':'2026-10-29','source':'TEST_old','amount':12}),('expenses',{'date':'2026-10-29','amount':1,'category_id':cat['id']}),('fuel',{'date':'2026-10-29','truck_id':t['id'],'price_per_gallon':2}),('loads',{'origin':'TEST_old','destination':'TEST_end','pay':3,'driver_id':d['id'],'truck_id':t['id'],'delivered_date':'2026-10-29'}),('inspections',{'date':'2026-10-29','result':'Passed','driver_id':d['id']})]:api.request(s,'POST','/'+table,json=payload)
                before=table_snapshot();preserved=['users','company_settings','drivers','trucks','categories','telemetry_sources']
                await nav('backup');await expect(page.get_by_test_id('erase-records-warning')).to_contain_text('telemetry connections are kept')
                await page.get_by_test_id('open-erase-records').click(force=True);await expect(page.get_by_test_id('erase-record-counts')).to_be_visible()
                text=await page.get_by_test_id('erase-record-counts').inner_text()
                assert all(name not in text.lower() for name in ['categories','drivers','trucks','sources'])
                await page.get_by_test_id('erase-records-cancel').click(force=True)
                await expect(page.get_by_test_id('erase-records-dialog')).to_have_count(0);await page.wait_for_timeout(250)
                assert table_snapshot()==before
                await page.get_by_test_id('open-erase-records').click(force=True);await expect(page.get_by_test_id('erase-record-counts')).to_be_visible()
                await page.get_by_test_id('erase-confirmation').fill('ERASE ALL RECORDS');await page.get_by_test_id('erase-owner-password').fill('wrong')
                await page.get_by_test_id('erase-records-confirm').click(force=True);await expect(page.get_by_test_id('erase-records-error')).to_contain_text('incorrect');assert table_snapshot()==before
                await page.get_by_test_id('erase-owner-password').fill('trucker123')
                await page.get_by_test_id('erase-records-confirm').click(force=True);await expect(page.get_by_test_id('erase-records-dialog')).to_have_count(0)
                after=table_snapshot();assert {k:after[k] for k in preserved}=={k:before[k] for k in preserved}
                assert all(after[k]==[] for k in ['income','expenses','fuel','loads','inspections','telemetry_events'])
                assert api.request(s,'GET',f"/drivers/{d['id']}/profile").json()['loads']==[]
                api.request(s,'POST','/telemetry/ingest',json=api.sample(2,session='ui_erase',job=job,attached=True));assert api.events(s)==[]
                api.request(s,'POST','/telemetry/ingest',json=api.sample(3,session='ui_erase'))
                api.request(s,'POST','/telemetry/ingest',json=api.sample(4,session='ui_erase',job=job,attached=True));assert len(api.events(s))==1
                for seq,fuel in enumerate([100,150,150,150,150],5):api.request(s,'POST','/telemetry/ingest',json=api.sample(seq,session='ui_erase',fuel=fuel))
                assert any(x['kind']=='fuel' for x in api.events(s))
                await nav('dashboard');await page.get_by_test_id('range-all').click(force=True);await expect(page.get_by_test_id('kpi-income-value')).to_have_text('$0.00')
                await nav('fuel');await page.get_by_test_id('add-fuel-btn').click(force=True)
                await page.get_by_test_id('input-truck-id').click(force=True);await page.wait_for_timeout(200)
                await page.get_by_test_id('input-truck-id-option-'+str(t['id'])).click(force=True)
                assert await page.get_by_test_id('input-gallons').input_value()=='123'
                await page.get_by_test_id('input-date').fill('2026-10-29');await page.get_by_test_id('input-price-per-gallon').fill('2');await page.get_by_test_id('input-miles').fill('738')
                await expect(page.get_by_test_id('fuel-mpg-preview')).to_have_text('6.00');await page.get_by_test_id('fuel-save-btn').click(force=True);await expect(page.get_by_test_id('fuel-dialog')).to_have_count(0)
                assert api.request(s,'GET','/fuel').json()[0]['gallons']==123
                diagnostics['UI_erase_exact_preservation_and_continuity']=True
            await step('UI cookieCSRF erase exact all setup source rows next job fuel manual fleet reusable',erase)
            for control,width in [('logout-btn',1920),('mobile-logout-btn',390)]:
                async def sidebar():
                    await page.set_viewport_size({'width':width,'height':800 if width==1920 else 844})
                    if width==390:await page.get_by_test_id('mobile-menu-btn').click(force=True)
                    await expect(page.get_by_test_id(control)).to_be_visible();await page.get_by_test_id(control).click(force=True)
                    await expect(page.get_by_test_id('login-form')).to_be_visible();await login()
                await step(control+' visible sidebar logout',sidebar)
            async def dispatch():
                await page.get_by_test_id('header-logout-btn').click(force=True);await expect(page.get_by_test_id('login-form')).to_be_visible()
                await login(user='dispatch1',password='haul1234')
                for width,height in [(1920,800),(390,844)]:
                    await page.set_viewport_size({'width':width,'height':height})
                    for mode in ['dark','light']:
                        await theme(mode)
                        for slug in ['dashboard','income','expenses','fuel','trucks','loads','telemetry','drivers','leaderboard','inspections','report']:
                            await nav(slug);await expect(page.get_by_test_id('header-logout-btn')).to_be_visible();assert await page.get_by_test_id('open-delete-entries').count()==0
                            assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                        assert await page.get_by_test_id('nav-users').count()==0
            await step('dispatcher eleven routes desktop mobile both themes no owner delete controls',dispatch)
            async def iframe():
                # External parent is a test-only document. Child remains the actual preview app.
                parent=await context.new_page()
                async def parent_html(route):await route.fulfill(content_type='text/html',body='<iframe src="'+BASE+'" style="width:100%;height:900px"></iframe>')
                await parent.route('https://security-parent.example/**',parent_html)
                await parent.goto('https://security-parent.example/')
                frame=parent.frame_locator('iframe');await expect(frame.get_by_test_id('login-form')).to_be_visible()
                await frame.get_by_test_id('login-username-input').fill('owner');await frame.get_by_test_id('login-password-input').fill('trucker123');await frame.get_by_test_id('login-submit-btn').click(force=True)
                await expect(frame.get_by_test_id('dashboard-page')).to_be_visible();await parent.reload();await expect(parent.frame_locator('iframe').get_by_test_id('dashboard-page')).to_be_visible()
                diagnostics['iframe']='Real child login/reload works under synthetic external parent; top-level cookie is separately partitioned by preview ingress.'
                await parent.close()
            await step('external parent MOCKED document real child iframe login reload',iframe)
            error_text=await page.evaluate("""() => {const errorElements=Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));return errorElements.map(el=>el.textContent).join(', ');} """)
            print('Found error message: '+error_text if error_text else 'No error messages found on the page')
            diagnostics['error_text']=error_text
        finally:
            await browser.close()
            (OUT/'results.json').write_text(json.dumps({'results':results,'diagnostics':diagnostics,'page_errors':errors,'http_errors':[x for x in network if x['status']>=400]},indent=2))
            print('UI_SECURITY',sum(x['status']=='PASS' for x in results),'passed',sum(x['status']=='FAIL' for x in results),'failed',flush=True)

if __name__=='__main__':asyncio.run(main())