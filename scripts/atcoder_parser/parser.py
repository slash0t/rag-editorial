import argparse
import json
import logging
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from .html_extractor import (
    parse_editorial_detail,
    parse_editorial_index,
    parse_statement,
    parse_task_list,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

BASE_URL = "https://atcoder.jp"
USER_AGENT = "Mozilla/5.0 (compatible; rag-algo-solver/1.0)"
DEFAULT_DELAY = 1.0
DEFAULT_OUTPUT = "scripts/atcoder_parser/output"

# a contest id is a type (abc/arc/agc/...) plus a number
CONTEST_RE = re.compile(r"^([a-z]+)(\d+)$")


def fetch(url: str, retries: int = 3, backoff: float = 2.0) -> str | None:
    """GET a page as English HTML, with simple retry."""
    sep = "&" if "?" in url else "?"
    full = f"{url}{sep}lang=en"
    req = urllib.request.Request(full, headers={"User-Agent": USER_AGENT})

    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            log.warning("Fetch failed (%d/%d) %s: %s", attempt, retries, full, exc)
            if attempt < retries:
                time.sleep(backoff * attempt)

    log.error("Giving up on %s", full)
    return None


def parse_contest(contest_id: str, delay: float) -> list[dict]:
    """Parse one contest into a list of per-task records."""
    m = CONTEST_RE.match(contest_id)
    if not m:
        log.error("Bad contest id: %s", contest_id)
        return []
    contest_type, number = m.group(1), int(m.group(2))

    log.info("Contest %s: loading task list...", contest_id)
    tasks_html = fetch(f"{BASE_URL}/contests/{contest_id}/tasks")
    if not tasks_html:
        return []
    tasks = parse_task_list(tasks_html, contest_id)
    if not tasks:
        log.warning("Contest %s: no tasks found", contest_id)
        return []

    log.info("Contest %s: loading editorial index...", contest_id)
    ed_html = fetch(f"{BASE_URL}/contests/{contest_id}/editorial")
    editorials = parse_editorial_index(ed_html, contest_id) if ed_html else {}

    records: list[dict] = []
    for task in tasks:
        letter = task["letter"]
        time.sleep(delay)

        log.info("  task %s-%s: statement...", contest_id, letter)
        stmt_html = fetch(task["url"])
        sections = parse_statement(stmt_html) if stmt_html else {}

        ed_urls = editorials.get(letter, [])
        if not ed_urls:
            log.info("  task %s-%s: no english text editorial, skipping", contest_id, letter)
            continue

        editorial_texts: list[dict] = []
        for ed_url in ed_urls:
            time.sleep(delay)
            log.info("  task %s-%s: editorial %s", contest_id, letter, ed_url)
            detail_html = fetch(ed_url)
            if not detail_html:
                continue
            detail = parse_editorial_detail(detail_html)
            if detail["content"]:
                editorial_texts.append({"url": ed_url, **detail})

        if not editorial_texts:
            log.info("  task %s-%s: editorial had no text, skipping", contest_id, letter)
            continue

        records.append(
            {
                "contest_id": contest_id,
                "contest_type": contest_type,
                "contest_number": number,
                "letter": letter,
                "url": task["url"],
                "statement": {
                    "title": task["title"],
                    "time_limit": task["time_limit"],
                    "memory_limit": task["memory_limit"],
                    "sections": sections,
                },
                "editorials": editorial_texts,
            }
        )

    return records


def run(contest_ids: list[str], output_dir: Path, delay: float):
    output_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    for contest_id in contest_ids:
        records = parse_contest(contest_id, delay)
        for rec in records:
            out_file = output_dir / f"problem_{rec['contest_id']}_{rec['letter']}.json"
            out_file.write_text(
                json.dumps(rec, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            log.info("Saved %s", out_file)
            total += 1

    log.info("Done. Saved %d task(s).", total)


def expand_contest_ids(spec: str) -> list[str]:
    """'abc460,abc461' or 'abc460-462' -> [abc460, abc461, abc462]."""
    ids: list[str] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = part.split("-", 1)
            m = CONTEST_RE.match(lo)
            if not m:
                raise ValueError(f"Bad contest id: {lo}")
            ctype, start = m.group(1), int(m.group(2))
            # hi may be a bare number ('abc460-462') or full id ('abc460-abc462')
            hi_m = CONTEST_RE.match(hi)
            end = int(hi_m.group(2)) if hi_m else int(hi)
            ids.extend(f"{ctype}{n}" for n in range(start, end + 1))
        else:
            ids.append(part)
    return ids


def main():
    parser = argparse.ArgumentParser(description="AtCoder tasks + editorial parser")
    parser.add_argument(
        "contests",
        help="Contest ids: 'abc460', list 'abc460,arc180', range 'abc460-462'",
    )
    parser.add_argument(
        "-o", "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output directory (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "-d", "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help=f"Delay between requests in seconds (default: {DEFAULT_DELAY})",
    )

    args = parser.parse_args()
    contest_ids = expand_contest_ids(args.contests)
    run(contest_ids, Path(args.output), args.delay)


if __name__ == "__main__":
    main()