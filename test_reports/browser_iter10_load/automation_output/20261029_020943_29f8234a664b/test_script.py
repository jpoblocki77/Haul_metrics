async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.get_by_test_id('login-form').wait_for(state='visible', timeout=15000)
        assert await page.get_by_test_id('login-username-input').is_editable()
        assert await page.get_by_test_id('login-password-input').is_editable()
        assert await page.get_by_test_id('login-submit-btn').is_enabled()
        await page.screenshot(path='/app/test_reports/browser_iter10_load/automation_output/20261029_020943_29f8234a664b/login.jpeg', type="jpeg", quality=40, full_page=False)
        print('PASS public login form and editable fields')
        error_text = await page.evaluate("""() => {const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));return errorElements.map(el => el.textContent).join(', ');} """)
        if error_text:
            print(f'Found error message: {error_text}')
        else:
            print('No error messages found on the page')
        assert not error_text
    except Exception as e:
        print(f'FAIL public login smoke: {e}')
