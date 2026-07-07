from __future__ import annotations
from typing import TypedDict, Annotated, Sequence, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


def keep_last(existing: str, new: str) -> str:
    """Reducer: 并行冲突时保留最后一个非空值。"""
    return new or existing or ""


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    session_id: str
    user_id: str
    routes: list[str]
    retrieved_docs: list[dict[str, Any]]
    tool_calls: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    need_human: bool
    summary: Annotated[str, keep_last]
    error: Annotated[str, keep_last]
