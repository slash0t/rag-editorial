from bs4 import BeautifulSoup, NavigableString, Tag


def extract_text_with_math(element: Tag) -> str:
    parts: list[str] = []
    for child in element.children:
        if isinstance(child, NavigableString):
            parts.append(str(child))
            continue
        if not isinstance(child, Tag):
            continue
        classes = child.get("class", [])
        if "ecm-inline-math" in classes:
            katex = child.find(class_="katex")
            parts.append(katex.get_text() if katex else "")
        elif "ecm-span" in classes:
            parts.append(child.get_text())
        else:
            parts.append(child.get_text())
    return "".join(parts)


def parse_sections(html: str) -> dict[str, list[str]]:
    soup = BeautifulSoup(html, "html.parser")
    sections: dict[str, list[str]] = {}
    current = "description"
    sections[current] = []

    content_div = soup.find("div", class_="MuiContainer-root")
    if not content_div:
        return sections

    for el in content_div.find_all(["h2", "p", "div"], recursive=True):
        if el.name == "h2":
            current = el.get_text(strip=True).lower()
            if current == "examples":
                break
            sections[current] = []
        elif "ecm-paragraph" in el.get("class", []):
            text = extract_text_with_math(el)
            if text.strip():
                sections.setdefault(current, []).append(text)
        elif "ecm-math" in el.get("class", []):
            katex = el.find(class_="katex")
            if katex:
                sections.setdefault(current, []).append(katex.get_text())

    return sections


def parse_editorial_content(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    parts: list[str] = []

    container = soup.find("div", class_="MuiContainer-root")
    if not container:
        return ""

    for el in container.find_all(["p", "div", "pre"], recursive=True):
        classes = el.get("class", [])
        if "ecm-paragraph" in classes:
            parts.append(extract_text_with_math(el))
        elif "ecm-math" in classes:
            katex = el.find(class_="katex")
            if katex:
                parts.append(katex.get_text())
        elif el.name == "pre" and not el.find_parent(class_="ecm-paragraph"):
            code = el.get_text().strip()
            if code:
                parts.append(f"```\n{code}\n```")

    return "\n".join(parts)
