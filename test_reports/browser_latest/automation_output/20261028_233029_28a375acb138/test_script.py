async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({'width':390,'height':844})
        await page.get_by_test_id('login-form').wait_for(state='visible')
        await page.get_by_test_id('login-username-input').fill('owner')
        await page.get_by_test_id('login-password-input').fill('trucker123')
        await page.get_by_test_id('login-submit-btn').click(force=True)
        await page.get_by_test_id('dashboard-page').wait_for(state='visible')
        await page.get_by_test_id('range-today').click(force=True)
        today=await page.evaluate("new Date(Date.now()-new Date().getTimezoneOffset()*60000).toISOString().slice(0,10)")
        assert await page.get_by_test_id('range-start').input_value()==today
        assert await page.get_by_test_id('range-end').input_value()==today
        print('PASS mobile login and Today local date:',today)
        await page.get_by_test_id('mobile-menu-btn').click(force=True)
        await page.get_by_test_id('nav-company').last.click(force=True)
        await page.get_by_test_id('company-settings-page').wait_for(state='visible')
        await page.screenshot(path='/app/test_reports/browser_latest/automation_output/20261028_233029_28a375acb138/company_mobile_latest.jpeg', type="jpeg", quality=40, full_page=False)
        print('PASS mobile company page navigation')
    except Exception as e:
        print('FAIL:',str(e))
    error_text=await page.evaluate("""() => {const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));return errorElements.map(el => el.textContent).join(', ');} """)
    print('Found error message: '+error_text if error_text else 'No error messages found on the page')
