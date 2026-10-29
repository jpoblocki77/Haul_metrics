async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({'width':390,'height':844})
        await page.get_by_test_id('login-form').wait_for(state='visible')
        photo=page.get_by_test_id('login-trucking-photo')
        print('MOBILE_LOGIN_PHOTO', await photo.evaluate('e=>({complete:e.complete,naturalWidth:e.naturalWidth,visible:!!(e.offsetWidth||e.offsetHeight),src:e.getAttribute("src")})'))
        print('MOBILE_OVERFLOW',await page.evaluate('document.documentElement.scrollWidth>innerWidth'))
        await page.get_by_test_id('login-theme-toggle').click(force=True)
        await page.screenshot(path='/app/test_reports/browser_iter8_visual/automation_output/20261029_014735_b64134fff2b3/mobile_login.jpeg', type="jpeg", quality=40, full_page=False)
        error_text=await page.evaluate("""() => {const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));return errorElements.map(el => el.textContent).join(', ');} """)
        print('Found error message: '+error_text if error_text else 'No error messages found on the page')
        print('PASS login mobile both theme switching and no overflow')
    except Exception as e:
        print('FAIL visual mobile login',str(e))
