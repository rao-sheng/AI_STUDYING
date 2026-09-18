from fastapi import FastAPI,status,HTTPException,Query,Response
from schemas import AskResponse,TaskCreate,TaskResponse,TaskUpdate,TaskStatus,ChatRequest,ChatResponse
from datetime import datetime,timezone
from store import get_task,get_connection,create_task,init_db,list_tasks,update_task,delete_task
from contextlib import asynccontextmanager
from llm_practice import ask_model
import httpx
from chat_service import reply_with_history
from rag_practice import load_or_build_chunks,answer_question
from tool_practice import run_agent
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    app.state.knowledge_chunks = load_or_build_chunks()
    print("启动阶段：知识库加载完成")
    yield

app = FastAPI(
    title="WorkMate API",
    lifespan=lifespan,
)

@app.get("/health")
def get_health():
    return {"status":"ok"}

@app.post("/tasks",status_code=status.HTTP_201_CREATED,response_model=TaskResponse)
def create_tasks(task:TaskCreate):
    
    now=datetime.now(timezone.utc).isoformat()
    return create_task(task.title, task.description,
                 task.status.value, now, now)
    
@app.get("/tasks/{task_id}",response_model=TaskResponse)
def get_task_byid(task_id:int):
    task=get_task(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return task 

@app.get("/tasks",response_model=list[TaskResponse])
def get_tasks(task_status:TaskStatus|None=Query(default=None,alias="status")):
    status_value = None if task_status is None else task_status.value
    return list_tasks(status_value)

@app.delete("/tasks/{task_id}",
            status_code=status.HTTP_204_NO_CONTENT)
def delete_task_by_id(task_id:int):
    deleted=delete_task(task_id)
   
    if  not deleted:
        raise HTTPException(status_code=404,
                            detail="Task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task_by_id(task_id: int, task: TaskUpdate):
    update_data = task.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="At least one field must be provided",
        )

    if "title" in update_data and update_data["title"] is None:
        raise HTTPException(
            status_code=422,
            detail="title cannot be null",
        )

    if "status" in update_data and update_data["status"] is None:
        raise HTTPException(
            status_code=422,
            detail="status cannot be null",
        )
    #这里进行了一个格式转换， TaskStatus.DONE  →  "done"
    if "status" in update_data:
        update_data["status"] = update_data["status"].value

    now = datetime.now(timezone.utc).isoformat()
    updated_task = update_task(task_id, update_data, now)

    if updated_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return updated_task


@app.post("/ask")
def answer_endpoint(body:AskResponse):
    question=body.question.strip()
    if not question:
        raise HTTPException(
            status_code=422,
            detail="问题不能为空"
        )
    try:
        knowledge_chunks = app.state.knowledge_chunks
        result = answer_question(question, knowledge_chunks)
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="模型服务请求超时，请稍后重试",
        )

    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=502,
            detail="模型服务返回异常，请稍后重试",
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="无法连接模型服务，请稍后重试",
        )

    return result

@app.post("/agent/chat")
def agent_chat(body:AskResponse):
    question=body.question.strip()
    if not question:
        raise HTTPException(
            status_code=422,
            detail="问题不能为空"
        )
    try:
        answer=run_agent(
            question=question,
            knowledge_chunks=app.state.knowledge_chunks,
            max_rounds=3
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="模型服务请求超时，请稍后重试",
        )

    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=502,
            detail="模型服务返回异常，请稍后重试",
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="无法连接模型服务，请稍后重试",
        )

    return {"answer": answer}


@app.post("/chat",response_model=ChatResponse)
def chat(request:ChatRequest):
    question=request.question.strip()
    conversation_id=request.conversation_id.strip()
    if not question:
        raise HTTPException(
            status_code=422,
            detail="问题不能只含空白字符"
        )
    if not conversation_id:
        raise HTTPException(
            status_code=422,
            detail="会话编号不能只包含空白字符"
        )
    try:
        answer=reply_with_history(conversation_id,question)

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="响应超时，请稍后重试"
        )
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=502,
            detail="服务模型返回错误"
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="连接服务模型失败"
        )
    return ChatResponse(conversation_id=conversation_id,answer=answer)