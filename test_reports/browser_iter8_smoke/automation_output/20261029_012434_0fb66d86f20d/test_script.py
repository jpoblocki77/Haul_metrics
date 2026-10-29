async def run_test(page, output_dir, page_url):
    await page.set_viewport_size({"width":1920,"height":800})
    try:
        await page.get_by_test_id('login-form').wait_for(state='visible')
        await page.get_by_test_id('login-username-input').fill('owner')
        await page.get_by_test_id('login-password-input').fill('trucker123')
        await page.get_by_test_id('login-submit-btn').click(force=True)
        await page.get_by_test_id('dashboard-page').wait_for(state='visible')
        assert await page.get_by_test_id('header-logout-btn').is_visible()
        photos = await page.locator('[data-testid^="trucking-photo-"]').evaluate_all('(els)=>els.map(e=>({id:e.dataset.testid,width:e.naturalWidth,complete:e.complete}))')
        assert len(photos)==3 and all(p['width']>0 for p in photos), photos
        print('PASS preview login, header logout, all three local photographs loaded')
        await page.screenshot(path='/app/test_reports/browser_iter8_smoke/automation_output/20261029_012434_0fb66d86f20d/dashboard.jpeg', type="jpeg", quality=40, full_page=False)
        await page.get_by_test_id('header-logout-btn').click(force=True)
        await page.get_by_test_id('login-form').wait_for(state='visible')
        print('PASS header logout returns to login')
    except Exception as e:
        print('FAIL smoke:', str(e))
    error_text = await page.evaluate("""() => {const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));return errorElements.map(el => el.textContent).join(', ');} """)
    print(f'Found error message: {error_text}' if error_text else 'No error messages found on the page')
