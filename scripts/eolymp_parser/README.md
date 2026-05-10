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

## Выходной формат

Файлы `problem_{N}.json` в папке вывода:

```json
{
  "number": 123,
  "url": "https://eolymp.com/en/problems/123",
  "statement": {
    "title": "Number of trailing zeros in factorial",
    "difficulty": "Very easy",
    "time_limit": "1s",
    "memory_limit": "128 MB",
    "sections": {
      "description": ["Find the number of trailing zeros in n!."],
      "input": ["The input contains a single integer n (1≤n≤2⋅10^9)."],
      "output": ["Print the number of trailing zeros in n!."]
    },
    "examples": [
      {"input": "7", "answer": "1"},
      {"input": "12", "answer": "2"}
    ]
  },
  "editorial": {
    "content": "The factorial of an integer n is the product of..."
  }
}
```
