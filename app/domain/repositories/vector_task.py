import uuid
from abc import ABC, abstractmethod

from app.infrastructure.database.models import Task


class VectorTaskRepository(ABC):
    @abstractmethod
    async def upsert(self, task: Task) -> None: ...

    @abstractmethod
    async def delete(self, task_id: uuid.UUID) -> None: ...
