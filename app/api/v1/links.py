from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession, enforce_rate_limit, get_link_service
from app.core.config import settings
from app.models.link import Link
from app.schemas.link import (
    DailyClicks,
    LinkAnalytics,
    LinkCreate,
    LinkOut,
    LinkUpdate,
    ReferrerStat,
)
from app.services.links import AliasTaken, LinkService

router = APIRouter(prefix="/links", tags=["links"])

LinkServiceDep = Annotated[LinkService, Depends(get_link_service)]


def _to_out(link: Link) -> LinkOut:
    out = LinkOut.model_validate(link)
    out.short_url = f"{settings.base_url}/{link.code}"
    return out


@router.post(
    "",
    response_model=LinkOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_rate_limit)],
)
async def create_link(
    payload: LinkCreate, user: CurrentUser, service: LinkServiceDep, db: DbSession
) -> LinkOut:
    try:
        link = await service.create_link(str(payload.target_url), user.id, payload.custom_alias)
    except AliasTaken:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Alias already in use"
        ) from None
    await db.commit()
    return _to_out(link)


@router.get("", response_model=list[LinkOut])
async def list_links(
    user: CurrentUser,
    service: LinkServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[LinkOut]:
    links = await service.links.list_for_owner(user.id, limit, offset)
    return [_to_out(link) for link in links]


@router.get("/{code}", response_model=LinkOut)
async def get_link(code: str, user: CurrentUser, service: LinkServiceDep) -> LinkOut:
    link = await service.links.get_by_code(code)
    if link is None or link.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return _to_out(link)


@router.patch("/{code}", response_model=LinkOut)
async def update_link(
    code: str,
    payload: LinkUpdate,
    user: CurrentUser,
    service: LinkServiceDep,
    db: DbSession,
) -> LinkOut:
    link = await service.links.get_by_code(code)
    if link is None or link.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    if payload.target_url is not None:
        link.target_url = str(payload.target_url)
    if payload.is_active is not None:
        link.is_active = payload.is_active
    await db.commit()
    await service.invalidate_cache(code)  # 失效缓存，避免脏读
    return _to_out(link)


@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(code: str, user: CurrentUser, service: LinkServiceDep, db: DbSession) -> None:
    link = await service.links.get_by_code(code)
    if link is None or link.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    await db.delete(link)
    await db.commit()
    await service.invalidate_cache(code)


@router.get("/{code}/analytics", response_model=LinkAnalytics)
async def link_analytics(code: str, user: CurrentUser, service: LinkServiceDep) -> LinkAnalytics:
    link = await service.links.get_by_code(code)
    if link is None or link.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    daily = await service.links.daily_clicks(link.id)
    refs = await service.links.top_referrers(link.id)
    return LinkAnalytics(
        code=link.code or "",
        total_clicks=link.click_count,
        daily=[DailyClicks(day=d, count=c) for d, c in daily],
        top_referrers=[ReferrerStat(referrer=r, count=c) for r, c in refs],
    )
