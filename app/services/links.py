import hashlib
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import settings
from app.models.link import Link
from app.repositories.link import LinkRepository
from app.services import shortcode


class AliasTaken(Exception):
    pass


def _cache_key(code: str) -> str:
    return f"link:{code}"


class LinkService:
    def __init__(self, links: LinkRepository, redis) -> None:
        self.links = links
        self.redis = redis

    async def create_link(self, target_url: str, owner_id: int, custom_alias: str | None) -> Link:
        if custom_alias:
            if await self.links.code_exists(custom_alias):
                raise AliasTaken(custom_alias)
            return await self.links.create(
                code=custom_alias, target_url=target_url, owner_id=owner_id
            )
        # 自动短码：先插入（code=NULL）拿到 id，再回填 base62(id)
        link = await self.links.create(code=None, target_url=target_url, owner_id=owner_id)
        link.code = shortcode.encode(link.id)
        return link

    async def resolve(self, code: str) -> str | None:
        """cache-aside 解析短码 -> 目标 URL，重定向热点路径只读缓存。"""
        cached = await self.redis.get(_cache_key(code))
        if cached is not None:
            return cached
        link = await self.links.get_by_code(code)
        if link is None or not link.is_active:
            return None
        await self.redis.set(_cache_key(code), link.target_url, ex=settings.cache_ttl_seconds)
        return link.target_url

    async def invalidate_cache(self, code: str) -> None:
        await self.redis.delete(_cache_key(code))


async def record_click_task(
    sessionmaker: async_sessionmaker,
    code: str,
    referrer: str | None,
    user_agent: str | None,
    ip: str | None,
) -> None:
    """后台埋点任务：用独立会话写入，避免阻塞重定向响应。

    放在 BackgroundTask 里执行，重定向先返回 307，分析写入异步完成。
    高并发下可进一步替换为 Redis Streams / Kafka 做削峰。
    """
    async with sessionmaker() as session:
        repo = LinkRepository(session)
        link = await repo.get_by_code(code)
        if link is None:
            return
        ip_hash = hashlib.sha256(ip.encode()).hexdigest() if ip else None
        await repo.add_click(
            link,
            event_day=datetime.now(UTC).date(),
            referrer=referrer,
            user_agent=(user_agent or "")[:512] or None,
            ip_hash=ip_hash,
        )
        await session.commit()
