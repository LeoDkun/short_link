from collections.abc import AsyncGenerator

import redis.asyncio as redis

from app.core.config import settings

# 全局连接池客户端。decode_responses=True 让返回值直接是 str。
redis_client: redis.Redis = redis.from_url(settings.redis_url, decode_responses=True)


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    yield redis_client
