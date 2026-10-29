# Independent mobile review/cancel regression; real API candidate seeded before browser navigation.
import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright, expect
import test_full_regression as api

async def main():
    s=api.login();before_loads=api.request(s,'GET','/loads').json();d=api.request(s,'POST','/drivers',json={'name':'TEST_mobile_review'}).json()
    t=api.request(s,'POST','/trucks',json={'truck_number':'TEST_mobile_review','tank_gallons':100}).json()
    api.request(s,'PUT','/telemetry/settings',json={'driver_id':d['id'],'truck_id':t['id'],'enabled':True,'server_url':'http://127.0.0.1:25555/api/ets2/telemetry'})
    assert api.request(s,'POST','/telemetry/ingest',json=api.sample(1,session='mobile_verified',job={'sourceCity':'TEST_mobile_verified','destinationCity':'TEST_end','income':100},attached=True)).json()['accepted']
    event=next(x for x in api.events(s) if x['payload'].get('origin')=='TEST_mobile_verified')
    out=Path('/app/test_reports/browser_iter8_mobile_review');out.mkdir(exist_ok=True);results=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(args=['--no-sandbox'])
        context=await browser.new_context(viewport={'width':390,'height':844});page=await context.new_page()
        try:
            await page.goto(api.BASE+'/login');await page.get_by_test_id('login-username-input').fill('owner');await page.get_by_test_id('login-password-input').fill('trucker123');await page.get_by_test_id('login-submit-btn').click(force=True);await expect(page.get_by_test_id('dashboard-page')).to_be_visible()
            await page.goto(api.BASE+'/telemetry');await expect(page.get_by_test_id('telemetry-page')).to_be_visible()
            for mode in ['dark','light']:
                try:
                    if await page.evaluate('document.documentElement.dataset.theme')!=mode:
                        await page.get_by_test_id('mobile-menu-btn').click(force=True);await page.get_by_test_id('mobile-theme-toggle').click(force=True);await page.get_by_test_id('mobile-menu-close').click(force=True);await page.wait_for_timeout(250)
                    await page.get_by_test_id('telemetry-review-'+str(event['id'])).click(force=True);await expect(page.get_by_test_id('telemetry-review-dialog')).to_be_visible()
                    box=await page.get_by_test_id('telemetry-review-dialog').bounding_box();assert box['x']>=0 and box['x']+box['width']<=390
                    await page.get_by_test_id('telemetry-review-delivered_date').fill('2026-10-29')
                    await page.get_by_test_id('telemetry-review-status').select_option('On Time',force=True);await page.wait_for_timeout(200)
                    await page.get_by_test_id('telemetry-review-cancel').scroll_into_view_if_needed()
                    await page.screenshot(path=str(out/(mode+'.jpg')),quality=40,full_page=False)
                    await page.get_by_test_id('telemetry-review-cancel').click(force=True);await expect(page.get_by_test_id('telemetry-review-dialog')).to_have_count(0);await page.wait_for_timeout(250)
                    assert next(x for x in api.events(s) if x['id']==event['id'])['status']=='pending' and api.request(s,'GET','/loads').json()==before_loads
                    results.append({'theme':mode,'status':'PASS'});print('PASS mobile telemetry review usable and cancel safe',mode)
                except Exception as e:results.append({'theme':mode,'status':'FAIL','error':str(e)});print('FAIL',mode,str(e))
        finally:
            await browser.close();(out/'results.json').write_text(json.dumps(results,indent=2))

if __name__=='__main__':asyncio.run(main())