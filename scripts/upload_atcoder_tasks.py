"""
Upload enriched AtCoder problems to the service via POST /tasks.

Tracks uploaded task keys ("{contest_id}_{letter}", e.g. "abc460_a") in a state
file to avoid duplicates on re-runs. Requires admin credentials to obtain a JWT.

Usage:
    poetry run python scripts/upload_atcoder_tasks.py --username admin --password secret
    poetry run python scripts/upload_atcoder_tasks.py --username admin --password secret -n 10
    poetry run python scripts/upload_atcoder_tasks.py --username admin --password secret --url http://localhost:8000
"""

import argparse
import asyncio
import json
import logging
from pathlib import Path

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

DEFAULT_INPUT = "scripts/atcoder_parser/output_enriched"
DEFAULT_STATE = "scripts/atcoder_parser/uploaded.json"
DEFAULT_URL = "http://localhost:8000"
DEFAULT_DELAY = 0.3


def _load_state(state_path: Path) -> set[str]:
    if state_path.exists():
        return set(json.loads(state_path.read_text(encoding="utf-8")))
    return set()


def _save_state(state_path: Path, uploaded: set[str]) -> None:
    state_path.write_text(
        json.dumps(sorted(uploaded), indent=2),
        encoding="utf-8",
    )


def _task_key(problem: dict) -> str | None:
    """Unique key for an AtCoder task: '{contest_id}_{letter}'."""
    contest_id = problem.get("contest_id")
    letter = problem.get("letter")
    if not contest_id or not letter:
        return None
    return f"{contest_id}_{letter}"


def _build_payload(problem: dict) -> dict | None:
    title = problem.get("statement", {}).get("title", "").strip()
    text = problem.get("enriched_statement", "").strip()

    if not title or not text:
        return None

    # editorials is a list; take the first english text editorial
    editorials = problem.get("editorials") or []
    first = editorials[0] if editorials else {}
    solution = (first.get("content") or "").strip() or None
    solution_url = first.get("url")

    return {
        "title": title,
        "text": text,
        "task_url": problem.get("url"),
        "solution": solution,
        "solution_url": solution_url,
        "comment": None,
    }


async def _login(client: httpx.AsyncClient, base_url: str, username: str, password: str) -> str:
    response = await client.post(
        f"{base_url}/auth/login",
        json={"username": username, "password": password},
    )
    response.raise_for_status()
    return response.json()["access_token"]


async def upload_all(
    input_dir: Path,
    state_path: Path,
    base_url: str,
    username: str,
    password: str,
    delay: float,
    max_tasks: int | None,
) -> None:
    files = sorted(input_dir.glob("problem_*.json"))
    if not files:
        log.warning("No problem_*.json files found in %s", input_dir)
        return

    uploaded = _load_state(state_path)
    log.info("Already uploaded: %d tasks", len(uploaded))

    async with httpx.AsyncClient(timeout=30) as client:
        token = await _login(client, base_url, username, password)
        headers = {"Authorization": f"Bearer {token}"}

        sent = 0
        skipped = 0

        for path in files:
            if max_tasks is not None and sent >= max_tasks:
                break

            problem = json.loads(path.read_text(encoding="utf-8"))
            key = _task_key(problem)

            if key is None:
                log.warning("Skip (missing contest_id/letter): %s", path.name)
                skipped += 1
                continue

            if key in uploaded:
                log.info("Skip (already uploaded): %s", path.name)
                skipped += 1
                continue

            payload = _build_payload(problem)
            if payload is None:
                log.warning("Skip (missing title or enriched_statement): %s", path.name)
                skipped += 1
                continue

            log.info("Uploading %s — %s ...", path.name, payload["title"])
            response = await client.post(
                f"{base_url}/tasks",
                json=payload,
                headers=headers,
            )

            if response.status_code == 201:
                uploaded.add(key)
                _save_state(state_path, uploaded)
                sent += 1
                log.info("OK: %s (id=%s)", path.name, response.json().get("id"))
            else:
                log.error("FAIL %s: %s %s", path.name, response.status_code, response.text)

            if max_tasks is None or sent < max_tasks:
                await asyncio.sleep(delay)

    log.info("Done. Uploaded: %d, Skipped: %d", sent, skipped)


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload enriched AtCoder tasks to the service")
    parser.add_argument("--username", required=True, help="Admin username")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"API base URL (default: {DEFAULT_URL})",
    )
    parser.add_argument(
        "-i", "--input",
        default=DEFAULT_INPUT,
        help=f"Directory with enriched problem_*.json (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--state",
        default=DEFAULT_STATE,
        help=f"Path to uploaded state file (default: {DEFAULT_STATE})",
    )
    parser.add_argument(
        "-d", "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help=f"Delay between requests in seconds (default: {DEFAULT_DELAY})",
    )
    parser.add_argument(
        "-n", "--max",
        type=int,
        default=None,
        metavar="N",
        help="Maximum number of tasks to upload (default: all)",
    )

    args = parser.parse_args()

    asyncio.run(
        upload_all(
            input_dir=Path(args.input),
            state_path=Path(args.state),
            base_url=args.url.rstrip("/"),
            username=args.username,
            password=args.password,
            delay=args.delay,
            max_tasks=args.max,
        )
    )


if __name__ == "__main__":
    main()