# Инструкция по парсингу задач с eolymp.com

## Общая информация

- **URL задачи:** `https://eolymp.com/en/problems/{number}` (number — целое число, например 101, 123)
- **Сайт:** Next.js SPA, рендерится на клиенте через JavaScript. Обычный HTTP-запрос вернёт пустую оболочку — нужен headless-браузер (Playwright, Selenium, Puppeteer).
- **UI-фреймворк:** MUI (Material UI), layout управляется библиотекой FlexLayout.

---

## Что нужно парсить

Для каждой задачи нужно извлечь:

1. **Statement** (условие задачи) — есть всегда
2. **Editorial** (разбор задачи) — может отсутствовать; если нет — задачу пропускаем

---

## Структура страницы

### Навигация по вкладкам

Вкладки (Statement, Discussion, Editorial) находятся внутри контейнера с классом `flexlayout__tabset`. Каждая вкладка — div внутри `flexlayout__tabset_header`:

```
div.flexlayout__tabset
  div.flexlayout__tabset_header
    div  -->  "Statement"
    div  -->  "Discussion"
    div  -->  "Editorial"     <-- может отсутствовать!
```

Текст вкладки лежит во вложенном `div` внутри каждого таба. Определить наличие Editorial можно по тексту: если среди табов нет элемента с текстом "Editorial" — разбора нет, задачу пропускаем.

### Содержимое вкладок

Содержимое каждой вкладки рендерится в отдельном `div.flexlayout__tab` с атрибутом `data-layout-path`:

- **Statement** — первый таб, `data-layout-path="/ts0/t0"`
- **Editorial** — появляется после клика, `data-layout-path="/ts0/t2"` (может варьироваться)

**Важно:** Editorial рендерится только после клика по вкладке. До клика DOM-элемент с контентом разбора не существует.

---

## Парсинг Statement (условие)

Контент statement находится внутри:

```
div.flexlayout__tab[data-layout-path="/ts0/t0"]
  div.flexlayout__tab_moveable
    div.MuiContainer-root
```

### Структура контента Statement

```html
<div class="MuiContainer-root MuiContainer-maxWidthMd">
  <div>
    <!-- Заголовок -->
    <h1 class="..."><span class="ecm-span">Название задачи</span></h1>

    <!-- Метаданные -->
    <div>
      <span>Very easy | Easy | Medium | Hard</span>   <!-- сложность -->
      <button>English</button>                         <!-- язык -->
    </div>

    <!-- Ограничения -->
    <div>
      <span>Execution time limit is X second(s)</span>
      <span>Runtime memory usage limit is X megabytes</span>
    </div>

    <!-- Текст условия — параграфы -->
    <p class="ecm-paragraph">
      <span class="ecm-span">Текст условия...</span>
      <span class="ecm-inline-math">          <!-- формулы KaTeX -->
        <span class="katex">...</span>
      </span>
    </p>

    <!-- Секция Input -->
    <h2>Input</h2>
    <p class="ecm-paragraph">...</p>

    <!-- Секция Output -->
    <h2>Output</h2>
    <p class="ecm-paragraph">...</p>

    <!-- Примеры -->
    <h2>Examples</h2>
    <div>
      <span>Input #1</span>
      <pre class="ui-17wemgl">содержимое входных данных</pre>

      <span>Answer #1</span>
      <pre class="ui-17wemgl">содержимое ответа</pre>
    </div>
    <!-- ...повтор для Input #2, Answer #2 и т.д. -->

    <!-- Статистика -->
    <hr />
    <div>
      <span>Submissions 21K</span>
      <span>Acceptance rate 33%</span>
    </div>
  </div>
</div>
```

### Какие данные извлекать из Statement

