import uuid

from qdrant_client import AsyncQdrantClient

from app.domain.models.query import SimilarTask
from app.domain.services.embedding_client import EmbeddingClient
from app.domain.services.similar_task_searcher import SimilarTaskSearcher
from app.settings.qdrant import QdrantConfig


class QdrantSimilarTaskSearcher(SimilarTaskSearcher):
    def __init__(
        self,
        client: AsyncQdrantClient,
        embedding_client: EmbeddingClient,
        config: QdrantConfig,
    ) -> None:
        self._client = client
        self._embedding_client = embedding_client
        self._config = config

    async def search(self, query_text: str) -> list[SimilarTask]:
        vectors = await self._embedding_client.embed([query_text])
        query_vector = vectors[0]

        results = await self._client.query_points(
            collection_name=self._config.collection_name,
            query=query_vector,
            limit=self._config.search_limit,
            with_payload=True,
        )

        return [
            SimilarTask(
                task_id=uuid.UUID(point.payload["task_id"]),
                title=point.payload["title"],
                task_text=point.payload["text"],
                solution=point.payload.get("solution", ""),
            )
            for point in results.points
        ]
