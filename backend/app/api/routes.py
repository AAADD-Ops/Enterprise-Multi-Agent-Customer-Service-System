from __future__ import annotations
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage

from app.agents.graph import get_graph
from app.agents.state import AgentState
from app.memory.session_memory import get_session_memory
from app.memory.user_profile import get_user_profile
from app.context.manager import get_sliding_window, get_context_compressor
from app.config import settings
from app.rag.ingestion import ingest_documents

router = APIRouter(prefix="/api/v1")


class ChatRequest(BaseModel):
    message: str = Field(..., description="用户消息")
    session_id: str | None = Field(None, description="会话ID，不传则创建新会话")
    user_id: str = Field("anonymous", description="用户ID")


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    routes: list[str] = []
    need_human: bool = False


class IngestRequest(BaseModel):
    directory: str | None = Field(None, description="文档目录路径")


class IngestResponse(BaseModel):
    chunks_ingested: int


class SessionMeta(BaseModel):
    session_id: str
    title: str
    created_at: str


class SessionListResponse(BaseModel):
    sessions: list[SessionMeta]


class SessionHistoryResponse(BaseModel):
    session_id: str
    messages: list[dict]


def _dict_to_langchain(msg: dict):
    role = msg.get("role", "user")
    content = msg.get("content", "")
    if role == "assistant":
        return AIMessage(content=content)
    return HumanMessage(content=content)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or uuid.uuid4().hex[:16]
    is_new = request.session_id is None
    session_memory = get_session_memory()
    user_profile = get_user_profile()

    prev_messages = await session_memory.get_messages(session_id)
    await user_profile.get_profile(request.user_id)

    history = [_dict_to_langchain(m) for m in prev_messages[-10:]]
    history.append(HumanMessage(content=request.message))

    # === 改动1: 滑动窗口截断（Token超限时自动截尾）===
    window = get_sliding_window()
    if window.estimate_tokens(history) > settings.summary_trigger_tokens:
        history = window.apply(history)

    graph = get_graph(checkpointer=None)

    # === 改动2: 注入历史摘要到 state ===
    compressor = get_context_compressor()
    history_summary = compressor.get_summary(session_id)

    initial_state: AgentState = {
        "messages": history,
        "session_id": session_id,
        "user_id": request.user_id,
        "routes": [],
        "retrieved_docs": [],
        "tool_calls": [],
        "tool_results": [],
        "need_human": False,
        "summary": history_summary,
        "error": "",
    }

    config = {"configurable": {"thread_id": session_id + "_" + uuid.uuid4().hex[:8]}}

    try:
        result = await graph.ainvoke(initial_state, config=config, stream_mode="values")

        reply = ""
        for msg in reversed(result.get("messages", [])):
            if hasattr(msg, "content") and msg.content and msg.type == "ai":
                reply = msg.content
                break

        await session_memory.append_message(session_id, "user", request.message)
        if reply:
            await session_memory.append_message(session_id, "assistant", reply)

        if is_new:
            title = request.message[:20] + ("..." if len(request.message) > 20 else "")
            await session_memory.register_session(request.user_id, session_id, title)

        routes = result.get("routes", ["knowledge"])
        for r in routes:
            await user_profile.add_tag(request.user_id, r)
        await user_profile.update_profile(request.user_id, {"last_interaction": datetime.now().isoformat()})

        if compressor.needs_compression(result.get("messages", [])):
            await compressor.compress(session_id, result.get("messages", []))

        return ChatResponse(
            session_id=session_id,
            reply=reply or "抱歉，处理您的请求时出现了一些问题，请稍后再试。",
            routes=routes,
            need_human=result.get("need_human", False),
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(user_id: str = Query("anonymous")):
    memory = get_session_memory()
    sessions = await memory.get_user_sessions(user_id)
    return SessionListResponse(
        sessions=[SessionMeta(**s) for s in sessions]
    )


@router.get("/sessions/{session_id}", response_model=SessionHistoryResponse)
async def get_session_history(session_id: str):
    memory = get_session_memory()
    messages = await memory.get_messages(session_id)
    return SessionHistoryResponse(session_id=session_id, messages=messages)


@router.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest):
    count = await ingest_documents(request.directory)
    return IngestResponse(chunks_ingested=count)


@router.get("/health")
async def health():
    return {"status": "ok", "service": "enterprise-customer-service"}
    