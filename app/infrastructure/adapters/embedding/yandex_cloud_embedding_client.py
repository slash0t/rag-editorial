import httpx

from app.domain.services.embedding_client import EmbeddingClient
from app.settings.yandex_cloud import YandexCloudConfig


class YandexCloudEmbeddingClient(EmbeddingClient):
    def __init__(self, config: YandexCloudConfig) -> None:
        self._config = config
        self._model_uri = f"emb://{config.folder}/{config.embedding_model}/latest"
        self._headers = {
            "Authorization": f"Api-Key {config.api_key}",
            "x-folder-id": config.folder,
            "Content-Type": "application/json",
        }

    async def embed(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient() as client:
            results = []
            for text in texts:
                response = await client.post(
                    self._config.embedding_url,
                    headers=self._headers,
                    json={"modelUri": self._model_uri, "text": text},
                )
                response.raise_for_status()
                results.append(response.json()["embedding"])
            return results
