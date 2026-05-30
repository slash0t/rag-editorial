from app.container import APP_CONTAINER
from app.domain.models.query import SimilarTask
from app.infrastructure.database.models import ProcessingStatus
from app.presentation.streams.app import broker, kafka_config
from app.presentation.streams.schemas.processing import ProcessingMessage


@broker.subscriber(kafka_config.topic_compose)
async def compose_handler(
    msg: ProcessingMessage,
) -> None:
    processing_repo = APP_CONTAINER.processing_repo()
    context_builder = APP_CONTAINER.context_builder()
    query_repo = APP_CONTAINER.query_repo()

    processing = await processing_repo.get(msg.processing_id)

    try:
        query = await query_repo.get_with_similar_tasks(processing.query_id)

        similar_tasks = [
            SimilarTask(
                task_id=task.id,
                title=task.title,
                task_text=task.text,
                solution=task.solution or "",
            )
            for task in query.similar_tasks
        ]

        task_context = await context_builder.build(similar_tasks)

        processing.task_context = task_context
        processing.status = ProcessingStatus.GENERATING
        await processing_repo.update(processing)

        await broker.publish(
            ProcessingMessage(processing_id=processing.id).model_dump(mode="json"),
            topic=kafka_config.topic_generate,
        )
    except Exception as e:
        processing.status = ProcessingStatus.FAILED
        processing.error_message = str(e)
        await processing_repo.update(processing)
