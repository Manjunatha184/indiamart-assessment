from __future__ import annotations
import os
import csv
import asyncio
import random
import time
import re
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from playwright.async_api import (
    async_playwright,
    TimeoutError as PWTimeout,
    Route,
    Page,
    ElementHandle,
)

load_dotenv()

UA_STRINGS = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.4 Safari/605.1.15"
    ),
]


def rnd_ua() -> str:
    return random.choice(UA_STRINGS)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def polite_sleep() -> None:
    time.sleep(random.uniform(3, 6))


BASE_URL = "https://dir.indiamart.com/impcat/{cat}.html"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)

SELECTOR_LIST = [
    "[itemtype*='Product']", 
    "li.prd-li",              
    "div.product-card",
    "li.listing-item",       
    "div.prd-cont",           
    "li.mListImg",           
]
WAIT_SELECTOR = ", ".join(SELECTOR_LIST)

FIELDS = [
    "scraped_ts",
    "category",
    "product_name",
    "company",
    "price_raw",
    "city",
    "state",
    "rating",
    "product_url",
]


async def route_block_assets(route: Route) -> None:
    if route.request.resource_type in {"image", "stylesheet", "font"}:
        await route.abort()
    else:
        await route.continue_()


async def navigate(page: Page, url: str, tries: int = 3) -> None:
    """Robust goto with retries & exponential back-off."""
    for attempt in range(1, tries + 1):
        try:
            await page.goto(
                url,
                timeout=180_000,
                wait_until="domcontentloaded",
            )
            return
        except PWTimeout:
            if attempt == tries:
                raise
            wait = 5 * attempt
            print(f"      – nav timeout, retry {attempt}/{tries} after {wait}s …")
            await asyncio.sleep(wait)


async def close_cookie(page: Page) -> None:
    try:
        btn = await page.query_selector("button:has-text('Accept')")
        if btn:
            await btn.click()
    except PWTimeout:
        pass


async def choose_cards(page: Page) -> list[ElementHandle]:
    """Return first selector variant that yields >0 product nodes."""
    for sel in SELECTOR_LIST:
        cards = await page.query_selector_all(sel)
        if cards:
            return cards
    return []


async def fetch_listing(page: Page, url: str, cat: str) -> list[dict]:
    await navigate(page, url)
    await close_cookie(page)

    # gently scroll to trigger lazy-load
    for _ in range(4):
        await page.mouse.wheel(0, 7000)
        polite_sleep()
    await page.wait_for_timeout(4000)

    try:
        await page.wait_for_selector(WAIT_SELECTOR, timeout=100_000)
    except PWTimeout:
        print("    ! none of the selectors appeared (timeout)")

    cards = await choose_cards(page)
    print(f"    → {len(cards)} products")

    if not cards:
        snap = DATA_DIR / f"debug_{slugify(cat)}.html"
        snap.write_bytes((await page.content()).encode("utf-8"))
        return []

    rows: list[dict] = []
    for c in cards:
    
        anchor = await c.query_selector("a[href]")
        if anchor:
            pname = (await anchor.inner_text()) or ""
        else:
            img = await c.query_selector("img[alt]")
            pname = await img.get_attribute("alt") if img else ""

        comp_node = await c.query_selector(
            "span.supplier-cont-name, span.sm-lbl"
        )
        comp = (await comp_node.inner_text()) if comp_node else ""

        price_node = await c.query_selector(
        "span.price, div.prc, span.mPrice"
        )


        price = (await price_node.inner_text()) if price_node else ""

        loc_node = await c.query_selector(
        "span.supplier-location, div.location, span.dashLoc"
        )

        loc = (await loc_node.inner_text()) if loc_node else ""

        rating_node = await c.query_selector("span.star-rat, span.rating")
        rating = (await rating_node.inner_text()) if rating_node else ""

        link = await anchor.get_attribute("href") if anchor else ""

        city, state = ("", "")
        if loc:
            parts = [p.strip() for p in loc.split(",")]
            city, state = (parts + [""])[:2]

        rows.append(
            {
                "scraped_ts": datetime.utcnow().isoformat(timespec="seconds"),
                "category": cat,
                "product_name": pname.strip(),
                "company": comp.strip(),
                "price_raw": price.strip(),
                "city": city,
                "state": state,
                "rating": rating.strip(),
                "product_url": link.strip(),
            }
        )
    return rows


async def crawl(cats: list[str], max_pg: int, headed: bool = False) -> None:
    proxy = os.getenv("PLAYWRIGHT_PROXY")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not headed)
        ctx = await browser.new_context(
            user_agent=rnd_ua(),
            locale="en-US",
            proxy={"server": proxy} if proxy else None,
            viewport={"width": 1280, "height": 720},
        )
        await ctx.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )
        await ctx.route("**/*", route_block_assets)
        page = await ctx.new_page()

        for cat in cats:
            for pg in range(1, max_pg + 1):
                url = BASE_URL.format(cat=cat) + (f"?page={pg}" if pg > 1 else "")
                print(f"[+] {cat} | page {pg}")
                try:
                    rows = await fetch_listing(page, url, cat)
                    _save(rows, cat)
                except Exception as e:
                    print(f"    !! {e}")
                polite_sleep()
        await browser.close()


def _save(rows: list[dict], cat: str) -> None:
    if not rows:
        return
    fp = DATA_DIR / f"{slugify(cat)}.csv"
    header_needed = not fp.exists()
    with fp.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if header_needed:
            writer.writeheader()
        writer.writerows(rows)
    print(f"    ✓ {len(rows)} rows → {fp.name}")

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="IndiaMART category crawler")
    ap.add_argument("--categories", nargs="+", required=True)
    ap.add_argument("--max-pages", type=int, default=2)
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    asyncio.run(crawl(args.categories, args.max_pages, headed=args.headed))
