import asyncio
from functools import partial

from FlagEmbedding import BGEM3FlagModel

from app.domain.services.embedding_client import EmbeddingClient
from app.settings.qdrant import QdrantConfig


class BgeM3EmbeddingClient(EmbeddingClient):
    def __init__(self, config: QdrantConfig) -> None:
        self._model = BGEM3FlagModel(config.embedding_model, use_fp16=True)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            partial(self._model.encode, texts),
        )
        return result["dense_vecs"].tolist()