| Поле | Как найти | Пример |
|------|-----------|--------|
| **Название** | `h1 span.ecm-span` | "Number of trailing zeros in factorial" |
| **Сложность** | `span.MuiTypography-labelLarge` (текст) | "Very easy", "Medium" |
| **Время** | Текст содержащий "Execution time limit is" | "1 second" |
| **Память** | Текст содержащий "Runtime memory usage limit is" | "128 megabytes" |
| **Условие** | Все `p.ecm-paragraph` до `h2` "Input" | Текст задачи |
| **Input** | `p.ecm-paragraph` после `h2` "Input" | Описание входных данных |
| **Output** | `p.ecm-paragraph` после `h2` "Output" | Описание выходных данных |
| **Примеры** | `pre` элементы, сгруппированные попарно (Input #N / Answer #N) | Пары вход/выход |
| **Формулы** | `span.ecm-inline-math` содержит KaTeX-разметку. Для текстового представления брать `textContent` из `.katex` | "n!", "1 <= n <= 2*10^9" |

### Математические формулы

Формулы рендерятся через KaTeX:

```html
<span class="ecm-inline-math">
  <span class="katex">
    <span class="katex-html" aria-hidden="true">
      <!-- визуальное представление -->
    </span>
  </span>
</span>
```

- Блочные формулы (на отдельной строке): `div.ecm-math > span.katex-display`
- Inline формулы: `span.ecm-inline-math > span.katex`

Для извлечения текста формулы: взять `.textContent` у `span.katex` — KaTeX рендерит читаемый Unicode (например `n!`, `1≤n≤2⋅10^9`).

---

## Парсинг Editorial (разбор)

### Как открыть вкладку Editorial

Editorial рендерится **только после клика** по вкладке. Алгоритм:

1. Найти все элементы внутри `flexlayout__tabset_header` первого tabset
2. Найти элемент с текстом "Editorial"
3. Кликнуть по нему
4. Дождаться появления нового `div.flexlayout__tab` с контентом (можно ждать по наличию `h1` с текстом "Editorial")

### Структура контента Editorial

```html
<div class="flexlayout__tab" data-layout-path="/ts0/t2">
  <div class="flexlayout__tab_moveable">
    <div class="MuiContainer-root MuiContainer-maxWidthMd">
      <h1>Editorial</h1>
      <div>
        <!-- Текст разбора — те же элементы что и в statement -->
        <p class="ecm-paragraph">
          <span class="ecm-span">Текст разбора...</span>
          <span class="ecm-inline-math">...</span>
        </p>

        <!-- Блочные формулы -->
        <div class="ecm-math">
          <span class="katex-display">...</span>
        </div>

        <!-- Может содержать примеры кода -->
        <pre>...</pre>
      </div>
    </div>
  </div>
</div>
```

### Какие данные извлекать из Editorial

| Поле | Как найти |
|------|-----------|
| **Текст разбора** | Все `p.ecm-paragraph` внутри контейнера Editorial |
| **Формулы** | `span.ecm-inline-math` и `div.ecm-math` (аналогично Statement) |
| **Код** | `pre` элементы (если есть) |

---

## Алгоритм парсинга (псевдокод)

```python
from playwright.async_api import async_playwright

async def parse_problem(number: int) -> dict | None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(f"https://eolymp.com/en/problems/{number}")

        # Ждём загрузки контента statement
        await page.wait_for_selector("div.flexlayout__tab h1")

        # 1. Проверяем наличие вкладки Editorial
        tabs = await page.query_selector_all(
            "div.flexlayout__tabset_header div"
        )
        has_editorial = False
        editorial_tab = None
        for tab in tabs:
            text = await tab.text_content()
            if text and "Editorial" in text:
                has_editorial = True
                editorial_tab = tab
                break

        if not has_editorial:
            await browser.close()
            return None  # Пропускаем задачу без разбора

        # 2. Парсим Statement
        statement_div = await page.query_selector(
            'div.flexlayout__tab[data-layout-path="/ts0/t0"] '
            '.MuiContainer-root'
        )
        statement = await extract_statement(statement_div)

        # 3. Кликаем на Editorial и ждём загрузки
        await editorial_tab.click()
        await page.wait_for_selector(
            'div.flexlayout__tab h1:text("Editorial")'
        )

        # 4. Парсим Editorial
        # Находим таб, начинающийся с "Editorial"
        editorial_tabs = await page.query_selector_all("div.flexlayout__tab")
        editorial_div = None
        for tab in editorial_tabs:
            h1 = await tab.query_selector("h1")
            if h1:
                text = await h1.text_content()
                if text and "Editorial" in text:
                    editorial_div = tab.query_selector(".MuiContainer-root")
                    break

        editorial = await extract_editorial(editorial_div)

        await browser.close()
        return {"statement": statement, "editorial": editorial}


async def extract_statement(container) -> dict:
    """Извлекает данные из контейнера Statement."""
    title_el = await container.query_selector("h1 span.ecm-span")
    title = await title_el.text_content() if title_el else ""

    # Сложность
    difficulty_el = await container.query_selector(
        "span.MuiTypography-labelLarge"
    )
    difficulty = await difficulty_el.text_content() if difficulty_el else ""

    # Ограничения — ищем по тексту
    all_text = await container.text_content()
    time_limit = extract_between(all_text, "Execution time limit is ", " second")
    memory_limit = extract_between(
        all_text, "Runtime memory usage limit is ", " megabyte"
    )

    # Секции текста (условие, input, output)
    # Вариант: получить innerHTML и распарсить через BeautifulSoup
    inner_html = await container.inner_html()
    sections = parse_sections_from_html(inner_html)

    # Примеры
    examples = []
    pres = await container.query_selector_all("pre")
    for i in range(0, len(pres), 2):
        inp = await pres[i].text_content()
        ans = await pres[i + 1].text_content() if i + 1 < len(pres) else ""
        examples.append({"input": inp.strip(), "answer": ans.strip()})

    return {
        "title": title,
        "difficulty": difficulty,
        "time_limit": time_limit,
        "memory_limit": memory_limit,
        "sections": sections,
        "examples": examples,
    }


async def extract_editorial(container) -> dict:
    """Извлекает текст разбора из контейнера Editorial."""
    inner_html = await container.inner_html()
    # Парсим HTML через BeautifulSoup, извлекаем текст и формулы
    content = parse_editorial_from_html(inner_html)
    return {"content": content}
```

---

## Вспомогательный парсинг HTML (BeautifulSoup)

```python
from bs4 import BeautifulSoup

def parse_sections_from_html(html: str) -> dict:
    """Разбивает HTML statement на секции по h2-заголовкам."""
    soup = BeautifulSoup(html, "html.parser")
    sections = {}
    current_section = "description"
    sections[current_section] = []

    # Пропускаем h1 (заголовок) и метаданные, начинаем с первого p.ecm-paragraph
    for el in soup.find_all(["h2", "p", "div", "pre"]):
        if el.name == "h2":
            current_section = el.get_text(strip=True).lower()
            sections[current_section] = []
        elif el.get("class") and "ecm-paragraph" in el.get("class", []):
            text = extract_text_with_math(el)
            sections.setdefault(current_section, []).append(text)

    return sections


def extract_text_with_math(element) -> str:
    """
    Извлекает текст, заменяя KaTeX-формулы их текстовым представлением.
    """
    result = []
    for child in element.children:
        if hasattr(child, "get") and child.get("class"):
            classes = child.get("class", [])
            if "ecm-inline-math" in classes:
                # Берём textContent из .katex
                katex = child.find(class_="katex")
                result.append(katex.get_text() if katex else "")
            elif "ecm-span" in classes:
                result.append(child.get_text())
            else:
                result.append(child.get_text())
        elif isinstance(child, str):
            result.append(child)
        else:
            result.append(child.get_text())
    return "".join(result)


def parse_editorial_from_html(html: str) -> str:
    """Извлекает текст editorial с формулами."""
    soup = BeautifulSoup(html, "html.parser")
    parts = []
    for el in soup.find_all(["p", "div", "pre"]):
        if el.get("class") and "ecm-paragraph" in el.get("class", []):
            parts.append(extract_text_with_math(el))
        elif el.get("class") and "ecm-math" in el.get("class", []):
            katex = el.find(class_="katex")
            if katex:
                parts.append("\n" + katex.get_text() + "\n")
    return "\n".join(parts)
```

---

## Важные нюансы

1. **JavaScript-рендеринг.** Страница — SPA. Без headless-браузера контент не получить. Используй Playwright (рекомендуется) или Selenium.

2. **Ожидание загрузки.** После `goto()` и после клика на вкладку нужно явно ждать появления контента (`wait_for_selector`). Рекомендуемый селектор для statement: `div.flexlayout__tab h1`, для editorial: появление нового `div.flexlayout__tab`.

3. **`data-layout-path` может меняться.** Не привязывайся жёстко к `/ts0/t2` для Editorial. Лучше искать `div.flexlayout__tab`, внутри которого `h1` содержит текст "Editorial".

4. **CSS-классы с хешами.** Классы вида `ui-17wemgl` генерируются MUI/Emotion и **могут меняться** между деплоями. Надёжные селекторы:
   - `div.flexlayout__tab` — стабильный (из библиотеки FlexLayout)
   - `h1`, `h2`, `p.ecm-paragraph`, `span.ecm-span`, `span.ecm-inline-math` — стабильные (контентные классы eolymp)
   - `pre` — примеры ввода/вывода
   - `div.ecm-math` — блочные формулы
   - `span.katex` — рендер формул

5. **MUI-классы** (`MuiTypography-labelLarge`, `MuiContainer-root` и т.д.) — относительно стабильны, но могут менять версию. Используй как fallback.

6. **Язык страницы.** URL `/en/problems/...` загружает английскую версию. Для русской: `/ru/problems/...`.

7. **Rate limiting.** Добавляй задержку между запросами (1-2 секунды), чтобы не быть заблокированным.

8. **Отсутствие Editorial.** Если вкладки "Editorial" нет в хедере табсета — задачу пропускаем (`return None`).

---

## Стабильные CSS-селекторы (рекомендуемые)

```
# Контейнер вкладок
div.flexlayout__tabset_header      — заголовки табов (Statement/Discussion/Editorial)
div.flexlayout__tab                — контент текущей вкладки

# Контентные элементы (стабильные классы eolymp)
h1 span.ecm-span                  — название задачи
p.ecm-paragraph                   — параграф текста
span.ecm-span                     — обычный текст внутри параграфа
span.ecm-inline-math > span.katex — inline-формула
div.ecm-math > span.katex-display — блочная формула
h2                                — заголовки секций (Input, Output, Examples)
pre                               — примеры ввода/вывода (чередуются: input, answer, input, answer...)
```