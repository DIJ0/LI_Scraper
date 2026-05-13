import asyncio
from playwright.async_api import async_playwright

from scraper import _ensure_logged_in


async def _easy_apply(page, job_url: str) -> bool:
    await page.goto(job_url)
    await asyncio.sleep(2)

    # Confirm Easy Apply button exists
    try:
        btn = page.locator(".jobs-apply-button--top-card").first
        btn_text = await btn.inner_text(timeout=3000)
        if "easy apply" not in btn_text.lower():
            print("  Not an Easy Apply job — skipping")
            return False
        await btn.click()
    except Exception:
        print("  Easy Apply button not found — skipping")
        return False

    await asyncio.sleep(2)

    for _step in range(10):
        await asyncio.sleep(1.5)

        # Bail out if the form has unfilled required fields we can't handle
        try:
            unfilled = await page.locator("input[required]:not([value])").count()
            if unfilled > 0:
                print(f"  {unfilled} required field(s) — cannot auto-fill, skipping")
                await page.keyboard.press("Escape")
                return False
        except Exception:
            pass

        # Next step
        try:
            btn = page.locator("button[aria-label='Continue to next step']")
            if await btn.is_visible(timeout=800):
                await btn.click()
                continue
        except Exception:
            pass

        # Review step
        try:
            btn = page.locator("button[aria-label='Review your application']")
            if await btn.is_visible(timeout=800):
                await btn.click()
                continue
        except Exception:
            pass

        # Submit
        try:
            btn = page.locator("button[aria-label='Submit application']")
            if await btn.is_visible(timeout=800):
                await btn.click()
                await asyncio.sleep(2)
                print("  Application submitted")
                return True
        except Exception:
            pass

        break

    await page.keyboard.press("Escape")
    return False


async def _run(job_url: str) -> bool:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context()
        page    = await context.new_page()
        await _ensure_logged_in(page, context)
        result = await _easy_apply(page, job_url)
        await browser.close()
        return result


def easy_apply(job_url: str) -> bool:
    return asyncio.run(_run(job_url))
