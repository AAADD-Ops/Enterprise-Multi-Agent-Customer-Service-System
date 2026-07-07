from __future__ import annotations
import json
from typing import Optional, Iterator, AsyncIterator
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    CheckpointTuple,
    Checkpoint,
)
import redis.asyncio as aioredis
from app.config import settings


class RedisCheckpointer(BaseCheckpointSaver):
    def __init__(self):
        super().__init__()
        self._redis: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    def _checkpoint_key(self, thread_id: str, checkpoint_ns: str = "", checkpoint_id: str = "") -> str:
        return f"checkpoint:{thread_id}:{checkpoint_ns}:{checkpoint_id}"

    async def aget_tuple(self, config: dict) -> Optional[CheckpointTuple]:
        redis = await self._get_redis()
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")
        checkpoint_id = config.get("configurable", {}).get("checkpoint_id", "")

        if not checkpoint_id:
            pattern = f"checkpoint:{thread_id}:{checkpoint_ns}:*"
            keys: list = []
            async for key in redis.scan_iter(match=pattern):
                keys.append(key)
            if not keys:
                return None
            keys.sort(reverse=True)
            checkpoint_id = keys[0].rsplit(":", 1)[-1]

        key = self._checkpoint_key(thread_id, checkpoint_ns, checkpoint_id)
        data = await redis.get(key)
        if not data:
            return None

        saved = json.loads(data)
        return CheckpointTuple(
            config=config,
            checkpoint=saved["checkpoint"],
            metadata=saved.get("metadata", {}),
            parent_config=saved.get("parent_config"),
        )

    async def aput(
        self,
        config: dict,
        checkpoint: Checkpoint,
        metadata: dict,
        new_versions: dict,
    ) -> dict:
        redis = await self._get_redis()
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")
        checkpoint_id = checkpoint.get("id", "")

        key = self._checkpoint_key(thread_id, checkpoint_ns, checkpoint_id)
        await redis.setex(
            key,
            settings.redis_session_ttl,
            json.dumps({
                "checkpoint": checkpoint,
                "metadata": metadata,
                "parent_config": config.get("configurable", {}),
            }, default=str),
        )
        return config

    def get_tuple(self, config: dict) -> Optional[CheckpointTuple]:
        raise NotImplementedError("Use async version: aget_tuple")

    def put(self, config: dict, checkpoint: Checkpoint, metadata: dict, new_versions: dict) -> dict:
        raise NotImplementedError("Use async version: aput")

    def list(self, config: dict, filter: Optional[dict] = None, before: Optional[dict] = None, limit: Optional[int] = None) -> Iterator[CheckpointTuple]:
        raise NotImplementedError("Use async version")

    async def alist(self, config: dict, filter: Optional[dict] = None, before: Optional[dict] = None, limit: Optional[int] = None) -> AsyncIterator[CheckpointTuple]:
        if limit == 0:
            return
        redis = await self._get_redis()
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")
        pattern = f"checkpoint:{thread_id}:{checkpoint_ns}:*"
        keys: list = []
        async for key in redis.scan_iter(match=pattern):
            keys.append(key)
        keys.sort(reverse=True)
        yielded = 0
        for k in keys:
            if limit and yielded >= limit:
                return
            data = await redis.get(k)
            if not data:
                continue
            saved = json.loads(data)
            yield CheckpointTuple(
                config=config,
                checkpoint=saved["checkpoint"],
                metadata=saved.get("metadata", {}),
                parent_config=saved.get("parent_config"),
            )
            yielded += 1


_checkpointer: Optional[RedisCheckpointer] = None


def get_redis_checkpointer() -> RedisCheckpointer:
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = RedisCheckpointer()
    return _checkpointer
