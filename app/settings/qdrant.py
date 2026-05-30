from pydantic_settings import BaseSettings, SettingsConfigDict


class QdrantConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="qdrant_")

    host: str = "localhost"
    port: int = 6333
    collection_name: str = "tasks"
    embedding_model: str = "BAAI/bge-m3"
    search_limit: int = 3
