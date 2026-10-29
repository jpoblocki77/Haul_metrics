# Independent public API/browser regression for decoded and restored payload search.
import asyncio,json,os,re,uuid
from pathlib import Path
from playwright.async_api import async_playwright,expect
import test_full_regression as api

OUT=Path('/app/test_reports/browser_iter7');BASE=os.environ['REACT_APP_BACKEND_URL'].rstrip('/')
text=Path('/app/memory/test_credentials.md').read_text();USER=re.search(r'username: (\S+)',text)[1];PASSWORD=re.search(r'password: (\S+)',text)[1]

async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    s=api.login(USER,PASSWORD);blob=api.archive(s);original=api.decrypt(blob);result={}
    safety=OUT/'search_safety.mccoy';safety.write_bytes(blob);safety.chmod(0o600)
    try:
        prefix='TEST_encoding_'+uuid.uuid4().hex[:6]
        d=api.request(s,'POST','/drivers',json={'name':prefix}).json()
        t=api.request(s,'POST','/trucks',json={'truck_number':prefix,'tank_gallons':100}).json()
        api.request(s,'PUT','/telemetry/settings',json={'driver_id':d['id'],'truck_id':t['id'],'enabled':True,'server_url':'http://127.0.0.1:25555/api/ets2/telemetry'})
        names=['Montréal','TEST_literal_\\','TEST_plain_token','TEST_plainXtoken','TEST_literal_%']
        for n,name in enumerate(names):api.request(s,'POST','/telemetry/ingest',json=api.sample(n,session=prefix,job={'sourceCity':name,'destinationCity':'TEST_end','income':1},attached=True))
        rows=api.events(s);result['visible_origins']=[r['payload']['origin'] for r in rows]
        populated=api.archive(s);decoded=api.decrypt(populated)
        unicode_row=next(r for r in decoded['tables']['telemetry_events'] if json.loads(r['payload'])['origin']=='Montréal')
        assert 'Montr\\u00e9al' in unicode_row['payload'],unicode_row
        result['ascii_escaped_payload_verified']=True
        def check_queries(session):
            queries={q:api.request(session,'GET','/telemetry/manage-events',params={'q':q}).json() for q in ['Montréal','MONTRÉAL','Montr','\\','plain_token','%','TEST_absent_query']}
            expected={'Montréal':'Montréal','MONTRÉAL':'Montréal','Montr':'Montréal','\\':'TEST_literal_\\','plain_token':'TEST_plain_token','%':'TEST_literal_%'}
            for q,origin in expected.items():
                row=next(r for r in rows if r['payload']['origin']==origin)
                data=queries[q]
                assert data['total']==1 and [r['id'] for r in data['items']]==[row['id']],(q,data)
                assert data['items'][0]['payload']['origin']==origin
                assert (data['offset'],data['limit'])==(0,100)
            assert queries['TEST_absent_query']=={'items':[],'total':0,'offset':0,'limit':100}
            return queries
        result['queries']=check_queries(s)
        print('PASS API Unicode casefold and exact percent/underscore/backslash matches',flush=True)
        api.request(s,'POST','/backup/restore',json={**api.body(populated),'confirm':'RESTORE MCCOY','owner_password':PASSWORD})
        s=api.login(USER,PASSWORD)
        result['restored_queries']=check_queries(s)
        result['restored_escaped_payload_search_passed']=True
        print('PASS restored ASCII-escaped payload search',flush=True)
        async with async_playwright() as p:
            browser=await p.chromium.launch(args=['--no-sandbox'])
            page=await browser.new_page()
            await page.set_viewport_size({"width": 1920, "height": 800})
            try:
                await page.goto(BASE+'/login')
                await page.get_by_test_id('login-username-input').fill(USER);await page.get_by_test_id('login-password-input').fill(PASSWORD)
                await page.get_by_test_id('login-submit-btn').click(force=True);await expect(page.get_by_test_id('dashboard-page')).to_be_visible()
                await page.get_by_test_id('open-delete-entries').click(force=True)
                await expect(page.get_by_test_id('delete-entries-dialog')).to_be_visible();await page.wait_for_timeout(200)
                await page.get_by_test_id('delete-entries-type').select_option('telemetry/events',force=True);await page.wait_for_timeout(200)
                await page.get_by_test_id('delete-entries-search').fill('Montr')
                await expect(page.get_by_test_id('delete-entries-count')).to_contain_text('1 entries')
                await expect(page.get_by_test_id('manage-entry-telemetry-events-'+str(next(r['id'] for r in rows if r['payload']['origin']=='Montréal')))).to_contain_text('Montréal')
                await page.get_by_test_id('delete-entries-search').fill('Montréal')
                await expect(page.get_by_test_id('delete-entries-count')).to_contain_text('1 entries')
                await expect(page.get_by_test_id('manage-entry-telemetry-events-'+str(unicode_row['id']))).to_contain_text('Montréal')
                await page.get_by_test_id('delete-entries-search').fill('MONTRÉAL')
                await expect(page.get_by_test_id('delete-entries-count')).to_contain_text('1 entries')
                await expect(page.get_by_test_id('manage-entry-telemetry-events-'+str(unicode_row['id']))).to_contain_text('Montréal')
                await page.screenshot(path=str(OUT/'unicode_search_fixed_1920.jpg'),quality=40,full_page=False)
                await page.get_by_test_id('delete-entries-search').fill('\\')
                await expect(page.get_by_test_id('delete-entries-count')).to_contain_text('1 entries')
                await expect(page.get_by_test_id('manage-entry-telemetry-events-'+str(unicode_row['id']))).to_have_count(0)
                for q,origin in [('\\','TEST_literal_\\'),('plain_token','TEST_plain_token'),('%','TEST_literal_%')]:
                    await page.get_by_test_id('delete-entries-search').fill(q)
                    await expect(page.get_by_test_id('delete-entries-count')).to_contain_text('1 entries')
                    row=next(r for r in rows if r['payload']['origin']==origin)
                    await expect(page.get_by_test_id('manage-entry-telemetry-events-'+str(row['id']))).to_contain_text(origin)
                await page.get_by_test_id('delete-entries-search').fill('TEST_absent_query')
                await expect(page.get_by_test_id('delete-entries-empty')).to_be_visible()
                await expect(page.get_by_test_id('delete-entries-count')).to_have_text('0 entries · all dates')
                error_text=await page.evaluate("""() => {
                    const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
                    return errorElements.map(el => el.textContent).join(", ");
                }""")
                assert not error_text,error_text
                result['browser_search_passed']=True
                print('PASS browser restored Unicode/casefold, literal searches and empty state; no page errors',flush=True)
            except Exception as exc:
                result['browser_failure']=str(exc)
                print('FAIL browser search: '+str(exc),flush=True)
                raise
            finally:await browser.close()
    finally:
        s=api.login(USER,PASSWORD);api.request(s,'POST','/backup/restore',json={**api.body(blob),'confirm':'RESTORE MCCOY','owner_password':PASSWORD})
        s=api.login(USER,PASSWORD);assert api.normalize(api.decrypt(api.archive(s)))==api.normalize(original)
        result['original_restored']=True
        (OUT/'search_encoding_results.json').write_text(json.dumps(result,indent=2))

if __name__=='__main__':asyncio.run(main())