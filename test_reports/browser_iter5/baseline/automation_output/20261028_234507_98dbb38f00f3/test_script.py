async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({'width':1920,'height':800})
        await page.get_by_test_id('login-form').wait_for(state='visible')
        await page.screenshot(path='/app/test_reports/browser_iter5/baseline/automation_output/20261028_234507_98dbb38f00f3/baseline.jpeg', type="jpeg", quality=40, full_page=False)
        print('PASS public frontend login loads')
    except Exception as e:
        print('FAIL frontend load',str(e))
