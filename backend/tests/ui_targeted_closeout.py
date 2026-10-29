# Independent public-browser closeout cases; no product mocks and encrypted restoration in finally.
import asyncio,json,os,re,uuid
from pathlib import Path
from playwright.async_api import async_playwright,expect
import test_full_regression as api

BASE=os.environ['REACT_APP_BACKEND_URL'].rstrip('/')
OUT=Path('/app/test_reports/browser_iter6');OUT.mkdir(exist_ok=True)
credentials=Path('/app/memory/test_credentials.md').read_text()
OWNER=re.search(r'username: (\S+)',credentials)[1];PASSWORD=re.search(r'password: (\S+)',credentials)[1]
DISPATCH,DPASS=re.search(r'Extra user created via Users page: (\S+) / (\S+)',credentials).groups()
results=[];diagnostics={};errors=[]

async def main():
    s=api.login(OWNER,PASSWORD);blob=api.archive(s);original=api.decrypt(blob)
    safety=OUT/'safety.mccoy';safety.write_bytes(blob);safety.chmod(0o600)
    prefix='TEST_close_'+uuid.uuid4().hex[:6]
    def create(table,payload):return api.request(s,'POST','/'+table,json=payload).json()
    def mapping(label):
        d=create('drivers',{'name':label});t=create('trucks',{'truck_number':prefix+'_'+str(d['id']),'tank_gallons':100})
        return {'driver_id':d['id'],'truck_id':t['id']}
    def configure(common):api.request(s,'PUT','/telemetry/settings',json={**common,'enabled':True,'server_url':'http://127.0.0.1:25555/api/ets2/telemetry'})
    async with async_playwright() as p:
        browser=await p.chromium.launch(args=['--no-sandbox'])
        async def fresh(size=1920,mode='dark',dispatcher=False):
            context=await browser.new_context(viewport={'width':size,'height':844 if size==390 else 800})
            await context.add_init_script(f"localStorage.setItem('mccoy-theme','{mode}')")
            page=await context.new_page();page.set_default_timeout(15000)
            page.on('pageerror',lambda e:errors.append(str(e)))
            await page.goto(BASE+'/login')
            await page.get_by_test_id('login-username-input').fill(DISPATCH if dispatcher else OWNER)
            await page.get_by_test_id('login-password-input').fill(DPASS if dispatcher else PASSWORD)
            await page.get_by_test_id('login-submit-btn').click(force=True)
            await expect(page.get_by_test_id('dashboard-page')).to_be_visible()
            assert await page.evaluate('document.documentElement.dataset.theme')==mode
            return context,page
        async def shot(page,name):await page.screenshot(path=str(OUT/(name+'.jpg')),quality=40,full_page=False)
        async def step(name,fn):
            try:
                await fn();results.append({'name':name,'status':'PASS'});print('PASS',name,flush=True)
            except Exception as e:
                results.append({'name':name,'status':'FAIL','error':repr(e)});print('FAIL',name,repr(e),flush=True)
        async def delete(page,tid,keep):
            await page.get_by_test_id(tid).click(force=True)
            await expect(page.get_by_test_id(tid+'-dialog')).to_be_visible()
            await page.get_by_test_id(tid+'-cancel').click(force=True)
            await expect(page.get_by_test_id(tid+'-dialog')).to_have_count(0)
            await page.wait_for_timeout(250)
            assert keep()
            await expect(page.get_by_test_id(tid)).to_be_visible()
            await page.get_by_test_id(tid).click(force=True)
            await expect(page.get_by_test_id(tid+'-dialog')).to_be_visible()
            await page.get_by_test_id(tid+'-confirm').click(force=True)
            await expect(page.get_by_test_id(tid+'-dialog')).to_have_count(0)
            await page.wait_for_timeout(250)
        async def global_open(page,table):
            await page.get_by_test_id('open-delete-entries').click(force=True)
            await expect(page.get_by_test_id('delete-entries-dialog')).to_be_visible()
            await page.wait_for_timeout(200)
            await page.get_by_test_id('delete-entries-type').select_option(table,force=True)
            await page.wait_for_timeout(200)
            await expect(page.get_by_test_id('delete-entries-loading')).to_have_count(0)
        try:
            for label,month in [('Sarah Kent','2010-01'),('Winner'+'UnbrokenName'*12,'2010-02')]:
                common=mapping(label)
                create('loads',{**common,'origin':prefix,'destination':'TEST_end','pay':777,'delivered_date':month+'-02','status':'On Time'})
                for size in [1920,390]:
                    for mode in ['dark','light']:
                        async def winner(label=label,month=month,size=size,mode=mode):
                            context,page=await fresh(size,mode)
                            try:
                                await page.goto(BASE+'/leaderboard')
                                await page.get_by_test_id('leaderboard-month').fill(month)
                                await expect(page.get_by_test_id('top-driver-name')).to_have_text(label)
                                await page.get_by_test_id('top-driver-card').scroll_into_view_if_needed()
                                await page.wait_for_timeout(350)
                                geom=await page.get_by_test_id('top-driver-name').evaluate('e=>{const r=e.getBoundingClientRect(),s=e.nextElementSibling.getBoundingClientRect();return {width:r.width,height:r.height,subtitle:s.width,scroll:document.documentElement.scrollWidth,viewport:innerWidth}}')
                                assert geom['width']>=260 and geom['subtitle']>=260,geom
                                assert geom['scroll']<=size,geom
                                if label=='Sarah Kent':assert geom['height']<=75,geom
                                key=f"winner_{'normal' if label=='Sarah Kent' else 'long'}_{size}_{mode}"
                                diagnostics[key]=geom;await shot(page,key)
                            finally:await context.close()
                        await step(f'winner {month} {size} {mode}',winner)
            for table in ['loads','fuel','inspections']:
                async def profile(table=table):
                    common=mapping(prefix+'_profile_'+table)
                    payload={'loads':{'origin':prefix,'destination':'TEST_end','pay':500,'delivered_date':'2011-01-01','status':'On Time'},'fuel':{'date':'2011-01-01','gallons':100,'price_per_gallon':3,'miles':600},'inspections':{'date':'2011-01-01','result':'Fined','fine_amount':20,'fine_reason':prefix}}[table]
                    row=create(table,{**common,**payload});context,page=await fresh()
                    try:
                        await page.goto(BASE+'/drivers/'+str(common['driver_id']))
                        await expect(page.get_by_test_id('driver-profile-page')).to_be_visible()
                        await page.get_by_test_id('profile-tab-'+table).click(force=True)
                        await expect(page.get_by_test_id(f'profile-{table}-{row["id"]}')).to_be_visible()
                        await expect(page.get_by_test_id('profile-tab-'+table)).to_contain_text('(1)')
                        if table=='fuel':await expect(page.get_by_test_id('profile-mpg-value')).to_have_text('6.00')
                        tid=f'profile-delete-{table}-{row["id"]}'
                        await delete(page,tid,lambda:any(r['id']==row['id'] for r in api.request(s,'GET','/'+table).json()))
                        await expect(page.get_by_test_id(f'profile-{table}-{row["id"]}')).to_have_count(0)
                        await expect(page.get_by_test_id('profile-tab-'+table)).to_contain_text('(0)')
                        await expect(page.get_by_test_id('profile-records-empty')).to_be_visible()
                        assert not any(r['id']==row['id'] for r in api.request(s,'GET','/'+table).json())
                        if table=='loads':
                            await expect(page.get_by_test_id('profile-loads-total-value')).to_have_text('0')
                            await expect(page.get_by_test_id('profile-revenue-value')).to_have_text('$0.00')
                            assert not any(r['load_id']==row['id'] for r in api.request(s,'GET','/income').json())
                        if table=='fuel':
                            await expect(page.get_by_test_id('profile-mpg-value')).to_have_text('—')
                            await expect(page.get_by_test_id('profile-mpg-chart')).to_contain_text('No data yet')
                            assert api.request(s,'GET',f'/drivers/{common["driver_id"]}/profile').json()['mpg_trend']==[]
                        await page.get_by_test_id('profile-tab-'+table).scroll_into_view_if_needed();await shot(page,'direct_profile_'+table)
                    finally:await context.close()
                await step('direct profile '+table+' cancel confirm immediate refresh',profile)
            for case in ['pending','approved_load','approved_fuel','dismissed']:
                async def detection(case=case):
                    common=mapping(prefix+'_'+case);configure(common)
                    session=prefix+'_'+case;job={'sourceCity':session,'destinationCity':'TEST_end','income':45}
                    if case=='approved_fuel':
                        for seq,fuel in enumerate([100,150,150,150,150],1):api.request(s,'POST','/telemetry/ingest',json=api.sample(seq,session=session,fuel=fuel))
                    else:api.request(s,'POST','/telemetry/ingest',json=api.sample(1,session=session,job=job,attached=True))
                    event=api.events(s)[0];rid=None
                    if case.startswith('approved'):
                        record={**event['payload'],'price_per_gallon':4} if case=='approved_fuel' else {**common,'origin':session,'destination':'TEST_end','pay':45,'delivered_date':'2012-01-01','status':'On Time'}
                        rid=api.request(s,'POST',f'/telemetry/events/{event["id"]}/review',json={'action':'approve','record':record}).json()['record_id']
                    elif case=='dismissed':api.request(s,'POST',f'/telemetry/events/{event["id"]}/review',json={'action':'dismiss'})
                    context,page=await fresh()
                    try:
                        await page.goto(BASE+'/telemetry');await expect(page.get_by_test_id('telemetry-page')).to_be_visible()
                        if case!='pending':await page.get_by_test_id('telemetry-tab-history').click(force=True)
                        tid='telemetry-delete-'+str(event['id']);await expect(page.get_by_test_id(tid)).to_be_visible()
                        await delete(page,tid,lambda:any(e['id']==event['id'] for e in api.events(s)))
                        await expect(page.get_by_test_id('telemetry-event-'+str(event['id']))).to_have_count(0)
                        assert not any(e['id']==event['id'] for e in api.events(s))
                        if rid:
                            table='fuel' if case=='approved_fuel' else 'loads'
                            saved=next(r for r in api.request(s,'GET','/'+table).json() if r['id']==rid)
                            assert saved['price_per_gallon' if table=='fuel' else 'pay']==(4 if table=='fuel' else 45)
                            if table=='loads':assert next(r for r in api.request(s,'GET','/income').json() if r['load_id']==rid)['amount']==45
                        if case=='pending':
                            api.request(s,'POST','/telemetry/ingest',json=api.sample(2,session=session,job=job,attached=True))
                            assert not any(e['payload'].get('origin')==session for e in api.events(s))
                            await page.get_by_test_id('telemetry-refresh').click(force=True)
                            await expect(page.get_by_test_id('telemetry-empty')).to_be_visible()
                            api.request(s,'POST','/telemetry/ingest',json=api.sample(3,session=session))
                            api.request(s,'POST','/telemetry/ingest',json=api.sample(4,session=session,job=job,attached=True))
                            new=api.events(s)[0];assert new['id']>event['id'] and new['payload']['origin']==session
                            await page.get_by_test_id('telemetry-refresh').click(force=True)
                            await expect(page.get_by_test_id('telemetry-delete-'+str(new['id']))).to_be_visible()
                            api.request(s,'DELETE',f'/telemetry/events/{new["id"]}')
                        await page.get_by_test_id('telemetry-tab-history' if case!='pending' else 'telemetry-tab-pending').scroll_into_view_if_needed();await shot(page,'direct_telemetry_'+case)
                    finally:await context.close()
                await step('direct telemetry '+case+' cancel confirm safety',detection)
            for mode in ['dark','light']:
                async def mobile(mode=mode):
                    row=create('income',{'date':'2013-01-01','amount':123,'source':prefix+'_mobile_'+mode})
                    before=api.request(s,'GET','/stats/dashboard').json()['income']
                    context,page=await fresh(390,mode)
                    try:
                        await expect(page.get_by_test_id('kpi-income-value')).to_have_text(f'${before:,.2f}')
                        await global_open(page,'income');await page.get_by_test_id('delete-entries-search').fill(row['source'])
                        tid='manage-delete-income-'+str(row['id'])
                        await delete(page,tid,lambda:any(r['id']==row['id'] for r in api.request(s,'GET','/income').json()))
                        await expect(page.get_by_test_id(tid)).to_have_count(0)
                        await page.keyboard.press('Escape');await expect(page.get_by_test_id('delete-entries-dialog')).to_have_count(0)
                        await expect(page.locator('[role="alertdialog"]')).to_have_count(0);await page.wait_for_timeout(300)
                        await expect(page.get_by_test_id('kpi-income-value')).to_have_text(f'${before-123:,.2f}')
                        await shot(page,'mobile_dashboard_refresh_'+mode)
                        await page.get_by_test_id('mobile-menu-btn').click(force=True)
                        await page.get_by_test_id('nav-income').last.click(force=True)
                        await expect(page.get_by_test_id('income-page')).to_be_visible()
                        await expect(page.get_by_test_id('income-row-'+str(row['id']))).to_have_count(0)
                        assert api.request(s,'GET','/stats/dashboard').json()['income']==before-123
                    finally:await context.close()
                await step('mobile '+mode+' global delete live dashboard and menu navigation',mobile)
            async def pagination():
                common=mapping(prefix+'_bulk');configure(common)
                for n in range(501):api.request(s,'POST','/telemetry/ingest',json=api.sample(n,session=prefix+'_bulk',job={'sourceCity':prefix+'_bulk_'+str(n),'destinationCity':'TEST_end','income':1},attached=True))
                allrows=[r for r in api.events(s) if r['payload'].get('origin','').startswith(prefix+'_bulk_')]
                assert len(allrows)==501;oldest=allrows[-1]
                context,page=await fresh()
                try:
                    await page.goto(BASE+'/telemetry');await expect(page.get_by_test_id('telemetry-tab-pending')).to_have_text('To review (501)')
                    await global_open(page,'telemetry/events')
                    await expect(page.get_by_test_id('delete-entries-count')).to_have_text('501 entries · all dates · showing 1–100')
                    assert await page.locator('[data-testid^="manage-entry-telemetry-events-"]').count()==100
                    await page.get_by_test_id('delete-entries-next-page').click(force=True)
                    await expect(page.get_by_test_id('delete-entries-count')).to_contain_text('showing 101–200')
                    await page.get_by_test_id('delete-entries-prev-page').click(force=True)
                    await expect(page.get_by_test_id('delete-entries-count')).to_contain_text('showing 1–100')
                    for offset in range(100,501,100):
                        await page.get_by_test_id('delete-entries-next-page').click(force=True)
                        await expect(page.get_by_test_id('delete-entries-count')).to_contain_text(f'showing {offset+1}–{min(offset+100,501)}')
                    await shot(page,'telemetry_last_page_501')
                    await page.get_by_test_id('delete-entries-search').fill(prefix+'_bulk_0')
                    await expect(page.get_by_test_id('delete-entries-count')).to_have_text('1 entries · all dates · showing 1–1')
                    await expect(page.get_by_test_id('manage-delete-telemetry-events-'+str(oldest['id']))).to_be_visible()
                    await page.get_by_test_id('delete-entries-search').fill('TEST_no_matching_history_!')
                    await expect(page.get_by_test_id('delete-entries-count')).to_have_text('0 entries · all dates')
                    await expect(page.get_by_test_id('delete-entries-empty')).to_be_visible()
                    await page.get_by_test_id('delete-entries-search').fill('')
                    await expect(page.get_by_test_id('delete-entries-count')).to_contain_text('showing 1–100')
                    for offset in range(100,501,100):
                        await page.get_by_test_id('delete-entries-next-page').click(force=True)
                        await expect(page.get_by_test_id('delete-entries-count')).to_contain_text(f'showing {offset+1}–{min(offset+100,501)}')
                    await delete(page,'manage-delete-telemetry-events-'+str(oldest['id']),lambda:any(e['id']==oldest['id'] for e in api.events(s)))
                    await expect(page.get_by_test_id('delete-entries-count')).to_have_text('500 entries · all dates · showing 401–500')
                    await expect(page.get_by_test_id('delete-entries-next-page')).to_be_disabled()
                    await shot(page,'telemetry_last_page_adjusted_500')
                    await page.get_by_test_id('delete-entries-search').fill(prefix+'_bulk_0')
                    await expect(page.get_by_test_id('delete-entries-empty')).to_be_visible()
                    assert not any(e['id']==oldest['id'] for e in api.events(s))
                finally:await context.close()
            await step('501 history complete server search pagination oldest delete last page adjusts',pagination)
            async def permissions():
                context,page=await fresh(dispatcher=True)
                try:
                    assert await page.get_by_test_id('open-delete-entries').count()==0
                    await page.goto(BASE+'/telemetry');await expect(page.get_by_test_id('telemetry-page')).to_be_visible()
                    assert await page.locator('[data-testid^="telemetry-delete-"]').count()==0
                    assert await page.get_by_test_id('open-delete-entries').count()==0
                    d=api.request(s,'GET','/drivers').json()[0]
                    await page.goto(BASE+'/drivers/'+str(d['id']));await expect(page.get_by_test_id('driver-profile-page')).to_be_visible()
                    assert await page.locator('[data-testid^="profile-delete-"]').count()==0
                    a=api.login(DISPATCH,DPASS)
                    assert 'owner' in api.request(a,'GET','/telemetry/manage-events',403).json()['detail']
                    event=api.events(s)[0];assert 'owner' in api.request(a,'DELETE',f'/telemetry/events/{event["id"]}',403).json()['detail']
                    diagnostics['error_text']=await page.evaluate("""() => {const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));return errorElements.map(el => el.textContent).join(', ');} """)
                    print('Found error message: '+diagnostics['error_text'] if diagnostics['error_text'] else 'No error messages found on the page')
                finally:await context.close()
            await step('dispatcher direct buttons hidden and manage/delete APIs forbidden',permissions)
        finally:
            await browser.close()
            s=api.login(OWNER,PASSWORD)
            api.request(s,'POST','/backup/restore',json={**api.body(blob),'confirm':'RESTORE MCCOY','owner_password':PASSWORD})
            s=api.login(OWNER,PASSWORD);final=api.decrypt(api.archive(s))
            assert api.normalize(final)==api.normalize(original)
            diagnostics['original_restored']=True;diagnostics['final_counts']={t:len(v) for t,v in final['tables'].items()}
            (OUT/'results.json').write_text(json.dumps({'results':results,'diagnostics':diagnostics,'page_errors':errors},indent=2))
            print('UI',sum(r['status']=='PASS' for r in results),'passed',sum(r['status']=='FAIL' for r in results),'failed',flush=True)

if __name__=='__main__':asyncio.run(main())