from app.domain.models.query import SimilarTask
from app.domain.services.task_context_builder import TaskContextBuilder


class PlainTaskContextBuilder(TaskContextBuilder):
    async def build(self, tasks: list[SimilarTask]) -> str:
        if not tasks:
            return ""

        parts: list[str] = []
        for i, task in enumerate(tasks, 1):
            block = f"### Similar problem {i}: {task.title}\n{task.task_text}"
            if task.solution:
                block += f"\n\n**Solution:**\n{task.solution}"
            parts.append(block)

        return "\n\n---\n\n".join(parts)
