from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Response, status

from schemas import TaskCreate, TaskResponse, TaskStatus, TaskUpdate
from store import create_task, delete_task, get_task, list_tasks, update_task


router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TaskResponse)
def create_tasks(task: TaskCreate):
    now = datetime.now(timezone.utc).isoformat()
    return create_task(
        task.title,
        task.description,
        task.status.value,
        now,
        now,
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task_by_id(task_id: int):
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.get("", response_model=list[TaskResponse])
def get_tasks(
    task_status: TaskStatus | None = Query(default=None, alias="status"),
):
    status_value = None if task_status is None else task_status.value
    return list_tasks(status_value)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_by_id(task_id: int):
    deleted = delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task_by_id(task_id: int, task: TaskUpdate):
    update_data = task.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one field must be provided")

    if update_data.get("title") is None and "title" in update_data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="title cannot be null")

    if update_data.get("status") is None and "status" in update_data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="status cannot be null")

    if "status" in update_data:
        update_data["status"] = update_data["status"].value

    now = datetime.now(timezone.utc).isoformat()
    updated_task = update_task(task_id, update_data, now)
    if updated_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return updated_task
