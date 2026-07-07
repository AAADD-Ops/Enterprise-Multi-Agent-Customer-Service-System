import json
from typing import Optional
import redis.asyncio as aioredis
from app.config import settings


class SessionMemory:
    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    def _session_key(self, session_id: str) -> str:
        return f"session:{session_id}"

    def _session_index_key(self, user_id: str) -> str:
        return f"session_index:{user_id}"

    async def save_messages(self, session_id: str, messages: list[dict]) -> None:
        redis = await self._get_redis()
        key = self._session_key(session_id)
        await redis.setex(key, settings.redis_session_ttl, json.dumps(messages, ensure_ascii=False))

    async def get_messages(self, session_id: str) -> list[dict]:
        redis = await self._get_redis()
        key = self._session_key(session_id)
        data = await redis.get(key)
        if data:
            return json.loads(data)
        return []

    async def append_message(self, session_id: str, role: str, content: str) -> None:
        messages = await self.get_messages(session_id)
        messages.append({"role": role, "content": content})
        await self.save_messages(session_id, messages)

    async def clear_session(self, session_id: str) -> None:
        redis = await self._get_redis()
        await redis.delete(self._session_key(session_id))

    async def get_session_context(self, session_id: str, max_messages: int = 10) -> list[dict]:
        messages = await self.get_messages(session_id)
        return messages[-max_messages:]

    async def register_session(self, user_id: str, session_id: str, title: str = "") -> None:
        redis = await self._get_redis()
        key = self._session_index_key(user_id)
        sessions = await self.get_user_sessions(user_id)
        existing = [s for s in sessions if s["session_id"] != session_id]
        existing.insert(0, {
            "session_id": session_id,
            "title": title,
            "created_at": "",
        })
        await redis.setex(key, settings.redis_session_ttl, json.dumps(existing, ensure_ascii=False))

    async def get_user_sessions(self, user_id: str) -> list[dict]:
        redis = await self._get_redis()
        key = self._session_index_key(user_id)
        data = await redis.get(key)
        if data:
            return json.loads(data)
        return []


_session_memory: Optional[SessionMemory] = None


def get_session_memory() -> SessionMemory:
    global _session_memory
    if _session_memory is None:
        _session_memory = SessionMemory()
    return _session_memory
