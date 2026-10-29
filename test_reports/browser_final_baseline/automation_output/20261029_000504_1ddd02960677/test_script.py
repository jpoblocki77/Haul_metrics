async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({'width':1920,'height':800})
        await page.get_by_test_id('login-username-input').fill('owner')
        await page.get_by_test_id('login-password-input').fill('trucker123')
        await page.get_by_test_id('login-submit-btn').click(force=True)
        await page.get_by_test_id('dashboard-page').wait_for(state='visible')
        await page.get_by_test_id('open-delete-entries').wait_for(state='visible')
        await page.screenshot(path='/app/test_reports/browser_final_baseline/automation_output/20261029_000504_1ddd02960677/browser_final_baseline.jpeg', type="jpeg", quality=40, full_page=False)
        print('PASS frontend loads; owner dashboard and global deletion control visible')
        error_text = await page.evaluate("""() => {const errorElements = Array.from(document.querySelectorAll('.error, [class*=\"error\"], [id*=\"error\"]'));return errorElements.map(el => el.textContent).join(', ');} """)
        print(f'Found error message: {error_text}' if error_text else 'No error messages found on the page')
    except Exception as e:
        print(f'FAIL frontend baseline: {e}')
