from app.container import APP_CONTAINER
from app.infrastructure.database.models import ProcessingStatus, QuerySimilarTask
from app.presentation.streams.app import broker, kafka_config
from app.presentation.streams.schemas.processing import ProcessingMessage


@broker.subscriber(kafka_config.topic_search)
async def search_handler(
    msg: ProcessingMessage,
) -> None:
    processing_repo = APP_CONTAINER.processing_repo()
    searcher = APP_CONTAINER.searcher()
    session_factory = APP_CONTAINER.session_factory()

    processing = await processing_repo.get(msg.processing_id)

    try:
        similar_tasks = await searcher.search(processing.enriched_text)

        if similar_tasks:
            async with session_factory() as session:
                for st in similar_tasks:
                    link = QuerySimilarTask(
                        query_id=processing.query_id,
                        task_id=st.task_id,
                    )
                    session.add(link)
                await session.commit()

        processing.status = ProcessingStatus.COMPOSING
        await processing_repo.update(processing)

        await broker.publish(
            ProcessingMessage(processing_id=processing.id).model_dump(mode="json"),
            topic=kafka_config.topic_compose,
        )
    except Exception as e:
        processing.status = ProcessingStatus.FAILED
        processing.error_message = str(e)
        await processing_repo.update(processing)
