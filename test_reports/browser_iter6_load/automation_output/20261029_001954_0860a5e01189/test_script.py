async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({'width':390,'height':844})
        await page.get_by_test_id('login-username-input').wait_for(state='visible')
        print('PASS public sign-in loads')
    except Exception as e:
        print('FAIL public sign-in',str(e))
