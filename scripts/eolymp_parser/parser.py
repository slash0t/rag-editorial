import asyncio
import json
import logging
import re
import sys
from pathlib import Path

from playwright.async_api import Page, async_playwright

from .html_extractor import parse_editorial_content, parse_sections

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

BASE_URL = "https://eolymp.com/en/problems"
STATEMENT_SELECTOR = 'div.flexlayout__tab[data-layout-path="/ts0/t0"]'
TAB_BUTTON_SELECTOR = "div.flexlayout__tab_button"
TAB_BUTTON_TEXT_SELECTOR = "div.flexlayout__tab_button_content"
DEFAULT_DELAY = 1.5

EDITORIAL_WAIT_JS = """() => {
    const tabs = document.querySelectorAll('div.flexlayout__tab');
    for (const t of tabs) {
        const h1 = t.querySelector('h1');
        if (h1 && h1.textContent.includes('Editorial')) return true;
    }
    return false;
}"""


async def _has_editorial_tab(page: Page) -> bool:
    buttons = await page.query_selector_all(TAB_BUTTON_TEXT_SELECTOR)
    for btn in buttons:
        text = (await btn.text_content() or "").strip()
        if text == "Editorial":
            return True
    return False


async def _click_editorial(page: Page) -> bool:
    buttons = await page.query_selector_all(TAB_BUTTON_SELECTOR)
    for btn in buttons:
        content = await btn.query_selector(TAB_BUTTON_TEXT_SELECTOR)
        if not content:
            continue
        text = (await content.text_content() or "").strip()
        if text == "Editorial":
            await btn.click()
            try:
                await page.wait_for_function(EDITORIAL_WAIT_JS, timeout=10000)
                return True
            except Exception:
                log.warning("Editorial tab clicked but content not loaded")
                return False
    return False


async def _find_editorial_tab(page: Page):
    tabs = await page.query_selector_all("div.flexlayout__tab")
    for tab in tabs:
        h1 = await tab.query_selector("h1")
        if h1:
            text = await h1.text_content()
            if text and "Editorial" in text:
                return tab
    return None


async def _extract_statement(page: Page) -> dict:
    container = await page.query_selector(f"{STATEMENT_SELECTOR}")
    if not container:
        return {}

    html = await container.inner_html()

    title_el = await container.query_selector("h1 span.ecm-span")
    title = (await title_el.text_content()).strip() if title_el else ""

    all_text = await container.text_content() or ""
    time_match = re.search(r"Execution time limit is (.+?) second", all_text)
    time_limit = time_match.group(1).strip() + "s" if time_match else ""

    mem_match = re.search(r"Runtime memory usage limit is (.+?) megabyte", all_text)
    memory_limit = mem_match.group(1).strip() + " MB" if mem_match else ""

    sections = parse_sections(html)

    return {
        "title": title,
        "time_limit": time_limit,
        "memory_limit": memory_limit,
        "sections": sections,
    }


async def _extract_editorial(page: Page) -> dict:
    tab = await _find_editorial_tab(page)
    if not tab:
        return {"content": ""}
    html = await tab.inner_html()
    content = parse_editorial_content(html)
    return {"content": content}


async def parse_problem(page: Page, number: int) -> dict | None:
    url = f"{BASE_URL}/{number}"
    log.info("Loading problem %d...", number)

    await page.goto(url, wait_until="domcontentloaded")
    try:
        await page.wait_for_selector(f"{STATEMENT_SELECTOR} h1", timeout=15000)
    except Exception:
        log.error("Problem %d: page load timeout", number)
        return None

    if not await _has_editorial_tab(page):
        log.info("Problem %d: no editorial, skipping", number)
        return None

    statement = await _extract_statement(page)

    if not await _click_editorial(page):
        log.warning("Problem %d: editorial exists but failed to open", number)
        return None

    editorial = await _extract_editorial(page)

    return {
        "number": number,
        "url": url,
        "statement": statement,
        "editorial": editorial,
    }


async def run(
    problem_numbers: list[int],
    output_dir: Path,
    delay: float = DEFAULT_DELAY,
    headless: bool = True,
):
    output_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        page = await browser.new_page()

        parsed = 0
        skipped = 0

        for i, num in enumerate(problem_numbers):
            result = await parse_problem(page, num)

            if result is None:
                skipped += 1
            else:
                out_file = output_dir / f"problem_{num}.json"
                out_file.write_text(
                    json.dumps(result, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                parsed += 1
                log.info("Saved %s", out_file)

            if i < len(problem_numbers) - 1:
                await asyncio.sleep(delay)

        await browser.close()

    log.info("Done. Parsed: %d, Skipped (no editorial): %d", parsed, skipped)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="eolymp.com problem parser")
    parser.add_argument(
        "problems",
        help="Problem numbers: comma-separated (1,2,3) or range (1-100)",
    )
    parser.add_argument(
        "-o", "--output",
        default="scripts/eolymp_parser/output",
        help="Output directory (default: scripts/eolymp_parser/output)",
    )
    parser.add_argument(
        "-d", "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help="Delay between requests in seconds (default: 1.5)",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run browser in headed mode (visible window)",
    )

    args = parser.parse_args()

    nums: list[int] = []
    for part in args.problems.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            nums.extend(range(int(start), int(end) + 1))
        else:
            nums.append(int(part))

    asyncio.run(run(nums, Path(args.output), args.delay, headless=not args.headed))


if __name__ == "__main__":
    main()
