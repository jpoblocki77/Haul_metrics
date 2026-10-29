# Targeted visual/PDF, long-name layouts, reload auth and mobile review verification with safeguarded fixtures.
import asyncio, json, os
from pathlib import Path
from playwright.async_api import async_playwright, expect
from pypdf import PdfReader
import test_full_regression as api

BASE=os.environ['REACT_APP_BACKEND_URL'].rstrip('/')
OUT=Path('/app/test_reports/browser_iter5_focused');OUT.mkdir(exist_ok=True)
results=[]; diagnostics={}; failures=[]

async def main():
    s=api.login();blob=api.archive(s);original=api.decrypt(blob);(OUT/'safety.mccoy').write_bytes(blob)
    api.request(s,'POST','/test-data')
    driver=api.request(s,'POST','/drivers',json={'name':'TEST_'+('VeryLongName'*20),'notes':'TEST_'+('LongNote'*25)}).json()
    truck=api.request(s,'POST','/trucks',json={'truck_number':'TEST_focused','tank_gallons':100}).json()
    async with async_playwright() as p:
        browser=await p.chromium.launch(args=['--no-sandbox'])
        page=await browser.new_page(viewport={'width':1920,'height':800})
        page.set_default_timeout(12000)
        page.on('response',lambda r:failures.append({'url':r.url,'status':r.status}) if '/api/' in r.url and r.status>=400 else None)
        page.on('pageerror',lambda e:failures.append({'pageerror':str(e)}))
        async def shot(name):await page.screenshot(path=str(OUT/(name+'.jpg')),quality=40,full_page=False)
        async def step(name,fn):
            try:await fn();results.append({'name':name,'status':'PASS'});print('PASS',name,flush=True)
            except Exception as e:results.append({'name':name,'status':'FAIL','error':repr(e)});print('FAIL',name,repr(e),flush=True)
        async def goto(path,tid):
            await page.goto(BASE+path);await expect(page.get_by_test_id(tid)).to_be_visible()
        async def theme(value):
            if await page.evaluate('document.documentElement.dataset.theme')!=value:
                if page.viewport_size['width']==390:
                    await page.get_by_test_id('mobile-menu-btn').click(force=True);await page.get_by_test_id('mobile-theme-toggle').click(force=True);await page.get_by_test_id('mobile-menu-close').click(force=True)
                else:await page.get_by_test_id('theme-toggle').click(force=True)
        async def nooverflow(label):
            d=await page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})');diagnostics[label]=d;assert d['width']==d['scroll'],d
        try:
            await page.goto(BASE+'/login');await page.get_by_test_id('login-username-input').fill('owner');await page.get_by_test_id('login-password-input').fill('trucker123');await page.get_by_test_id('login-submit-btn').click(force=True);await expect(page.get_by_test_id('dashboard-page')).to_be_visible();await page.wait_for_timeout(400)
            async def charts():
                await goto('/report','report-page');await page.get_by_test_id('report-month').fill('2026-07');await expect(page.get_by_test_id('report-income')).not_to_have_text('$0.00')
                await expect(page.locator('.report-chart svg text').first).to_be_visible()
                for size in [{'width':1920,'height':800},{'width':390,'height':844}]:
                    await page.set_viewport_size(size)
                    for mode in ['dark','light']:
                        await theme(mode);await page.wait_for_timeout(500)
                        geometry=await page.locator('.report-chart').evaluate_all("els=>els.map(e=>({ticks:[...e.querySelectorAll('svg text')].map(t=>t.textContent),paths:[...e.querySelectorAll('path')].map(p=>({w:p.getBoundingClientRect().width,h:p.getBoundingClientRect().height})),width:e.querySelector('.recharts-wrapper').getBoundingClientRect().width}))")
                        diagnostics['chart_'+str(size['width'])+'_'+mode]=geometry
                        assert all(len(x['ticks'])>0 and x['width']>0 and any(y['w']>0 and y['h']>0 for y in x['paths']) for x in geometry),geometry
                        await page.get_by_test_id('report-income-expense-chart').scroll_into_view_if_needed();await shot('report_cash_'+str(size['width'])+'_'+mode)
                        await page.get_by_test_id('report-mpg-chart').scroll_into_view_if_needed();await shot('report_mpg_'+str(size['width'])+'_'+mode)
                        await nooverflow('report_'+str(size['width'])+'_'+mode)
                await page.set_viewport_size({'width':1920,'height':800});await page.pdf(path=str(OUT/'populated_report.pdf'),format='Letter',print_background=True,prefer_css_page_size=True)
                reader=PdfReader(OUT/'populated_report.pdf');diagnostics['pdf_pages']=len(reader.pages);diagnostics['pdf_text']=reader.pages[0].extract_text();assert len(reader.pages)==1
            await step('populated charts visible axes bars line dark light desktop mobile and one-page PDF',charts)
            async def layouts():
                for size in [{'width':1920,'height':800},{'width':390,'height':844}]:
                    await page.set_viewport_size(size)
                    for mode in ['dark','light']:
                        await goto('/leaderboard','leaderboard-page');await theme(mode);await page.get_by_test_id('leaderboard-month').fill('2026-07');await expect(page.get_by_test_id('top-driver-name')).to_be_visible();await page.wait_for_timeout(400)
                        diagnostics['winner_name_'+str(size['width'])+'_'+mode]=await page.get_by_test_id('top-driver-name').evaluate('e=>({text:e.textContent,width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height})')
                        await nooverflow('leaderboard_'+str(size['width'])+'_'+mode);await shot('leaderboard_'+str(size['width'])+'_'+mode)
                        await goto('/drivers/'+str(driver['id']),'driver-profile-page');await page.wait_for_timeout(500);await nooverflow('long_driver_'+str(size['width'])+'_'+mode);await shot('long_driver_'+str(size['width'])+'_'+mode)
                await page.set_viewport_size({'width':1920,'height':800})
            await step('leaderboard and worst-case profile layouts both sizes themes no overflow',layouts)
            async def reloads():
                failures.clear()
                for i in range(12):
                    await goto('/','dashboard-page');await page.wait_for_timeout(250)
                assert not any(x.get('status')==401 for x in failures),failures
            await step('twelve full document reloads preserve login',reloads)
            async def mobile_review():
                await goto('/telemetry','telemetry-page');await expect(page.get_by_test_id('telemetry-driver_id').locator('option',has_text=driver['name'])).to_have_count(1)
                await page.wait_for_timeout(500)
                await page.get_by_test_id('telemetry-driver_id').select_option(str(driver['id']),force=True);await page.get_by_test_id('telemetry-truck_id').select_option(str(truck['id']),force=True);await page.get_by_test_id('telemetry-enabled').check(force=True)
                async with page.expect_response(lambda r:'/telemetry/settings' in r.url and r.request.method=='PUT') as pending:await page.get_by_test_id('telemetry-save-settings').click(force=True)
                assert (await pending.value).status==200
                await page.wait_for_timeout(500)
                response=await page.request.post(BASE+'/api/telemetry/ingest',data=api.sample(1,session='final_mobile',job={'sourceCity':'TEST_FINAL_MOBILE','destinationCity':'TEST_FINAL_END','income':100},attached=True));assert response.ok;assert (await response.json())['accepted']
                r=await page.request.get(BASE+'/api/telemetry/events');event=next(x for x in await r.json() if x['payload'].get('origin')=='TEST_FINAL_MOBILE')
                await page.get_by_test_id('telemetry-refresh').click(force=True);await expect(page.get_by_test_id('telemetry-review-'+str(event['id']))).to_be_visible()
                await page.set_viewport_size({'width':390,'height':844});await page.get_by_test_id('telemetry-review-'+str(event['id'])).click(force=True);await expect(page.get_by_test_id('telemetry-review-dialog')).to_be_visible();await shot('mobile_review');await page.get_by_test_id('telemetry-review-cancel').click(force=True);await expect(page.get_by_test_id('telemetry-review-dialog')).to_have_count(0)
            await step('mobile telemetry review opens scrolls cancels after confirmed settings save',mobile_review)
            async def sample_remove():
                await page.set_viewport_size({'width':1920,'height':800});await goto('/test-data','test-data-page')
                await expect(page.get_by_test_id('test-count-loads')).to_have_text('60')
                await expect(page.get_by_test_id('clear-test-data-btn')).to_be_enabled()
                async with page.expect_response(lambda r:'/api/test-data' in r.url and r.request.method=='DELETE') as response:
                    await page.get_by_test_id('clear-test-data-btn').click(force=True)
                r=await response.value;assert r.status==200;assert (await r.json())['removed']['loads']==60
                await expect(page.get_by_test_id('test-count-loads')).to_have_text('0')
                assert any(x['id']==driver['id'] for x in api.request(s,'GET','/drivers').json())
            await step('sample removal confirmed API and UI counts preserve manual driver',sample_remove)
            diagnostics['visible_errors']=await page.evaluate("""() => {const errorElements=Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));return errorElements.map(el=>el.textContent).join(', ');} """)
        finally:
            await browser.close();s=api.login();api.request(s,'POST','/backup/restore',json={**api.body(blob),'confirm':'RESTORE MCCOY','owner_password':'trucker123'});s=api.login();assert api.normalize(api.decrypt(api.archive(s)))==api.normalize(original)
            diagnostics['original_restored']=True
            (OUT/'results.json').write_text(json.dumps({'results':results,'diagnostics':diagnostics,'failed_requests':failures},indent=2))

if __name__=='__main__':asyncio.run(main())