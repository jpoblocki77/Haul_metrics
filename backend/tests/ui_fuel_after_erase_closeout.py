"""Real preview erase-to-normal-fuel flow; execute only inside the exact SQLite guard."""
import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright, expect
from regression_safety import table_snapshot
from test_full_regression import login, request

BASE = os.environ['REACT_APP_BACKEND_URL'].rstrip('/')
OUT = Path(os.environ['FUEL_BROWSER_OUTPUT'])
OUT.mkdir(exist_ok=True)


async def main():
    api_session = login(os.environ['OWNER_USERNAME'], os.environ['OWNER_PASSWORD'])
    truck = request(api_session, 'GET', '/trucks').json()[0]
    driver = request(api_session, 'GET', '/drivers').json()[0]
    results = []
    diagnostics = {'page_errors': [], 'responses_429': []}
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=['--no-sandbox'])
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        page.set_default_timeout(15000)
        page.on('pageerror', lambda e: diagnostics['page_errors'].append(str(e)))
        page.on('response', lambda r: diagnostics['responses_429'].append(r.url) if r.status == 429 else None)

        async def step(name, fn):
            try:
                await fn()
                results.append({'name': name, 'status': 'PASS'})
                print('PASS', name, flush=True)
            except Exception as exc:
                results.append({'name': name, 'status': 'FAIL', 'error': str(exc)})
                print('FAIL', name, str(exc), flush=True)
                raise

        try:
            async def signin():
                await page.goto(BASE + '/login')
                await page.get_by_test_id('login-username-input').fill(os.environ['OWNER_USERNAME'])
                await page.get_by_test_id('login-password-input').fill(os.environ['OWNER_PASSWORD'])
                await page.get_by_test_id('login-submit-btn').click(force=True)
                await expect(page.get_by_test_id('dashboard-page')).to_be_visible()
                await page.wait_for_timeout(1000)
            await step('real browser sign-in', signin)

            async def erase():
                await page.get_by_test_id('nav-backup').first.click(force=True)
                await expect(page.get_by_test_id('backup-page')).to_be_visible()
                before = table_snapshot()
                setup = ['users', 'company_settings', 'categories', 'drivers', 'trucks', 'telemetry_sources']
                await page.get_by_test_id('open-erase-records').click(force=True)
                await expect(page.get_by_test_id('erase-record-counts')).to_be_visible()
                await page.get_by_test_id('erase-owner-password').fill(os.environ['OWNER_PASSWORD'])
                await page.get_by_test_id('erase-confirmation').fill('ERASE ALL RECORDS')
                await page.get_by_test_id('erase-records-confirm').click(force=True)
                await expect(page.get_by_test_id('erase-records-dialog')).to_have_count(0)
                after = table_snapshot()
                assert {k: before[k] for k in setup} == {k: after[k] for k in setup}
                counts = request(api_session, 'GET', '/company/record-counts').json()
                assert len(counts) == 6 and all(v == 0 for v in counts.values()), counts
                diagnostics['exact_setup_preserved_at_erase'] = True
                diagnostics['activity_counts_after_erase'] = counts
            await step('cookie-authenticated erase preserves setup and clears six activity tables', erase)

            async def fuel():
                await page.get_by_test_id('nav-fuel').first.click(force=True)
                await expect(page.get_by_test_id('fuel-page')).to_be_visible()
                await page.get_by_test_id('range-all').click(force=True)
                await expect(page.get_by_test_id('fuel-empty')).to_be_visible()
                await page.get_by_test_id('add-fuel-btn').click(force=True)
                await expect(page.get_by_test_id('fuel-dialog')).to_be_visible()
                await page.get_by_test_id('input-truck-id').click(force=True)
                await page.wait_for_timeout(200)
                await page.get_by_test_id('input-truck-id-option-' + str(truck['id'])).click(force=True)
                assert float(await page.get_by_test_id('input-gallons').input_value()) == truck['tank_gallons']
                await page.get_by_test_id('input-driver-id').click(force=True)
                await page.wait_for_timeout(200)
                await page.get_by_test_id('input-driver-id-option-' + str(driver['id'])).click(force=True)
                await page.get_by_test_id('input-price-per-gallon').fill('4')
                miles = truck['tank_gallons'] * 6
                await page.get_by_test_id('input-miles').fill(str(miles))
                await page.get_by_test_id('input-location').fill('TEST_iter10_normal_fuel')
                await expect(page.get_by_test_id('fuel-total-preview')).to_have_text(f"${truck['tank_gallons'] * 4:,.2f}")
                await expect(page.get_by_test_id('fuel-mpg-preview')).to_have_text('6.00')
                async with page.expect_response(lambda r: r.url == BASE + '/api/fuel' and r.request.method == 'POST') as response:
                    await page.get_by_test_id('fuel-save-btn').click(force=True)
                saved_response = await response.value
                assert saved_response.status == 200, await saved_response.text()
                saved = await saved_response.json()
                await expect(page.get_by_test_id('fuel-dialog')).to_have_count(0)
                await expect(page.get_by_test_id('fuel-row-' + str(saved['id']))).to_be_visible()
                rows = request(api_session, 'GET', '/fuel').json()
                assert len(rows) == 1 and rows[0]['id'] == saved['id']
                assert (rows[0]['gallons'], rows[0]['price_per_gallon'], rows[0]['total'], rows[0]['mpg']) == (truck['tank_gallons'], 4, truck['tank_gallons'] * 4, 6)
                await expect(page.get_by_test_id('fuel-kpi-fillups')).to_contain_text('1')
                await page.screenshot(path=str(OUT / 'normal_fuel_after_erase.jpg'), quality=40, full_page=False)
                diagnostics['normal_fuel_persisted'] = True
            await step('preserved truck auto-fill normal fuel preview save persistence and stats', fuel)

            async def logout():
                await page.get_by_test_id('logout-btn').first.click(force=True)
                await expect(page.get_by_test_id('login-form')).to_be_visible()
                error_text = await page.evaluate("""() => {const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));return errorElements.map(el => el.textContent).join(', ');} """)
                print(f'Found error message: {error_text}' if error_text else 'No error messages found on the page')
                diagnostics['final_visible_errors'] = error_text
                assert not error_text and not diagnostics['page_errors'] and not diagnostics['responses_429']
            await step('logout no browser errors or429', logout)
        finally:
            await browser.close()
            (OUT / 'results.json').write_text(json.dumps({'results': results, 'diagnostics': diagnostics}, indent=2))


if __name__ == '__main__':
    asyncio.run(main())