# eolymp.com Parser

Парсер задач и разборов (editorial) с сайта eolymp.com.
Задачи без editorial пропускаются. Результат сохраняется в JSON.

## Установка

```bash
poetry install
poetry run playwright install chromium
```

## Запуск

```bash
# Одна задача
poetry run python -m scripts.eolymp_parser 123

# Несколько задач
poetry run python -m scripts.eolymp_parser 101,123,456

# Диапазон
poetry run python -m scripts.eolymp_parser 1-200

# Комбинация
poetry run python -m scripts.eolymp_parser 1-50,123,200-210

# Указать папку вывода
poetry run python -m scripts.eolymp_parser 1-100 -o ./parsed_problems

# Видимый браузер (для отладки)
poetry run python -m scripts.eolymp_parser 123 --headed

# Задержка между запросами (секунды)
poetry run python -m scripts.eolymp_parser 1-100 -d 2.0
```

## Обогащение задач (LLM enrichment)

Скрипт `scripts/enrich_tasks.py` убирает нарративную обёртку из условий задач и приводит их к единому абстрактному виду — чтобы похожие задачи с разными историями давали близкие эмбеддинги.

Добавляет поле `enriched_statement` в каждый `problem_*.json`.

### Проверка на маленьком примере

Спарсите 2–3 задачи в отдельную папку, затем обогатите:

```bash
poetry run python -m scripts.eolymp_parser 1,2,3 -o scripts/eolymp_parser/test_output
poetry run python -m scripts.enrich_tasks -i scripts/eolymp_parser/test_output -o scripts/eolymp_parser/test_enriched -n 3
```

Проверьте результат:

```bash
cat scripts/eolymp_parser/test_enriched/problem_1.json
```

Поле `enriched_statement` должно содержать очищенное условие без сюжета.

### Обогатить все задачи

```bash
# Читает из output/, пишет в output_enriched/
poetry run python -m scripts.enrich_tasks

# Пропустить уже обогащённые (для продолжения после обрыва)
poetry run python -m scripts.enrich_tasks --skip-existing

# Перезаписать исходные файлы (обогатить in-place)
poetry run python -m scripts.enrich_tasks --in-place --skip-existing
```

| Флаг | Описание |
|------|----------|
| `-i` | Входная папка (по умолчанию `scripts/eolymp_parser/output`) |
| `-o` | Выходная папка (по умолчанию `scripts/eolymp_parser/output_enriched`) |
| `--in-place` | Перезаписывать исходные файлы |
| `--skip-existing` | Пропускать файлы с уже заполненным `enriched_statement` |
| `-d` | Задержка между запросами в секундах (по умолчанию `0.5`) |
| `-n` | Максимальное количество задач для обогащения |

---

## Загрузка задач в сервис

Скрипт `scripts/upload_tasks.py` читает обогащённые файлы из `output_enriched/` и отправляет их через `POST /tasks`. Требует запущенного сервиса и учётные данные администратора.

**Идемпотентность:** номера уже отправленных задач сохраняются в `scripts/eolymp_parser/uploaded.json`. При повторном запуске эти задачи пропускаются.

### Проверка на маленьком примере

```bash
# Отправить 3 задачи
poetry run python scripts/upload_tasks.py --username admin --password secret -n 3
```

Убедитесь, что в `uploaded.json` появились номера. Повторный запуск той же команды покажет `Skip (already uploaded)` для этих задач.

### Загрузить все задачи

```bash
# Все задачи из output_enriched/
poetry run python scripts/upload_tasks.py --username admin --password secret

# Нестандартный адрес сервиса
poetry run python scripts/upload_tasks.py --username admin --password secret --url http://localhost:8000
```

| Флаг | Описание |
|------|----------|
| `--username` | Логин администратора (обязательно) |
| `--password` | Пароль администратора (обязательно) |
| `--url` | Базовый URL сервиса (по умолчанию `http://localhost:8000`) |
| `-i` | Папка с обогащёнными файлами (по умолчанию `scripts/eolymp_parser/output_enriched`) |
| `--state` | Файл состояния (по умолчанию `scripts/eolymp_parser/uploaded.json`) |
| `-d` | Задержка между запросами в секундах (по умолчанию `0.3`) |
| `-n` | Максимальное количество задач для загрузки |

---

## Выходной формат

Файлы `problem_{N}.json` в папке вывода:

```json
{
  "number": 123,
  "url": "https://eolymp.com/en/problems/123",
  "statement": {
    "title": "Number of trailing zeros in factorial",
    "time_limit": "1s",
    "memory_limit": "128 MB",
    "sections": {
      "description": ["Find the number of trailing zeros in n!."],
      "input": ["The input contains a single integer n (1≤n≤2⋅10^9)."],
      "output": ["Print the number of trailing zeros in n!."]
    }
  },
  "editorial": {
    "content": "The factorial of an integer n is the product of..."
  }
}
```
