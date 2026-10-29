# Public UI: all global deletion types, direct deletes, confirmation safety, bulk erase, and safeguards.
import asyncio, json, os, uuid, traceback
from pathlib import Path
from playwright.async_api import async_playwright, expect
from pypdf import PdfReader
from regression_safety import table_snapshot
import test_full_regression as api

BASE=os.environ['REACT_APP_BACKEND_URL'].rstrip('/')
OUT=Path('/app/test_reports/browser_iter8_delete');OUT.mkdir(exist_ok=True)
results=[];diagnostics={};errors=[]

async def main():
    s=api.login();blob=api.archive(s);original=api.decrypt(blob);(OUT/'safety.mccoy').write_bytes(blob)
    prefix='TEST_del_'+uuid.uuid4().hex[:6];name=prefix.lower()
    fixtures={}
    def create(table,payload):
        row=api.request(s,'POST','/'+table,json=payload).json();fixtures[table]=row;return row
    d=create('drivers',{'name':prefix});t=create('trucks',{'truck_number':prefix,'tank_gallons':100});c=create('categories',{'name':prefix})
    common={'driver_id':d['id'],'truck_id':t['id']}
    payloads={'loads':{**common,'origin':prefix,'destination':'TEST_end','pay':500,'delivered_date':'1901-01-01'},'fuel':{**common,'date':'1901-01-01','gallons':100,'price_per_gallon':3,'miles':600,'location':prefix},'income':{**common,'date':'1901-01-01','amount':100,'source':prefix},'expenses':{**common,'date':'1901-01-01','amount':25,'description':prefix,'category_id':c['id']},'inspections':{**common,'date':'1901-01-01','result':'Fined','fine_amount':20,'fine_reason':prefix},'users':{'username':name,'password':'secret123'}}
    for table,payload in payloads.items():create(table,payload)
    api.request(s,'PUT','/telemetry/settings',json={**common,'server_url':'http://127.0.0.1:25555/api/ets2/telemetry','enabled':True})
    job={'sourceCity':prefix,'destinationCity':'TEST_end','income':100}
    api.request(s,'POST','/telemetry/ingest',json=api.sample(1,session=prefix,job=job,attached=True))
    event=next(x for x in api.events(s) if x['payload'].get('origin')==prefix);fixtures['telemetry/events']=event
    async with async_playwright() as p:
        browser=await p.chromium.launch(args=['--no-sandbox'])
        context=await browser.new_context(viewport={'width':1920,'height':800})
        page=await context.new_page();page.set_default_timeout(10000)
        page.on('pageerror',lambda e:errors.append(str(e)))
        async def shot(name):await page.screenshot(path=str(OUT/(name+'.jpg')),quality=40,full_page=False)
        async def step(name,fn):
            try:await fn();results.append({'name':name,'status':'PASS'});print('PASS',name,flush=True)
            except Exception as e:
                results.append({'name':name,'status':'FAIL','error':traceback.format_exc()});print('FAIL',name,traceback.format_exc(),flush=True);await shot(name.replace(' ','_')+'_failure')
        async def login(page,user='owner',password='trucker123'):
            await page.goto(BASE+'/login');await page.get_by_test_id('login-username-input').fill(user);await page.get_by_test_id('login-password-input').fill(password);await page.get_by_test_id('login-submit-btn').click(force=True);await expect(page.get_by_test_id('dashboard-page')).to_be_visible();await page.wait_for_timeout(400)
        async def nav(slug):
            await page.wait_for_timeout(300)
            if page.viewport_size['width']==390:await page.get_by_test_id('mobile-menu-btn').click(force=True)
            link=page.locator('[data-testid="nav-'+slug+'"]:visible').first
            await expect(link).to_be_visible()
            await link.click(force=True)
            await page.get_by_test_id('company-settings-page' if slug=='company' else slug+'-page').wait_for(state='visible')
        async def theme(mode):
            if await page.evaluate('document.documentElement.dataset.theme')!=mode:
                if page.viewport_size['width']==390:
                    await page.get_by_test_id('mobile-menu-btn').click(force=True);await page.get_by_test_id('mobile-theme-toggle').click(force=True);await page.get_by_test_id('mobile-menu-close').click(force=True)
                else:await page.get_by_test_id('theme-toggle').click(force=True)
        async def open_global(table):
            await page.get_by_test_id('open-delete-entries').click(force=True);await expect(page.get_by_test_id('delete-entries-dialog')).to_be_visible();await page.wait_for_timeout(200)
            await page.get_by_test_id('delete-entries-type').select_option(table,force=True);await page.wait_for_timeout(200)
            await expect(page.get_by_test_id('delete-entries-loading')).to_have_count(0)
        async def erase_open():
            await page.get_by_test_id('open-erase-records').click(force=True);await expect(page.get_by_test_id('erase-record-counts')).to_be_visible()
        async def delete_button(tid):
            await page.get_by_test_id(tid).click(force=True);await expect(page.get_by_test_id(tid+'-dialog')).to_be_visible()
            await page.get_by_test_id(tid+'-cancel').click(force=True);await expect(page.get_by_test_id(tid+'-dialog')).to_have_count(0);await page.wait_for_timeout(250)
            await page.get_by_test_id(tid).click(force=True);await expect(page.get_by_test_id(tid+'-dialog')).to_be_visible()
            await page.get_by_test_id(tid+'-confirm').click(force=True);await expect(page.get_by_test_id(tid+'-dialog')).to_have_count(0)
        try:
            await login(page)
            async def routes():
                for size in [{'width':1920,'height':800},{'width':390,'height':844}]:
                    await page.set_viewport_size(size)
                    for mode in ['dark','light']:
                        await theme(mode)
                        for slug in ['dashboard','income','expenses','fuel','loads','inspections','drivers','trucks','leaderboard','telemetry','users','create-user','company','report','backup','test-data']:
                            await nav(slug);await page.get_by_test_id('open-delete-entries').click(force=True);await expect(page.get_by_test_id('delete-entries-dialog')).to_be_visible();await page.wait_for_timeout(200)
                            geom=await page.get_by_test_id('delete-entries-dialog').evaluate('e=>({left:e.getBoundingClientRect().left,right:e.getBoundingClientRect().right,width:innerWidth,scroll:document.documentElement.scrollWidth})')
                            assert geom['left']>=0 and geom['right']<=size['width'] and geom['scroll']<=size['width'],geom
                            await page.keyboard.press('Escape');await expect(page.get_by_test_id('delete-entries-dialog')).to_have_count(0)
                await page.set_viewport_size({'width':1920,'height':800})
            await step('global utility every page both sizes themes no overflow',routes)
            async def all_types():
                await nav('dashboard');await page.get_by_test_id('range-today').click(force=True)
                for table,row in fixtures.items():
                    await open_global(table);await page.get_by_test_id('delete-entries-search').fill(prefix if table!='users' else name)
                    tid=f"manage-delete-{table.replace('/','-')}-{row['id']}";await expect(page.get_by_test_id(tid)).to_be_visible()
                    before=api.normalize(api.decrypt(api.archive(s)))
                    await page.get_by_test_id(tid).click(force=True);await expect(page.get_by_test_id(tid+'-dialog')).to_be_visible();await page.get_by_test_id(tid+'-cancel').click(force=True);await expect(page.get_by_test_id(tid+'-dialog')).to_have_count(0)
                    assert api.normalize(api.decrypt(api.archive(s)))==before
                    await page.wait_for_timeout(250);await page.get_by_test_id(tid).click(force=True);await page.get_by_test_id(tid+'-confirm').click(force=True);await expect(page.get_by_test_id(tid+'-dialog')).to_have_count(0);await expect(page.get_by_test_id(tid)).to_have_count(0)
                    assert not any(x['id']==row['id'] for x in api.request(s,'GET','/'+table).json())
                    await page.keyboard.press('Escape');await expect(page.get_by_test_id('delete-entries-dialog')).to_have_count(0)
                await open_global('users');assert await page.get_by_test_id('manage-delete-users-'+str(s.user['id'])).count()==0;await page.keyboard.press('Escape')
                await page.wait_for_timeout(400);await page.get_by_test_id('range-all').click(force=True);await expect(page.get_by_test_id('range-start')).to_have_count(0)
                await expect(page.get_by_test_id('kpi-income-value')).to_have_text('$0.00')
            await step('ten global types all dates nested cancel confirm safe self account',all_types)
            async def hundred_search():
                for i in range(105):api.request(s,'POST','/income',json={'date':'1901-01-01','amount':1,'source':prefix+'_bulk_'+str(i)})
                await open_global('income');await expect(page.get_by_test_id('delete-entries-count')).to_contain_text('105 entries');assert await page.locator('[data-testid^="manage-entry-income-"]').count()==100
                await page.get_by_test_id('delete-entries-search').fill(prefix+'_bulk_104');await expect(page.get_by_test_id('delete-entries-count')).to_contain_text('1 entries');assert await page.locator('[data-testid^="manage-entry-income-"]').count()==1
                await page.keyboard.press('Escape')
            await step('first hundred count search finds entries beyond display limit',hundred_search)
            async def refresh():
                await nav('dashboard');await page.reload();await expect(page.get_by_test_id('dashboard-page')).to_be_visible();await page.get_by_test_id('range-all').click(force=True);await expect(page.get_by_test_id('range-start')).to_have_count(0);await expect(page.get_by_test_id('kpi-income-value')).to_have_text('$105.00')
                row=api.request(s,'GET','/income').json()[0];await open_global('income');tid='manage-delete-income-'+str(row['id']);await delete_button(tid);await page.keyboard.press('Escape');await expect(page.get_by_test_id('kpi-income-value')).to_have_text('$104.00')
                await page.set_viewport_size({'width':390,'height':844});await nav('income');await open_global('income');row=api.request(s,'GET','/income').json()[0];tid='manage-delete-income-'+str(row['id']);await page.get_by_test_id(tid).click(force=True);await shot('nested_mobile_delete');await page.get_by_test_id(tid+'-confirm').click(force=True);await expect(page.get_by_test_id(tid+'-dialog')).to_have_count(0);await page.keyboard.press('Escape');await expect(page.get_by_test_id('income-row-'+str(row['id']))).to_have_count(0)
                await page.set_viewport_size({'width':1920,'height':800})
            await step('global delete refreshes current dashboard and mobile income without reload',refresh)
            async def direct_profile():
                await page.set_viewport_size({'width':1920,'height':800})
                d2=api.request(s,'POST','/drivers',json={'name':prefix+'_profile'}).json();t2=api.request(s,'POST','/trucks',json={'truck_number':prefix+'_profile','tank_gallons':100}).json()
                for table in ['loads','fuel','inspections']:
                    payload={**payloads[table],'driver_id':d2['id'],'truck_id':t2['id']};row=api.request(s,'POST','/'+table,json=payload).json()
                    if table=='loads':
                        await page.get_by_test_id('nav-drivers').first.click(force=True);await page.get_by_test_id('driver-profile-link-'+str(d2['id'])).click(force=True)
                    await page.reload();await expect(page.get_by_test_id('driver-profile-page')).to_be_visible();await page.get_by_test_id('range-all').click(force=True);await expect(page.get_by_test_id('range-start')).to_have_count(0);await page.get_by_test_id('profile-tab-'+table).click(force=True);await delete_button(f"profile-delete-{table}-{row['id']}");await expect(page.get_by_test_id(f"profile-{table}-{row['id']}")).to_have_count(0)
                    assert not any(x['id']==row['id'] for x in api.request(s,'GET','/'+table).json())
                    if table=='loads':await expect(page.get_by_test_id('profile-loads-total-value')).to_have_text('0');assert not any(x['load_id']==row['id'] for x in api.request(s,'GET','/income').json())
                await nav('telemetry');api.request(s,'PUT','/telemetry/settings',json={'driver_id':d2['id'],'truck_id':t2['id'],'server_url':'http://127.0.0.1:25555/api/ets2/telemetry','enabled':True})
                for i,status in enumerate(['pending','approved'],1):
                    api.request(s,'POST','/telemetry/ingest',json=api.sample(i,session='direct_'+prefix,job={'sourceCity':prefix+status,'destinationCity':'TEST_end','income':45},attached=True));e=api.events(s)[0]
                    if status=='approved':
                        saved=api.request(s,'POST',f"/telemetry/events/{e['id']}/review",json={'action':'approve','record':{**payloads['loads'],'driver_id':d2['id'],'truck_id':t2['id'],'status':'On Time'}}).json()['record_id'];await page.get_by_test_id('telemetry-tab-history').click(force=True)
                    await page.get_by_test_id('telemetry-refresh').click(force=True);await expect(page.get_by_test_id('telemetry-delete-'+str(e['id']))).to_be_visible();await delete_button('telemetry-delete-'+str(e['id']));await expect(page.get_by_test_id('telemetry-event-'+str(e['id']))).to_have_count(0)
                    if status=='approved':assert any(x['id']==saved for x in api.request(s,'GET','/loads').json())
            await step('direct profile three tables and telemetry pending history deletion',direct_profile)
            async def role_and_failure():
                dispatcher=await browser.new_context(viewport={'width':1920,'height':800});dp=await dispatcher.new_page();await login(dp,'dispatch1','haul1234');assert await dp.get_by_test_id('open-delete-entries').count()==0
                for slug in ['income','telemetry','drivers']:
                    await dp.get_by_test_id('nav-'+slug).first.click(force=True);assert await dp.get_by_test_id('open-delete-entries').count()==0
                await dispatcher.close()
                temp=api.request(s,'POST','/users',json={'username':name+'_owner','password':'secret123','role':'owner'}).json()
                ownercontext=await browser.new_context(viewport={'width':390,'height':844});op=await ownercontext.new_page();await login(op,temp['username'],'secret123')
                await op.get_by_test_id('open-delete-entries').click(force=True);await op.get_by_test_id('delete-entries-type').select_option('users',force=True);await op.wait_for_timeout(200)
                tid='manage-delete-users-'+str(s.user['id']);await op.get_by_test_id(tid).click(force=True);await op.get_by_test_id(tid+'-confirm').click(force=True);await expect(op.get_by_test_id(tid+'-error')).to_contain_text("owner account can't be removed");await expect(op.get_by_test_id(tid+'-dialog')).to_be_visible();await op.get_by_test_id(tid+'-cancel').click(force=True);await ownercontext.close()
            await step('dispatcher no delete controls protected owner failure stays visible',role_and_failure)
            async def erase_dialogs():
                await nav('backup');before=api.normalize(api.decrypt(api.archive(s)));preserved=api.decrypt(api.archive(s))['tables']
                preserved_names=['users','company_settings','categories','drivers','trucks','telemetry_sources']
                exact={k:v for k,v in table_snapshot().items() if k in preserved_names}
                for size in [{'width':1920,'height':800},{'width':390,'height':844}]:
                    await page.set_viewport_size(size)
                    for mode in ['dark','light']:
                        await theme(mode);await erase_open();assert await page.get_by_test_id('erase-records-confirm').is_disabled();await page.get_by_test_id('erase-owner-password').fill('trucker123');await page.get_by_test_id('erase-confirmation').fill('erase all records');assert await page.get_by_test_id('erase-records-confirm').is_disabled()
                        await page.get_by_test_id('erase-confirmation').fill('ERASE ALL RECORDS');assert await page.get_by_test_id('erase-records-confirm').is_enabled();await shot('erase_'+str(size['width'])+'_'+mode)
                        geom=await page.get_by_test_id('erase-records-dialog').evaluate('e=>({left:e.getBoundingClientRect().left,right:e.getBoundingClientRect().right})');assert geom['left']>=0 and geom['right']<=size['width']
                        await page.get_by_test_id('erase-records-cancel').click(force=True);await expect(page.get_by_test_id('erase-records-dialog')).to_have_count(0)
                        assert api.normalize(api.decrypt(api.archive(s)))==before
                await erase_open();await page.get_by_test_id('erase-owner-password').fill('wrong');await page.get_by_test_id('erase-confirmation').fill('ERASE ALL RECORDS');await page.get_by_test_id('erase-records-confirm').click(force=True);await expect(page.get_by_test_id('erase-records-error')).to_contain_text('incorrect');assert api.normalize(api.decrypt(api.archive(s)))==before
                await page.get_by_test_id('erase-owner-password').fill('trucker123');await page.get_by_test_id('erase-records-confirm').click(force=True);await expect(page.get_by_test_id('erase-records-dialog')).to_have_count(0)
                assert all(x==0 for x in api.request(s,'GET','/company/record-counts').json().values())
                after=api.decrypt(api.archive(s));assert after['tables']['users']==preserved['users'];assert after['tables']['company_settings']==preserved['company_settings']
                assert {k:v for k,v in table_snapshot().items() if k in preserved_names}==exact
                diagnostics['erased_accounts_and_branding_preserved']=True
                await nav('dashboard');await expect(page.get_by_test_id('kpi-income-value')).to_have_text('$0.00');await expect(page.get_by_test_id('kpi-profit-value')).to_have_text('$0.00')
                await nav('telemetry');assert api.request(s,'GET','/telemetry/status').json()['source']['enabled']
                await nav('expenses');await expect(page.locator('[data-testid^="category-delete-"]')).to_have_count(len(preserved['categories']))
                await page.get_by_test_id('new-category-input').fill(prefix+'_after');await page.get_by_test_id('add-category-btn').click(force=True);await expect(page.get_by_test_id('new-category-input')).to_have_value('')
                assert any(x['name']==prefix+'_after' for x in api.request(s,'GET','/categories').json())
            await step('erase dialogs both themes sizes cancel invalid reauth success signed in zero recreate',erase_dialogs)
            diagnostics['error_text']=await page.evaluate("""() => {const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));return errorElements.map(el => el.textContent).join(', ');} """)
            print('Found error message: '+diagnostics['error_text'] if diagnostics['error_text'] else 'No error messages found on the page')
        finally:
            await browser.close();s=api.login();api.request(s,'POST','/backup/restore',json={**api.body(blob),'confirm':'RESTORE MCCOY','owner_password':'trucker123'});s=api.login();assert api.normalize(api.decrypt(api.archive(s)))==api.normalize(original)
            diagnostics['original_restored']=True
            (OUT/'results.json').write_text(json.dumps({'results':results,'diagnostics':diagnostics,'page_errors':errors},indent=2));print('UI',sum(x['status']=='PASS' for x in results),'passed',sum(x['status']=='FAIL' for x in results),'failed',flush=True)

if __name__=='__main__':asyncio.run(main())