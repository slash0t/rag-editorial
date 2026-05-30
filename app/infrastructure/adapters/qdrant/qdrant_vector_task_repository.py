import uuid

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointIdsList, PointStruct

from app.domain.repositories.vector_task import VectorTaskRepository
from app.domain.services.embedding_client import EmbeddingClient
from app.infrastructure.database.models import Task
from app.settings.qdrant import QdrantConfig


class QdrantVectorTaskRepository(VectorTaskRepository):
    def __init__(
        self,
        client: AsyncQdrantClient,
        embedding_client: EmbeddingClient,
        config: QdrantConfig,
    ) -> None:
        self._client = client
        self._embedding_client = embedding_client
        self._config = config

    async def upsert(self, task: Task) -> None:
        embed_text = f"{task.title}\n{task.text}"
        vectors = await self._embedding_client.embed([embed_text])

        point = PointStruct(
            id=str(task.id),
            vector=vectors[0],
            payload={
                "task_id": str(task.id),
                "title": task.title,
                "text": task.text,
                "solution": task.solution or "",
            },
        )

        await self._client.upsert(
            collection_name=self._config.collection_name,
            points=[point],
        )

    async def delete(self, task_id: uuid.UUID) -> None:
        await self._client.delete(
            collection_name=self._config.collection_name,
            points_selector=PointIdsList(points=[str(task_id)]),
        )
