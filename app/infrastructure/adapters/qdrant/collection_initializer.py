from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams

from app.settings.qdrant import QdrantConfig


async def ensure_collection_exists(
    client: AsyncQdrantClient,
    config: QdrantConfig,
) -> None:
    collections = await client.get_collections()
    existing = {c.name for c in collections.collections}

    if config.collection_name not in existing:
        await client.create_collection(
            collection_name=config.collection_name,
            vectors_config=VectorParams(
                size=config.vector_size,
                distance=Distance.COSINE,
            ),
        )
