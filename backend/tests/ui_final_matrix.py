# Follow-up public-preview UI: branding, Today, all mobile themes, visible chart geometry, dispatcher, delete.
import asyncio, json, os, sys, uuid
from pathlib import Path
from playwright.async_api import async_playwright, expect
import test_full_regression as api

BASE=os.environ['REACT_APP_BACKEND_URL'].rstrip('/')
OUT=Path('/app/test_reports/browser_iter8_matrix');OUT.mkdir(exist_ok=True)
results=[];diagnostics={};errors=[]

async def main():
    s=api.login();blob=api.archive(s);original=api.decrypt(blob)
    (OUT/'safety.mccoy').write_bytes(blob)
    name='test_latest_'+uuid.uuid4().hex[:8]
    u=api.request(s,'POST','/users',json={'username':name,'password':'secret123'}).json()
    api.request(s,'POST','/test-data')
    async with async_playwright() as p:
        browser=await p.chromium.launch(args=['--no-sandbox'])
        context=await browser.new_context(viewport={'width':1920,'height':800})
        page=await context.new_page();page.set_default_timeout(12000)
        page.on('pageerror',lambda e:errors.append(str(e)))
        async def step(name,fn):
            try:await fn();results.append({'name':name,'status':'PASS'});print('PASS',name,flush=True)
            except Exception as e:results.append({'name':name,'status':'FAIL','error':str(e)});print('FAIL',name,str(e),flush=True)
        async def login(username='owner',password='trucker123'):
            await page.goto(BASE+'/login');await page.get_by_test_id('login-username-input').fill(username);await page.get_by_test_id('login-password-input').fill(password)
            await page.get_by_test_id('login-submit-btn').click(force=True);await expect(page.get_by_test_id('dashboard-page')).to_be_visible();await page.wait_for_timeout(400)
        async def nav(slug):
            mobile=page.viewport_size['width']==390
            if mobile:await page.get_by_test_id('mobile-menu-btn').click(force=True)
            await page.get_by_test_id('nav-'+slug).last.click(force=True);await page.wait_for_timeout(500)
        async def shot(name):await page.screenshot(path=str(OUT/(name+'.jpg')),quality=40,full_page=False)
        async def overflow(name):
            d=await page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})');diagnostics[name]=d
            if d['scroll']>d['width']+1:results.append({'name':'overflow '+name,'status':'FAIL','error':str(d)})
        try:
            await login()
            async def branding():
                await nav('company')
                await page.get_by_test_id('company-name-input').fill('  TEST Azure Fleet  ')
                for k,v in [('primary','#228844'),('accent','#8844aa'),('dark-background','#101010'),('light-background','#eeeeee')]:
                    tid='company-'+k+('-color' if k in ['primary','accent'] else '')
                    await page.get_by_test_id(tid).fill(v)
                await page.get_by_test_id('company-save').click(force=True)
                await expect(page.get_by_test_id('company-name-input')).to_have_value('TEST Azure Fleet')
                assert await page.title()=='TEST Azure Fleet | Fleet Manager'
                assert await page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--brand-primary').trim()")=='#228844'
                await shot('company_desktop_dark');await page.reload();await expect(page.get_by_test_id('company-name-input')).to_have_value('TEST Azure Fleet')
                await nav('report');await page.get_by_test_id('report-month').fill('2026-07');await expect(page.get_by_test_id('report-income')).to_be_visible()
                assert 'TEST Azure Fleet' in await page.get_by_test_id('report-sheet').inner_text()
                await page.get_by_test_id('logout-btn').first.click(force=True);await expect(page.get_by_test_id('login-form')).to_be_visible();assert 'TEST Azure Fleet' in await page.get_by_test_id('login-form').locator('..').inner_text()
                await login();await nav('company');await page.get_by_test_id('company-dark-background').fill('#ffffff');await page.get_by_test_id('company-save').click(force=True);await expect(page.get_by_test_id('company-settings-error')).to_contain_text('darker')
                await page.get_by_test_id('company-reset-colors').click(force=True);assert await page.get_by_test_id('company-primary-color').input_value()=='#3b82f6'
                await page.get_by_test_id('company-name-input').fill('TEST_'+('X'*55));await page.get_by_test_id('company-save').click(force=True);await page.wait_for_timeout(400)
                await page.set_viewport_size({'width':390,'height':844});await overflow('company_long_name_mobile');await shot('company_mobile_dark')
                await page.get_by_test_id('mobile-menu-btn').click(force=True);await page.get_by_test_id('mobile-theme-toggle').click(force=True);await page.get_by_test_id('mobile-menu-close').click(force=True);await shot('company_mobile_light')
                await page.set_viewport_size({'width':1920,'height':800})
            await step('company save colors validation default reload header report login long mobile',branding)
            async def today():
                await nav('dashboard');await page.get_by_test_id('range-today').click(force=True)
                day=await page.evaluate("new Date(Date.now()-new Date().getTimezoneOffset()*60000).toISOString().slice(0,10)")
                assert await page.get_by_test_id('range-start').input_value()==day and await page.get_by_test_id('range-end').input_value()==day
                st=api.request(s,'GET','/stats/dashboard',params={'start':day,'end':day}).json();await expect(page.get_by_test_id('kpi-income-value')).to_have_text(f"${st['income']:,.2f}")
                for slug in ['income','expenses','fuel','loads','inspections']:
                    await nav(slug);assert await page.get_by_test_id('range-start').input_value()==day
                    async with page.expect_download() as pending:await page.get_by_test_id('export-'+slug+'-btn').click(force=True)
                    download=await pending.value;await download.save_as(str(OUT/(slug+'_today.csv')))
                await nav('drivers');await page.locator('[data-testid^="driver-profile-link-"]').first.click(force=True);await expect(page.get_by_test_id('driver-profile-page')).to_be_visible();assert await page.get_by_test_id('range-start').input_value()==day
                await page.get_by_test_id('range-all').click(force=True);await expect(page.get_by_test_id('profile-loads-total-value')).not_to_have_text('0')
            await step('Today local date dashboard lists CSV profile shared range',today)
            async def chart():
                await nav('report');await page.get_by_test_id('report-month').fill('2026-07');await page.wait_for_timeout(1000)
                d=await page.locator('.report-chart').evaluate_all('''els=>els.map(e=>({svg:e.querySelectorAll('svg.recharts-surface').length,paths:[...e.querySelectorAll('svg.recharts-surface path')].map(p=>({box:{w:p.getBoundingClientRect().width,h:p.getBoundingClientRect().height},fill:getComputedStyle(p).fill,stroke:getComputedStyle(p).stroke})),ticks:e.querySelectorAll('.recharts-cartesian-axis-tick text').length,wrapper:[...e.querySelectorAll('.recharts-wrapper')].map(w=>({w:w.getBoundingClientRect().width,h:w.getBoundingClientRect().height})),root:e.outerHTML.slice(0,500)}))''')
                diagnostics['report_visible_geometry']=d;await shot('report_visible_geometry')
                assert all(x['svg']>0 and any(p['box']['w']>0 and p['box']['h']>0 for p in x['paths']) for x in d),d
                assert all(x['ticks']>0 for x in d),'Report axes have no text tick labels'
            await step('report charts nonzero visible path geometry and axis labels',chart)
            async def matrix():
                for size in [{'width':1920,'height':800},{'width':390,'height':844}]:
                    await page.set_viewport_size(size)
                    for theme in ['dark','light']:
                        current=await page.evaluate('document.documentElement.dataset.theme')
                        if current!=theme:
                            if size['width']==390:
                                await page.get_by_test_id('mobile-menu-btn').click(force=True);await page.get_by_test_id('mobile-theme-toggle').click(force=True);await page.get_by_test_id('mobile-menu-close').click(force=True)
                            else:await page.get_by_test_id('theme-toggle').click(force=True)
                        for slug in ['dashboard','income','expenses','fuel','trucks','loads','telemetry','drivers','leaderboard','inspections','users','create-user','company','report','backup','test-data']:
                            await nav(slug);await overflow(slug+'_'+str(size['width'])+'_'+theme)
                            if slug in ['report','leaderboard']:
                                await page.get_by_test_id(slug+'-month').fill('2026-07');await page.wait_for_timeout(400);await shot(slug+'_'+str(size['width'])+'_'+theme)
                        await page.reload();await expect(page.get_by_test_id('test-data-page')).to_be_visible();assert await page.evaluate('document.documentElement.dataset.theme')==theme
            await step('all sixteen routes desktop mobile dark light persistence sidebar scroll',matrix)
            async def dispatch():
                await page.set_viewport_size({'width':1920,'height':800});await page.get_by_test_id('logout-btn').first.click(force=True);await expect(page.get_by_test_id('login-form')).to_be_visible();await login(name,'secret123')
                for slug in ['users','create-user','company','backup','test-data']:assert await page.get_by_test_id('nav-'+slug).count()==0
                for route in ['/company','/users/new','/backup']:
                    await page.goto(BASE+route);await expect(page.get_by_test_id('dashboard-page')).to_be_visible()
                await nav('income');assert await page.locator('[data-testid^="delete-income-"]').count()==0
                await page.get_by_test_id('logout-btn').first.click(force=True);await expect(page.get_by_test_id('login-form')).to_be_visible();await login()
            await step('dispatcher signs in hides owner links direct guards no deletes',dispatch)
            async def deletion():
                await nav('income');await page.get_by_test_id('add-income-btn').click(force=True)
                for field,val in [('date','2026-10-28'),('source','TEST_UI_DELETE'),('amount','10')]:await page.get_by_test_id('input-'+field).fill(val)
                async with page.expect_response(lambda r:'/api/income' in r.url and r.request.method=='POST') as pending:await page.get_by_test_id('income-save-btn').click(force=True)
                record=await (await pending.value).json();rid=record['id'];await expect(page.get_by_test_id('income-dialog')).to_have_count(0);await expect(page.get_by_test_id(f'income-row-{rid}')).to_be_visible();await page.wait_for_timeout(400);await page.get_by_test_id(f'delete-income-{rid}').click(force=True);await page.get_by_test_id('confirm-delete-cancel').click(force=True);await expect(page.get_by_test_id(f'income-row-{rid}')).to_be_visible();await page.wait_for_timeout(300)
                await page.get_by_test_id(f'delete-income-{rid}').click(force=True);await page.get_by_test_id('confirm-delete-btn').click(force=True);await expect(page.get_by_test_id(f'income-row-{rid}')).to_have_count(0)
            await step('delete confirm cancel persisted removal',deletion)
            diagnostics['error_text']=await page.evaluate("""() => {const errorElements=Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));return errorElements.map(el=>el.textContent).join(', ');} """)
        finally:
            await browser.close();s=api.login();api.request(s,'POST','/backup/restore',json={**api.body(blob),'confirm':'RESTORE MCCOY','owner_password':'trucker123'});s=api.login()
            assert api.normalize(api.decrypt(api.archive(s)))==api.normalize(original)
            diagnostics['cleanup_original_restored']=True
            (OUT/'ui_results.json').write_text(json.dumps({'results':results,'diagnostics':diagnostics,'page_errors':errors},indent=2))
            print('RESULTS',sum(x['status']=='PASS' for x in results),'passed',sum(x['status']=='FAIL' for x in results),'failed',flush=True)

if __name__=='__main__':asyncio.run(main())