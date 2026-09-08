from fastapi import FastAPI,status,HTTPException
from schemas import TaskCreate,TaskResponse,TaskUpdate
from datetime import datetime,timezone

app=FastAPI(title="WorkMate API")

tasks:dict[int,TaskResponse]={}
next_task_id=1

@app.get("/health")
def get_health():
    return {"status":"ok"}

@app.post("/tasks",status_code=status.HTTP_201_CREATED,response_model=TaskResponse)
def create_tasks(task:TaskCreate):
    global next_task_id
    now=datetime.now(timezone.utc)
    new_task=TaskResponse(
        id=next_task_id,
        title=task.title,
        description=task.description,
        created_at=now,
        updated_at=now
    )
    tasks[new_task.id]=new_task
    next_task_id +=1
    return new_task

@app.get("/tasks/{task_id}",response_model=TaskResponse)
def get_task_byid(task_id:int):
    task=tasks.get(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task
 

@app.get("/tasks",response_model=list[TaskResponse])
def get_tasks():
    return list(tasks.values())

@app.delete("/tasks/{task_id}")
def delete_task(task_id:int):
    task=tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404,detail="Task not found")
    del tasks[task_id]

@app.patch("/tasks/{task_id},response_model=TaskResponse")
def patch_tasks(task_id:int,update_data: TaskUpdate):
    task=tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404,detail="无")
    updates = update_data.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(
            status_code=422,
            detail="At least one field must be provided",
        )

    if "title" in updates:
        if updates["title"] is None:
            raise HTTPException(
                status_code=422,
                detail="Title cannot be null",
            )
        task.title = updates["title"]

    if "description" in updates:
        task.description = updates["description"]

    task.updated_at = datetime.now(timezone.utc)

    return task