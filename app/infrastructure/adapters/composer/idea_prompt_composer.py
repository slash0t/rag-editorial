from app.domain.models.query import PreparedQuery
from app.domain.services.prompt_composer import PromptComposer

_SYSTEM = """\
Ты помощник для разбора алгоритмических задач. Твоя цель — коротко объяснить ключевую идею решения.

Правила:
- Объясни только суть: какой подход использовать и почему он работает для этой задачи.
- Не объясняй базовые алгоритмические техники (бинарный поиск, ДП, дерево отрезков и т.д.) — просто используй их названия.
- Никакого кода.
- Без лишних вступлений и выводов — сразу по делу.
- Не пересказывай условие задачи.
- Не злоупотребляй форматированием.
- Язык: русский.\
"""


class IdeaPromptComposer(PromptComposer):
    async def compose(
        self,
        original_text: str,
        enriched_text: str,
        task_context: str,
    ) -> PreparedQuery:
        parts = [_SYSTEM, f"Задача:\n{enriched_text}"]
        if task_context:
            parts.append(f"Похожие задачи для ориентира:\n{task_context}")
        parts.append("Объясни ключевую идею решения.")
        return PreparedQuery(text="\n\n".join(parts))