from pydantic_settings import SettingsConfigDict, BaseSettings


class YandexCloudConfig(BaseSettings):
    api_key: str
    folder: str
    model: str
    temperature: float = 0.3
    max_output_tokens: int = 500
    base_url: str = "https://ai.api.cloud.yandex.net/v1"
    embedding_model: str = "text-search-doc"
    embedding_url: str = (
        "https://llm.api.cloud.yandex.net/foundationModels/v1/textEmbedding"
    )

    model_config = SettingsConfigDict(env_prefix="yandex_cloud_")
