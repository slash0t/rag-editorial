from app.domain.models.query import PreparedQuery
from app.domain.services.prompt_composer import PromptComposer


class OnlyTextPromptComposer(PromptComposer):
    async def compose(
        self,
        original_text: str,
        enriched_text: str,
        task_context: str,
    ) -> PreparedQuery:
        return PreparedQuery(text=original_text)
