from typing import Sequence, Optional
import tiktoken
import redis
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from app.config import settings


class SlidingWindowManager:
    def __init__(self, window_size: int | None = None):
        self.window_size = window_size or settings.sliding_window_size
        self._encoder = tiktoken.get_encoding("cl100k_base")

    def apply(self, messages: Sequence[BaseMessage]) -> list[BaseMessage]:
        if len(messages) <= self.window_size:
            return list(messages)

        system_messages = [m for m in messages if isinstance(m, SystemMessage)]
        conversation = [m for m in messages if not isinstance(m, SystemMessage)]

        kept = conversation[-self.window_size:]
        return system_messages + kept

    def estimate_tokens(self, messages: Sequence[BaseMessage]) -> int:
        total = 0
        for m in messages:
            content = m.content if hasattr(m, "content") and isinstance(m.content, str) else str(m)
            total += len(self._encoder.encode(content))
        return total


class ContextCompressor:
    def __init__(self):
        self._redis = redis.from_url(settings.redis_url, decode_responses=True)

    def _summary_key(self, session_id: str) -> str:
        return f"context:summary:{session_id}"

    def needs_compression(self, messages: Sequence[BaseMessage]) -> bool:
        window = SlidingWindowManager()
        estimated = window.estimate_tokens(messages)
        return estimated > settings.summary_trigger_tokens

    async def compress(self, session_id: str, messages: Sequence[BaseMessage]) -> str:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            temperature=0,
        )

        conversation_text = "\n".join([
            f"{"用户" if isinstance(m, HumanMessage) else "客服"}: {m.content}"
            for m in messages
            if isinstance(m, (HumanMessage, AIMessage)) and isinstance(m.content, str)
        ])

        existing = await self.get_summary(session_id)

        prompt = f"""请将以下对话压缩为简洁摘要，保留关键实体、用户需求和解决状态。

已有摘要：
{existing if existing else "无"}

待压缩对话：
{conversation_text[-3000:]}

请生成更新后的摘要（200字以内）："""

        response = await llm.ainvoke([HumanMessage(content=prompt)])
        summary = response.content.strip()
        self._redis.setex(self._summary_key(session_id), settings.redis_cache_ttl, summary)
        return summary

    def get_summary(self, session_id: str) -> str:
        data = self._redis.get(self._summary_key(session_id))
        return data if data else ""


_sliding_window: SlidingWindowManager | None = None
_compressor: ContextCompressor | None = None


def get_sliding_window() -> SlidingWindowManager:
    global _sliding_window
    if _sliding_window is None:
        _sliding_window = SlidingWindowManager()
    return _sliding_window


def get_context_compressor() -> ContextCompressor:
    global _compressor
    if _compressor is None:
        _compressor = ContextCompressor()
    return _compressor
