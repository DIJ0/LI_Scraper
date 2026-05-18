import json
import asyncio
import random
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright, Page, BrowserContext

from config import (
    LINKEDIN_EMAIL, LINKEDIN_PASSWORD, COOKIES_PATH,
    JOB_TITLES, LOCATION_NAME, LOCATION_DISTANCE_MILES, SEARCH_REMOTE,
    DATE_POSTED_FILTER, EXPERIENCE_LEVELS, JOB_TYPES, JOB_FUNCTION,
)

LINKEDIN_HOME       = "https://www.linkedin.com"
JOB_SEARCH_URL      = "https://www.linkedin.com/jobs/search/"
MAX_JOBS_PER_SEARCH = 20


def _pause(min_s: float, max_s: float):
    return asyncio.sleep(random.uniform(min_s, max_s))


async def _save_cookies(context: BrowserContext):
    cookies = await context.cookies()
    with open(COOKIES_PATH, "w") as f:
        json.dump(cookies, f)


async def _load_cookies(context: BrowserContext) -> bool:
    try:
        with open(COOKIES_PATH) as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)
        return True
    except (FileNotFoundError, json.JSONDecodeError):
        return False


async def _login(page: Page, context: BrowserContext):
    await page.goto(f"{LINKEDIN_HOME}/login", wait_until="domcontentloaded")
    await page.wait_for_selector("#username", timeout=30000)
    await _pause(1.0, 2.5)
    await page.fill("#username", LINKEDIN_EMAIL)
    await _pause(0.5, 1.5)
    await page.fill("#password", LINKEDIN_PASSWORD)
    await _pause(0.8, 2.0)
    await page.click('[type="submit"]')
    await page.wait_for_url("**/feed/**", timeout=30000)
    await _save_cookies(context)


async def _ensure_logged_in(page: Page, context: BrowserContext):
    loaded = await _load_cookies(context)
    await page.goto(LINKEDIN_HOME, wait_until="domcontentloaded")
    await _pause(3.0, 5.0)
    if "/feed" not in page.url:
        if not loaded:
            await _login(page, context)
        else:
            await _login(page, context)


async def _extract_job_card(page: Page, card) -> dict | None:
    try:
        await card.click()
        await _pause(1.5, 3.0)

        raw_id = await card.get_attribute("data-job-id") or ""
        # data-job-id is sometimes missing/wrong on remote results — fall back to URL
        if not raw_id.isdigit():
            params = parse_qs(urlparse(page.url).query)
            raw_id = params.get("currentJobId", [""])[0]
        job_id = raw_id

        try:
            title = await page.locator(
                ".job-details-jobs-unified-top-card__job-title h1"
            ).inner_text(timeout=4000)
        except Exception:
            title = await page.locator(
                ".job-details-jobs-unified-top-card__job-title"
            ).inner_text(timeout=4000)

        company = await page.locator(
            ".job-details-jobs-unified-top-card__company-name"
        ).inner_text(timeout=4000)

        location = await page.locator(
            ".job-details-jobs-unified-top-card__primary-description-container"
        ).inner_text(timeout=3000)

        try:
            description = await page.locator(
                ".jobs-description__content"
            ).inner_text(timeout=4000)
        except Exception:
            description = ""

        try:
            salary = await page.locator(
                ".compensation__salary-range"
            ).inner_text(timeout=2000)
        except Exception:
            salary = ""

        loc_lower = location.lower()
        remote_type = (
            "Remote"  if "remote"  in loc_lower else
            "Hybrid"  if "hybrid"  in loc_lower else
            "On-site"
        )

        return {
            "job_id":          job_id,
            "job_title":       title.strip(),
            "company_name":    company.strip(),
            "location":        location.strip()[:200],
            "remote_type":     remote_type,
            "salary_range":    salary.strip(),
            "job_description": description.strip(),
            "job_url":         page.url,
        }
    except Exception as e:
        print(f"    [skip] could not extract job: {e}")
        return None


async def _search(page: Page, keyword: str, remote: bool) -> list:
    params = {
        "keywords": keyword,
        "f_TPR":    DATE_POSTED_FILTER,
        "f_E":      EXPERIENCE_LEVELS,
        "f_JT":     JOB_TYPES,
        "f_F":      JOB_FUNCTION,
    }
    if remote:
        params["f_WT"] = "2"
    else:
        params["location"] = LOCATION_NAME
        params["distance"]  = str(LOCATION_DISTANCE_MILES)

    query = "&".join(f"{k}={v}" for k, v in params.items())
    label = "remote" if remote else LOCATION_NAME
    print(f"  Searching '{keyword}' [{label}]")

    await page.goto(f"{JOB_SEARCH_URL}?{query}")
    await _pause(2.5, 4.5)

    cards = await page.locator(".job-card-container").all()
    print(f"    {len(cards)} cards found")

    jobs = []
    for card in cards[:MAX_JOBS_PER_SEARCH]:
        job = await _extract_job_card(page, card)
        if job:
            jobs.append(job)
        await _pause(1.0, 2.5)

    return jobs


async def _run_scraper() -> list:
    all_jobs = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()
        await _ensure_logged_in(page, context)

        for title in JOB_TITLES:
            jobs = await _search(page, title, remote=False)
            all_jobs.extend(jobs)
            await _pause(2.0, 4.0)

            if SEARCH_REMOTE:
                jobs = await _search(page, title, remote=True)
                all_jobs.extend(jobs)
                await _pause(2.0, 4.0)

        await browser.close()

    seen, unique = set(), []
    for job in all_jobs:
        jid = job.get("job_id")
        if jid and jid not in seen:
            seen.add(jid)
            unique.append(job)

    print(f"Total unique jobs scraped: {len(unique)}")
    return unique


def scrape_jobs() -> list:
    return asyncio.run(_run_scraper())
