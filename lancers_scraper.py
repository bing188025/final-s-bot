"""
Lancers job scraper.
Fetches new job listings from Lancers search pages and returns structured data.
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en;q=0.9",
}

SEARCH_URLS = [
    "https://www.lancers.jp/work/search/system?open=1&ref=header_menu",
    "https://www.lancers.jp/work/search/web?open=1&ref=header_menu",
]


def _parse_jobs(html: str, blocked_clients: list[str]) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    for card in soup.select(".p-search-job-media"):
        # Title and link
        title_el = card.select_one(".p-search-job-media__title")
        if not title_el:
            continue

        href = title_el.get("href", "")
        # Strip badge text (e.g. "NEW") from title
        for tag in title_el.select(".p-search-job-media__tag"):
            tag.decompose()
        title = title_el.get_text(strip=True)

        job_url = "https://www.lancers.jp" + href if href else ""
        job_id = href.strip("/").split("/")[-1] if href else ""
        if not job_id:
            continue

        # Price
        price_el = card.select_one(".p-search-job-media__price")
        price = price_el.get_text(strip=True) if price_el else "要相談"

        # Client name
        client_name_el = card.select_one(".p-search-job-media__avatar-note a")
        client_name = client_name_el.get_text(strip=True) if client_name_el else "不明"

        # Skip blocked clients
        if client_name in blocked_clients:
            continue

        # Client avatar
        avatar_el = card.select_one("img.c-avatar__image")
        client_avatar = avatar_el.get("src", "") if avatar_el else ""

        jobs.append({
            "id": job_id,
            "title": title,
            "url": job_url,
            "price": price,
            "client_name": client_name,
            "client_avatar": client_avatar,
        })

    return jobs


async def _fetch_url(session: aiohttp.ClientSession, url: str, blocked_clients: list[str]) -> list[dict]:
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                print(f"[LANCERS] Failed to fetch {url}: HTTP {resp.status}")
                return []
            html = await resp.text()
            return _parse_jobs(html, blocked_clients)
    except Exception as e:
        print(f"[LANCERS] Error fetching {url}: {e}")
        return []


async def fetch_lancers_jobs(session: aiohttp.ClientSession, blocked_clients: list[str]) -> list[dict]:
    """Fetch both Lancers search URLs concurrently and return all jobs."""
    results = await asyncio.gather(*[_fetch_url(session, url, blocked_clients) for url in SEARCH_URLS])
    return [job for page_jobs in results for job in page_jobs]
