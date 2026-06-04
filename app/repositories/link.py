from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import ClickEvent, Link


class LinkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, code: str | None, target_url: str, owner_id: int) -> Link:
        link = Link(code=code, target_url=target_url, owner_id=owner_id)
        self.session.add(link)
        await self.session.flush()  # 触发 INSERT，拿到自增 id
        return link

    async def get_by_code(self, code: str) -> Link | None:
        result = await self.session.execute(select(Link).where(Link.code == code))
        return result.scalar_one_or_none()

    async def get_by_id(self, link_id: int) -> Link | None:
        return await self.session.get(Link, link_id)

    async def list_for_owner(self, owner_id: int, limit: int, offset: int) -> list[Link]:
        result = await self.session.execute(
            select(Link)
            .where(Link.owner_id == owner_id)
            .order_by(Link.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def code_exists(self, code: str) -> bool:
        result = await self.session.execute(select(Link.id).where(Link.code == code))
        return result.first() is not None

    async def add_click(
        self,
        link: Link,
        event_day: date,
        referrer: str | None,
        user_agent: str | None,
        ip_hash: str | None,
    ) -> None:
        link.click_count += 1
        self.session.add(
            ClickEvent(
                link_id=link.id,
                event_day=event_day,
                referrer=referrer,
                user_agent=user_agent,
                ip_hash=ip_hash,
            )
        )

    async def daily_clicks(self, link_id: int) -> list[tuple[date, int]]:
        result = await self.session.execute(
            select(ClickEvent.event_day, func.count())
            .where(ClickEvent.link_id == link_id)
            .group_by(ClickEvent.event_day)
            .order_by(ClickEvent.event_day)
        )
        return [(row[0], row[1]) for row in result.all()]

    async def top_referrers(self, link_id: int, limit: int = 5) -> list[tuple[str, int]]:
        result = await self.session.execute(
            select(ClickEvent.referrer, func.count())
            .where(ClickEvent.link_id == link_id, ClickEvent.referrer.is_not(None))
            .group_by(ClickEvent.referrer)
            .order_by(func.count().desc())
            .limit(limit)
        )
        return [(row[0], row[1]) for row in result.all()]
