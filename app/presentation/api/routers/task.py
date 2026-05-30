from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.container import APP_CONTAINER
from app.infrastructure.database.models import Task, User
from app.presentation.api.dependencies.auth import get_current_admin
from app.presentation.api.schemas.task import (
    TaskCreateRequest,
    TaskResponse,
    TaskUpdateRequest,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    request: TaskCreateRequest,
    _current_user: User = Depends(get_current_admin),
) -> TaskResponse:
    task_repo = APP_CONTAINER.task_repo()

    task = Task(
        title=request.title,
        text=request.text,
        task_url=request.task_url,
        solution=request.solution,
        solution_url=request.solution_url,
        comment=request.comment,
    )
    task = await task_repo.create(task)

    vector_task_repo = APP_CONTAINER.vector_task_repo()
    await vector_task_repo.upsert(task)

    return TaskResponse(
        id=task.id,
        title=task.title,
        text=task.text,
        task_url=task.task_url,
        solution=task.solution,
        solution_url=task.solution_url,
        comment=task.comment,
        created_at=task.created_at,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    _current_user: User = Depends(get_current_admin),
) -> TaskResponse:
    task_repo = APP_CONTAINER.task_repo()

    task = await task_repo.get(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return TaskResponse(
        id=task.id,
        title=task.title,
        text=task.text,
        task_url=task.task_url,
        solution=task.solution,
        solution_url=task.solution_url,
        comment=task.comment,
        created_at=task.created_at,
    )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    request: TaskUpdateRequest,
    _current_user: User = Depends(get_current_admin),
) -> TaskResponse:
    task_repo = APP_CONTAINER.task_repo()

    task = await task_repo.get(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    task.title = request.title
    task.text = request.text
    task.task_url = request.task_url
    task.solution = request.solution
    task.solution_url = request.solution_url
    task.comment = request.comment

    task = await task_repo.update(task)

    vector_task_repo = APP_CONTAINER.vector_task_repo()
    await vector_task_repo.upsert(task)

    return TaskResponse(
        id=task.id,
        title=task.title,
        text=task.text,
        task_url=task.task_url,
        solution=task.solution,
        solution_url=task.solution_url,
        comment=task.comment,
        created_at=task.created_at,
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    _current_user: User = Depends(get_current_admin),
) -> None:
    task_repo = APP_CONTAINER.task_repo()

    deleted = await task_repo.delete(task_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    vector_task_repo = APP_CONTAINER.vector_task_repo()
    await vector_task_repo.delete(task_id)
