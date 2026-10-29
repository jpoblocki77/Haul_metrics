# Public-preview Playwright regression: all navigation, CRUD, accounts, telemetry, backup, themes and PDF.
import asyncio
import importlib.util
import json
import os
from pathlib import Path
import traceback
import uuid
from playwright.async_api import async_playwright, expect
from pypdf import PdfReader

spec=importlib.util.spec_from_file_location('regression',Path(__file__).with_name('test_full_regression.py'))
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
BASE=os.environ['REACT_APP_BACKEND_URL'].rstrip('/')
OUT=Path('/app/test_reports/browser_iter4');OUT.mkdir(exist_ok=True)
results=[]; errors=[]; diagnostics={}

def save():
    (OUT/'ui_results.json').write_text(json.dumps({'results':results,'page_errors':errors,'diagnostics':diagnostics},indent=2,default=str))

async def main():
    safety=api.login(); original=api.archive(safety); (OUT/'initial_ui_state.mccoy').write_bytes(original)
    prefix='test_ui_'+uuid.uuid4().hex[:8]
    async with async_playwright() as p:
        browser=await p.chromium.launch(args=['--no-sandbox'])
        context=await browser.new_context(viewport={'width':1920,'height':800},accept_downloads=True)
        page=await context.new_page(); page.set_default_timeout(7000)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('dialog',lambda d:d.accept())
        async def step(name,fn):
            try:
                await fn();results.append({'name':name,'status':'PASS'});print('PASS',name,flush=True)
            except Exception as e:
                results.append({'name':name,'status':'FAIL','error':str(e)});print('FAIL',name,str(e),flush=True)
                await page.screenshot(path=str(OUT/(name.replace(' ','_').replace('/','_')+'_failure.jpg')),quality=40,full_page=False)
            save()
        async def ui_login(username='owner',password='trucker123'):
            await page.goto(BASE+'/login');await page.get_by_test_id('login-username-input').fill(username)
            await page.get_by_test_id('login-password-input').fill(password)
            await page.get_by_test_id('login-submit-btn').click()
            await expect(page.get_by_test_id('dashboard-page')).to_be_visible()
        async def nav(name):
            await page.get_by_test_id('nav-'+name).first.click();await page.wait_for_timeout(250)
        async def get(path):
            r=await page.request.get(BASE+'/api'+path);assert r.ok,(path,r.status,await r.text());return await r.json()
        async def post(path,data,method='post'):
            r=await getattr(page.request,method)(BASE+'/api'+path,data=data);assert r.ok,(path,r.status,await r.text());return await r.json()
        async def field(name,value,select=False):
            tid='input-'+name.replace('_','-')
            if select:
                await page.get_by_test_id(tid).click(force=True);await page.wait_for_timeout(200)
                await page.get_by_test_id(tid+'-option-'+str(value)).click(force=True)
            else: await page.get_by_test_id(tid).fill(str(value))
        async def shot(name):
            await page.screenshot(path=str(OUT/(name+'.jpg')),quality=40,full_page=False)
        async def overflow(label):
            d=await page.evaluate('''() => ({width:innerWidth,scroll:document.documentElement.scrollWidth, offenders:[...document.querySelectorAll('main *')].filter(e=>{const r=e.getBoundingClientRect();return r.right>innerWidth+2 && !e.closest('.overflow-x-auto')}).slice(0,12).map(e=>({tag:e.tagName,testid:e.dataset.testid,class:e.className,text:e.textContent.slice(0,80)}))})''')
            diagnostics['overflow_'+label]=d
            assert d['scroll']<=d['width']+1,d
        try:
            async def auth():
                await page.goto(BASE+'/trucks');await expect(page.get_by_test_id('login-form')).to_be_visible()
                assert await page.evaluate("document.documentElement.dataset.theme")=='dark'
                await page.get_by_test_id('login-username-input').fill('owner');await page.get_by_test_id('login-password-input').fill('wrong_password')
                await page.get_by_test_id('login-submit-btn').click();await expect(page.get_by_test_id('login-form')).to_contain_text('Wrong username or password')
                await ui_login();await expect(page.get_by_test_id('dashboard-page')).to_be_visible()
                await shot('dashboard_empty_dark')
            await step('auth protected invalid valid login',auth)
            async def themes():
                await page.get_by_test_id('theme-toggle').click();assert await page.evaluate("document.documentElement.dataset.theme")=='light'
                await page.reload();await expect(page.get_by_test_id('dashboard-page')).to_be_visible();assert await page.evaluate("document.documentElement.dataset.theme")=='light'
                await page.get_by_test_id('logout-btn').first.click();await expect(page.get_by_test_id('login-form')).to_be_visible();assert await page.evaluate("document.documentElement.dataset.theme")=='light'
                await page.get_by_test_id('login-theme-toggle').click();assert await page.evaluate("document.documentElement.dataset.theme")=='dark'
                await ui_login()
            await step('theme persists routes reload logout login',themes)
            async def allnav():
                for name,tid in [('income','income-page'),('expenses','expenses-page'),('fuel','fuel-page'),('trucks','trucks-page'),('loads','loads-page'),('telemetry','telemetry-page'),('drivers','drivers-page'),('leaderboard','leaderboard-page'),('inspections','inspections-page'),('users','users-page'),('create-user','create-user-page'),('report','report-page'),('backup','backup-page'),('test-data','test-data-page'),('dashboard','dashboard-page')]:
                    await nav(name);await expect(page.get_by_test_id(tid)).to_be_visible()
            await step('all fifteen sidebar routes including scroll',allnav)
            async def users():
                await nav('create-user');assert await page.get_by_test_id('new-user-role').input_value()=='dispatcher'
                await page.get_by_test_id('create-user-btn').click();assert not await page.get_by_test_id('new-user-username').evaluate('(e)=>e.checkValidity()')
                await page.get_by_test_id('new-user-username').fill('bad name!');await page.get_by_test_id('new-user-password').fill('123');await page.get_by_test_id('new-user-confirm').fill('123')
                await page.get_by_test_id('create-user-btn').click();assert not await page.get_by_test_id('new-user-username').evaluate('(e)=>e.checkValidity()')
                await page.get_by_test_id('new-user-username').fill(prefix);await page.get_by_test_id('create-user-btn').click();assert not await page.get_by_test_id('new-user-password').evaluate('(e)=>e.checkValidity()')
                await page.get_by_test_id('new-user-password').fill('secret123');await page.get_by_test_id('new-user-confirm').fill('different123')
                await page.get_by_test_id('new-user-toggle-password').click();assert await page.get_by_test_id('new-user-password').get_attribute('type')=='text'
                await page.get_by_test_id('create-user-btn').click();await expect(page.get_by_test_id('create-user-error')).to_contain_text("don't match")
                await page.get_by_test_id('new-user-confirm').fill('secret123');await page.get_by_test_id('create-user-btn').click()
                await expect(page.get_by_test_id('user-created-confirmation')).to_contain_text(prefix)
                await nav('create-user');await page.get_by_test_id('new-user-username').fill(prefix);await page.get_by_test_id('new-user-password').fill('secret123');await page.get_by_test_id('new-user-confirm').fill('secret123');await page.get_by_test_id('create-user-btn').click();await expect(page.get_by_test_id('create-user-error')).to_contain_text('taken')
                await page.get_by_test_id('create-user-cancel').click();await expect(page.get_by_test_id('users-page')).to_be_visible()
            await step('create user validation visibility duplicate success',users)
            async def dispatcher():
                await page.get_by_test_id('logout-btn').first.click();await ui_login(prefix,'secret123')
                assert await page.get_by_test_id('nav-users').count()==0
                for path in ['/users','/users/new','/test-data','/backup']:
                    await page.goto(BASE+path);await expect(page.get_by_test_id('dashboard-page')).to_be_visible();assert page.url.rstrip('/')==BASE
                await nav('income');assert await page.locator('[data-testid^="delete-income-"]').count()==0
                await page.get_by_test_id('add-income-btn').click();await field('date','2026-10-12');await field('source','TEST_dispatcher');await field('amount',75)
                async with page.expect_response(lambda r:'/api/income' in r.url and r.request.method=='POST') as resp:await page.get_by_test_id('income-save-btn').click()
                d=await (await resp.value).json();await expect(page.get_by_test_id(f"income-row-{d['id']}")).to_be_visible();await page.get_by_test_id(f"edit-income-{d['id']}").click();await field('amount',80);await page.get_by_test_id('income-save-btn').click();await expect(page.get_by_test_id(f"income-row-{d['id']}")).to_contain_text('$80.00')
                await page.get_by_test_id('logout-btn').first.click();await ui_login()
            await step('dispatcher login owner-route redirects create edit no-delete',dispatcher)
            async def edituser():
                await nav('users');await page.get_by_test_id('edit-user-'+prefix).click();await page.get_by_test_id('edit-user-save').click();await expect(page.get_by_test_id('edit-user-error')).to_contain_text('No changes')
                await page.get_by_test_id('edit-user-role').select_option('owner',force=True);await page.wait_for_timeout(200)
                await page.get_by_test_id('edit-user-password').fill('newsecret123');await page.get_by_test_id('edit-user-confirm').fill('bad');await page.get_by_test_id('edit-user-save').click();await expect(page.get_by_test_id('edit-user-error')).to_contain_text("don't match")
                await page.get_by_test_id('edit-user-confirm').fill('newsecret123');await page.get_by_test_id('edit-user-save').click();await expect(page.get_by_test_id('user-role-'+prefix)).to_contain_text('owner')
                await page.get_by_test_id('logout-btn').first.click();await ui_login(prefix,'newsecret123');await nav('users');await page.get_by_test_id('edit-user-'+prefix).click();assert await page.get_by_test_id('edit-user-role').is_disabled()
                await page.get_by_test_id('edit-user-password').fill('selfchanged123');await page.get_by_test_id('edit-user-confirm').fill('selfchanged123');await page.get_by_test_id('edit-user-save').click();await expect(page.get_by_test_id('login-form')).to_be_visible();await ui_login(prefix,'selfchanged123')
                await page.get_by_test_id('logout-btn').first.click();await ui_login();await nav('users');await page.get_by_test_id('delete-user-'+prefix).click();await expect(page.get_by_test_id('user-row-'+prefix)).to_have_count(0)
            await step('user editor role reset self reset logout and delete',edituser)
            ids={}; records={}
            async def crud(table,fields,editfield,editvalue):
                await nav(table);await page.get_by_test_id('add-'+table+'-btn').click()
                await expect(page.get_by_test_id(table+'-dialog')).to_be_visible()
                for key,value in fields.items():await field(key,value,select=key.endswith('_id') or key in ['status','result'])
                if table=='fuel':
                    assert await page.get_by_test_id('input-gallons').input_value()=='180'
                    await expect(page.get_by_test_id('fuel-total-preview')).to_have_text('$720.00');await expect(page.get_by_test_id('fuel-mpg-preview')).to_have_text('6.00')
                async with page.expect_response(lambda r:'/api/'+table in r.url and r.request.method=='POST') as resp:await page.get_by_test_id(table+'-save-btn').click()
                response=await resp.value;assert response.ok,await response.text();r=await response.json();ids[table]=r['id'];records[table]=r
                await expect(page.get_by_test_id(f"{table}-row-{r['id']}")).to_be_visible()
                await page.get_by_test_id(f"edit-{table}-{r['id']}").click();await field(editfield,editvalue,select=editfield in ['status','result'])
                await page.get_by_test_id(table+'-save-btn').click();await expect(page.get_by_test_id(table+'-dialog')).to_have_count(0)
                changed=next(x for x in await get('/'+table) if x['id']==r['id']);assert changed[editfield]==editvalue
                await page.get_by_test_id(table+'-search').fill('NEVER_MATCH_TEST');await expect(page.get_by_test_id(table+'-empty')).to_be_visible();await page.get_by_test_id(table+'-search').fill('')
            await step('trucks create edit search capacity',lambda:crud('trucks',{'truck_number':'TEST_UI_TRUCK','tank_gallons':180,'make_model':'TEST_Peterbilt'},'make_model','TEST_Kenworth'))
            await step('drivers create edit search',lambda:crud('drivers',{'name':'TEST_UI_DRIVER','notes':'TEST_notes'},'notes','TEST_edited'))
            async def categories():
                await nav('expenses');await page.get_by_test_id('new-category-input').fill('TEST_UI_CATEGORY');await page.get_by_test_id('add-category-btn').click();await page.wait_for_timeout(300)
                c=next(x for x in await get('/categories') if x['name']=='TEST_UI_CATEGORY');ids['categories']=c['id']
                await page.get_by_test_id(f"category-rename-{c['id']}").click();await page.get_by_test_id(f"category-edit-input-{c['id']}").fill('TEST_UI_RENAMED');await page.get_by_test_id(f"category-save-{c['id']}").click();await expect(page.get_by_test_id(f"category-{c['id']}")).to_contain_text('TEST_UI_RENAMED')
            await step('category add rename',categories)
            await step('income create edit search',lambda:crud('income',{'date':'2026-10-12','source':'TEST_UI_BONUS','amount':100,'driver_id':ids['drivers'],'truck_id':ids['trucks']},'amount',125))
            await step('expenses create edit search',lambda:crud('expenses',{'date':'2026-10-12','amount':100,'description':'TEST_UI_REPAIRS','category_id':ids['categories'],'driver_id':ids['drivers'],'truck_id':ids['trucks']},'amount',150))
            await step('fuel create edit search computed preview',lambda:crud('fuel',{'date':'2026-10-12','truck_id':ids['trucks'],'price_per_gallon':4,'miles':1080,'driver_id':ids['drivers'],'location':'TEST_UI_STATION'},'price_per_gallon',5))
            await step('loads create edit status linked income',lambda:crud('loads',{'origin':'TEST_UI_ORIGIN','destination':'TEST_UI_DEST','cargo':'TEST_boxes','pay':1000,'driver_id':ids['drivers'],'truck_id':ids['trucks'],'miles':500,'due_date':'2026-10-12','delivered_date':'2026-10-12'},'status','Late'))
            await step('inspections create edit fines passed clears',lambda:crud('inspections',{'date':'2026-10-12','result':'Fined','fine_amount':50,'fine_reason':'TEST_UI_SPEED','driver_id':ids['drivers'],'truck_id':ids['trucks'],'location':'TEST_UI_DOT'},'result','Passed'))
            async def range_exports():
                for table in ['income','expenses','fuel','loads','inspections']:
                    await nav(table);await page.get_by_test_id('range-custom').click();await page.get_by_test_id('range-start').fill('2026-10-12');await page.get_by_test_id('range-end').fill('2026-10-12');await page.wait_for_timeout(300)
                    async with page.expect_download() as dl:await page.get_by_test_id('export-'+table+'-btn').click()
                    download=await dl.value;path=OUT/('export_'+table+'.csv');await download.save_as(str(path));assert path.stat().st_size>20
                    await page.get_by_test_id('range-start').fill('1990-01-01');await page.get_by_test_id('range-end').fill('1990-01-31');await expect(page.get_by_test_id(table+'-empty')).to_be_visible();await page.get_by_test_id('range-all').click()
                await nav('dashboard')
                for preset in ['today','week','month','last-month','custom','all']:
                    await page.get_by_test_id('range-'+preset).click();await expect(page.get_by_test_id('dashboard-page')).to_be_visible()
                stats=await get('/stats/dashboard');assert await page.get_by_test_id('kpi-income-value').inner_text()==f"${stats['income']:,.2f}"
            await step('all CSV downloads custom empty ranges and presets',range_exports)
            async def seed():
                await nav('test-data');await page.get_by_test_id('seed-test-data-btn').click();await expect(page.get_by_test_id('test-count-loads')).to_have_text('60');await expect(page.get_by_test_id('test-count-fuel')).to_have_text('70')
                await nav('dashboard');await page.wait_for_timeout(500)
                diag=await page.locator('[data-testid^="chart-"]').evaluate_all('(els)=>els.map(e=>({id:e.dataset.testid,svg:e.querySelectorAll("svg.recharts-surface").length,bars:e.querySelectorAll(".recharts-bar-rectangle").length}))');diagnostics['dashboard_charts']=diag
                assert len(diag)==7 and all(x['svg']>0 for x in diag),diag
                await shot('dashboard_populated_dark')
            await step('sample data add and seven dashboard charts',seed)
            async def leaderboard():
                await nav('leaderboard');h=await get('/stats/leaderboard-history');assert len(h['history'])>0
                for item in h['history'][:3]:
                    await page.get_by_test_id('history-'+item['month']).click();await expect(page.get_by_test_id('leaderboard-month')).to_have_value(item['month']);await expect(page.get_by_test_id('top-driver-name')).to_have_text(item['name'])
                for month in ['2026-05','2026-06','2026-07']:await page.get_by_test_id('leaderboard-month').fill(month)
                h7=next(x for x in h['history'] if x['month']=='2026-07');await expect(page.get_by_test_id('top-driver-name')).to_have_text(h7['name'])
                await page.get_by_test_id('leaderboard-month').fill('1990-01');await expect(page.get_by_test_id('leaderboard-empty')).to_be_visible()
            await step('leaderboard history trophies quick month changes empty',leaderboard)
            async def profiles():
                await nav('drivers');await page.get_by_test_id('driver-profile-link-'+str(ids['drivers'])).click();await expect(page.get_by_test_id('driver-profile-page')).to_be_visible();await expect(page.get_by_test_id('profile-loads-total-value')).to_have_text('1')
                for tab in ['loads','fuel','inspections']:
                    await page.get_by_test_id('profile-tab-'+tab).click();await expect(page.get_by_test_id('profile-'+tab+'-records')).to_be_visible()
                await page.get_by_test_id('range-custom').click();await page.get_by_test_id('range-start').fill('1990-01-01');await page.get_by_test_id('range-end').fill('1990-01-31');await expect(page.get_by_test_id('profile-records-empty')).to_be_visible()
                await page.get_by_test_id('range-all').click();await page.get_by_test_id('driver-profile-back').click();await expect(page.get_by_test_id('drivers-page')).to_be_visible()
                await page.goto(BASE+'/drivers/999999');await expect(page.get_by_test_id('driver-profile-error')).to_contain_text('Driver not found');await page.get_by_test_id('driver-profile-error-back').click()
            await step('driver profile links totals tabs empty invalid navigation',profiles)
            async def report():
                await nav('report');await page.get_by_test_id('report-month').fill('2026-07');await expect(page.get_by_test_id('report-income')).to_be_visible();await page.wait_for_timeout(500)
                stats=await get('/stats/dashboard?start=2026-07-01&end=2026-07-31');assert await page.get_by_test_id('report-income').inner_text()==f"${stats['income']:,.2f}"
                assert await page.get_by_test_id('print-report-btn').is_enabled()
                charts=await page.locator('.report-chart').evaluate_all('''els=>els.map(e=>({rect:{width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height},container:[...e.querySelectorAll('.recharts-responsive-container')].map(c=>({width:c.getBoundingClientRect().width,height:c.getBoundingClientRect().height,display:getComputedStyle(c).display,parent:c.parentElement.outerHTML.slice(0,1800)})),svg:e.querySelectorAll('svg.recharts-surface').length,html:e.outerHTML.slice(0,3500)}))''')
                diagnostics['report_chart_dom']=charts
                await shot('report_dark_populated')
                pdf=OUT/'monthly_report_july.pdf';await page.pdf(path=str(pdf),format='Letter',print_background=True,prefer_css_page_size=True)
                reader=PdfReader(pdf);diagnostics['report_pdf']={'pages':len(reader.pages),'text':''.join(x.extract_text() for x in reader.pages)}
                assert len(reader.pages)==1,f'{len(reader.pages)} PDF pages'
                assert all(x['svg']>0 for x in charts),'Nonzero data but charts have no SVG: '+str(charts)
            await step('monthly report stats chart DOM actual PDF',report)
            async def report_switch():
                for month in ['2026-05','2026-06','2026-07']:await page.get_by_test_id('report-month').fill(month)
                await expect(page.get_by_test_id('report-title')).to_have_text('July 2026');await expect(page.get_by_test_id('report-income')).to_be_visible()
                s=await get('/stats/dashboard?start=2026-07-01&end=2026-07-31');await expect(page.get_by_test_id('report-income')).to_have_text(f"${s['income']:,.2f}")
                await page.get_by_test_id('report-month').fill('1990-01');await expect(page.get_by_test_id('report-income-expense-chart')).to_contain_text('No transactions');await expect(page.get_by_test_id('report-mpg-chart')).to_contain_text('No measured MPG')
            await step('report rapid month switching and empty',report_switch)
            telemetry_ids={}
            async def telemetry():
                await nav('telemetry');await page.get_by_test_id('telemetry-driver_id').select_option(str(ids['drivers']));await page.get_by_test_id('telemetry-truck_id').select_option(str(ids['trucks']))
                await page.get_by_test_id('telemetry-server-url').fill('https://example.com/api/ets2/telemetry');await page.get_by_test_id('telemetry-save-settings').click();await expect(page.get_by_test_id('telemetry-error')).to_contain_text('local HTTP')
                await page.get_by_test_id('telemetry-server-url').fill('http://127.0.0.1:25555/api/ets2/telemetry');await page.get_by_test_id('telemetry-enabled').check();await page.get_by_test_id('telemetry-save-settings').click();await page.wait_for_timeout(300)
                async with page.expect_download() as dl:await page.get_by_test_id('telemetry-download-bridge').click()
                download=await dl.value;await download.save_as(str(OUT/'McCoyTelemetry.py'));compile((OUT/'McCoyTelemetry.py').read_text(),'bridge','exec')
                job={'sourceCity':'TEST_UI_TELEMETRY','destinationCity':'TEST_UI_END','income':200,'deadlineTime':'2026-10-29T12:00:00Z'}
                await post('/telemetry/ingest',api.sample(1,session=prefix,job=job,attached=True));await page.get_by_test_id('telemetry-refresh').click();await page.wait_for_timeout(300)
                e=next(x for x in await get('/telemetry/events') if x['payload'].get('origin')=='TEST_UI_TELEMETRY');telemetry_ids['load']=e['id']
                await page.get_by_test_id(f"telemetry-review-{e['id']}").click();await expect(page.get_by_test_id('telemetry-review-dialog')).to_be_visible()
                await page.get_by_test_id('telemetry-review-save').click();assert not await page.get_by_test_id('telemetry-review-delivered_date').evaluate('(e)=>e.checkValidity()')
                await page.get_by_test_id('telemetry-review-delivered_date').fill('2026-10-28');await page.get_by_test_id('telemetry-review-status').select_option('On Time',force=True);await page.wait_for_timeout(200);await shot('telemetry_review_desktop_dark')
                await page.get_by_test_id('telemetry-review-save').click();await expect(page.get_by_test_id('telemetry-review-dialog')).to_have_count(0)
                await page.get_by_test_id('telemetry-tab-history').click();await expect(page.get_by_test_id(f"telemetry-event-status-{e['id']}")).to_have_text('approved')
                for seq,f in enumerate([100,150,150,150,150],2):await post('/telemetry/ingest',api.sample(seq,session=prefix,fuel=f))
                await page.get_by_test_id('telemetry-tab-pending').click();await page.get_by_test_id('telemetry-refresh').click();await page.wait_for_timeout(300)
                e=next(x for x in await get('/telemetry/events') if x['kind']=='fuel');telemetry_ids['fuel']=e['id'];await page.get_by_test_id(f"telemetry-review-{e['id']}").click();await page.get_by_test_id('telemetry-review-price_per_gallon').fill('4')
                await expect(page.get_by_test_id('telemetry-review-total')).to_contain_text('$52.83');await page.get_by_test_id('telemetry-review-save').click();await expect(page.get_by_test_id('telemetry-review-dialog')).to_have_count(0)
                job['destinationCity']='TEST_UI_DISMISS';await post('/telemetry/ingest',api.sample(7,session=prefix,job=job,attached=True));await page.get_by_test_id('telemetry-refresh').click();await page.wait_for_timeout(300)
                e=next(x for x in await get('/telemetry/events') if x['payload'].get('destination')=='TEST_UI_DISMISS');await page.get_by_test_id(f"telemetry-dismiss-{e['id']}").click();await page.get_by_test_id('telemetry-tab-history').click();await expect(page.get_by_test_id(f"telemetry-event-status-{e['id']}")).to_have_text('dismissed')
            await step('telemetry settings errors bridge approve fuel load dismiss history',telemetry)
            async def viewport_theme_matrix():
                profile=ids['drivers']
                routes=[('create_user','/users/new','create-user-page'),('users','/users','users-page'),('backup','/backup','backup-page'),('telemetry','/telemetry','telemetry-page'),('report','/report','report-page'),('profile',f'/drivers/{profile}','driver-profile-page')]
                for size in [{'width':1920,'height':800},{'width':390,'height':844}]:
                    await page.set_viewport_size(size)
                    for theme in ['dark','light']:
                        await page.goto(BASE+'/');await expect(page.get_by_test_id('dashboard-page')).to_be_visible()
                        if await page.evaluate('document.documentElement.dataset.theme')!=theme:
                            if size['width']==390:
                                await page.get_by_test_id('mobile-menu-btn').click();await page.get_by_test_id('mobile-theme-toggle').click();await page.get_by_test_id('mobile-menu-close').click()
                            else: await page.get_by_test_id('theme-toggle').click()
                        for name,path,tid in routes:
                            await page.goto(BASE+path);await expect(page.get_by_test_id(tid)).to_be_visible();await page.wait_for_timeout(250)
                            if name=='report':await expect(page.get_by_test_id('report-income')).to_be_visible();assert await page.get_by_test_id('report-sheet').evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(255, 255, 255)'
                            await shot(f'{name}_{size["width"]}_{theme}')
                            try:await overflow(f'{name}_{size["width"]}_{theme}')
                            except AssertionError as e:results.append({'name':f'overflow {name} {size["width"]} {theme}','status':'FAIL','error':str(e)})
                        for name in ['income','expenses','fuel','trucks','loads','drivers','leaderboard','inspections','test-data']:
                            await page.goto(BASE+'/'+name);await page.wait_for_timeout(350)
                            try:await overflow(f'{name}_{size["width"]}_{theme}')
                            except AssertionError as e:results.append({'name':f'overflow {name} {size["width"]} {theme}','status':'FAIL','error':str(e)})
                await page.get_by_test_id('mobile-menu-btn').click();await expect(page.get_by_test_id('mobile-theme-toggle')).to_be_visible();await page.get_by_test_id('nav-backup').last.click();await expect(page.get_by_test_id('backup-page')).to_be_visible()
                await page.set_viewport_size({'width':1920,'height':800})
            await step('desktop mobile all pages both themes overflow sidebar',viewport_theme_matrix)
            async def long_name():
                d=await post('/drivers',{'name':'TEST_'+('VeryLongName'*20),'notes':'TEST_'+('LongNote'*25)})
                await page.set_viewport_size({'width':390,'height':844});await page.goto(BASE+f"/drivers/{d['id']}");await expect(page.get_by_test_id('driver-profile-page')).to_be_visible();await shot('profile_long_name_mobile');await overflow('profile_long_name_mobile')
            await step('mobile profile unbreakable long names',long_name)
            async def backup():
                await page.set_viewport_size({'width':1920,'height':800});await page.goto(BASE+'/backup');await expect(page.get_by_test_id('backup-page')).to_be_visible()
                await page.get_by_test_id('backup-password').fill(api.PASS);await page.get_by_test_id('backup-repeat').fill('different_password');await page.get_by_test_id('backup-download').click();await expect(page.get_by_test_id('backup-error')).to_contain_text("don't match")
                await page.get_by_test_id('backup-repeat').fill(api.PASS)
                async with page.expect_download() as dl:await page.get_by_test_id('backup-download').click()
                download=await dl.value;file=OUT/'ui_download.mccoy';await download.save_as(str(file));assert file.read_bytes().startswith(b'MCCOY-BACKUP-1')
                await page.get_by_test_id('restore-file').set_input_files(str(file));await page.get_by_test_id('restore-password').fill('wrong_password123');await page.get_by_test_id('backup-inspect').click();await expect(page.get_by_test_id('backup-error')).to_contain_text('Incorrect backup password')
                await page.get_by_test_id('restore-password').fill(api.PASS);await page.get_by_test_id('backup-inspect').click();await expect(page.get_by_test_id('restore-dialog')).to_be_visible();await expect(page.get_by_test_id('restore-owner-list')).to_contain_text('owner');assert await page.get_by_test_id('backup-restore').is_disabled();await shot('restore_dialog_desktop_light')
                await page.get_by_test_id('restore-cancel').click();await expect(page.get_by_test_id('restore-dialog')).to_have_count(0)
                await page.get_by_test_id('backup-inspect').click();await expect(page.get_by_test_id('restore-dialog')).to_be_visible();await page.set_viewport_size({'width':390,'height':844});await shot('restore_dialog_mobile_light');await page.get_by_test_id('restore-owner-password').fill('wrong');await page.get_by_test_id('restore-confirmation').fill('RESTORE MCCOY');await page.get_by_test_id('backup-restore').click();await expect(page.get_by_test_id('restore-error')).to_contain_text('incorrect')
                await page.get_by_test_id('restore-owner-password').fill('trucker123');await page.get_by_test_id('backup-restore').click();await expect(page.get_by_test_id('login-form')).to_be_visible();await ui_login();diagnostics['ui_restore_success']=True
                await page.set_viewport_size({'width':1920,'height':800})
            await step('backup download preview cancel errors confirmed replace logout login',backup)
            async def mobile_modal():
                await page.goto(BASE+'/telemetry');await expect(page.get_by_test_id('telemetry-page')).to_be_visible()
                await page.get_by_test_id('telemetry-driver_id').select_option(str(ids['drivers']));await page.get_by_test_id('telemetry-truck_id').select_option(str(ids['trucks']))
                await page.get_by_test_id('telemetry-enabled').check();await page.get_by_test_id('telemetry-save-settings').click();await page.wait_for_timeout(300)
                await post('/telemetry/ingest',api.sample(1,session='mobile_ui',job={'sourceCity':'TEST_UI_MOBILE','destinationCity':'TEST_UI_MOBILE_END','income':100},attached=True));await page.get_by_test_id('telemetry-refresh').click();await page.wait_for_timeout(300)
                e=next(x for x in await get('/telemetry/events') if x['payload'].get('origin')=='TEST_UI_MOBILE')
                await page.set_viewport_size({'width':390,'height':844});await page.get_by_test_id(f"telemetry-review-{e['id']}").click();await shot('telemetry_review_mobile_light');await page.get_by_test_id('telemetry-review-cancel').click();await expect(page.get_by_test_id('telemetry-review-dialog')).to_have_count(0)
                await page.set_viewport_size({'width':1920,'height':800})
            await step('telemetry mobile review modal scrolling cancel',mobile_modal)
            async def deletecrud():
                for table in ['inspections','loads','fuel','expenses','income','drivers','trucks']:
                    await page.goto(BASE+'/'+table);await expect(page.get_by_test_id(table+'-page')).to_be_visible();rid=ids[table]
                    await page.get_by_test_id(f'delete-{table}-{rid}').click();await page.get_by_test_id('confirm-delete-cancel').click();await expect(page.get_by_test_id(f'{table}-row-{rid}')).to_be_visible()
                    await page.get_by_test_id(f'delete-{table}-{rid}').click();await page.get_by_test_id('confirm-delete-btn').click();await expect(page.get_by_test_id(f'{table}-row-{rid}')).to_have_count(0)
                    assert not any(x['id']==rid for x in await get('/'+table))
                await page.goto(BASE+'/expenses');await page.get_by_test_id('category-delete-'+str(ids['categories'])).click();await expect(page.get_by_test_id('category-'+str(ids['categories']))).to_have_count(0)
                await page.goto(BASE+'/test-data');await page.get_by_test_id('clear-test-data-btn').click();await expect(page.get_by_test_id('test-count-loads')).to_have_text('0');assert len(await get('/income'))>=1
            await step('all CRUD delete cancel confirm category remove sample preserves manual',deletecrud)
            error_text=await page.evaluate("""() => {const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));return errorElements.map(el => el.textContent).join(", ");}""")
            diagnostics['final_visible_errors']=error_text;print('Found error message: '+error_text if error_text else 'No error messages found on the page')
        finally:
            await browser.close()
            s=api.login();api.request(s,'POST','/backup/restore',json={**api.body(original),'confirm':'RESTORE MCCOY','owner_password':'trucker123'})
            s=api.login();final=api.decrypt(api.archive(s));assert api.normalize(final)==api.normalize(api.decrypt(original))
            diagnostics['cleanup_original_restored']=True;diagnostics['retained_accounts']=[];save()
    print('UI RESULTS',sum(x['status']=='PASS' for x in results),'passed',sum(x['status']=='FAIL' for x in results),'failed',flush=True)

if __name__=='__main__':asyncio.run(main())