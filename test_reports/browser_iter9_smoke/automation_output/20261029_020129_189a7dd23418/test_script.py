async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({'width':1920,'height':1080})
        await page.get_by_test_id('login-form').wait_for(state='visible')
        await page.screenshot(path='/app/test_reports/browser_iter9_smoke/automation_output/20261029_020129_189a7dd23418/login.jpeg', type="jpeg", quality=40, full_page=False)
        print('PASS public frontend login loads')
        error_text = await page.evaluate("""() => {const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));return errorElements.map(el => el.textContent).join(', ');} """)
        print(f'Found error message: {error_text}' if error_text else 'No error messages found on the page')
    except Exception as e:
        print(f'FAIL frontend load: {e}')
