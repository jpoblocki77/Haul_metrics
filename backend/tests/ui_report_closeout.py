"""Paced real preview SPA report retest, populated chart geometry and one-page PDF."""
import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright, expect
from pypdf import PdfReader

from test_full_regression import login, request

BASE = os.environ['REACT_APP_BACKEND_URL'].rstrip('/')
OUT = Path(os.environ.get('REPORT_BROWSER_OUTPUT', '/app/test_reports/browser_iter9_report'))
OUT.mkdir(exist_ok=True)


async def main():
    s = login(os.environ['OWNER_USERNAME'], os.environ['OWNER_PASSWORD'])
    dashboard = request(s, 'GET', '/stats/dashboard').json()
    month = next(x['m'] for x in reversed(dashboard['monthly']) if x['income'] > 0)
    results = []
    diagnostics = {'month': month, 'responses_429': [], 'page_errors': []}
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=['--no-sandbox'])
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        page.on('pageerror', lambda e: diagnostics['page_errors'].append(str(e)))

        async def capture(response):
            if response.status == 429:
                headers = await response.all_headers()
                diagnostics['responses_429'].append({'url': response.url, 'status': 429,
                                                     'headers': {k: v for k, v in headers.items() if k not in ['set-cookie', 'authorization']},
                                                     'body': (await response.text())[:500]})
        page.on('response', capture)

        async def step(name, fn):
            try:
                await fn()
                results.append({'name': name, 'status': 'PASS'})
                print('PASS', name, flush=True)
            except Exception as exc:
                results.append({'name': name, 'status': 'FAIL', 'error': str(exc)})
                print('FAIL', name, str(exc), flush=True)

        try:
            async def signin():
                await page.goto(BASE + '/login')
                await page.get_by_test_id('login-username-input').fill(os.environ['OWNER_USERNAME'])
                await page.get_by_test_id('login-password-input').fill(os.environ['OWNER_PASSWORD'])
                await page.get_by_test_id('login-submit-btn').click(force=True)
                await expect(page.get_by_test_id('dashboard-page')).to_be_visible()
                await page.wait_for_timeout(1500)
            await step('real browser sign-in and dashboard', signin)

            async def paced_navigation():
                for name in ['income', 'fuel', 'dashboard', 'report']:
                    await page.get_by_test_id('nav-' + name).first.click(force=True)
                    await expect(page.get_by_test_id(name + '-page')).to_be_visible()
                    await page.wait_for_timeout(1500)
                await page.get_by_test_id('report-month').fill(month)
                await expect(page.get_by_test_id('report-income')).to_be_visible()
                await page.wait_for_timeout(1500)
                assert not diagnostics['responses_429'], diagnostics['responses_429']
                await expect(page.get_by_test_id('print-report-btn')).to_be_enabled()
            await step('user-paced SPA navigation no429', paced_navigation)

            async def charts_pdf():
                start = month + '-01'
                end = month + '-31'
                stats = request(s, 'GET', '/stats/dashboard', params={'start': start, 'end': end}).json()
                await expect(page.get_by_test_id('report-income')).to_have_text(f"${stats['income']:,.2f}")
                charts = await page.locator('.report-chart').evaluate_all('els => els.map(e=>({width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height,svg:e.querySelectorAll("svg.recharts-surface").length,bars:e.querySelectorAll(".recharts-bar-rectangle").length,paths:e.querySelectorAll(".recharts-line-curve").length}))')
                diagnostics['charts'] = charts
                assert len(charts) == 2 and all(x['svg'] > 0 and x['width'] > 100 and x['height'] > 100 for x in charts), charts
                assert any(x['bars'] > 0 or x['paths'] > 0 for x in charts), charts
                await page.screenshot(path=str(OUT / 'populated_report.jpg'), quality=40, full_page=False)
                pdf = OUT / 'populated_report.pdf'
                await page.pdf(path=str(pdf), format='Letter', print_background=True, prefer_css_page_size=True)
                reader = PdfReader(pdf)
                diagnostics['pdf_pages'] = len(reader.pages)
                text = ''.join(x.extract_text() for x in reader.pages)
                assert len(reader.pages) == 1 and 'Income' in text and 'McCoy' in text
            await step('visible populated charts actual one-page PDF', charts_pdf)

            async def logout():
                await page.get_by_test_id('logout-btn').first.click(force=True)
                await expect(page.get_by_test_id('login-form')).to_be_visible()
                error_text = await page.evaluate("""() => {const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));return errorElements.map(el => el.textContent).join(', ');} """)
                print(f'Found error message: {error_text}' if error_text else 'No error messages found on the page')
                diagnostics['final_visible_errors'] = error_text
                assert not diagnostics['page_errors'] and not error_text
            await step('real logout and no browser errors', logout)
        finally:
            await browser.close()
            (OUT / 'results.json').write_text(json.dumps({'results': results, 'diagnostics': diagnostics}, indent=2))
    assert all(x['status'] == 'PASS' for x in results), results


if __name__ == '__main__':
    asyncio.run(main())