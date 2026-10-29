async def run_test(page, output_dir, page_url):
    await page.set_viewport_size({"width":1920,"height":800})
    try:
        await page.get_by_test_id('login-username').fill('owner')
        await page.get_by_test_id('login-password').fill('trucker123')
        await page.get_by_test_id('login-submit').click()
        await page.wait_for_timeout(1200)
        print('LOGIN URL', page.url)
    except Exception as e:
        print('LOGIN selector result',str(e))
        print(await page.locator('[data-testid]').evaluate_all('(els)=>els.map(e=>e.dataset.testid)'))
    await page.screenshot(path='/app/test_reports/browser_iter4/automation_output/20261028_231423_7c97059c8731/baseline.jpeg', type="jpeg", quality=40, full_page=False)

