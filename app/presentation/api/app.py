from contextlib import asynccontextmanager

from fastapi import FastAPI

from utils.env import load_env

from app.container import APP_CONTAINER
from app.infrastructure.adapters.qdrant.collection_initializer import (
    ensure_collection_exists,
)
from app.presentation.api.routers.auth import router as auth_router  # noqa: E402
from app.presentation.api.routers.query import router as query_router  # noqa: E402
from app.presentation.api.routers.task import router as task_router  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    qdrant_client = APP_CONTAINER.qdrant_client()
    qdrant_config = APP_CONTAINER.qdrant_config()
    await ensure_collection_exists(qdrant_client, qdrant_config)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="RAG Algo Solver",
        version="0.1.0",
        root_path="/api",
        lifespan=lifespan,
    )
    app.include_router(auth_router)
    app.include_router(query_router)
    app.include_router(task_router)
    return app


load_env()

app = create_app()
