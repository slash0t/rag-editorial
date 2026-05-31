"""Pure HTML -> data extraction for AtCoder pages (no network)."""

import re

from bs4 import BeautifulSoup, Tag

# slug like "abc460_a" / "abc460_ex" -> trailing letter part
_SLUG_RE = re.compile(r"_([a-z0-9]+)$")


def _letter_from_task_href(href: str) -> str | None:
    """abc460_a -> 'a', abc460_ex -> 'ex'."""
    slug = href.rstrip("/").rsplit("/", 1)[-1]
    m = _SLUG_RE.search(slug)
    return m.group(1) if m else None


def parse_task_list(html: str, contest_id: str) -> list[dict]:
    """Tasks table -> [{letter, title, url, time_limit, memory_limit}]."""
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("table.table tbody tr")
    tasks: list[dict] = []

    for row in rows:
        cells = row.find_all("td", recursive=False)
        if len(cells) < 2:
            continue

        letter_link = cells[0].find("a")
        title_link = cells[1].find("a")
        if not letter_link or not title_link:
            continue

        href = title_link.get("href", "")
        letter = _letter_from_task_href(href) or letter_link.get_text(strip=True).lower()

        tasks.append(
            {
                "letter": letter,
                "title": title_link.get_text(strip=True),
                "url": f"https://atcoder.jp{href}",
                "time_limit": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                "memory_limit": cells[3].get_text(strip=True) if len(cells) > 3 else "",
            }
        )

    return tasks


def parse_statement(html: str) -> dict[str, str]:
    """#task-statement span.lang-en -> {section_name: text}.

    Sections keyed by their <h3> (Problem Statement, Constraints, Input,
    Output, Sample Input N, Sample Output N).
    """
    soup = BeautifulSoup(html, "html.parser")

    block = soup.select_one("#task-statement span.lang-en")
    if block is None:  # single-language contests have no lang span
        block = soup.select_one("#task-statement")
    if block is None:
        return {}

    sections: dict[str, str] = {}
    for part in block.select("div.part"):
        h3 = part.find("h3")
        if not h3:
            continue
        name = h3.get_text(strip=True)
        # text of the part without the heading itself
        h3.extract()
        text = part.get_text("\n", strip=True)
        if text:
            sections[name] = text

    return sections


def parse_editorial_index(html: str, contest_id: str) -> dict[str, list[str]]:
    """Editorial index -> {letter: [editorial_url, ...]}.

    Keeps only ENGLISH TEXT editorials:
      - internal link /contests/{id}/editorial/<number>
      - NOT a video / external (/jump? or glyphicon-film)
      - NOT a Japanese entry (<li class="lang-other">)
    """
    soup = BeautifulSoup(html, "html.parser")
    internal_re = re.compile(rf"^/contests/{re.escape(contest_id)}/editorial/\d+$")

    result: dict[str, list[str]] = {}

    for h3 in soup.find_all("h3"):
        task_link = h3.find("a", href=re.compile(r"/tasks/"))
        if not task_link:  # e.g. "Overall Editorial" -> skip
            continue
        letter = _letter_from_task_href(task_link.get("href", ""))
        if not letter:
            continue

        section = h3.find_next("div", class_="editorial-section")
        if not section:
            continue

        urls: list[str] = []
        for li in section.select("li"):
            classes = li.get("class", [])
            if "lang-other" in classes:  # Japanese
                continue
            a = li.find("a", href=True)
            if not a:
                continue
            if a.find("span", class_="glyphicon-film"):  # video
                continue
            href = a["href"]
            if not internal_re.match(href):  # external / video
                continue
            urls.append(f"https://atcoder.jp{href}")

        if urls:
            result[letter] = urls

    return result


def parse_editorial_detail(html: str) -> dict[str, str]:
    """Editorial detail page -> {author, content}.

    Body is the block between <hr class="mt-1"> and <div class="clearfix">.
    Sample/solution code (<pre class="prettyprint">) is dropped.
    """
    soup = BeautifulSoup(html, "html.parser")

    title = soup.select_one("h2.mt-1")
    author = ""
    if title:
        author_link = title.select_one("span.small a.username")
        if author_link:
            author = author_link.get_text(strip=True)

    hr = soup.find("hr", class_="mt-1")
    if not hr:
        return {"author": author, "content": ""}

    parts: list[str] = []
    for sib in hr.next_siblings:
        if not isinstance(sib, Tag):
            continue
        if "clearfix" in sib.get("class", []):  # footer reached
            break
        # drop code blocks before reading text
        for pre in sib.select("pre.prettyprint, pre.linenums"):
            pre.decompose()
        text = sib.get_text("\n", strip=True)
        if text:
            parts.append(text)

    return {"author": author, "content": "\n\n".join(parts)}