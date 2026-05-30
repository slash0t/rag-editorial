from dependency_injector import containers, providers
from faststream.kafka import KafkaBroker
from qdrant_client import AsyncQdrantClient

from app.domain.services.auth_service import AuthService
from app.infrastructure.adapters.composer.plain_prompt_composer import (
    PlainPromptComposer,
)
from app.infrastructure.adapters.context.plain_task_context_builder import (
    PlainTaskContextBuilder,
)
from app.infrastructure.adapters.embedding.bge_m3_embedding_client import (
    BgeM3EmbeddingClient,
)
from app.infrastructure.adapters.enricher.passthrough_query_enricher import (
    PassthroughQueryEnricher,
)
from app.infrastructure.adapters.llm.yandex_cloud_llm_client import YandexCloudLLMClient
from app.infrastructure.adapters.publisher.kafka_publisher import KafkaPublisher
from app.infrastructure.adapters.qdrant.qdrant_similar_task_searcher import (
    QdrantSimilarTaskSearcher,
)
from app.infrastructure.adapters.qdrant.qdrant_vector_task_repository import (
    QdrantVectorTaskRepository,
)
from app.infrastructure.database.repositories.query import SQLQueryRepository
from app.infrastructure.database.repositories.query_processing import (
    SQLQueryProcessingRepository,
)
from app.infrastructure.database.repositories.task import SQLTaskRepository
from app.infrastructure.database.repositories.user import SQLUserRepository
from app.infrastructure.database.session import create_async_session_factory
from app.settings.jwt import JWTConfig
from app.settings.kafka import KafkaConfig
from app.settings.postgres import PostgresConfig
from app.settings.qdrant import QdrantConfig
from app.settings.yandex_cloud import YandexCloudConfig


class AppContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    yandex_cloud_config: providers.Singleton[YandexCloudConfig] = providers.Singleton(
        YandexCloudConfig
    )

    kafka_config: providers.Singleton[KafkaConfig] = providers.Singleton(KafkaConfig)

    postgres_config: providers.Singleton[PostgresConfig] = providers.Singleton(
        PostgresConfig
    )

    jwt_config: providers.Singleton[JWTConfig] = providers.Singleton(JWTConfig)

    session_factory = providers.Singleton(
        create_async_session_factory,
        config=postgres_config,
    )

    query_repo: providers.Singleton[SQLQueryRepository] = providers.Singleton(
        SQLQueryRepository,
        session_factory=session_factory,
    )

    processing_repo: providers.Singleton[SQLQueryProcessingRepository] = (
        providers.Singleton(
            SQLQueryProcessingRepository,
            session_factory=session_factory,
        )
    )

    user_repo: providers.Singleton[SQLUserRepository] = providers.Singleton(
        SQLUserRepository,
        session_factory=session_factory,
    )

    task_repo: providers.Singleton[SQLTaskRepository] = providers.Singleton(
        SQLTaskRepository,
        session_factory=session_factory,
    )

    auth_service: providers.Singleton[AuthService] = providers.Singleton(
        AuthService,
        user_repo=user_repo,
        jwt_config=jwt_config,
    )

    broker: providers.Singleton[KafkaBroker] = providers.Singleton(
        KafkaBroker, kafka_config.provided.bootstrap_servers
    )

    publisher: providers.Singleton[KafkaPublisher] = providers.Singleton(
        KafkaPublisher, bootstrap_servers=kafka_config.provided.bootstrap_servers
    )

    qdrant_config: providers.Singleton[QdrantConfig] = providers.Singleton(QdrantConfig)

    qdrant_client: providers.Singleton[AsyncQdrantClient] = providers.Singleton(
        AsyncQdrantClient,
        host=qdrant_config.provided.host,
        port=qdrant_config.provided.port,
    )

    embedding_client: providers.Singleton[BgeM3EmbeddingClient] = providers.Singleton(
        BgeM3EmbeddingClient,
        config=qdrant_config,
    )

    enricher: providers.Singleton[PassthroughQueryEnricher] = providers.Singleton(
        PassthroughQueryEnricher
    )

    searcher: providers.Singleton[QdrantSimilarTaskSearcher] = providers.Singleton(
        QdrantSimilarTaskSearcher,
        client=qdrant_client,
        embedding_client=embedding_client,
        config=qdrant_config,
    )

    vector_task_repo: providers.Singleton[QdrantVectorTaskRepository] = (
        providers.Singleton(
            QdrantVectorTaskRepository,
            client=qdrant_client,
            embedding_client=embedding_client,
            config=qdrant_config,
        )
    )

    context_builder: providers.Singleton[PlainTaskContextBuilder] = providers.Singleton(
        PlainTaskContextBuilder
    )

    composer: providers.Singleton[PlainPromptComposer] = providers.Singleton(
        PlainPromptComposer
    )

    llm_client: providers.Singleton[YandexCloudLLMClient] = providers.Singleton(
        YandexCloudLLMClient,
        yandex_cloud_config,
    )


APP_CONTAINER = AppContainer()
