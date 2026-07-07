import json
from typing import Optional
import redis.asyncio as aioredis
from app.config import settings


class UserProfile:
    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    def _profile_key(self, user_id: str) -> str:
        return f"user_profile:{user_id}"

    async def get_profile(self, user_id: str) -> dict:
        redis = await self._get_redis()
        data = await redis.get(self._profile_key(user_id))
        if data:
            return json.loads(data)
        return {
            "user_id": user_id,
            "preferences": {},
            "history_tags": [],
            "interaction_count": 0,
            "last_interaction": None,
        }

    async def update_profile(self, user_id: str, updates: dict) -> dict:
        profile = await self.get_profile(user_id)
        profile.update(updates)
        profile["interaction_count"] = profile.get("interaction_count", 0) + 1
        redis = await self._get_redis()
        await redis.set(self._profile_key(user_id), json.dumps(profile, ensure_ascii=False))
        return profile

    async def add_tag(self, user_id: str, tag: str) -> None:
        profile = await self.get_profile(user_id)
        tags = profile.get("history_tags", [])
        if tag not in tags:
            tags.append(tag)
            if len(tags) > 20:
                tags = tags[-20:]
        profile["history_tags"] = tags
        redis = await self._get_redis()
        await redis.set(self._profile_key(user_id), json.dumps(profile, ensure_ascii=False))


_profile: Optional[UserProfile] = None


def get_user_profile() -> UserProfile:
    global _profile
    if _profile is None:
        _profile = UserProfile()
    return _profile
