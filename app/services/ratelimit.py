from uuid import uuid4

from app.core.config import settings


class RateLimiter:
    """基于 Redis 有序集合的滑动窗口限流器。

    每个 key 维护一份请求时间戳的 sorted set：每次请求先剔除窗口外的旧条目，
    再统计剩余数量，超过阈值即拒绝。相比固定窗口，它没有窗口边界处的突刺问题。
    用 pipeline 把多条命令打包，减少网络往返。
    """

    def __init__(self, redis, limit: int | None = None, window: int | None = None) -> None:
        self.redis = redis
        self.limit = limit if limit is not None else settings.rate_limit_requests
        self.window = window if window is not None else settings.rate_limit_window_seconds

    async def hit(self, key: str) -> tuple[bool, int]:
        import time

        now = time.time()
        window_start = now - self.window
        redis_key = f"ratelimit:{key}"

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(redis_key, 0, window_start)
        pipe.zadd(redis_key, {uuid4().hex: now})
        pipe.zcard(redis_key)
        pipe.expire(redis_key, self.window)
        _, _, count, _ = await pipe.execute()

        allowed = count <= self.limit
        remaining = max(0, self.limit - count)
        return allowed, remaining
