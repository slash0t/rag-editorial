"""
Enrich eolymp problem statements using LLM normalization.

Reads problem_*.json from input dir, adds `enriched_statement` field,
writes results to output dir.

Usage:
    poetry run python -m scripts.enrich_tasks
    poetry run python -m scripts.enrich_tasks -i scripts/eolymp_parser/output -o scripts/eolymp_parser/output_enriched
    poetry run python -m scripts.enrich_tasks --in-place        # overwrite input files
    poetry run python -m scripts.enrich_tasks --skip-existing   # skip already enriched
    poetry run python -m scripts.enrich_tasks -n 10             # enrich at most 10 tasks
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.env import load_env

load_env()

from app.container import APP_CONTAINER
from app.domain.models.query import RawQuery

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = APP_CONTAINER.logger()

DEFAULT_INPUT = "scripts/eolymp_parser/output"
DEFAULT_OUTPUT = "scripts/eolymp_parser/output_enriched"
DEFAULT_DELAY = 0.5


def _build_statement_text(problem: dict) -> str:
    stmt = problem.get("statement", {})
    title = stmt.get("title", "").strip()
    sections = stmt.get("sections", {})

    parts: list[str] = []
    if title:
        parts.append(f"Title: {title}")

    for section_name in ("description", "input", "output"):
        lines = sections.get(section_name, [])
        if lines:
            joined = "\n".join(lines).strip()
            parts.append(f"{section_name.capitalize()}:\n{joined}")

    time_limit = stmt.get("time_limit", "")
    memory_limit = stmt.get("memory_limit", "")
    if time_limit or memory_limit:
        limits = ", ".join(x for x in [time_limit, memory_limit] if x)
        parts.append(f"Limits: {limits}")

    return "\n\n".join(parts)


async def enrich_all(
    input_dir: Path,
    output_dir: Path,
    delay: float,
    skip_existing: bool,
    in_place: bool,
    max_tasks: int | None,
) -> None:
    enricher = APP_CONTAINER.enricher()

    files = sorted(input_dir.glob("problem_*.json"))
    if not files:
        log.warning("No problem_*.json files found in %s", input_dir)
        return

    if not in_place:
        output_dir.mkdir(parents=True, exist_ok=True)

    enriched = 0
    skipped = 0

    for path in files:
        if max_tasks is not None and enriched >= max_tasks:
            break

        out_path = path if in_place else output_dir / path.name
        problem = json.loads(path.read_text(encoding="utf-8"))

        if skip_existing and problem.get("enriched_statement"):
            log.info("Skip (already enriched): %s", path.name)
            skipped += 1
            continue

        text = _build_statement_text(problem)
        if not text.strip():
            log.warning("Skip (empty statement): %s", path.name)
            skipped += 1
            continue

        log.info("Enriching %s ...", path.name)
        result = await enricher.enrich(RawQuery(text=text))

        problem["enriched_statement"] = result
        out_path.write_text(
            json.dumps(problem, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        enriched += 1

        if max_tasks is None or enriched < max_tasks:
            await asyncio.sleep(delay)

    log.info("Done. Enriched: %d, Skipped: %d", enriched, skipped)


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich eolymp problems with LLM")
    parser.add_argument(
        "-i", "--input",
        default=DEFAULT_INPUT,
        help=f"Input directory with problem_*.json (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "-o", "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output directory (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite input files instead of writing to output dir",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip files that already have enriched_statement",
    )
    parser.add_argument(
        "-d", "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help=f"Delay between LLM requests in seconds (default: {DEFAULT_DELAY})",
    )
    parser.add_argument(
        "-n", "--max",
        type=int,
        default=None,
        metavar="N",
        help="Maximum number of tasks to enrich (default: all)",
    )

    args = parser.parse_args()

    asyncio.run(
        enrich_all(
            input_dir=Path(args.input),
            output_dir=Path(args.output),
            delay=args.delay,
            skip_existing=args.skip_existing,
            in_place=args.in_place,
            max_tasks=args.max,
        )
    )


if __name__ == "__main__":
    main()