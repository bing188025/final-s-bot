"""
Lancers job scraper.
Uses lxml with XPath for maximum parsing speed.
"""

import asyncio
import aiohttp
from lxml import html as lxml_html

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


def _parse_jobs(page_html: str, blocked_clients: set[str]) -> list[dict]:
    tree = lxml_html.fromstring(page_html)
    jobs = []

    for card in tree.xpath('//div[contains(@class, "p-search-job-media") and contains(@class, "c-media--item")]'):
        # Title and link
        title_els = card.xpath('.//a[contains(@class, "p-search-job-media__title")]')
        if not title_els:
            continue
        title_el = title_els[0]

        href = title_el.get("href", "")
        job_id = href.strip("/").split("/")[-1] if href else ""
        if not job_id:
            continue

        job_url = "https://www.lancers.jp" + href
        if not job_url.startswith("https://"):
            continue

        # Title text — exclude tag text (e.g. "NEW")
        tag_texts = title_el.xpath('.//li[contains(@class, "p-search-job-media__tag")]/text()')
        full_text = title_el.text_content().strip()
        for t in tag_texts:
            full_text = full_text.replace(t.strip(), "", 1).strip()
        title = full_text

        # Price
        price_els = card.xpath('.//span[contains(@class, "p-search-job-media__price")]')
        price = price_els[0].text_content().strip() if price_els else "要相談"

        # Client name
        client_els = card.xpath('.//p[contains(@class, "p-search-job-media__avatar-note")]/a')
        client_name = client_els[0].text_content().strip() if client_els else "不明"

        if client_name in blocked_clients:
            continue

        # Client avatar — fix protocol-relative URLs
        avatar_els = card.xpath('.//img[contains(@class, "c-avatar__image")]')
        client_avatar = avatar_els[0].get("src", "") if avatar_els else ""
        if client_avatar.startswith("//"):
            client_avatar = "https:" + client_avatar
        if not client_avatar.startswith("https://"):
            client_avatar = ""

        jobs.append({
            "id": job_id,
            "title": title,
            "url": job_url,
            "price": price,
            "client_name": client_name,
            "client_avatar": client_avatar,
        })

    return jobs


async def _fetch_url(session: aiohttp.ClientSession, url: str, blocked_clients: set[str]) -> list[dict]:
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                print(f"[LANCERS] Failed to fetch {url}: HTTP {resp.status}")
                return []
            data = await resp.read()
            page_html = data.decode("utf-8", errors="replace")
            return _parse_jobs(page_html, blocked_clients)
    except Exception as e:
        print(f"[LANCERS] Error fetching {url}: {e}")
        return []


async def fetch_lancers_jobs(session: aiohttp.ClientSession, blocked_clients: list[str]) -> list[dict]:
    """Fetch both Lancers search URLs concurrently and return all jobs."""
    bc = set(blocked_clients)
    results = await asyncio.gather(*[_fetch_url(session, url, bc) for url in SEARCH_URLS])
    return [job for page_jobs in results for job in page_jobs]
