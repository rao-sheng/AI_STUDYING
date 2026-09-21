from fastapi import FastAPI, HTTPException
from schemas import AskResponse, ChatRequest, ChatResponse
from store import init_db
from contextlib import asynccontextmanager
import httpx
from chat_service import reply_with_history
from rag_practice import load_or_build_chunks,answer_question
from tool_practice import run_agent
from app.api.health import router as health_router
from app.api.tasks import router as tasks_router
from app.api.meta import router as meta_router
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

app.include_router(health_router)
app.include_router(tasks_router)
app.include_router(meta_router)

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
