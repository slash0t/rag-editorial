from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TaskCreateRequest(BaseModel):
    title: str
    text: str
    task_url: str | None = None
    solution: str | None = None
    solution_url: str | None = None
    comment: str | None = None


class TaskUpdateRequest(BaseModel):
    title: str
    text: str
    task_url: str | None = None
    solution: str | None = None
    solution_url: str | None = None
    comment: str | None = None


class TaskResponse(BaseModel):
    id: UUID
    title: str
    text: str
    task_url: str | None = None
    solution: str | None = None
    solution_url: str | None = None
    comment: str | None = None
    created_at: datetime


class TaskPaginatedResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    page: int
    size: int


class SimilarTaskResponse(BaseModel):
    id: UUID
    title: str
    task_url: str | None = None
    solution_url: str | None = None
