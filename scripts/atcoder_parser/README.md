# AtCoder Parser

Парсер задач и разборов (editorial) с сайта [AtCoder](https://atcoder.jp).
Парсит **только английские** условия и разборы. **Видео-разборы пропускаются**,
**код решений в разборах не сохраняется**.

Подробное описание структуры страниц — в [`docs/atcoder-parser-guide.md`](../../docs/atcoder-parser-guide.md).

## Что парсится

Контест задаётся id вида `{тип}{номер}` — тип (`abc`, `arc`, `agc`, ...) хранится
отдельно от номера, т.к. на сайте есть разные серии контестов.

Внутри одного контеста:

- **Tasks** (`/contests/{id}/tasks`) — список задач, для каждой берём условие со страницы задачи.
- **Editorial** (`/contests/{id}/editorial`) — индекс разборов; внутри отдельные ссылки на разбор каждой задачи.

Для каждой задачи извлекается условие + один или несколько английских текстовых разборов.
Задача без английского текстового разбора пропускается.

## Что пропускается

- **Японские разборы** (`<li class="lang-other">`).
- **Видео-разборы** (ссылки `/jump?url=...` с иконкой `glyphicon-film`, напр. в `abc300`).
- **Код решений** в разборах (`<pre class="prettyprint linenums">`).

## Установка

```bash
poetry install
```

(Сетевые запросы идут через `urllib` из стандартной библиотеки, парсинг — через `beautifulsoup4`.
Headless-браузер не нужен — страницы AtCoder отдаются сервером готовыми.)

## Запуск

```bash
# Один контест
poetry run python -m scripts.atcoder_parser abc460

# Несколько контестов (через запятую)
poetry run python -m scripts.atcoder_parser abc460,arc180,agc065

# Диапазон номеров одного типа
poetry run python -m scripts.atcoder_parser abc460-462

# Указать папку вывода
poetry run python -m scripts.atcoder_parser abc460 -o ./parsed

# Задержка между запросами (секунды)
poetry run python -m scripts.atcoder_parser abc460-462 -d 2.0
```

| Флаг | Описание |
|------|----------|
| `-o`, `--output` | Папка вывода (по умолчанию `scripts/atcoder_parser/output`) |
| `-d`, `--delay` | Задержка между запросами в секундах (по умолчанию `1.0`) |

> **Вежливость к сайту.** AtCoder ограничивает агрессивный парсинг. Не уменьшайте
> задержку без необходимости.

## Выходной формат

Один файл `problem_{contest_id}_{letter}.json` на задачу:

```json
{
  "contest_id": "abc460",
  "contest_type": "abc",
  "contest_number": 460,
  "letter": "a",
  "url": "https://atcoder.jp/contests/abc460/tasks/abc460_a",
  "statement": {
    "title": "Mod While Positive",
    "time_limit": "2 sec",
    "memory_limit": "1024 MiB",
    "sections": {
      "Problem Statement": "You are given positive integers ...",
      "Constraints": "1 \\leq N, M \\leq 1000 ...",
      "Input": "The input is given from Standard Input ...",
      "Output": "Output the answer.",
      "Sample Input 1": "8 5",
      "Sample Output 1": "3 ..."
    }
  },
  "editorials": [
    {
      "url": "https://atcoder.jp/contests/abc460/editorial/21036",
      "author": "en_translator",
      "content": "Actually repeatedly perform the operation while \\(M\\) is not \\(0\\) ..."
    }
  ]
}
```

Заметки по формату:

- Математика сохраняется как есть, в виде MathJax: `\( ... \)`.
- Примеры ввода/вывода — это секции `Sample Input N` / `Sample Output N`.
  Пояснение к примеру AtCoder хранит в том же блоке, поэтому оно попадает в `Sample Output N`.
- У задачи может быть несколько английских разборов (official + user) — все в массиве `editorials`.

## Обогащение задач (LLM enrichment)

Скрипт `scripts/enrich_atcoder_tasks.py` убирает нарративную обёртку из условий и
приводит их к единому абстрактному виду — чтобы похожие задачи с разными историями
давали близкие эмбеддинги. Добавляет поле `enriched_statement` в каждый `problem_*.json`.

В обогащение идут только секции `Problem Statement`, `Constraints`, `Input`, `Output`
(без примеров `Sample Input/Output`).

```bash
# Проверка на маленьком примере
poetry run python -m scripts.atcoder_parser abc460 -o scripts/atcoder_parser/test_output
poetry run python -m scripts.enrich_atcoder_tasks -i scripts/atcoder_parser/test_output -o scripts/atcoder_parser/test_enriched -n 3

# Обогатить все задачи (читает из output/, пишет в output_enriched/)
poetry run python -m scripts.enrich_atcoder_tasks

# Пропустить уже обогащённые (продолжение после обрыва)
poetry run python -m scripts.enrich_atcoder_tasks --skip-existing

# Перезаписать исходные файлы (in-place)
poetry run python -m scripts.enrich_atcoder_tasks --in-place --skip-existing
```

| Флаг | Описание |
|------|----------|
| `-i` | Входная папка (по умолчанию `scripts/atcoder_parser/output`) |
| `-o` | Выходная папка (по умолчанию `scripts/atcoder_parser/output_enriched`) |
| `--in-place` | Перезаписывать исходные файлы |
| `--skip-existing` | Пропускать файлы с уже заполненным `enriched_statement` |
| `-d` | Задержка между LLM-запросами в секундах (по умолчанию `0.5`) |
| `-n` | Максимальное число задач для обогащения |

## Загрузка задач в сервис

Скрипт `scripts/upload_atcoder_tasks.py` читает обогащённые файлы из `output_enriched/`
и отправляет их через `POST /tasks`. Требует запущенного сервиса и учётные данные
администратора. В качестве `solution` берётся первый английский текстовый разбор задачи.

**Идемпотентность:** ключи уже отправленных задач (`{contest_id}_{letter}`, напр. `abc460_a`)
сохраняются в `scripts/atcoder_parser/uploaded.json`. При повторном запуске они пропускаются.

```bash
# Проверка на маленьком примере
poetry run python scripts/upload_atcoder_tasks.py --username admin --password secret -n 3

# Загрузить все задачи из output_enriched/
poetry run python scripts/upload_atcoder_tasks.py --username admin --password secret

# Нестандартный адрес сервиса
poetry run python scripts/upload_atcoder_tasks.py --username admin --password secret --url http://localhost:8000
```

| Флаг | Описание |
|------|----------|
| `--username` | Логин администратора (обязательно) |
| `--password` | Пароль администратора (обязательно) |
| `--url` | Базовый URL сервиса (по умолчанию `http://localhost:8000`) |
| `-i` | Папка с обогащёнными файлами (по умолчанию `scripts/atcoder_parser/output_enriched`) |
| `--state` | Файл состояния (по умолчанию `scripts/atcoder_parser/uploaded.json`) |
| `-d` | Задержка между запросами в секундах (по умолчанию `0.3`) |
| `-n` | Максимальное число задач для загрузки |

## Структура пакета

| Файл | Назначение |
|------|------------|
| `parser.py` | сеть, оркестрация по контестам, CLI |
| `html_extractor.py` | чистый разбор HTML (без сети): список задач, условие, индекс разборов, текст разбора |
| `__main__.py` | точка входа для `python -m` |